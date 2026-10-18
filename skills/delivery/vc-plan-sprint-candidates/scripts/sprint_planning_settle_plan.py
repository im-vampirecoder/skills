"""
Work out settle's moves from candidates.md without writing anything
(references/settle-to-iteration.md has the rules). set_iteration.py
applies them.
"""
import os
from datetime import date

import sprint_planning_ado_tracker as ado_tracker
import sprint_planning_local_tracker as local_tracker
from sprint_planning_candidates_file import read_candidates
from sprint_planning_config import classify_sprints, read_config

CARRY_DECISIONS = {"keep", "backlog", "split", "drop"}


def pick_sprint(sprints, slug, today):
    if slug:
        return next((s for s in sprints if s["slug"] == slug), None)
    _, current, future = classify_sprints(sprints, today)
    # Before planning the next sprint is the one being settled; once it has
    # started (a mid-sprint scope change) it is the current one.
    for sprint in future[:1] + ([current] if current else []):
        if os.path.isfile(os.path.join(os.path.dirname(sprint["capacity_path"]), "candidates.md")):
            return sprint
    return None


def build_plan(args):
    root = os.path.abspath(args.root)
    plan = {"problems": [], "warnings": [], "moves": [], "followups": []}
    config = read_config(root)
    ado = config.get("tracker") == "azure-devops"
    cfg = config.get("ado") or {}
    plan["tracker"] = "azure-devops" if ado else "local"
    today = date.fromisoformat(args.today) if args.today else date.today()
    try:
        sprints = ado_tracker.list_sprints(cfg, root) if ado else local_tracker.discover_sprints(root)
    except RuntimeError as error:
        plan["problems"].append(f"Azure DevOps call failed: {error}")
        return plan
    sprint = pick_sprint(sprints, args.sprint, today)
    if sprint is None:
        plan["problems"].append("no candidates.md found for the next or current sprint")
        return plan
    path = os.path.join(os.path.dirname(sprint["capacity_path"]), "candidates.md")
    if not os.path.isfile(path):
        plan["problems"].append(f"{os.path.relpath(path, root)} does not exist")
        return plan
    parsed = read_candidates(path)
    target_path, target_slug = sprint["iteration_path"], sprint["slug"]
    plan.update(sprint=sprint["name"], iteration_path=target_path,
                candidates_file=os.path.relpath(path, root),
                file_status=parsed["meta"].get("status"))
    plan["problems"] += parsed["problems"]
    if plan["file_status"] == "draft":
        plan["warnings"].append("candidates.md is still `draft` - confirm planning is done")

    try:
        all_items = ado_tracker.read_items(cfg, root, sprints, [target_path]) if ado else \
            local_tracker.read_stories(root) + local_tracker.read_bugs(root)
    except RuntimeError as error:
        plan["problems"].append(f"Azure DevOps call failed: {error}")
        return plan
    items = {i["id"]: i for i in all_items}
    listed = set()

    def move(item, to, reason):
        # `to` is this sprint's path or None (backlog); skip when already there.
        if item["iteration_slug"] == (target_slug if to else None):
            return
        plan["moves"].append({"id": item["id"], "ado_id": item.get("ado_id"), "title": item["title"],
                              "path": item["path"], "from": item["iteration"], "to": to,
                              "reason": reason})

    for row in parsed["carryover"]:
        listed.add(row["id"])
        item = items.get(row["id"])
        if item is None:
            plan["problems"].append(f"carryover {row['id']}: no such story or bug")
        elif row["value"] not in CARRY_DECISIONS:
            plan["problems"].append(f"carryover {row['id']}: decision is "
                                    f"'{row['value'] or 'empty'}' (keep/backlog/split/drop)")
        elif row["value"] == "keep":
            move(item, target_path, "carryover kept")
        elif row["value"] == "backlog":
            move(item, None, "carryover back to backlog")
        else:
            plan["followups"].append(
                f"{row['id']} ({row['value']}): " + (
                    "write the remaining part as a new story, then close this one"
                    if row["value"] == "split" else "the PO sets `status: removed` when agreed"))

    for row in parsed["candidates"]:
        if row["id"] in listed:
            plan["problems"].append(f"{row['id']} is in both the carryover and candidates tables")
            continue
        listed.add(row["id"])
        item = items.get(row["id"])
        if item is None:
            plan["problems"].append(f"candidate {row['id']}: no such story or bug")
        elif row["value"] not in ("yes", "no"):
            plan["problems"].append(f"candidate {row['id']}: In sprint is '{row['value']}' (yes/no)")
        elif row["value"] == "yes":
            if item["status"] in ("done", "removed"):
                plan["warnings"].append(f"{item['id']} is {item['status']}; not moved")
            elif item["status"] not in ("ready", "in-progress") and item["iteration_slug"] != target_slug:
                plan["problems"].append(
                    f"{item['id']} is `{item['status']}`, not ready - only ready items can join "
                    "the sprint (make it ready first, or set In sprint to no)")
            else:
                move(item, target_path, "agreed in planning")
        elif item["iteration_slug"] == target_slug:
            move(item, None, "taken out of the sprint")

    for item in items.values():
        if item["iteration_slug"] == target_slug and item["id"] not in listed:
            plan["warnings"].append(f"{item['id']} is in this sprint but not in candidates.md; left as is")
    return plan
