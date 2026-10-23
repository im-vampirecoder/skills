---
name: vc-define-user-flow
description: Map a feature's screens and the moves between them before any mockup is drawn - a Mermaid flow diagram with happy, error and edge branches, a screen inventory, flows, and a transitions table, each tied to the PRD's FR / ERR requirement IDs. Reviewed independently, signed off by the PO, checked by a script, and hashed so later skills notice when it changes. Writes <feature folder>/ux/user-flow.md; never edits the PRD or stories. Triggered by /vc:define-user-flow.
---

# Define User Flow

Before anyone draws a screen, agree on the feature's map: which screens
exist, how users move between them, and where they land when something
fails. The approved map is the one place that decides how the feature
splits into flows. `vc-create-ui-mockup` builds from it instead of
working the flows out again, and QA reads its transitions.

## Ground rules

- **A feature PRD is required.** No free-text start; without a PRD, point
  to `/vc:prd`.
- **The PRD is the scope.** Screens and branches come from its
  requirements. A branch the map needs but the PRD doesn't cover (an
  error with no `ERR-`, a limit with no value) becomes an open question
  and a PRD gap, never an invented requirement or value.
- **Requirement IDs in full, live only.** Cite `FR-<slug>.<name>` and
  `ERR-<slug>.<name>` exactly as the PRD defines them. Skip IDs that are
  retired (`Retired.`) or superseded (`> Superseded by`, or listed in
  `artifacts/requirements-current.md` as superseded).
- **Glossary words.** Screen names and labels use the terms in
  `docs/glossary.md`; a word in its Avoid column is replaced.
- **Never edits the PRD, stories or the tracker.** Writes only
  `ux/user-flow.md`, and `ux/clarification-questions.md` when the user
  asks.
- **Scripts.** `<skill-dir>` is this skill's folder. Run from the
  tracking repo root:
  `python3 <skill-dir>/scripts/check_user_flow.py check <map> --prd <prd>`
  and `python3 <skill-dir>/scripts/check_user_flow.py hash <map>`.
- **Language.** Discuss in the user's language; write the file in
  English, keeping UI labels as the PRD or user wrote them.

## `status <feature>` (read-only)

Called by `vc-create-ui-mockup` through the Skill tool, or by hand.
Resolve the PRD as in step 0, run `check_user_flow.py check <map> --prd
<prd> --no-compile`, and report one line plus the findings:

- `missing`: no `ux/user-flow.md`.
- `draft`: written, not approved yet.
- `approved`: approved, `flow_hash` matches, `requirements` matches the
  PRD.
- `stale`: approved, but the hash or the `requirements` list no longer
  matches; list what changed (IDs added or no longer live, or that
  sections 1-4 were edited since approval).

Writes nothing and asks nothing.

## Workflow

0. **Resolve the PRD and any earlier map**
   - First token `status` → the `status` mode above, then stop.
   - `$ARGUMENTS` → a feature slug, `FEATURE-<slug>`, or a path to a
     feature `prd.md` (`artifacts/<slug>/` or
     `artifacts/epic-*/feature-<slug>/`). Empty → list feature PRDs and
     ask.
   - `status: needs-review` → stop; point to `/vc:prd review`.
   - No `## Requirements` section → stop; point to `/vc:prd migrate
     <feature>`, since the map is tied to requirement IDs.
   - `status: done` → the feature's map is read-only, like its PRD.
     Show the existing map's status if there is one and stop. A change to
     a `done` feature's screens belongs to the superseding feature's
     own map.
   - `<feature folder>/ux/user-flow.md` exists → run the check with
     `--prd`, then:
     - `approved`, hash matches and no `requirements-stale` error → say
       it's already approved (by whom, when) and stop, unless the user
       asks to redo it.
     - `approved` but stale (hash mismatch or `requirements-stale`) →
       show what changed (the IDs added or no longer live; for a hash
       mismatch, `git log -p` of the map since its approval when the repo
       tracks it, else say sections 1-4 were edited) and ask: accept the current map as
       the new baseline (only when the user says the PO approved it; go
       to step 8), or revise it (continue, keeping everything the user
       doesn't ask to change).
     - `draft` → ask: revise it, start over, or stop.

1. **Read the inputs**
   - The PRD in full: Scope, Anti-goals, `## Requirements` (FR, BR, ERR,
     and the State transitions and Interrupted flows tables when
     present), Touchpoints, Open Questions, Decisions.
   - `artifacts/prd.md`, `artifacts/requirements-current.md` when present,
     `docs/glossary.md`, `stories-*.md` in the feature folder,
     `clarifications.md` / `clarification-questions.md` when
     `vc-prd-clarify` saved them.
   - Baseline screens under `docs/design-system/<app>/` when present, to
     name screens the feature changes. For a feature with `supersedes` in
     its frontmatter, also the superseded feature's `ux/user-flow.md`.

2. **Short interview (only what the inputs leave open)**
   - **Devices**, asked once: which devices and contexts this feature is
     used on. Written to `devices`; `vc-create-ui-mockup` reuses it.
   - **Unclear rules** that change the map: where a user lands after an
     error, whether a step can be skipped, what happens on back or cancel,
     who can reach each entry point.
   - One question per round when offering options. One follow-up per
     vague answer, then record an open question with the assumption the
     map will use; never a third ask and never an invented value.

3. **Draft the map** from `references/user-flow-template.md` and
   `references/flow-diagram-conventions.md`:
   - Entry points from the PRD's scenarios and Touchpoints.
   - Each P0 FR on at least one screen or transition. Each decision with
     its happy outcome, its failures from the Errors table (one branch per
     user-facing `ERR-`), and its edge cases from State transitions and
     Interrupted flows. Temporary states (locked, expired, pending) get a
     way out.
   - Screens marked `new` or `changed` (naming the baseline screen, or the
     superseded feature's screen).
   - Group screens into flows by the user's goal.

4. **Preview (plain text)** — `references/preview-and-review.md`. At most
   3 rounds with the user.

5. **Independent review** — `references/preview-and-review.md`: the
   `vc-flow-reviewer` subagent when the environment supports subagents,
   otherwise a separate review pass in this session against the same
   lenses. Apply blocking findings and missing screens or branches; rules
   that need a business value become open questions. At most 2 rounds.

6. **Sign-off (hard stop)** — show the reviewed map and what review
   changed. Write only on an explicit yes.

7. **Write and check**
   - Write `ux/user-flow.md` with `status: draft`, `requirements` set to
     the PRD's live FR and ERR IDs (sorted), and `flow_hash` empty.
   - Run `check_user_flow.py check <map> --prd <prd>`. Fix errors and
     re-check, at most twice; a fix that changes the flow goes back to
     the user first. Report each level on its own line, as the script
     prints it: structure, renderer, consistency, requirements, compile
     (`skipped (no Node)` is not OK, say so), and business correctness
     (always "not machine-checked").
   - Then run `check_user_flow.py hash <map>` and write the value to
     `flow_hash`.

8. **Approval**
   - The map stays `status: draft` until the user says the PO approved
     it. Then set `status: approved`, `approved: <role or name>,
     <YYYY-MM-DD>`, recompute `flow_hash` with the `hash` subcommand, and
     re-run the check.
   - Accepting a stale map as the new baseline (step 0) is the same
     update, plus `requirements` refreshed from the PRD.

9. **PRD gaps → PO/BA questions**
   - Every branch, value or rule the PRD didn't answer: offer them as a
     PO/BA questionnaire using
     `../vc-prd-clarify/references/questionnaire-format.md` (PO/BA
     questionnaire section), shown in the console, each question naming
     the requirement ID it affects.
   - Save it to `<feature folder>/ux/clarification-questions.md` only if
     the user wants. `vc-create-ui-mockup` saves its questions to the
     same file: when it exists, add a `## From the user flow (<date>)`
     section instead of replacing it. Answers go into the PRD through
     `/vc:prd`; the map is then revised with this skill.

10. **Next step**
    - Suggest `/vc:create-ui-mockup <feature>`, which builds from the
      approved map. `/vc:create-test-cases` can use its transitions for
      navigation and error-path scenarios.

## Notes

- The map doesn't replace the mockups' per-screen states (loading,
  empty, disabled) or exact wording; `vc-create-ui-mockup` adds those.
- Numbers are stable: once approved, a screen keeps its `[n]`, and a
  removed screen leaves a gap rather than renumbering the rest.
- The map lives in `ux/`, so `/vc:propose-epic` moving the feature
  folder carries it along.
