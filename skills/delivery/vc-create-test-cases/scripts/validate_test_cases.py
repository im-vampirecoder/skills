"""Validate <feature>/test-cases/test-cases.json and recompute its coverage.

Usage:
  python3 validate_test_cases.py DIR [--write] [--json]

DIR is the feature's test-cases/ folder. --write stores the recomputed
coverage and the quality_checks summary back into test-cases.json.
Exit code 1 when any error-level finding exists; warnings never fail.
"""

import argparse
import json
import sys
from pathlib import Path

from test_case_checks import (
    check_cases, check_enums, check_exclusions, check_ids, check_refs, compute_coverage,
)
from test_case_contract import CASES_FILE, STATE_FILE, active, load_json, save_json

CHECK_GROUPS = (
    ("ids-unique-and-allocated", ("id-format", "id-registry", "id-unique")),
    ("review-exclusions-applied", ("gate-exclusion",)),
    ("references-resolve", ("ref-source", "ref-location", "ref-link", "ref-story", "ref-gap")),
    ("enums-and-risk-bands", ("source", "requirement", "question", "scenario", "gap",
                              "risk", "risk-scale", "risk-band", "case")),
    ("steps-observable", ("steps-order", "step-empty", "step-vague", "case-trace")),
    ("ready-cases-grounded", ("ready-data", "ready-oracle", "ready-blocked", "ready-scenario")),
    ("execution-not-run", ("not-run",)),
    ("coverage-complete", ("coverage",)),
)


def summarise(findings):
    """One quality_checks row per group, so the report stays readable."""
    rows = []
    for name, checks in CHECK_GROUPS:
        hits = [f for f in findings if f["check"] in checks]
        if not hits:
            result = "pass"
        elif any(f["level"] == "error" for f in hits):
            result = "fail"
        else:
            result = "warning"
        details = "; ".join(f"{f['id']}: {f['message']}" for f in hits[:10])
        if len(hits) > 10:
            details += f"; +{len(hits) - 10} more"
        rows.append({"name": name, "result": result, "details": details})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dir")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    base = Path(args.dir)
    doc = load_json(base / CASES_FILE)
    state = load_json(base / STATE_FILE) if (base / STATE_FILE).exists() else {}
    slug = doc.get("feature_slug") or state.get("feature_slug")
    if not slug:
        sys.exit("feature_slug missing from test-cases.json")

    findings = check_ids(doc, slug, state.get("id_registry"))
    findings += check_refs(doc)
    findings += check_enums(doc)
    findings += check_cases(doc, state.get("mode", "reviewed"))
    findings += check_exclusions(doc, state.get("approvals"))
    coverage, coverage_findings = compute_coverage(doc)
    findings += coverage_findings
    checks = summarise(findings)

    if args.write:
        doc["coverage"] = coverage
        doc["quality_checks"] = checks
        save_json(base / CASES_FILE, doc)

    errors = [f for f in findings if f["level"] == "error"]
    totals = {status: sum(1 for row in coverage if row["status"] == status)
              for status in ("mapped", "uncovered", "deferred", "out_of_scope")}
    summary = {
        "cases": len(active(doc.get("test_cases"))),
        "errors": len(errors),
        "warnings": len(findings) - len(errors),
        "coverage": totals,
    }
    if args.json:
        print(json.dumps({"summary": summary, "findings": findings,
                          "quality_checks": checks}, indent=2))
    else:
        print(f"cases={summary['cases']} errors={summary['errors']} "
              f"warnings={summary['warnings']} coverage={totals}")
        for finding in findings:
            print(f"  [{finding['level']}] {finding['check']} {finding['id']}: "
                  f"{finding['message']}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
