"""Semantic checks for test-cases.json that JSON shape alone cannot express:
unique feature-scoped IDs, resolvable references, step numbering, readiness
rules, risk bands, and coverage recomputed from the actual links.

Each check returns findings: {"level": "error"|"warning", "check", "id", "message"}.
"""

from test_case_contract import (
    CASE_STATUSES, ENTITY_PREFIXES, GAP_STATUSES, PRIORITIES, QUESTION_STATUSES,
    READINESS, REQUIREMENT_STATUSES, RISK_LEVELS, SCENARIO_STATUSES, SOURCE_ACCESS,
    VAGUE_EXPECTED, active, id_pattern, risk_band,
)


def _finding(level, check, item_id, message):
    return {"level": level, "check": check, "id": item_id, "message": message}


def _index(doc, key):
    return {item["id"]: item for item in doc.get(key, []) if "id" in item}


def check_ids(doc, slug, registry):
    findings = []
    for key, prefix in ENTITY_PREFIXES.items():
        pattern, seen = id_pattern(prefix, slug), set()
        for item in doc.get(key, []):
            item_id = item.get("id", "<missing>")
            match = pattern.match(item_id)
            if not match:
                findings.append(_finding("error", "id-format", item_id,
                                         f"expected {prefix}-{slug}-<nnn> in {key}"))
            elif registry is not None and int(match.group(1)) > registry.get(prefix, 0):
                findings.append(_finding("error", "id-registry", item_id,
                                         "not allocated by test_case_state.py next-ids"))
            if item_id in seen:
                findings.append(_finding("error", "id-unique", item_id, f"duplicate in {key}"))
            seen.add(item_id)
    return findings


def _enum(findings, item, field, allowed, check):
    if item.get(field) not in allowed:
        findings.append(_finding("error", check, item.get("id"),
                                 f"{field}={item.get(field)!r} not in {sorted(allowed)}"))


def check_refs(doc):
    findings = []
    idx = {key: _index(doc, key) for key in ENTITY_PREFIXES}
    stories = set(doc.get("scope", {}).get("story_ids", []))
    live = {key: {i for i, item in idx[key].items() if not item.get("retired")}
            for key in idx}
    all_live = set().union(*live.values())
    links = {"requirement_ids": "requirements", "scenario_ids": "scenarios",
             "risk_ids": "risks"}
    for key in ("requirements", "questions", "risks", "scenarios", "test_cases"):
        for item in active(doc.get(key)):
            for ref in item.get("source_refs", []):
                if ref.get("source_id") not in live["sources"]:
                    findings.append(_finding("error", "ref-source", item["id"],
                                             f"unknown source {ref.get('source_id')}"))
                if not ref.get("location"):
                    findings.append(_finding("error", "ref-location", item["id"],
                                             "source_ref without a precise location"))
            for field, target in links.items():
                for ref in item.get(field, []):
                    if ref not in live[target]:
                        findings.append(_finding("error", "ref-link", item["id"],
                                                 f"{field} -> {ref} missing or retired"))
            story_refs = item.get("story_ids", []) + [item.get("story_id")]
            for story in filter(None, story_refs):
                if story not in stories:
                    findings.append(_finding("error", "ref-story", item["id"],
                                             f"{story} not in scope.story_ids"))
    for gap in active(doc.get("gaps")):
        for ref in gap.get("affected_ids", []):
            if ref not in all_live and ref not in stories:
                findings.append(_finding("error", "ref-gap", gap["id"], f"unknown {ref}"))
    return findings


def check_enums(doc):
    findings = []
    for item in active(doc.get("sources")):
        _enum(findings, item, "access", SOURCE_ACCESS, "source")
    for item in active(doc.get("requirements")):
        _enum(findings, item, "status", REQUIREMENT_STATUSES, "requirement")
    for item in active(doc.get("questions")):
        _enum(findings, item, "status", QUESTION_STATUSES, "question")
    for item in active(doc.get("scenarios")):
        _enum(findings, item, "status", SCENARIO_STATUSES, "scenario")
    for item in active(doc.get("gaps")):
        _enum(findings, item, "status", GAP_STATUSES, "gap")
    for risk in active(doc.get("risks")):
        _enum(findings, risk, "level", RISK_LEVELS, "risk")
        impact, likelihood = risk.get("impact"), risk.get("likelihood")
        if impact not in (1, 2, 3) or likelihood not in (1, 2, 3):
            findings.append(_finding("error", "risk-scale", risk["id"],
                                     "impact and likelihood must be 1..3"))
        elif risk.get("level") != risk_band(impact, likelihood) and not risk.get("override_reason"):
            findings.append(_finding("error", "risk-band", risk["id"],
                                     f"level should be {risk_band(impact, likelihood)} "
                                     "or carry override_reason"))
    return findings


def check_cases(doc, mode):
    findings = []
    reqs, scenarios = _index(doc, "requirements"), _index(doc, "scenarios")
    blocking = {rid for q in active(doc.get("questions"))
                if q.get("blocking") and q.get("status") == "open"
                for rid in q.get("requirement_ids", [])}
    for case in active(doc.get("test_cases")):
        cid = case["id"]
        for field, allowed in (("status", CASE_STATUSES), ("readiness", READINESS),
                               ("risk_level", RISK_LEVELS), ("priority", PRIORITIES)):
            _enum(findings, case, field, allowed, "case")
        if case.get("execution_status") != "not_run":
            findings.append(_finding("error", "not-run", cid,
                                     "generated cases must stay execution_status=not_run"))
        if not case.get("requirement_ids") or not case.get("scenario_ids"):
            findings.append(_finding("error", "case-trace", cid,
                                     "needs requirement_ids and scenario_ids"))
        steps = case.get("steps", [])
        if not steps:
            findings.append(_finding("error", "step-empty", cid, "case has no steps"))
        if [s.get("number") for s in steps] != list(range(1, len(steps) + 1)):
            findings.append(_finding("error", "steps-order", cid, "steps must number 1..n"))
        for step in steps:
            expected = (step.get("expected") or "").strip().lower()
            if not (step.get("action") or "").strip() or not expected:
                findings.append(_finding("error", "step-empty", cid,
                                         f"step {step.get('number')} lacks action or expected"))
            elif expected.rstrip(".") in VAGUE_EXPECTED:
                findings.append(_finding("error", "step-vague", cid,
                                         f"step {step.get('number')} expected is not observable"))
        if case.get("readiness") != "ready":
            continue
        if not case.get("test_data") and not case.get("preconditions"):
            findings.append(_finding("error", "ready-data", cid,
                                     "ready case needs test_data or fixture preconditions"))
        for rid in case.get("requirement_ids", []):
            req = reqs.get(rid, {})
            if req.get("status") != "confirmed" or not req.get("in_scope"):
                findings.append(_finding("error", "ready-oracle", cid,
                                         f"{rid} is not a confirmed in-scope rule"))
            if rid in blocking:
                findings.append(_finding("error", "ready-blocked", cid,
                                         f"{rid} has an open blocking question"))
        if mode == "reviewed":
            for sid in case.get("scenario_ids", []):
                if scenarios.get(sid, {}).get("status") != "approved":
                    findings.append(_finding("error", "ready-scenario", cid,
                                             f"{sid} is not an approved scenario"))
    return findings


def check_exclusions(doc, approvals):
    """Scope a reviewer excluded at a gate must be out of scope in the data."""
    findings = []
    excluded = {ref for record in approvals or [] if record.get("decision") == "approve"
                for ref in record.get("excluded_ids", [])}
    still_in = [r["id"] for r in active(doc.get("requirements"))
                if r["id"] in excluded and r.get("in_scope")]
    still_in += [s["id"] for s in active(doc.get("scenarios"))
                 if s["id"] in excluded and s.get("status") != "excluded"]
    for item_id in still_in:
        findings.append(_finding("error", "gate-exclusion", item_id,
                                 "excluded at a review gate but still in scope"))
    return findings


def compute_coverage(doc):
    """Coverage rebuilt from links; a model-written coverage list is never trusted."""
    rows, findings = [], []
    cases = active(doc.get("test_cases"))
    scenarios = [s for s in active(doc.get("scenarios")) if s.get("status") != "excluded"]
    for req in active(doc.get("requirements")):
        rid = req["id"]
        case_ids = [c["id"] for c in cases if rid in c.get("requirement_ids", [])]
        scenario_ids = [s["id"] for s in scenarios if rid in s.get("requirement_ids", [])]
        override = req.get("coverage_override") or {}
        if not req.get("in_scope"):
            status, reason = "out_of_scope", override.get("reason") or "excluded from scope"
        elif case_ids:
            status, reason = "mapped", None
        elif override.get("status") == "deferred":
            status, reason = "deferred", override.get("reason")
        else:
            status, reason = "uncovered", None
            if req.get("status") == "confirmed":
                findings.append(_finding("warning", "coverage", rid,
                                         "confirmed in-scope rule has no case and no deferral"))
        rows.append({"requirement_id": rid, "scenario_ids": scenario_ids,
                     "case_ids": case_ids, "status": status, "reason": reason})
    return rows, findings
