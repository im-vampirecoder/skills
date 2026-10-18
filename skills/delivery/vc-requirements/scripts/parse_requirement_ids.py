"""Shared parser for named requirement IDs in a vc tracking repo.

Reads every feature PRD under artifacts/ (unassigned `artifacts/<slug>/prd.md`
and epic-assigned `artifacts/epic-*/feature-<slug>/prd.md`), the requirement
definitions inside each PRD's `## Requirements` section, and every citation of
an ID anywhere under artifacts/ (stories, test cases, mockups, other PRDs).

ID format: <FR|NFR|BR|ERR>-<feature-slug>.<name>, e.g. FR-checkout.pay-with-stripe.
Python 3 stdlib only. Imported by the other scripts in this folder.
"""

import hashlib
import re
from pathlib import Path

TYPES = ("FR", "NFR", "BR", "ERR")
SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ID_RE = re.compile(rf"\b(FR|NFR|BR|ERR)-({SLUG})\.({SLUG})\b")
# Anything that starts like an ID; used to spot malformed ones.
LOOSE_ID_RE = re.compile(r"(?<![\w-])(FR|NFR|BR|ERR)-[A-Za-z0-9][A-Za-z0-9._-]*")
DEF_BULLET_RE = re.compile(rf"^\s*-\s+\*\*((?:FR|NFR|BR|ERR)-{SLUG}\.{SLUG}):?\*\*:?\s*(?:\(([^)]*)\))?:?\s*(.*)$")
DEF_ROW_RE = re.compile(rf"^\s*\|\s*((?:FR|NFR|BR|ERR)-{SLUG}\.{SLUG})\s*\|(.*)$")
REPLACED_RE = re.compile(rf"Replaced by\s+((?:FR|NFR|BR|ERR)-{SLUG}\.{SLUG})")
SUPERSEDED_RE = re.compile(r"^\s*>\s*Superseded by\s+(\S+?)\s+on\s+(\S+)")
CLARIFIED_RE = re.compile(r"^\s*>\s*Clarified on\s+(\S+?):\s*(.*)$")
RETIRED_MARK_RE = re.compile(rf"\s*Retired\.?(?:\s*Replaced by\s+(?:FR|NFR|BR|ERR)-{SLUG}\.{SLUG}\.?)?")
PRIORITY_RE = re.compile(r"^P[0-2]$")
ALIAS_RE = re.compile(r"^(FR|NFR|BR|ERR)\d+$")
MAX_NAME = 40
DRAFT_NAME = "prd.draft.md"
SKIP_FILES = ("requirements-current.md", DRAFT_NAME)



def read_frontmatter(text):
    """Minimal YAML subset: `key: value` and `key: [a, b]` lines only."""
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    for line in text[3:end if end != -1 else 0].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        value = value.split(" #", 1)[0].strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = None if value in ("", "null", "~") else value.strip("'\"")
    return meta


def feature_slug_of(prd_path):
    folder = prd_path.parent.name
    return folder[len("feature-"):] if folder.startswith("feature-") else folder


def find_feature_prds(root, drafts=False):
    """Feature PRD paths. With drafts=True a `prd.draft.md` (an in-progress
    vc-prd write) stands in for its folder's `prd.md`, or adds a new feature."""
    artifacts, out = Path(root) / "artifacts", {}
    for name in ("prd.md", DRAFT_NAME) if drafts else ("prd.md",):
        for p in [*artifacts.glob(f"*/{name}"), *artifacts.glob(f"epic-*/feature-*/{name}")]:
            if not p.parent.name.startswith("epic-"):
                out[p.parent] = p
    return [out[k] for k in sorted(out)]


def text_hash(text):
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def _requirement_lines(lines):
    """Yield (index, line) inside the `## Requirements` section only."""
    inside = False
    for i, line in enumerate(lines):
        if line.startswith("## "):
            inside = line.strip() == "## Requirements"
            continue
        if inside:
            yield i, line


def parse_definitions(prd_path):
    lines = Path(prd_path).read_text(encoding="utf-8").splitlines()
    defs, current = [], None
    for i, line in _requirement_lines(lines):
        bullet, row = DEF_BULLET_RE.match(line), DEF_ROW_RE.match(line)
        if bullet or row:
            req_id = (bullet or row).group(1)
            note = bullet.group(2) if bullet else None
            body = bullet.group(3) if bullet else row.group(2)
            priority = alias = None
            for part in (note or "").split(","):
                part = part.strip()
                if PRIORITY_RE.match(part):
                    priority = part
                elif ALIAS_RE.match(part):
                    alias = part
            replaced = REPLACED_RE.search(body)
            current = {
                "id": req_id, "type": req_id.split("-", 1)[0],
                "feature": ID_RE.match(req_id).group(2), "name": ID_RE.match(req_id).group(3),
                "priority": priority, "alias": alias, "text": body.strip(),
                "hash": text_hash(RETIRED_MARK_RE.sub("", body.rstrip(" |"))), "file": str(prd_path), "line": i + 1,
                "retired": bool(replaced) or "Retired" in body,
                "replaced_by": replaced.group(1) if replaced else None,
                "superseded_by": None, "clarifications": [],
            }
            defs.append(current)
            continue
        if current is None:
            continue
        superseded, clarified = SUPERSEDED_RE.match(line), CLARIFIED_RE.match(line)
        if superseded:
            current["superseded_by"] = superseded.group(1)
        elif clarified:
            current["clarifications"].append({"date": clarified.group(1), "detail": clarified.group(2)})
        elif line.strip() and not line.startswith(">"):
            current = None
    return defs


def citation_kind(path):
    name, parts = path.name, path.parts
    if name.startswith("stories-"):
        return "story"
    if "test-cases" in parts:
        return "test-case"
    if "ux" in parts:
        return "mockup"
    if name == "prd.md":
        return "prd"
    if "bugs" in parts:
        return "bug"
    return "other"


def scan_citations(root, definition_sites):
    """Every ID mention under artifacts/, minus the definition lines themselves."""
    artifacts, out = Path(root) / "artifacts", []
    files = [p for p in artifacts.rglob("*") if p.suffix in (".md", ".json", ".html") and p.is_file()]
    for path in sorted(files):
        if path.name in SKIP_FILES:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for match in ID_RE.finditer(line):
                if (str(path), n, match.group(0)) in definition_sites:
                    continue
                out.append({"id": match.group(0), "file": str(path), "line": n, "kind": citation_kind(path)})
    return out


def scan_malformed(root):
    artifacts, out = Path(root) / "artifacts", []
    for path in sorted(artifacts.rglob("*.md")):
        if path.name in SKIP_FILES:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for match in LOOSE_ID_RE.finditer(line):
                token = match.group(0).rstrip(".,;:)")
                full = ID_RE.fullmatch(token)
                if ALIAS_RE.match(token) or (full and len(full.group(3)) <= MAX_NAME):
                    continue
                out.append({"token": token, "file": str(path), "line": n})
    return out


def read_stories(prd_path):
    stories = []
    for story in sorted(Path(prd_path).parent.glob("stories-*.md")):
        text = story.read_text(encoding="utf-8")
        implements = re.search(r"^\s*-?\s*Implements:\s*(.*)$", text, re.MULTILINE)
        stories.append({
            "file": str(story), "id": read_frontmatter(text).get("id"),
            "status": read_frontmatter(text).get("status"),
            "implements": ID_RE.findall(implements.group(1)) if implements else [],
        })
    for s in stories:
        s["implements"] = [f"{t}-{f}.{n}" for t, f, n in s["implements"]]
    return stories


def load_project(root, drafts=False):
    """One pass over the repo: features, definitions, stories, citations."""
    features = []
    for prd in find_feature_prds(root, drafts):
        text = prd.read_text(encoding="utf-8")
        meta = read_frontmatter(text)
        features.append({
            "slug": feature_slug_of(prd), "file": str(prd), "meta": meta,
            "status": meta.get("status") or "draft",
            "supersedes": meta.get("supersedes") or [],
            "definitions": parse_definitions(prd), "stories": read_stories(prd),
            "open_markers": text.count("[NEEDS CLARIFICATION"),
        })
    sites = {(d["file"], d["line"], d["id"]) for f in features for d in f["definitions"]}
    return {"features": features, "citations": scan_citations(root, sites)}
