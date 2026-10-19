---
name: vc-tasks-breakdown
description: Turn one confirmed user story into an implementation task breakdown, scoped to the code that already exists. Estimates complexity in Story Points (per task and on the story itself), never hours. A leading `validate` token re-verifies an existing breakdown against the current codebase instead. Built-in only — never delegates to a third-party spec-writing skill.
---

# Tasks Breakdown

Read one confirmed user story's business-level artifacts, scout the code it
actually touches, and produce an implementation-level task breakdown —
never the reverse. This is vc's last developer-pipeline step: it does not
invoke or assume any particular next step (test-first implementation, code
review, whatever the team uses) — the output is meant to be read by
whichever tool the team runs next.

## Workflow

0. **Resolve the mode**
   - Parse `$ARGUMENTS` for a leading `validate` token. If present, the
     rest of `$ARGUMENTS` (if any) is a story identifier — go to
     **Validate Mode** below instead of the steps that follow. No
     `validate` token → continue with step 1 as normal.

1. **Resolve the story**
   - Take `$ARGUMENTS` as a story identifier: `STORY-<feature-slug>-<n>`, a
     story's `ado_id`, or a path to its `stories-<n>-*.md` file.
   - If `$ARGUMENTS` instead resolves to a *feature* (an ADO ticket ID, a
     `FEATURE-<slug>` ID, or a feature slug/name) with more than one story
     under it, list its stories and ask which one — never assume "all of
     them," each story's breakdown is independent work. A feature with
     exactly one story proceeds with that one directly, no need to ask.
   - If nothing matches, or the resolved feature has no stories yet, stop
     and tell the user — don't guess at scope from the identifier alone.
   - Epic assignment is not required. The story's feature lives in either
     `artifacts/<feature-slug>/` (not assigned to an epic yet, which
     `vc-create-user-stories` allows) or
     `artifacts/epic-<epic-slug>/feature-<feature-slug>/` (assigned). Call
     the folder holding the story's `stories-<n>-*.md` file the **feature
     folder**; every path below is relative to it.

2. **Gather context**
   - Read the target story's own file and its feature's `prd.md`, plus
     its epic's `epic.md` when the feature is epic-assigned (unassigned →
     skip it, don't block on it) — not sibling stories under the same
     feature. Each
     story's breakdown stands alone: the underlying code changes for two
     stories may legitimately overlap, but one story's tasks must be
     independently complete against its own acceptance criteria, never
     dependent on another story's spec.
   - From the PRD's `## Requirements`, read the entries the story's
     `- Implements:` bullet names (and the `BR-` / `ERR-` / `NFR-` entries
     that apply to them): their exact limits, error wording and outcomes
     are what the tasks must deliver.
   - Read whichever `architecture.md` is most specific to this story —
     feature-level (`<feature folder>/architecture.md`),
     then epic-level (`artifacts/epic-<epic-slug>/architecture.md`, only
     when the feature is epic-assigned), then product-level (`artifacts/architecture.md`) — and the
     `.decisions.md` beside it, when either exists. A feature spine's
     Criteria Coverage table maps this story's acceptance criteria to the
     decisions and components that serve them; follow it rather than
     re-deciding the shape (both files are optional —
     `/vc:architecture-design` produces them, but it's never a required
     step, so they're often absent; that's fine, proceed to the next
     source). When present,
     read its Submodule Ownership table to identify which
     `src/<repo-name>/` submodule(s) this story's work belongs in.
   - Not found there: read `docs/architecture.md` (or, if auto-split,
     `docs/architecture/`'s System Boundaries shard) — `vc-docs`'s own
     code-derived brownfield doc, when it exists. Its `System Boundaries`
     section lists each `src/<repo-name>/` submodule and what it owns;
     match the story's action/keywords against that to identify the
     submodule(s). This is evidence read straight from the code, so a
     match here resolves it the same as a match in
     `artifacts/architecture.md` — don't ask when this alone answers it.
   - Neither exists, or neither names a matching submodule: ask the user
     directly which `src/<repo-name>/` submodule(s) this story belongs
     in — never infer silently.
   - When `docs/architecture.md` exists (regardless of whether it was
     needed for submodule resolution above), also read its `Invariants`
     and `Auth and Access Model`/`Storage Model` sections as binding
     context for step 5 — real, code-enforced constraints (e.g. "request
     handlers don't run long-lived background work") that should shape
     how a task is designed, not just where it lives.

3. **Scout the resolved submodule(s)**
   - **One resolved submodule**: scout it inline yourself with
     `Glob`/`Grep`/`Read` — spawn overhead isn't worth it for one.
   - **2+ resolved submodules**: spawn the `vc-scout` subagent
     (`vc:vc-scout` when installed through the plugin) in `focused`
     mode once per submodule, in parallel. Its brief is the story's
     action/persona/keywords, each Given/When/Then criterion, and the
     conventions listed below; work from its `path:line` findings,
     reading a cited file yourself only where a task needs more than the
     finding says.
   - What the brief asks for, per resolved submodule: code overlapping the story's
     action/persona/keywords: existing routes, functions, or modules that
     already implement — fully or partially — one of the story's
     Given/When/Then criteria, and the conventions already in use there
     (naming, folder structure, error-handling/validation style, test
     structure) so new tasks follow them instead of introducing a parallel
     style.
   - For each piece of evidence found, note whether it means a task is
     **New** (nothing exists yet), **Extend** (partial coverage, cite the
     real file), or **Verify** (looks already complete — the task is to
     confirm and add/adjust tests, not build). Cite real file paths; never
     invent one.

4. **Built-in task breakdown**
   - List the concrete implementation tasks needed to satisfy the story's
     acceptance criteria: which files/modules are touched, what the new or
     changed behavior is, which Given/When/Then criterion each task
     addresses, and its New/Extend/Verify status from step 3.
   - Order tasks so each is independently completable and testable —
     vertical slices, not "all models then all views."
   - Flag any task whose scope depends on code outside the resolved
     submodule(s), or code you still haven't seen, as needing
     investigation first, rather than guessing.
   - Respect step 2's `Invariants`/Auth/Storage findings when present —
     a task that would violate one is a sign the approach is wrong, not
     a detail to note and move past.
   - **Rate each task's complexity in Story Points** (Fibonacci scale: 1, 2,
     3, 5, 8) — relative complexity, not effort. Weigh how many moving
     parts it touches, how much is unknown, and risk, grounded in its
     New/Extend/Verify status and how much of the surrounding code you
     actually saw in step 3. Never give hours, days, or any time-based
     estimate anywhere in the output. A task rated 8 is a sign it should
     probably be split.
   - **Propose one Story Points value for the story as a whole** (same
     scale, plus 13) — a holistic complexity call across every task
     together, not necessarily the sum of the task values.
   - **Story-size sanity check**: if the drafted list comes out to more
     than 6 tasks, or touches more than 8 distinct files across all
     tasks, that's large for a "1-3 day" story (`vc-create-user-stories`'s own
     sizing rule). Stop before writing anything and ask once via
     `AskUserQuestion` ("Continue — write the full breakdown anyway" vs.
     "Stop — this should probably be re-split via `/vc:create-user-stories`
     first"). Ask exactly once; if the user says continue, don't raise it
     again for this run.
   - **Cross-story overlap check**: for each drafted task, search every
     other story's task files project-wide
     (`artifacts/*/tasks/story-*-task-*.md` for unassigned features plus
     `artifacts/epic-*/feature-*/tasks/story-*-task-*.md`, any feature)
     for one whose `Files:` line or described behavior already covers the
     same ground. A match found → flag it before writing
     anything: `AskUserQuestion` (batched, up to 4 per call), naming the
     conflicting `TASK-<feature-slug>-<n>-<m>` and its story/title, with
     options "Skip this task here (mark the overlap, don't sync)"
     (Recommended) and "Keep it as its own task anyway (accept the
     duplicate work)". A skipped task still gets written in step 5 (for
     traceability) with `Status: Skipped` and a note identifying the
     other task/story it overlaps — it's just excluded from tracker sync.

5. **Write the task files and summary**
   - Path: `<feature folder>/tasks/` (create if needed) —
     `artifacts/<feature-slug>/tasks/` for an unassigned feature,
     `artifacts/epic-<epic-slug>/feature-<feature-slug>/tasks/` for an
     assigned one — alongside its `prd.md`/`stories-*.md`, not a separate
     top-level tree. `/vc:propose-epic` later moves the whole feature
     folder with `git mv`, so the `tasks/` folder travels with it
     unchanged; task files carry only `story_id`, never an epic path. Every story under the same feature shares this one
     `tasks/` folder; the story number in each filename is what keeps
     them apart.
   - **Regenerating an existing breakdown**: if this story already has
     task files from a prior run (`story-<n>-task-*.md` in this folder),
     this is a refresh, not a blind overwrite — match each newly drafted
     task to an existing file (by which criterion it addresses, or clear
     title similarity). Matched → update that file in place, keeping its
     `id` and, critically, whatever `ado_id`/`last_synced` it already
     has — never reset a task's sync state to `null` just because the
     breakdown re-ran. Unmatched draft → new file, next available `<m>`.
     An existing file that no longer matches any drafted task → leave it,
     don't silently delete it, and flag it to the user as possibly stale
     (same instinct as `vc-docs`: never drop a section still backed by
     prior evidence without saying so).
   - One file per task, `story-<n>-task-<m>-<task-slug>.md`, `<m>`
     numbered in implementation order starting at 1:
     ```markdown
     ---
     id: TASK-<feature-slug>-<n>-<m>
     story_id: STORY-<feature-slug>-<n>
     ado_id: null
     last_synced: null
     ---

     # <m>. <Task title>

     - Status: New | Extend | Verify | Skipped
     - Addresses: criterion "..."
     - Files: ...
     - Story Points: <1 | 2 | 3 | 5 | 8>

     ## Notes
     ...
     ```
     A task marked `Skipped` (from step 4's overlap check) adds one more
     line right after `Status`: `- Overlaps: TASK-<feature-slug>-<n>-<m>
     (STORY-<feature-slug>-<n>, "<other story title>") — <one line on
     what it already covers>` — the "task A was done in story S, also
     needed here" record. `vc-sync-to-tracker` never syncs a `Skipped`
     task.
   - The summary file, `story-<n>-spec.md`, alongside the task files (same
     `tasks/` folder, same naming scheme — no separate subfolder):
     ```markdown
     ---
     story_id: STORY-<feature-slug>-<n>
     feature_id: FEATURE-<feature-slug>
     ---

     # Spec: <Story Title>

     Source: ../stories-<n>-<short-description>.md
     Implements: <the story's Implements IDs, copied as written, or "none">

     ## Approach
     ...

     ## Tasks

     | # | Title | Status | Story Points |
     |---|---|---|---|
     | 1 | ... | New | 3 |
     | 2 | ... | Extend | 2 |
     | 3 | ... | Skipped (overlap) | — |

     Story complexity: <the story-level Story Points value>

     ## Open Questions
     - ...
     ```
     This is the file meant for whatever runs next — a TDD skill, or a
     person reading it directly. This skill doesn't invoke or assume any
     of them.
   - Write the proposed Story Points value back into the story's own
     `stories-<n>-<short-description>.md`, as a new `- Story Points: <n>`
     bullet in its `## Details` section, the same bullet shape as
     Priority/Dependencies/Design (sync and sprint planning read it as a
     bullet) — add the bullet if missing, overwrite the value if a prior
     run already set one.

6. **Post-breakdown handoff**
   - **Readiness offer first.** When the story's frontmatter `status` is
     `new` (missing counts as `new`):
     - `story-<n>-spec.md` has items under `## Open Questions` → don't
       offer. Say the story can be marked ready once they're answered;
       `/vc:tasks-breakdown validate` offers it again.
     - Otherwise ask via `AskUserQuestion` whether the story is ready to
       be put into a sprint ("Not yet" / "Mark ready"). Mark ready → set
       `status: ready` in the story file's frontmatter (add the line if
       missing), nothing else. On an Azure DevOps project, note the board
       changes only when `/vc:sync-to-tracker` runs.
   - Then ask via `AskUserQuestion` what to do next — never invoke any of
     these automatically. `AskUserQuestion` caps a question at 4 options,
     so offer these three always, in this order, plus a 4th slot:
     - "Validate this breakdown
       (`/vc:tasks-breakdown validate <story>`)" (Recommended)
     - "Implement this story (`/vc:implement <story>`)"
     - "Sync this story's tasks to the tracker
       (`/vc:sync-to-tracker tasks <story>`)" — for an unassigned
       feature, replace this with "Assign this feature to an epic
       (`/vc:propose-epic <feature-slug>`)", since tracker sync still
       needs the epic.
     - 4th slot: "Break down another story in this feature" when the
       feature has another story with no `story-<n>-spec.md` in this
       feature's `tasks/` folder yet; otherwise "Done for now".
   - This still doesn't invoke any of these — the choice stays entirely
     outside this skill either way.

## Validate Mode (`/vc:tasks-breakdown validate`)

Re-verifies an existing task breakdown against the current codebase
(files can drift between generation and now), interviews the user on
anything uncertain or missing, and logs the outcome in `spec.md` — before
the team commits real time to implementing it. Reached only via step 0's
`validate` token.

Load: `references/validate-workflow.md` for the full workflow (story
resolution, verification pass, question generation, interview, logging,
and consistency sweep).

## Notes

- No delegation branch — always runs its own built-in breakdown, same as
  `vc-create-user-stories`/`vc-prd`/`vc-bug-report`. It previously offered
  a `preferences.writing_spec` delegation to a third-party spec-writing
  skill (`vc-setup` no longer asks about this); the old `vc-tdd` and
  its separate `preferences.tdd` delegation are also gone, replaced by
  `vc-implement` — a built-in, non-delegating implementation step with
  no config switch. This skill still doesn't invoke it, or assume it runs
  next; that stays the user's own call (step 6).
- A task file's `Status:` can also become `Done`, a value only
  `vc-implement` ever writes, once that task's tests pass and its
  criterion is met.
- Writes entirely under the story's feature folder (unassigned or
  epic-assigned) — the `tasks/` subfolder (step 5) plus, in the story's own file, the
  one Story Points line and (only on the user's yes in step 6) its
  `status: ready` line. Never touches `docs/` — that tree is owned by
  `vc-docs`. There is no longer a separate top-level `specs/` tree; see
  `vc-setup migrate` for moving output written under the old layout.
- `vc-sync-to-tracker` reads a story's task files (when present) to sync
  them as Azure DevOps Tasks, parented to that story — see its own
  `references/task-field-mapping.md`. Sync still requires the feature to
  be epic-assigned (a story can't get an `ado_id` before its feature and
  epic are synced), so a breakdown written for an unassigned feature
  waits for `/vc:propose-epic` before it can be synced. It skips any task file with
  `Status: Skipped` entirely — never creates or updates a work item for
  one.
