"""Derived requirement state shared by check, view and conflict shortlisting:
which IDs are current / being replaced / superseded / retired, which are
frozen, who cites what, and the frozen-text baseline kept inside the
generated `artifacts/requirements-current.md`.
"""

import json
import re
from pathlib import Path

BASELINE_RE = re.compile(r"<!-- vc-frozen-baseline (\{.*?\}) -->")
VIEW_NAME = "requirements-current.md"


def kebab(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read_glossary(root):
    """docs/glossary.md table -> {term: [aliases to avoid]}, all kebab-case."""
    path, terms = Path(root) / "docs" / "glossary.md", {}
    if not path.exists():
        return terms
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0] or cells[0].lower() == "term" or set(cells[0]) <= set("-: "):
            continue
        terms[kebab(cells[0])] = [kebab(a) for a in re.split(r"[,;]", cells[2]) if kebab(a)]
    return terms


def view_path(root):
    return Path(root) / "artifacts" / VIEW_NAME


def read_baseline(root):
    """Frozen ID -> text hash, recorded the first time each ID froze."""
    path = view_path(root)
    if not path.exists():
        return {}
    match = BASELINE_RE.search(path.read_text(encoding="utf-8"))
    return json.loads(match.group(1)) if match else {}


def index_definitions(project):
    """ID -> (feature, definition). First definition wins; duplicates are check's job."""
    out = {}
    for feature in project["features"]:
        for d in feature["definitions"]:
            out.setdefault(d["id"], (feature, d))
    return out


def citations_by_id(project):
    out = {}
    for c in project["citations"]:
        out.setdefault(c["id"], []).append(c)
    return out


def pending_supersessions(project):
    """ID or FEATURE-<slug> -> FEATURE id of a not-yet-done feature replacing it."""
    out = {}
    for feature in project["features"]:
        if feature["status"] == "done":
            continue
        for target in feature["supersedes"]:
            out[target] = f"FEATURE-{feature['slug']}"
    return out


def state_of(feature, definition, pending):
    if definition["retired"]:
        return "retired" + (f" (replaced by {definition['replaced_by']})" if definition["replaced_by"] else "")
    if definition["superseded_by"]:
        return f"superseded by {definition['superseded_by']}"
    replacer = pending.get(definition["id"]) or pending.get(f"FEATURE-{feature['slug']}")
    if replacer:
        return f"being replaced by {replacer} (draft)"
    return "current"


def frozen_reason(feature, definition):
    """Why an ID can no longer change meaning, or None while it is still editable."""
    if feature["status"] == "done":
        return "feature done"
    for story in feature["stories"]:
        if story["status"] == "done" and definition["id"] in story["implements"]:
            return f"implemented by done story {story['id'] or story['file']}"
    return None


def new_baseline(project, old):
    """Keep each frozen ID's first recorded hash; record newly frozen ones."""
    baseline = {}
    for feature in project["features"]:
        for d in feature["definitions"]:
            if frozen_reason(feature, d):
                baseline[d["id"]] = old.get(d["id"], d["hash"])
    return baseline


def coverage_gaps(project):
    """Live P0 FRs with no story, and live ERRs with no test case."""
    cited, pending = citations_by_id(project), pending_supersessions(project)
    no_story, no_test = [], []
    for feature in project["features"]:
        story_ids = {i for s in feature["stories"] for i in s["implements"]}
        for d in feature["definitions"]:
            if state_of(feature, d, pending).startswith(("retired", "superseded")):
                continue
            kinds = {c["kind"] for c in cited.get(d["id"], [])}
            if d["type"] == "FR" and d["priority"] == "P0" and d["id"] not in story_ids and "story" not in kinds:
                no_story.append(d["id"])
            if d["type"] == "ERR" and "test-case" not in kinds:
                no_test.append(d["id"])
    return no_story, no_test
