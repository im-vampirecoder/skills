# Review Gate

Full procedure for `vc-architecture-design` step 9, and for Review Mode.
Runs after the spine is written, before the summary. It never rewrites the
spine on its own — every change goes through the user.

## 1. Lint (always)

Run, from this skill's directory:

```
python scripts/lint_spine.py <target-root>/architecture.md
```

(`python3` where `python` isn't on PATH.) It checks frontmatter per
scope, leftover placeholders, `AD-n` numbering, required `AD` fields,
supersession links, unpinned Stack versions, Criteria Coverage gaps,
proposed parent changes without a status, and debt without a payoff
trigger.

- Any `ERROR` line: fix it in the spine now — these are mechanical (a
  missing field, a leftover `<placeholder>`), not decisions — and re-run
  until it exits 0. A fix that would change what a decision says isn't
  mechanical: take it to the user instead.
- `WARN` lines (coverage gaps) carry into triage below as blockers.
- Python isn't available: walk the same checks by hand and say in the
  summary that the lint was manual.

## 2. Reviewers (parallel)

Spawn the `vc-architecture-reviewer` agent once
per lens, all in the same turn so they run in parallel:

| Lens | Run when |
| --- | --- |
| `evidence` | any brownfield submodule, inherited ids, or a Stack table |
| `divergence` | always |
| `failure-modes` | the spine crosses submodules, adds data or a datastore, or touches auth |

A small Update run that touched one or two `AD`s can run `divergence`
alone — say so in the summary. Give each instance: the spine and
`.decisions.md` paths, the parent spine path(s), the in-scope PRD paths,
`submodule_root`, its lens, and its review file path:
`<target-root>/reviews/architecture-review-<lens>.md`. Each overwrites its
own file, so the folder always holds the latest review only.

Read each instance's returned summary, then each review file for the
findings themselves — not every file in full if a lens reported nothing.

## 3. Triage (with the user)

- Drop any finding without evidence, and any duplicate across lenses
  (keep the better-evidenced one).
- **Blockers and coverage gaps**: one at a time. State the finding and
  the suggested change, and let the user pick:
  - **Fix** — goes back through step 6's elicitation for that one point:
    a new `AD`, an amendment, a supersession, or a Criteria Coverage
    row, logged to `.decisions.md` like any other decision, then the
    spine is re-distilled and the lint re-run.
  - **Accept** — the user keeps it as is. Append to `.decisions.md`:
    `- [<date>] ACCEPTED RISK R-<n> (<lens>): <finding> — reason: <why>`.
- **Should-fix**: list them together and ask which, if any, to fix now;
  the rest are listed in the summary as open.
- **Notes**: list in the summary only.

Don't re-run the reviewers after fixes — the lint re-run is enough unless
a fix added a new `AD` that crosses submodules, in which case re-run
`divergence` alone.

## 4. Status

Set the spine's frontmatter `status: reviewed` once no blocker is left
unresolved (each fixed or accepted). Otherwise leave `status: draft` and
list the open blockers in the summary.

## Review Mode

`/vc:architecture-design review [scope argument]` runs this gate alone
against an existing spine — resolve the scope as step 1 does, then lint,
reviewers, and triage as above, with no elicitation beyond fixes the user
chooses. No spine at that scope: stop and say so.
