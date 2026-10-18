"""Persisted workflow state for vc-create-test-cases (<feature>/test-cases/.state.json).

Subcommands:
  init      DIR --feature-slug SLUG [--mode reviewed|fast]   create state + empty cases file
  mode      DIR reviewed|fast                                switch generation mode
  next-ids  DIR PREFIX [--count N]                           allocate feature-scoped IDs
  approve   DIR --gate A|B|final --reviewer WHO --decision approve|request_changes
            [--excluded ID ...] [--note TEXT]                record a review decision
  status    DIR [--repo-root PATH]                           derived stage, gates, changed sources

The stage is derived from the cases file and approvals every time, never
stored, so a resumed session cannot trust a stale label.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from test_case_contract import (
    CASES_FILE, CONTRACT_VERSION, ENTITY_PREFIXES, GATES, PREFIXES, STATE_FILE,
    active, format_id, gate_hash, load_json, save_json,
)
from test_case_progress import changed_sources, derive_stage, gate_status


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _paths(directory):
    base = Path(directory)
    return base / STATE_FILE, base / CASES_FILE


def cmd_init(args):
    state_path, cases_path = _paths(args.dir)
    if state_path.exists():
        sys.exit(f"{state_path} already exists; use `status` to resume")
    Path(args.dir).mkdir(parents=True, exist_ok=True)
    state = {
        "feature_slug": args.feature_slug,
        "mode": args.mode,
        "id_registry": {prefix: 0 for prefix in sorted(PREFIXES)},
        "approvals": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    save_json(state_path, state)
    if not cases_path.exists():
        doc = {
            "contract_version": CONTRACT_VERSION,
            "feature_id": f"FEATURE-{args.feature_slug}",
            "feature_slug": args.feature_slug,
            "artifact_language": "en",
            "scope": {"summary": "", "story_ids": [], "environment": "",
                      "roles": [], "exclusions": []},
        }
        doc.update({key: [] for key in ENTITY_PREFIXES})
        doc.update({"coverage": [], "quality_checks": []})
        save_json(cases_path, doc)
    print(f"initialised {state_path}")


def cmd_mode(args):
    state_path, _ = _paths(args.dir)
    state = load_json(state_path)
    state["mode"] = args.mode
    state["updated_at"] = _now()
    save_json(state_path, state)
    print(f"mode: {args.mode}")


def cmd_next_ids(args):
    if args.prefix not in PREFIXES:
        sys.exit(f"unknown prefix {args.prefix}; expected one of {sorted(PREFIXES)}")
    state_path, _ = _paths(args.dir)
    state = load_json(state_path)
    start = state["id_registry"].get(args.prefix, 0)
    ids = [format_id(args.prefix, state["feature_slug"], n)
           for n in range(start + 1, start + args.count + 1)]
    state["id_registry"][args.prefix] = start + args.count
    state["updated_at"] = _now()
    save_json(state_path, state)
    print("\n".join(ids))


def cmd_approve(args):
    state_path, cases_path = _paths(args.dir)
    state, doc = load_json(state_path), load_json(cases_path)
    record = {
        "gate": args.gate,
        "content_hash": gate_hash(doc, args.gate),
        "reviewer": args.reviewer,
        "recorded_at": _now(),
        "decision": args.decision,
        "excluded_ids": args.excluded or [],
        "note": args.note,
    }
    state["approvals"].append(record)
    state["updated_at"] = record["recorded_at"]
    save_json(state_path, state)
    print(json.dumps(record, indent=2))


def cmd_status(args):
    state_path, cases_path = _paths(args.dir)
    if not state_path.exists():
        print(json.dumps({"stage": "not_started"}))
        return
    state, doc = load_json(state_path), load_json(cases_path)
    gates = {gate: gate_status(state, doc, gate) for gate in GATES}
    changed = changed_sources(doc, args.repo_root)
    cased = {sid for case in active(doc.get("test_cases"))
             for sid in case.get("scenario_ids", [])}
    planned = [s for s in active(doc.get("scenarios")) if s.get("status") != "excluded"]
    uncased = [s["id"] for s in planned if s["id"] not in cased]
    pending_stories = sorted({s.get("story_id") or "feature-level"
                              for s in planned if s["id"] in uncased})
    report = {
        "feature_slug": state["feature_slug"],
        "mode": state["mode"],
        "stage": derive_stage(doc, gates, changed, uncased),
        "gates": gates,
        "changed_sources": changed,
        "scenarios_without_cases": uncased,
        "stories_pending_generation": pending_stories,
        "counts": {key: len(active(doc.get(key))) for key in ENTITY_PREFIXES},
        "updated_at": state["updated_at"],
    }
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("dir")
    p.add_argument("--feature-slug", required=True)
    p.add_argument("--mode", choices=("reviewed", "fast"), default="reviewed")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("mode")
    p.add_argument("dir")
    p.add_argument("mode", choices=("reviewed", "fast"))
    p.set_defaults(func=cmd_mode)
    p = sub.add_parser("next-ids")
    p.add_argument("dir")
    p.add_argument("prefix")
    p.add_argument("--count", type=int, default=1)
    p.set_defaults(func=cmd_next_ids)
    p = sub.add_parser("approve")
    p.add_argument("dir")
    p.add_argument("--gate", choices=GATES, required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--decision", choices=("approve", "request_changes"), required=True)
    p.add_argument("--excluded", nargs="*")
    p.add_argument("--note")
    p.set_defaults(func=cmd_approve)
    p = sub.add_parser("status")
    p.add_argument("dir")
    p.add_argument("--repo-root", default=".")
    p.set_defaults(func=cmd_status)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
