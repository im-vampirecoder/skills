"""
Read sprint planning data from a `tracker = "local"` tracking repo.

  - Sprints are the folders under artifacts/sprints/ that hold a
    capacity.md (its sprint name, iteration path, and dates define the
    sprint - see references/capacity-file-contract.md).
  - Stories are every artifacts/**/stories-<n>-*.md file. Sprint state
    comes from their `status` (missing = new) and `iteration` (missing =
    null) frontmatter fields.
  - Bugs are every artifacts/bugs/<bug-slug>.md file (vc-bug-report),
    with the same `status` / `iteration` fields.
  - Features are every feature prd.md (any prd.md except the product one
    at artifacts/prd.md).

Every story/feature is returned as a plain dict in the tracker-neutral
shape fetch_sprint_planning_data.py works with; the ADO reader returns
the same shape.
"""
import glob
import os
import re

from sprint_planning_frontmatter import read_markdown, sprint_slug
from sprint_planning_local_bugs import read_bug, read_bugs  # noqa: F401 (re-exported)
from sprint_planning_local_signals import blocking_clarifications, breakdown
from sprint_planning_local_signals import section as _section

STATUSES = {"new", "ready", "in-progress", "done", "removed"}


def _detail(details, label):
    match = re.search(rf"^\s*-\s*{re.escape(label)}\s*:\s*(.+)$", details, re.M | re.I)
    return match.group(1).strip() if match else None


def _folder_slug(path, prefix):
    for part in reversed(os.path.normpath(path).split(os.sep)):
        if part.startswith(prefix):
            return part[len(prefix):]
    return None


def discover_sprints(root):
    sprints = []
    for path in sorted(glob.glob(os.path.join(root, "artifacts", "sprints", "*", "capacity.md"))):
        data, _ = read_markdown(path)
        name = data.get("sprint") or os.path.basename(os.path.dirname(path))
        sprints.append({
            "slug": os.path.basename(os.path.dirname(path)),
            "name": str(name),
            "iteration_path": str(data.get("iteration_path") or name),
            "start_date": str(data.get("start_date") or ""),
            "finish_date": str(data.get("finish_date") or ""),
            "capacity_path": path,
        })
    return sprints


def read_features(root):
    """Return (features by id, warnings). A feature id found in more than one
    prd.md is warned about; the copy inside an epic folder wins, since
    vc-propose-epic moves features there and an outside copy is a leftover."""
    features, warnings = {}, []
    product_prd = os.path.normpath(os.path.join(root, "artifacts", "prd.md"))
    for path in glob.glob(os.path.join(root, "artifacts", "**", "prd.md"), recursive=True):
        if os.path.normpath(path) == product_prd:
            continue
        folder = os.path.basename(os.path.dirname(path))
        slug = folder[len("feature-"):] if folder.startswith("feature-") else folder
        data, body = read_markdown(path)
        heading = re.search(r"^#\s+(?:Feature PRD:\s*)?(.+)$", body, re.M)
        feature_id = data.get("id") or f"FEATURE-{slug}"
        entry = {
            "id": feature_id,
            "slug": slug,
            "title": heading.group(1).strip() if heading else slug,
            "epic": _folder_slug(path, "epic-") or data.get("epic_id"),
            "ado_id": data.get("ado_id"),
            "path": os.path.relpath(path, root),
        }
        previous = features.get(feature_id)
        if previous:
            keep, drop = (entry, previous) if entry["path"].count("epic-") > \
                previous["path"].count("epic-") else (previous, entry)
            warnings.append(f"{feature_id} has more than one prd.md: using {keep['path']}, "
                            f"ignoring {drop['path']} - remove or merge the duplicate")
            entry = keep
        features[feature_id] = entry
    return features, warnings


def read_story(path, root):
    data, body = read_markdown(path)
    number = re.match(r"stories-(\d+)-", os.path.basename(path))
    heading = re.search(r"^#\s+(.+)$", body, re.M)
    title = heading.group(1).strip() if heading else os.path.basename(path)
    title = re.sub(r"^\d+\.\s*", "", title)
    title = re.sub(r"^\[[^\]]+\]\s*", "", title)

    criteria = _section(body, "Acceptance Criteria")
    ac_count = len(re.findall(r"^\s*(?:-|\d+\.)\s+\S", criteria, re.M))
    details = _section(body, "Details")
    deps_raw = _detail(details, "Dependencies") or ""
    dependencies = [] if deps_raw.lower() in ("", "none", "n/a") else \
        [dep.strip() for dep in re.split(r"[,;]", deps_raw) if dep.strip()]
    points = _detail(details, "Story Points")

    feature_slug = _folder_slug(path, "feature-") or os.path.basename(os.path.dirname(path))
    status = str(data.get("status") or "new").lower()
    iteration = data.get("iteration")
    return {
        "id": data.get("id") or f"STORY-{feature_slug}-{number.group(1) if number else '?'}",
        "ado_id": data.get("ado_id"),
        "title": title,
        "path": os.path.relpath(path, root),
        "number": int(number.group(1)) if number else None,
        "feature_id": data.get("feature_id") or f"FEATURE-{feature_slug}",
        "epic": _folder_slug(path, "epic-"),
        "status": status,
        "status_known": status in STATUSES,
        "iteration": str(iteration) if iteration else None,
        "iteration_slug": sprint_slug(str(iteration)) if iteration else None,
        "acceptance_criteria": ac_count,
        "priority": (_detail(details, "Priority") or "").lower() or None,
        "dependencies": dependencies,
        "type": (_detail(details, "Type") or "story").lower(),
        "kind": "story",
        "story_points_info": points,  # informational only, never summed
        "breakdown": breakdown(path, int(number.group(1)) if number else None, root),
        "blocking_clarifications": blocking_clarifications(path),
    }


def read_stories(root):
    pattern = os.path.join(root, "artifacts", "**", "stories-*.md")
    paths = [p for p in glob.glob(pattern, recursive=True)
             if f"{os.sep}sprints{os.sep}" not in p and f"{os.sep}tasks{os.sep}" not in p]
    return [read_story(path, root) for path in sorted(paths)]
