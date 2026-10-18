"""Progress derived from test-cases.json and .state.json: per-gate approval
status, source files changed since analysis, and the current workflow stage.

Nothing here is stored. Deriving it on every call means a resumed session
always sees the real stage, not a label written before the data changed.
"""

from pathlib import Path

from test_case_contract import active, file_fingerprint, gate_hash


def gate_status(state, doc, gate):
    if state["mode"] == "fast" and gate in ("A", "B"):
        return "skipped"
    records = [r for r in state["approvals"] if r["gate"] == gate]
    if not records:
        return "missing"
    latest = records[-1]
    if latest["decision"] != "approve":
        return "changes_requested"
    return "approved" if latest["content_hash"] == gate_hash(doc, gate) else "stale"


def changed_sources(doc, repo_root):
    changed = []
    for source in active(doc.get("sources")):
        if not source.get("path") or source.get("access") != "read":
            continue
        current = file_fingerprint(Path(repo_root) / source["path"])
        if current != source.get("revision"):
            changed.append({"id": source["id"], "path": source["path"],
                            "recorded": source.get("revision"), "current": current})
    return changed


def derive_stage(doc, gates, changed, uncased):
    if not active(doc.get("requirements")) or changed:
        return "analyzing"
    if gates["A"] not in ("approved", "skipped"):
        return "awaiting_analysis_review"
    if not active(doc.get("scenarios")):
        return "planning"
    if gates["B"] not in ("approved", "skipped"):
        return "awaiting_scenario_review"
    if uncased:
        return "generating"
    if gates["final"] != "approved":
        return "awaiting_final_review"
    return "approved"
