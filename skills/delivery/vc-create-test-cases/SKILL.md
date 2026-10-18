---
name: vc-create-test-cases
description: Draft reviewed, traceable manual test cases for one feature — requirement analysis, risk-based scenarios, then detailed cases — with two QC review gates (skippable with `--fast`) and a final approval, resumable across sessions. Takes a feature PRD (one combined case set) or a story ID (that story's part of the same set). Writes test-cases.json (canonical, ready for a later Azure DevOps sync) plus rendered Markdown under the feature's test-cases/ folder. Triggered by /vc:create-test-cases. Never runs tests or touches the tracker.
---

# Create Test Cases

Turn a feature's PRD, stories, and clarifications into manual test cases a
QC reviewer can approve: every case traces to a rule and a source, every
rule without a case is listed, and nothing claims a test was run.

Load `references/qa-core-rules.md` before step 2 and keep it in force for
the whole run. The other references load at the step that names them.

## Ground rules

- **Input is a feature under `artifacts/`.** A PRD, story, or slug that
  does not resolve there → stop and point to `/vc:prd` or
  `/vc:create-user-stories`.
- **One case set per feature**, in `<feature folder>/test-cases/`. A
  story input works on that same set, never a second one.
- **The QC reviewer approves; the PO/BA decides business rules.** Your
  "this looks complete" is never an approval. Only an answer from the
  user, recorded with `test_case_state.py approve`, is.
- **Artifacts in English**, whatever language the conversation uses.
- **Scripts own state.** IDs come from `next-ids`, stages from `status`,
  coverage from the validator, Markdown from the renderer. See
  `references/state-resume-and-revisions.md`.
- **Never** runs tests, writes automation, edits the PRD or stories, or
  touches the tracker.

## Workflow

0. **Resolve the target**
   - Strip `--fast` from `$ARGUMENTS` and remember it.
   - A feature: `FEATURE-<slug>`, a slug, or a path to a feature
     `prd.md`. Resolve `artifacts/<slug>/` or
     `artifacts/epic-*/feature-<slug>/`. Scope: all its stories.
   - A story: `STORY-<slug>-<n>`, a story's `ado_id`, or a path to a
     `stories-<n>-*.md`. Resolve its feature; the story is the **focus**.
   - Empty → list feature folders that have a `prd.md` and ask which one.
   - Nothing matches → stop and say so; never guess scope from the name.
   - PRD `status: needs-review` → warn that it is an unconfirmed stub
     (`/vc:prd review` completes it) and ask whether to continue.

1. **Load or start state**
   - `D=<feature folder>/test-cases`. Run `test_case_state.py status $D`.
   - `not_started` → `init $D --feature-slug <slug>` (add `--mode fast`
     when `--fast` was given).
   - Otherwise show the user the stage, gate states, counts,
     `changed_sources`, and `stories_pending_generation`, then continue at
     the step the stage maps to (table in
     `references/state-resume-and-revisions.md`). `--fast` on a reviewed
     run → ask before switching with `mode`.
   - Reviewer name: default to `git config user.name`, confirm once,
     reuse it for every `approve` in this run.

2. **Collect sources**
   - Read the PRD, every story in the feature, and whatever exists of
     `clarifications.md`, `clarification-questions.md`, `ux/user-flow.md`,
     `ux/ux-spec.md` and its mockups, the most specific `architecture.md`,
     and `docs/architecture.md` (Auth and Access Model, Invariants).
   - `ux/user-flow.md`, when present, is read-only input: its Transitions
     table (from, to, trigger, condition) feeds navigation and error-path
     scenarios, each tied to the row's requirement ID. A `status: draft`
     map is still used, with a note in its source that the flow isn't
     approved yet.
   - No `clarifications.md` and no `clarification-questions.md` → warn:
     "No `/vc:prd-clarify` output for this feature. Gaps a QA read-through
     would catch may surface here as questions instead." Then continue.
   - Record each in `sources` with IDs from `next-ids SRC` and its
     fingerprint (`references/requirement-analysis.md` §1).

3. **Analyze** — follow `references/requirement-analysis.md`.
   - Rules, questions, risks, scope into `test-cases.json`, IDs from
     `next-ids`. Reuse IDs already there; retire, never delete.
   - Each rule lists the PRD requirement IDs it checks in `prd_ids`
     (full `FR-` / `NFR-` / `BR-` / `ERR-` IDs, live ones only; read
     `artifacts/requirements-current.md` when it exists to tell which
     are retired or superseded).
   - On re-entry after a source change: update only what the change
     touched and say what moved.
   - Story focus: analyse the whole feature on the first run (rules shared
     between stories live once); on later runs revisit only the focus
     story's rules.

4. **Gate A — analysis review** (skipped in fast mode)
   - `render_test_cases_markdown.py $D --view analysis`; point the user at
     `analysis.md` and summarise: rule counts by status, blocking
     questions, high risks, proposed exclusions.
   - `AskUserQuestion`: approve / approve with exclusions / request
     changes. Exclusions → list the candidate rules (multi-select).
   - Request changes → apply them, re-render, ask again. Record nothing
     until the user approves; then apply exclusions (`in_scope: false`)
     and run `approve --gate A --decision approve --excluded <ids>`.
   - Open questions may stay open: they block only their own rules. Offer
     to hand them to the PO/BA as a list.

5. **Plan scenarios** — follow `references/test-design-techniques.md`.
   - Scenarios linked to rules and risks, one technique choice each, and a
     reason for every confirmed in-scope rule left without one.
   - Story focus: add or revise scenarios for that story only.

6. **Gate B — scenario review** (skipped in fast mode)
   - Render `--view scenarios`, summarise per story, ask as in step 4.
   - On approval: set each kept scenario `status: "approved"`, dropped
     ones `"excluded"`, then `approve --gate B`.
   - After this gate, generate every approved batch without asking again.

7. **Generate cases** — follow `references/case-format-and-quality-gate.md`.
   - One batch per story (feature-level scenarios last), in story order;
     story focus → that story's batch only.
   - `next-ids TC --count <n>` per batch, write the batch into
     `test-cases.json`, run `status` to confirm progress, then the next.
   - Questions that come up mid-batch go into `questions`; the affected
     cases are `blocked`, not guessed.

8. **Validate**
   - `validate_test_cases.py $D --write`. Fix every error and re-run until
     it exits 0.
   - Do the semantic review in the quality-gate reference; fix what you
     find, and record anything not fixable as a gap.

9. **Final review**
   - Render all views. Summarise: cases per story and priority, readiness
     counts, coverage (mapped / uncovered / deferred / out of scope),
     open questions and gaps, and that nothing has been executed.
   - `AskUserQuestion`: approve / request changes. Changes → edit,
     validate, re-render, ask again.
   - On approval: set every live case `status: "approved"`, re-run the
     validator with `--write`, render, then `approve --gate final`.

10. **Report**
    - Paths written, the final counts, open questions with their owners,
      and gaps.
    - Next steps: share `test-cases.md` with QC; send open questions to the
      PO/BA (or `/vc:prd` once they answer); Azure DevOps Test Plans sync
      is not built yet, and `test-cases.json` is the file it will read.

## Notes

- Pausing anywhere is safe: state is on disk. Suggest `/vc:handoff` if
  another session or person will continue.
- A later edit to the PRD or a story shows up as `changed_sources` on the
  next run and sends the set back through the gates for what changed.
  A retired, replaced, superseded or clarified PRD ID arrives the same
  way and marks the cases citing it for revision
  (`references/state-resume-and-revisions.md`, Source changes).
- Excel output is not built yet; it will be another renderer over
  `test-cases.json`.
