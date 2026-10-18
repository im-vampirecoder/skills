"""
Read local bug files (artifacts/bugs/<bug-slug>.md, written by
vc-bug-report) into the tracker-neutral item shape. Ready bugs are
sprint candidates like stories.
"""
import glob
import os
import re

from sprint_planning_frontmatter import read_markdown, sprint_slug

STATUSES = {"new", "ready", "in-progress", "done", "removed"}


def read_bug(path, root):
    data, body = read_markdown(path)
    slug = os.path.splitext(os.path.basename(path))[0]
    heading = re.search(r"^#\s+(?:Bug:\s*)?(.+)$", body, re.M)
    status = str(data.get("status") or "new").lower()
    iteration = data.get("iteration")

    def has(label):
        found = re.search(rf"\*\*{label}:\*\*\s*(.*)", body)
        return bool(found and found.group(1).strip() not in ("", "..."))

    repro = re.search(r"\*\*Steps to Reproduce:\*\*(.*?)(?=\*\*Expected Result)", body, re.S)
    return {
        "id": data.get("id") or f"BUG-{slug}",
        "ado_id": data.get("ado_id"),
        "title": heading.group(1).strip() if heading else slug,
        "path": os.path.relpath(path, root),
        "number": None,
        "feature_id": data.get("feature_id"),
        "epic": data.get("epic_id"),
        "status": status,
        "status_known": status in STATUSES,
        "iteration": str(iteration) if iteration else None,
        "iteration_slug": sprint_slug(str(iteration)) if iteration else None,
        "kind": "bug",
        "severity": (str(data.get("severity") or "")).lower() or None,
        "has_repro_steps": bool(repro and re.search(r"^\s*\d+\.\s+\w", repro.group(1), re.M)),
        "has_expected_actual": has("Expected Result") and has("Actual Result"),
        "dependencies": [],
        "breakdown": None,
        "blocking_clarifications": None,
    }


def read_bugs(root):
    paths = glob.glob(os.path.join(root, "artifacts", "bugs", "*.md"))
    return [read_bug(path, root) for path in sorted(paths)]
