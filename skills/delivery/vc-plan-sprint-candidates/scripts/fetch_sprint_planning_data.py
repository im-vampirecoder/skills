#!/usr/bin/env python3
"""
Gather everything vc-plan-sprint-candidates needs to propose a sprint,
as one JSON object on stdout:

  - the sprint being planned, its capacity (checked against
    references/capacity-file-contract.md), and the current sprint
  - carryover: unfinished stories in the current sprint
  - the backlog split into ready / not ready, in proposed order
  - throughput: stories Done per past sprint, scaled by this sprint's
    available hours vs the usual hours (story points are never used)
  - a per-feature roll-up of story states

The model does the judgment (goal, which stories serve it, slip test);
this script only does the counting, so the numbers are the same every run.

Usage:
  python fetch_sprint_planning_data.py [--root <tracking repo>]
      [--tracker local|azure-devops] [--sprint <slug>] [--today YYYY-MM-DD]
      [--history 5]

`problems` non-empty means stop and show them; `warnings` are shown and
the run continues.
"""
import argparse
import json
import os
import sys
from datetime import date

import sprint_planning_ado_tracker as ado_tracker
import sprint_planning_local_tracker as local_tracker
from sprint_planning_analysis import (backlog_order, feature_rollup, readiness_flags,
                                      throughput)
from sprint_planning_capacity import load_capacity
from sprint_planning_config import classify_sprints, read_config

def build(args):
    out = {"problems": [], "warnings": []}
    root = os.path.abspath(args.root)
    config = read_config(root)
    tracker = args.tracker or config.get("tracker")
    out["tracker"] = tracker
    ado = tracker == "azure-devops"
    if ado:
        cfg = config.get("ado") or {}
        missing = [k for k in ("organization", "project", "area_path") if not cfg.get(k)]
        if missing:
            out["problems"].append(f"[ado] in .vc/config.toml is missing {', '.join(missing)} "
                                   "- run /vc:setup")
            return out
    elif tracker not in ("local", None):
        out["problems"].append(f"tracker '{tracker}' is not supported (local or azure-devops)")
        return out

    today = date.fromisoformat(args.today) if args.today else date.today()
    out["today"] = today.isoformat()
    try:
        sprints = ado_tracker.list_sprints(cfg, root) if ado else local_tracker.discover_sprints(root)
    except RuntimeError as error:
        out["problems"].append(f"Azure DevOps call failed: {error}")
        return out
    past, current, future = classify_sprints(sprints, today)
    target = next((s for s in past + future + ([current] if current else [])
                   if s["slug"] == args.sprint), None) if args.sprint else \
        (future[0] if future else None)
    out["current_sprint"], out["target_sprint"] = current, target
    if target is None:
        out["problems"].append(
            "no next sprint found: add the next iteration to the team in Azure DevOps"
            if ado else "no capacity published for the next sprint: expected "
            "artifacts/sprints/<sprint-slug>/capacity.md (see the capacity file contract)")
        return out
    past = [s for s in past if s["slug"] != target["slug"]]

    capacity = load_capacity(target["capacity_path"],
                             {"sprint": target["name"], "iteration_path": target["iteration_path"]})
    if capacity is None:
        out["problems"].append(
            f"no capacity published for {target['name']}: expected "
            f"{os.path.relpath(target['capacity_path'], root)} (see the capacity file contract)")
        return out
    out["capacity"] = capacity
    out["problems"] += capacity["problems"]
    out["warnings"] += capacity["warnings"]
    if out["problems"]:
        return out

    # "stories" below means every plannable item: user stories, PBIs/spikes, and bugs.
    if ado:
        try:
            history_paths = [s["iteration_path"] for s in past[:args.history]]
            stories = ado_tracker.read_items(cfg, root, sprints, history_paths)
            features = ado_tracker.read_features(cfg, root, stories)
        except RuntimeError as error:
            out["problems"].append(f"Azure DevOps call failed: {error}")
            return out
    else:
        stories = local_tracker.read_stories(root) + local_tracker.read_bugs(root)
        features, feature_warnings = local_tracker.read_features(root)
        out["warnings"] += feature_warnings
    by_id = {}
    for story in stories:
        if story["id"] in by_id:
            out["warnings"].append(f"{story['id']} is used by more than one story file: "
                                   f"{by_id[story['id']]['path']} and {story['path']}")
        by_id.setdefault(story["id"], story)
    open_story = lambda s: s["status"] not in ("done", "removed")
    current_slug = current["slug"] if current else None

    out["carryover"] = [s for s in stories if current_slug and open_story(s)
                        and s["iteration_slug"] == current_slug]
    out["already_planned"] = [s for s in stories if open_story(s)
                              and s["iteration_slug"] == target["slug"]]
    backlog = sorted((s for s in stories if s["iteration"] is None and s["status"] in ("new", "ready")),
                     key=backlog_order)
    for story in backlog:
        story["readiness_flags"] = readiness_flags(story, by_id, features)
    out["backlog_ready"] = [s for s in backlog if s["status"] == "ready"]
    out["backlog_not_ready"] = [s for s in backlog if s["status"] != "ready"]
    out["stale_in_past_sprint"] = [s for s in stories if open_story(s) and s["iteration_slug"]
                                   and s["iteration_slug"] in {p["slug"] for p in past}]
    out["throughput"] = throughput(past, stories, capacity, args.history)
    out["features"] = feature_rollup(stories, features)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--tracker", choices=["local", "azure-devops"])
    parser.add_argument("--sprint", help="slug of the sprint to plan (default: next sprint)")
    parser.add_argument("--today", help="YYYY-MM-DD, for testing")
    parser.add_argument("--history", type=int, default=5)
    result = build(parser.parse_args())
    json.dump(result, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
