#!/usr/bin/env python3
"""
Settle: record the sprint scope the team agreed in planning by setting
each item's iteration, from artifacts/sprints/<sprint-slug>/candidates.md.

  plan   - read candidates.md and the items, print the moves as JSON.
           Writes nothing.
  apply  - recompute the same plan, refuse if it has problems, then set
           only the `iteration:` frontmatter line of each moved item and
           mark candidates.md settled with a dated record.

Local: the item file's `iteration:` line. Azure DevOps: the work item's
System.IterationPath (`az boards work-item update --iteration`); taking an
item out sets the team's backlog iteration.

Moves (references/settle-to-iteration.md has the full rules):
  candidates `In sprint` yes    -> iteration = this sprint
  candidates `In sprint` no     -> cleared, only if it is in this sprint now
  carryover `keep`              -> iteration = this sprint
  carryover `backlog`           -> cleared
  carryover `split` / `drop`    -> no move; listed as a follow-up
Items not named in candidates.md are never touched. Status is never changed.

Usage:
  python set_iteration.py plan|apply [--root .] [--sprint <slug>]
      [--exclude <ID> ...] [--by <name>] [--today YYYY-MM-DD]
"""
import argparse
import json
import os
import re
import sys
from datetime import date

import sprint_planning_ado_tracker as ado_tracker
from sprint_planning_candidates_file import mark_settled
from sprint_planning_config import read_config
from sprint_planning_frontmatter import split_frontmatter
from sprint_planning_settle_plan import build_plan

def set_iteration_line(path, value):
    """Rewrite only the `iteration:` frontmatter line (added if missing)."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    fm_text, body = split_frontmatter(text)
    if not fm_text:
        raise ValueError("file has no frontmatter")
    line = f"iteration: {value if value else 'null'}"
    if re.search(r"^iteration:.*$", fm_text, re.M):
        fm_text = re.sub(r"^iteration:.*$", lambda _: line, fm_text, count=1, flags=re.M)
    else:
        fm_text += "\n" + line
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"---\n{fm_text}\n---\n{body}")


def apply(args, plan):
    root = os.path.abspath(args.root)
    if plan["problems"]:
        return plan
    ado = plan["tracker"] == "azure-devops"
    cfg = read_config(root).get("ado") or {}
    backlog_path = None
    excluded = set(args.exclude or [])
    applied, record = [], [f"### {args.today or date.today().isoformat()} - settled by {args.by or 'unknown'}", ""]
    for entry in plan["moves"]:
        if entry["id"] in excluded:
            entry["result"] = "excluded"
            continue
        try:
            if ado:
                if entry["to"] is None and backlog_path is None:
                    backlog_path = ado_tracker.backlog_iteration(cfg)
                ado_tracker.az(["boards", "work-item", "update", "--id", str(entry["ado_id"]),
                                "--iteration", entry["to"] or backlog_path,
                                "--org", f"https://dev.azure.com/{cfg['organization']}"])
            else:
                set_iteration_line(os.path.join(root, entry["path"]), entry["to"])
            entry["result"] = "done"
            applied.append(entry)
            record.append(f"- {entry['id']}: {entry['from'] or 'backlog'} -> "
                          f"{entry['to'] or 'backlog'} ({entry['reason']})")
        except (OSError, ValueError, RuntimeError) as error:
            entry["result"] = f"failed: {error}"
    if not applied:
        record.append("- no iteration changes")
    for followup in plan["followups"]:
        record.append(f"- follow-up: {followup}")
    mark_settled(os.path.join(root, plan["candidates_file"]), record)
    plan["applied"] = len(applied)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["plan", "apply"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--sprint")
    parser.add_argument("--exclude", nargs="*")
    parser.add_argument("--by")
    parser.add_argument("--today")
    args = parser.parse_args()
    plan = build_plan(args)
    if args.command == "apply":
        plan = apply(args, plan)
    json.dump(plan, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 1 if plan["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
