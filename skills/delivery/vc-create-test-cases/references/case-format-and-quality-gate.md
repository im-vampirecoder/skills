# Case Format and Quality Gate

Used in step 7 (Generate) and step 8 (Validate).

## Test case

```json
{
  "id": "TC-<slug>-012",
  "title": "Validity of 49 hours is refused",
  "story_id": "STORY-<slug>-1",
  "requirement_ids": ["REQ-<slug>-004"],
  "scenario_ids": ["SC-<slug>-003"],
  "source_refs": [{"source_id": "SRC-<slug>-001", "location": "BR-<slug>.validity-hours"}],
  "risk_level": "high",
  "priority": "P1",
  "readiness": "ready",
  "status": "draft",
  "preconditions": [
    "Signed in as fixture ADMIN-A (portal admin, tenant TENANT-A)",
    "Student fixture STUDENT-001 exists in TENANT-A with no access code"
  ],
  "test_data": {"student": "STUDENT-001", "validity_hours": 49},
  "steps": [
    {"number": 1, "action": "Open Create access code for STUDENT-001",
     "expected": "The form opens with an empty Validity (hours) field"},
    {"number": 2, "action": "Enter 49 in Validity (hours) and select Save",
     "expected": "Save is refused, the Validity field shows a range error, and no code is created for STUDENT-001"}
  ],
  "cleanup": [],
  "tags": ["boundary"],
  "execution_status": "not_run",
  "ado_id": null,
  "last_synced": null
}
```

Rules:

- **One objective per case.** The title says what is checked.
- **Traceable.** At least one rule and one scenario; `story_id` matches
  the scenario's story (`null` for feature-level).
- **Steps numbered 1..n**, each with an action and an observable expected
  result. An intermediate result ("the form opens") is fine. Do not pad a
  case with checks unrelated to its objective.
- **Concrete data.** Fixed synthetic values, or a recipe for values that
  must be unique per run ("`code-<timestamp>`"). Accounts are fixture
  references with selection criteria.
- **Independent.** Each case sets up its own preconditions and states its
  cleanup where it leaves data behind.
- **Error vs message.** "An error is shown" when the text is not
  specified; quote the exact message only when a source gives it.
- **`readiness`**:
  - `ready`: every linked rule is confirmed and in scope, no open blocking
    question touches it, its scenarios are approved (reviewed mode), and
    it has concrete data or fixture preconditions.
  - `needs_review`: depends on a proposed or observed rule, or is
    exploratory.
  - `blocked`: depends on an open blocking question or an unreadable
    essential source.
- **`status`**: `draft` until final approval, then `approved`. A case
  dropped later gets `"retired": true` and stays in the file.
- **`ado_id` / `last_synced`** stay `null`. Only a future tracker sync
  writes them; the final-approval hash ignores them.
- **Execution** is always `not_run`.

## Gaps

```json
{"id": "GAP-<slug>-001", "description": "No audit-log rules supplied; audit not tested",
 "affected_ids": ["STORY-<slug>-2"], "status": "open"}
```

Status: `open`, `accepted_exclusion` (QC agreed to leave it out), or
`resolved`. Use gaps for whole areas with no rules; use questions for a
specific missing fact.

## Quality gate

`validate_test_cases.py` computes the structural checks; you review the
meaning.

**Script (blocks on any error):**

- IDs match `<PREFIX>-<slug>-<nnn>`, are unique, and were allocated.
- Every reference resolves to a live (non-retired) record; every
  `source_ref` has a location; every story ID is in `scope.story_ids`.
- Enum values are valid; risk levels match impact × likelihood or carry
  `override_reason`.
- Steps are numbered 1..n with a non-empty, non-vague expected result.
- Ready cases satisfy the readiness rules above.
- Everything is `not_run`.
- Scope excluded at a gate is out of scope in the data.
- Coverage is rebuilt from the links (warning for a confirmed in-scope
  rule with no case and no deferral).

**Your semantic review (report findings, then fix):**

- Each important risk, boundary, transition, role, tenant, and field
  dependency has a case, or the gap is stated.
- No two cases test the same thing; no two oracles contradict each other.
- Setup, cleanup, environment, and clock control are clear where needed.
- Totals in your summary match the validator's numbers.

Report mapped coverage, QC-reviewed coverage, and execution (none) as
three separate facts. Your own review is a filter, not a replacement for
the QC reviewer's final approval.
