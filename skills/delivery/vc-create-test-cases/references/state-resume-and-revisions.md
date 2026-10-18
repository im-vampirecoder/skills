# State, Resume, and Revisions

Every run reads and writes `<feature folder>/test-cases/`. Scripts live in
this skill's `scripts/` folder; call them with `python3`, from the
tracking repo root.

```
S=<this skill's folder>/scripts
D=<feature folder>/test-cases
```

## Files

| File | Written by | Purpose |
|---|---|---|
| `test-cases.json` | you (the model) | Canonical data: scope, sources, rules, questions, risks, scenarios, cases, gaps; coverage and quality checks are written by the validator |
| `.state.json` | `test_case_state.py` only | Mode, ID registry, approvals |
| `analysis.md`, `scenarios.md`, `test-cases.md` | `render_test_cases_markdown.py` only | What people review; never hand-edited |

Edit `test-cases.json` with `Edit` or a short script; keep it valid JSON,
UTF-8, two-space indent. Never edit `.state.json` or the rendered files
by hand.

## Commands

| Command | When |
|---|---|
| `python3 $S/test_case_state.py status $D` | Start of every run, and after each step |
| `python3 $S/test_case_state.py init $D --feature-slug <slug> [--mode fast]` | First run only |
| `python3 $S/test_case_state.py mode $D reviewed\|fast` | User switches mode mid-way |
| `python3 $S/test_case_state.py next-ids $D <PREFIX> --count <n>` | Before adding any entity; PREFIX is SRC, REQ, Q, RISK, SC, TC, or GAP |
| `python3 $S/test_case_state.py approve $D --gate A\|B\|final --reviewer <name> --decision approve\|request_changes [--excluded <id> ...] [--note <text>]` | After the user answers a gate |
| `python3 $S/validate_test_cases.py $D --write` | Step 8; exit 1 means errors to fix |
| `python3 $S/render_test_cases_markdown.py $D [--view analysis\|scenarios\|cases]` | Before each gate and at the end |

## IDs

- Always take IDs from `next-ids`; never number by hand. Allocated
  numbers are never handed out again, even if you end up not using them.
- To drop a record, set `"retired": true` on it and leave it in place.
  Retired records are skipped by coverage and must not be referenced by
  live ones.

## Approvals and stages

An approval stores a hash of what was approved. Hashes are chained:

- **Gate A** covers scope, sources, rules, questions, risks.
- **Gate B** covers Gate A's content plus scenarios.
- **Final** covers Gate B's content plus cases (not `ado_id` /
  `last_synced`).

So editing a rule after Gate B makes A, B, and final all `stale`, and the
user must approve again. Make every edit the reviewer asked for, and set
excluded rules `in_scope: false` / excluded scenarios
`status: "excluded"`, **before** calling `approve`; otherwise the
approval binds to the old content.

`status` derives the stage each time; it is never stored:

| Stage | Meaning | Next step in SKILL.md |
|---|---|---|
| `not_started` | No `.state.json` | Step 1 |
| `analyzing` | No rules yet, or a source changed since it was read | Step 3 |
| `awaiting_analysis_review` | Gate A missing, stale, or changes requested | Step 4 |
| `planning` | No scenarios yet | Step 5 |
| `awaiting_scenario_review` | Gate B missing, stale, or changes requested | Step 6 |
| `generating` | Planned scenarios without a case (`stories_pending_generation`) | Step 7 |
| `awaiting_final_review` | Every scenario has cases; final approval missing or stale | Steps 8-9 |
| `approved` | Final approval matches the current cases | Step 10 |

In `fast` mode Gates A and B report `skipped`.

## Source changes

Each source's `revision` is its `sha256` prefix at the time you read it
(`test_case_contract.file_fingerprint`). Get it with:

```bash
python3 -c "import sys; sys.path.insert(0, '$S'); from test_case_contract import file_fingerprint as f; print(f(sys.argv[1]))" <path>
```

`status` re-hashes every `read` source and lists `changed_sources`. When
one changed:

1. Re-read it and update the affected rules, questions, and risks. Keep
   rule IDs for revised behaviour; retire rules that disappeared.
2. Write the new `revision`. That changes the Gate A hash, so every
   approval goes stale and the gates run again on the changed content.
3. Tell the user which rules, scenarios, and cases the change touched.

**Retired, replaced, superseded or clarified PRD IDs.** These all edit
the PRD itself (`Replaced by <id>`, a `> Superseded by` banner, a
`> Clarified on` line), so they arrive as a changed `prd` source. While
re-reading it in step 1, check every live rule's `prd_ids`:

- An ID now retired or superseded → point the rule at the replacement
  (or retire the rule if nothing replaces it), revise its statement, and
  set every live case citing that rule back to `status: "draft"` with
  `readiness: "needs_review"`, so the final review covers it again.
- An ID with a new `> Clarified on` line → re-check the rule's statement
  and expected results against the clarification; set the citing cases
  to `needs_review` only when they no longer match.
- List the affected IDs, rules and cases in the step 3 message.

## Resume

A new session runs `status` and continues at the step its stage names.
During generation, write each story's cases into `test-cases.json` as
soon as that batch is done; an interrupted run loses at most one batch,
and `stories_pending_generation` shows what is left. Never mark the run
complete while a batch is missing.
