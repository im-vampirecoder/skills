"""Requirements level of check_user_flow.py: the map against its feature PRD.

Reads the PRD's `## Requirements` with its own small regexes (the ID format is
defined in vc-prd's references/requirements-section.md); never imports another
skill's scripts. Python 3 stdlib only.
"""

import re
from pathlib import Path

from user_flow_parse import cell, ids_in, read_frontmatter

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ID_FORM_RE = re.compile(rf"^(FR|NFR|BR|ERR)-({SLUG})\.({SLUG})$")
FR_RE = re.compile(rf"^\s*-\s+\*\*(FR-{SLUG}\.{SLUG}):?\*\*\s*\((P\d)")
ERR_RE = re.compile(rf"^\s*\|\s*(ERR-{SLUG}\.{SLUG})\s*\|([^|]*)\|([^|]*)\|")
OTHER_DEF_RE = re.compile(rf"^\s*-\s+\*\*((?:NFR|BR)-{SLUG}\.{SLUG}):?\*\*")
NOTHING_SEEN = {"", "-", "—", "none", "nothing", "n/a", "(none)", "no message"}


def feature_slug(prd_path, meta):
    feature_id = meta.get("feature_id", "")
    if feature_id.startswith("FEATURE-"):
        return feature_id[len("FEATURE-"):]
    folder = Path(prd_path).parent.name
    return folder[len("feature-"):] if folder.startswith("feature-") else folder


def read_prd(prd_path):
    """{id: {"type", "priority", "live", "user_facing"}} for the PRD's own definitions."""
    lines = Path(prd_path).read_text(encoding="utf-8").splitlines()
    defs = {}
    for i, line in enumerate(lines):
        fr, err, other = FR_RE.match(line), ERR_RE.match(line), OTHER_DEF_RE.match(line)
        if fr:
            req_id, entry = fr.group(1), {"type": "FR", "priority": fr.group(2)}
        elif err:
            req_id = err.group(1)
            entry = {"type": "ERR", "user_facing": err.group(3).strip().lower() not in NOTHING_SEEN}
        elif other:
            req_id, entry = other.group(1), {"type": other.group(1).split("-")[0]}
        else:
            continue
        following = []
        for nxt in lines[i + 1:]:
            if not nxt.lstrip().startswith(">"):
                break
            following.append(nxt)
        entry["live"] = "Retired." not in line and not any("Superseded by" in l for l in following)
        defs[req_id] = entry
    meta = read_frontmatter("\n".join(lines))
    for req_id in meta.get("superseded", []) if isinstance(meta.get("superseded"), list) else []:
        if req_id in defs:
            defs[req_id]["live"] = False
    return defs, meta


def check(flow, prd_path):
    """List of (level, check, message, line) for the requirements level."""
    findings = []
    add = lambda level, name, msg, line=None: findings.append((level, name, msg, line))
    defs, prd_meta = read_prd(prd_path)
    slug = feature_slug(prd_path, prd_meta)
    if not defs:
        add("error", "no-requirements", f"{prd_path} has no requirement IDs; run /vc:prd migrate first")
        return findings

    cited = []  # (id, line, where)
    for row in flow["screens"]:
        cited += [(i, row["_line"], "screen") for i in ids_in(cell(row, "requirement"))]
    for row in flow["transitions"]:
        cited += [(i, row["_line"], "transition") for i in ids_in(cell(row, "requirement"))]

    for req_id, line, _ in cited:
        form = ID_FORM_RE.match(req_id)
        if not form:
            add("error", "malformed-id", f"{req_id} is not <TYPE>-<feature-slug>.<name>", line)
        elif form.group(2) != slug:
            add("info", "other-feature", f"{req_id} belongs to another feature; not checked here", line)
        elif req_id not in defs:
            add("error", "undefined-id", f"{req_id} is not defined in the PRD", line)
        elif not defs[req_id]["live"]:
            add("error", "dead-id", f"{req_id} is retired or superseded; cite its replacement", line)

    on_screens = {i for i, _, where in cited if where == "screen"}
    on_edges = {i for i, _, where in cited if where == "transition"}
    for req_id, entry in sorted(defs.items()):
        if not entry["live"]:
            continue
        if entry["type"] == "FR" and entry.get("priority") == "P0" and req_id not in on_screens | on_edges:
            add("error", "uncovered-p0", f"{req_id} (P0) is on no screen or transition")
        if entry["type"] == "ERR" and entry.get("user_facing") and req_id not in on_edges:
            add("error", "uncovered-err", f"{req_id} shows the user something but no transition leads to it")

    live = {i for i, e in defs.items() if e["live"] and e["type"] in ("FR", "ERR")}
    recorded = flow["meta"].get("requirements")
    recorded = set(recorded) if isinstance(recorded, list) else set()
    if recorded != live:
        added, gone = sorted(live - recorded), sorted(recorded - live)
        detail = "; ".join(p for p in (added and "new in PRD: " + ", ".join(added),
                                        gone and "no longer live: " + ", ".join(gone)) if p)
        add("error", "requirements-stale", f"frontmatter `requirements` doesn't match the PRD ({detail})")
    return findings
