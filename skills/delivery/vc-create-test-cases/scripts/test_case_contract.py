"""Shared contract for vc-create-test-cases: file names, ID rules, enums,
JSON load/save, and the chained content hashes that review approvals bind to.

stdlib only. Imported by test_case_state.py, validate_test_cases.py and
render_test_cases_markdown.py.
"""

import hashlib
import json
import re
from pathlib import Path

CONTRACT_VERSION = "1.0"
CASES_FILE = "test-cases.json"
STATE_FILE = ".state.json"

# Entity list in test-cases.json -> ID prefix allocated by test_case_state.py.
ENTITY_PREFIXES = {
    "sources": "SRC",
    "requirements": "REQ",
    "questions": "Q",
    "risks": "RISK",
    "scenarios": "SC",
    "test_cases": "TC",
    "gaps": "GAP",
}
PREFIXES = set(ENTITY_PREFIXES.values())

REQUIREMENT_STATUSES = {"confirmed", "proposed", "observed", "unresolved"}
QUESTION_STATUSES = {"open", "resolved", "deferred"}
SCENARIO_STATUSES = {"draft", "approved", "excluded"}
CASE_STATUSES = {"draft", "approved"}
READINESS = {"ready", "needs_review", "blocked"}
RISK_LEVELS = {"low", "medium", "high"}
PRIORITIES = {"P1", "P2", "P3"}
GAP_STATUSES = {"open", "accepted_exclusion", "resolved"}
SOURCE_ACCESS = {"read", "unreadable", "missing"}
COVERAGE_OVERRIDES = {"deferred", "out_of_scope"}
GATES = ("A", "B", "final")

# Expected results that state no observable outcome.
VAGUE_EXPECTED = (
    "works correctly",
    "works as expected",
    "as expected",
    "behaves correctly",
    "no issues",
    "functions properly",
)


def id_pattern(prefix, slug):
    """Feature-scoped ID, e.g. TC-access-codes-007."""
    return re.compile(rf"^{re.escape(prefix)}-{re.escape(slug)}-(\d{{3,}})$")


def format_id(prefix, slug, number):
    return f"{prefix}-{slug}-{number:03d}"


def risk_band(impact, likelihood):
    """Impact x likelihood on 1..3 scales: 1-2 low, 3-4 medium, 6-9 high."""
    score = impact * likelihood
    if score <= 2:
        return "low"
    if score <= 4:
        return "medium"
    return "high"


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def active(items):
    """Entities that are not retired. Retired records stay for traceability."""
    return [item for item in items or [] if not item.get("retired")]


def _digest(value):
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def gate_content(cases_doc, gate):
    """What each gate approves. Chained: B includes A's content, final
    includes B's, so any upstream edit invalidates every later approval."""
    analysis = {
        key: cases_doc.get(key, [])
        for key in ("scope", "sources", "requirements", "questions", "risks")
    }
    if gate == "A":
        return analysis
    scenarios = {"analysis": analysis, "scenarios": cases_doc.get("scenarios", [])}
    if gate == "B":
        return scenarios
    # Final excludes ado_id/last_synced so a later tracker sync does not
    # invalidate QC approval.
    cases = [
        {k: v for k, v in case.items() if k not in ("ado_id", "last_synced")}
        for case in cases_doc.get("test_cases", [])
    ]
    return {"scenarios": scenarios, "test_cases": cases}


def gate_hash(cases_doc, gate):
    return _digest(gate_content(cases_doc, gate))


def file_fingerprint(path):
    """sha256 prefix of a source file, or None when it cannot be read."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return "sha256:" + hashlib.sha256(data).hexdigest()[:16]
