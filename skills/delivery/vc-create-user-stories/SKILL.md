---
name: vc-create-user-stories
description: Write INVEST-checked user stories with Given/When/Then acceptance criteria for a feature, whether or not it is assigned to an epic yet. Triggered by /vc:create-user-stories. Built-in only — never delegates to a third-party story-writing skill.
---

# Create User Stories

Break a feature's PRD into user stories. Always runs its own logic below —
never checks `.vc/config.toml` preferences and never delegates to
`/user-story`, `bmad-create-epics-and-stories`, or any other third-party
skill, regardless of what's installed.

## What a User Story is

Per the backlog hierarchy rules, a Story is a **vertical slice**: it
touches whatever layers it needs (DB/API/UI) to be independently
demoable and testable on its own, in the format "As a [role], I want
[goal], so that [benefit]," where the "so that" clause is user/business
value, never a technical concern. It must pass INVEST. A Task (a
technical step with no independent value, e.g. "add a PUT endpoint") is
never written as its own story here — it belongs under whichever story's
implementation needs it, which is `vc-tasks-breakdown`'s concern once
that story is approved, not this skill's. Steps 2-3 below are the mechanical,
per-story checks that keep this true instead of aspirational.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as a path to a feature's `prd.md` or a feature
     slug. It resolves to either location — epic assignment is not
     required:
     - `artifacts/<feature-slug>/prd.md` (not assigned to an epic yet), or
     - `artifacts/epic-<epic-slug>/feature-<feature-slug>/prd.md`
       (assigned).
   - Call the folder holding that `prd.md` the **feature folder**; every
     story file is written there (step 6).
   - Read the feature's `prd.md` (including its `## Acceptance Criteria`
     — the feature's own Definition of Done). If the feature is
     epic-assigned, also read its epic's `epic.md` for context; if not,
     skip that and don't block on it.
   - A `status: needs-review` stub (from `vc-docs`) is an unconfirmed
     guess — stop and point the user to `/vc:prd review` first.
   - Read the PRD's `## Requirements` section: the functional (`FR-`),
     non-functional (`NFR-`), business rule (`BR-`) and error (`ERR-`)
     entries, each with its full ID (`<TYPE>-<feature-slug>.<name>`).
     If `artifacts/requirements-current.md` exists, read this feature's
     part of it too and treat only IDs in state current (or being
     replaced, still current until the replacing feature is delivered)
     as **live**. A retired ID (`Replaced by <id>`) or a superseded one
     (`> Superseded by <id>`) is never cited by a new story; cite its
     replacement when it lives in this feature, otherwise leave it out.
     Without the view file, read the same states from the PRD itself.
     A PRD with no `## Requirements` section (written before named IDs)
     → say so, suggest `/vc:prd migrate <feature>`, and continue
     without `Implements:` lines rather than inventing IDs.

2. **Draft candidate stories**
   - Decompose the feature into vertical slices, each completable in
     roughly 1-3 days, each delivering end-to-end value on its own.
   - **Splitting method**: split by workflow step, business rule, data
     variation, or happy-path vs. edge-case. Never split by technical
     layer (DB / API / UI) or by CRUD verb alone — those produce
     task-slices, not stories.
   - Apply INVEST: Independent, Negotiable, Valuable, Estimable, Small,
     Testable. Format: "As a [persona], I want to [action], so that
     [benefit]."
   - Note which live requirement IDs each candidate implements: the FRs
     it builds, plus the BRs and ERRs that apply to those FRs and the
     NFRs it must meet. A requirement can be implemented by more than one
     story; each story should implement at least one FR.

3. **Run the hard-rule checks on every candidate — reject and re-slice
   before writing anything**
   - **Demoable-AC check**: if a candidate can't be demoed on its own to
     a stakeholder, it fails. Don't write it; re-slice it instead (merge
     it into a sibling, or reframe around the real user value) rather
     than shipping a non-demoable story with a `[TECH]` label or similar
     — there is no technical-only exception at this level. If a genuine
     non-demoable technical prerequisite remains after re-slicing, it's a
     Task: don't give it its own story file. Note it in step 6's summary
     as a dependency for whichever story needs it, so
     `/vc:tasks-breakdown` picks it up as a task when that story gets
     broken down.
   - **"So that" test**: read the benefit clause. If it names a
     technical concern (schema, API shape, framework) instead of a
     user/business outcome, the story fails — either the wording is
     hiding a real user benefit (rewrite it to surface that benefit), or
     there isn't one (it's a Task per the rule above).
   - **Vertical-slice check**: after drafting the full candidate set,
     check whether any story only becomes demoable when combined with
     one or more siblings. If so, it's a task-slice wearing a story's
     format — merge it into the sibling(s) it depends on, or re-split
     the whole group along a different axis per step 2's splitting
     method.
   - Re-run these checks after any re-slice. Only candidates that pass
     all three move on to step 4.

4. **Write acceptance criteria per story**
   - Given/When/Then format, 3-7 criteria per story. Each criterion is one
     numbered list item (`1.`, `2.`, ...), in order; break `Given`/`When`/
     `Then` onto their own line inside that item (hard line break, i.e.
     trailing two spaces), with `**Given**`, `**When**`, `**Then**`
     bolded, and a blank line between each numbered item so they read as
     clearly separate — see the template in step 6.
   - Cover the happy path, at least one edge case, and at least one error
     state. Business rules (valid formats, duplicate checks, what happens
     on invalid input, etc.) surface here as their own edge-case/error-state
     criteria — they don't get a separate section.
   - Draw those criteria from the PRD's entries for the FRs this story
     implements: each applicable `BR-` becomes an edge-case criterion
     using the rule's exact limit or value, and each applicable `ERR-`
     becomes an error-state criterion whose **Then** uses the error's
     "The user sees" wording as written (or says the wording is `TBD`
     when the PRD does). Never invent a limit or message the PRD
     doesn't state.

5. **Add story metadata**
   - Priority: must-have, should-have, or nice-to-have.
   - Dependencies on other stories from this same feature, if any.
   - Implements: the full requirement IDs from step 2, comma-separated
     (`FR-<feature-slug>.<name>, BR-<feature-slug>.<name>`), always
     written in full, never shortened. Live IDs only.
   - Design: link to a wireframe/mockup if one already exists for this
     story's UI, else "n/a". Never required, never fabricated — this is a
     pointer to an existing artifact, not a prompt to produce one. If
     `<feature folder>/ux/ux-spec.md` exists (from `/vc:create-ui-mockup`),
     link the mockups whose screens cover this story's criteria.

6. **Write one file per story**
   - Path: `<feature folder>/stories-<n>-<short-description>.md` —
     `artifacts/<feature-slug>/…` for an unassigned feature,
     `artifacts/epic-<epic-slug>/feature-<feature-slug>/…` for an
     assigned one. `<n>` numbered in implementation order, continuing
     after the highest `<n>` already used by any `stories-<n>-*.md` in
     that folder (from an earlier run of this skill or of
     `vc-create-pbi`, which share one numbering space per feature) -
     starting at 1 only when there are none. Never reuse a number: the
     story `id` (`STORY-<feature-slug>-<n>`) must stay unique.
     `<short-description>` a few kebab-case words.
   - Content:
     ```markdown
     ---
     id: STORY-<feature-slug>-<n>
     feature_id: FEATURE-<feature-slug>
     ado_id: null
     last_synced: null
     status: new
     iteration: null
     ---

     # <n>. [<feature-slug>] <Story title>

     **As a** <persona>
     **I want to** <action>
     **So that** <benefit>

     ## Acceptance Criteria

     1. **Given** ...,  
        **When** ...,  
        **Then** ...

     2. **Given** ...,  
        **When** ...,  
        **Then** ...

     3. ...

     ## Details

     - Priority: must-have | should-have | nice-to-have
     - Dependencies: <story IDs, or "none">
     - Design: <wireframe/mockup link, or "n/a">
     - Implements: <full requirement IDs, comma-separated>
     ```
   - `feature_id`, not `epic_id` — a story's Azure DevOps parent is its
     feature, not the epic directly (`vc-sync-to-tracker` now syncs a
     Feature work item too). The epic is still derivable, one hop away,
     via the feature's own `epic_id`; there's no need to duplicate it
     here.
   - `status` and `iteration` are sprint tracking. Always write them as
     `new` / `null` here.
     - `status` is one of `new | ready | in-progress | done | removed`.
       Only a `ready` story can be planned into a sprint. A story becomes
       `ready` only when the user agrees at the readiness offer in
       `vc-prd-clarify` or `vc-tasks-breakdown` - never set it here.
     - `iteration` is the sprint's iteration path once the story is
       planned into one (`vc-plan-sprint-candidates settle` sets it).
     - On an Azure DevOps project the work item's State and Iteration
       Path are the truth. The one exception is `ready`:
       `vc-sync-to-tracker` pushes it as `.vc/config.toml`'s
       `[ado].ready_state`. The other values and `iteration` are only read
       on `tracker = "local"` projects.

7. **Summarize**
   - After writing all files, list them with a one-line description each,
     the suggested implementation order, and which stories form the MVP
     subset (deliver the core value with the fewest stories).
   - List any Task-level dependency flagged in step 3 (technical
     prerequisites with no story of their own), naming which story each
     one belongs under.
   - **Coverage warning**: list every live P0 `FR-` that no story in the
     feature folder implements (counting stories written earlier, not
     only this run's, and ignoring `status: removed` ones). Warn plainly
     — "no story implements FR-<feature-slug>.<name> (P0)" — and offer to
     draft one; never silently skip it.
   - Suggest `/vc:requirements check` so the new `Implements:`
     citations are verified.

## Notes

- **Stories before an epic.** Writing stories for an unassigned feature
  is fine: `/vc:propose-epic` later moves the whole feature folder
  (`git mv`), so its story files (and any `tasks/` folder) travel with it
  unchanged — they carry only `feature_id`, never an epic path.
  `/vc:tasks-breakdown` works on an unassigned feature too; only
  `/vc:sync-to-tracker` requires the feature to be epic-assigned first.
  When writing stories for an unassigned feature, say so in step 7's
  summary and name `/vc:propose-epic` as needed before tracker sync.
- This skill never syncs to a tracker — `ado_id` and `last_synced` stay
  `null` until `vc-sync-to-tracker` runs.
- This skill never touches `epic.md`'s Features section, a feature's own
  `prd.md`, or `artifacts/epics.md` — those are `vc-propose-epic`'s (and
  `vc-prd`'s) responsibility.
- There is no reassignment flow for a single story to a different
  feature — a story's `feature_id` is fixed at creation. If a feature
  itself moves to a different epic, that's `vc-propose-epic` updating
  the feature's own `epic_id`; it never touches any story file.
