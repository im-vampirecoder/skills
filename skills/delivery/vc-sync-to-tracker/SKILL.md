---
name: vc-sync-to-tracker
description: Create or update a feature's epic, feature, stories, and (when available) each story's tasks as work items in the configured tracker, in an Epic → Feature → Story → Task hierarchy. A `tasks [feature|story]` mode syncs only tasks. A `bug [bug-id]` mode syncs a standalone `vc-bug-report` file, parented under the confirmed "Bug Triage" > "Inbox" work item. Only Azure DevOps is implemented; other targets are recognized but do nothing yet.
---

# Sync to Tracker

Push a feature's epic, feature, stories, and each story's tasks (when
`vc-tasks-breakdown` has generated them) to the configured issue
tracker, creating new work items or updating already-synced ones in
place, preserving the Epic → Feature → Story → Task hierarchy. This is
the real sync logic — `vc-sync-to-ado` is a thin alias over this skill.

A story's tasks are entirely optional at sync time: a story with no task
breakdown yet still syncs fine up through the Story level, and gains its
tasks on a later run once `vc-tasks-breakdown` has produced them. A
`tasks <feature|story>` mode (below) syncs only tasks, for re-pushing a
task breakdown without touching the epic/feature/story content above it.

A Bug is a separate, flat concern outside this hierarchy entirely — a
`bug <bug-id>` mode (below) pushes one `vc-bug-report` file, parented
under whichever work item the "Bug Triage" > "Inbox" search resolves to
(always confirmed with the user, never guessed or cached).

## Why this skill works the way it does

- Each work item's own frontmatter (`ado_id`, `last_synced`) is the
  create-vs-update source of truth for the epic, the feature, and every
  story — there's no separate mapping file to keep in sync, because each
  file already carries its own state. Querying the tracker to answer
  "does this already exist?" would be slower and fragile (titles change,
  IDs aren't in the markdown until we write them back).
- **Sync never changes `status`.** A non-null `ado_id` is what marks an
  epic, feature or story as synced. `status` is the lifecycle field
  (`needs-review` → `draft` → `delivered` for features) and belongs to
  the skills that own that lifecycle. Before v1.11.1 this skill set
  `status: synced` on epics and features; when a file still has it,
  read it as `draft` and write `status: draft` back during this sync.
- The hierarchy this skill pushes is always **Epic → Feature → Story →
  Task**, matching the backlog hierarchy rules exactly — never a story
  parented straight to an epic, never a task parented straight to a
  feature or epic, and never a statically configured "default parent" at
  any level. The epic syncs first (step 3), then the feature (step 4),
  then each story (step 5), each recording a fresh `ado_id` before the
  level below it tries to parent to it.
- Only the **feature's** parent can actually drift after the fact — via
  `vc-propose-epic` reassigning it to a different epic — so only step 4
  carries re-parenting logic. A story's `feature_id` is fixed at creation
  by `vc-create-user-stories`, and a task's `story_id` is fixed at creation by
  `vc-tasks-breakdown` — nothing in this pipeline ever reassigns a
  story to a different feature, or a task to a different story — so
  steps 5 and 6 have no drift to detect; each always parents to whatever
  its owner's `ado_id` is *this run* (or already on record, in Task-only
  Mode), which is already correct by construction.

## Story work item type

The story level's actual Azure DevOps type name depends on the project's
process template — "User Story" (Agile), "Product Backlog Item" (Scrum),
or something else entirely (e.g. "Requirement" for CMMI). `vc-setup`
detects this once, at setup time, via the Work Item Types List API, and
stores it as `.vc/config.toml`'s `[ado].story_work_item_type`. Step 5
below always reads that value rather than assuming a name — a hardcoded
`"User Story"` would 404 on a Scrum-process project.

`.vc/config.toml` predating this field (no `story_work_item_type` under
`[ado]`) → default to `"User Story"` for backward compatibility, and
mention in the run's summary that re-running `/vc:setup` will detect
and store the project's actual type instead of assuming.

## Workflow

1. **Resolve the feature and target**
   - Parse `$ARGUMENTS` for a leading `tasks` or `bug` token. `tasks` →
     go to **Task-only Mode** below. `bug` → go to **Sync a Bug** below.
     Either way, pass the rest of `$ARGUMENTS` as the target to resolve
     there, instead of continuing with the steps that follow.
   - Take `$ARGUMENTS` as a feature slug, epic ID, or path under
     `artifacts/epic-*/feature-*/`. It must already be epic-assigned and
     have stories under `epic-<epic-slug>/feature-<feature-slug>/`. Still
     at `artifacts/<feature-slug>/` (unassigned, possibly with stories
     already written) → tell the user to run `/vc:propose-epic` first.
     Assigned but no stories → tell them to run
     `/vc:create-user-stories` first.
   - Resolve the target tracker: an explicit `--target <tracker>` flag if
     given, otherwise `tracker` from `.vc/config.toml`.
   - If the resolved target is `github`, `linear`, or `local`: stop and
     tell the user plainly that only `azure-devops` has a working sync
     implementation right now — do not attempt a partial sync, do not
     guess at an API call for an unimplemented backend.

2. **Read the feature's current state**
   - Read the epic's `epic.md` frontmatter (`id`, `ado_id`, `status`),
     the feature's own `prd.md` frontmatter (`id`, `epic_id`, `ado_id`,
     `last_synced`, `status`), and every `stories-*.md` file's
     frontmatter (`id`, `feature_id`, `ado_id`) under that feature's
     folder.
   - Confirm the CLI is ready: `az account show` succeeds and
     `az devops configure --list` shows `organization`/`project` matching
     `.vc/config.toml`'s `[ado]` values. If not, tell the user to run
     `az login` and/or `az devops configure --defaults organization=...
     project=...` themselves — this skill never handles credentials.

3. **Sync the epic**
   - Epic content is short (title only, no long HTML fields), so plain
     `az boards` commands are fine here — see the transport rule below
     for why that changes once we get to the feature and stories.
   - `ado_id` is `null` → create it:
     ```bash
     az boards work-item create \
       --org https://dev.azure.com/<ado.organization> \
       --project "<ado.project>" \
       --type "Epic" \
       --title "<epic title>"
     ```
     Record the returned `id` as `ado_id`, and today's date/time as
     `last_synced`, in `epic.md`'s frontmatter. Leave `status` as it is
     (see "Sync never changes `status`" below).
   - `ado_id` is already set → update it in place:
     ```bash
     az boards work-item update \
       --org https://dev.azure.com/<ado.organization> \
       --id <ado_id> \
       --title "<epic title>"
     ```
     Refresh `last_synced`.

4. **Sync the feature**
   - Parse the feature's `prd.md` and build its Azure DevOps fields
     following `references/feature-field-mapping.md` — title, Description
     (Overview + Problem/Motivation), and Acceptance Criteria (the
     feature's own `## Acceptance Criteria` section). Like stories, these
     are HTML fields that can exceed a few KB, so use the same JSON Patch
     path via `az devops invoke` as stories — never plain `az boards
     --fields` for this, and never `az rest`. See
     `references/azure-devops-transport.md`.
   - `ado_id` is `null` → **create**: POST the JSON Patch body (Title,
     Description, AcceptanceCriteria, AreaPath, IterationPath, Tags),
     read the new `id` from the response, then add the parent relation to
     the epic's `ado_id` from step 3 — never a configured default.
     Record `ado_id` and `last_synced` in the feature's `prd.md`
     frontmatter. Leave `status` as it is.
   - `ado_id` already set → **update**: send the same fields via `az boards work-item update` (never `az devops invoke` PATCH — see the transport reference). Then check
     for parent drift: read the feature's current parent relation from
     Azure DevOps and compare it to the epic's `ado_id` from step 3. If
     they differ (`vc-propose-epic` reassigned this feature to a
     different epic since the last sync), remove the stale parent
     relation and add the correct one — see
     `references/feature-field-mapping.md`'s re-parenting section.
     Refresh `last_synced`.
   - **Delivered feature** (the only Feature State this skill sets).
     When the `prd.md` says `status: delivered` (set by
     `/vc:prd deliver`) and `.vc/config.toml`'s
     `[ado].feature_closed_state` is non-empty:
     - Read the work item's current State the same way as a story's
       "Ready state" below. Already `feature_closed_state` → nothing to
       do.
     - Otherwise collect the move (feature title, ADO id,
       `<current> -> <feature_closed_state>`), confirm it with the user,
       and only then send it with
       `az boards work-item update --id <ado_id> --state "<feature_closed_state>"`.
       Azure DevOps refuses the move while open children block it on
       some processes → report the error and leave the State as it is.
     - Key missing (config written before this existed) → skip and
       suggest re-running `/vc:setup`, which asks for it.

5. **Sync each story**
   - Parse the story file and build its Azure DevOps fields following
     `references/story-field-mapping.md` — title (stripping the leading
     `<n>. ` numbering, keeping the `[<feature-slug>]` tag that
     `vc-create-user-stories` already baked into the title), Description
     (the As-a/I-want/So-that block + a source link back to the story
     file), Acceptance Criteria (the numbered Given/When/Then items), and Story
     Points (the `## Details` section's `- Story Points: <n>` bullet, when
     `vc-tasks-breakdown` has already set one — omit the field
     entirely when absent), and Tags (the `- Implements:` requirement
     IDs as one tag each, kept in step on every sync; see the
     reference's "Requirement ID tags").
   - Because Description and Acceptance Criteria are HTML fields that can
     easily exceed a few KB, push them via a JSON Patch body file through
     `az devops invoke`, never inline `--fields` on `az boards`, and never
     `az rest`. See `references/azure-devops-transport.md` for exactly
     why (auth-path divergence, Windows `cmd.exe`'s ~8,191-char limit,
     shell-quoting hazards) and the exact command forms.
   - `ado_id` is `null` → **create**: POST the JSON Patch body (Title,
     Description, AcceptanceCriteria, StoryPoints if present, AreaPath,
     IterationPath, Tags) with `type` set to `.vc/config.toml`'s
     `[ado].story_work_item_type` — never a hardcoded `"User Story"`,
     since a Scrum-process project names this level "Product Backlog
     Item" instead (see "Story work item type" below). Read the new `id`
     from the response, then add the parent relation to the **feature's**
     `ado_id` (the one just synced in step 4 — never the epic directly,
     never a configured default). Record `ado_id` and `last_synced` in
     the story's frontmatter.
   - `ado_id` already set → **update**: send the same fields via `az boards work-item update` (never `az devops invoke` PATCH — see the transport reference), with Tags merged
     as the reference describes (add missing requirement IDs, drop ones
     the story no longer implements, keep every other tag). No
     re-parenting check here — see "Why this skill works the way it
     does" for why a story's parent never drifts. Refresh `last_synced`.
   - **Ready state** (the only State this skill ever sets). After the
     create or update, when the story file says `status: ready` and
     `.vc/config.toml`'s `[ado].ready_state` is non-empty:
     - Read the work item's current State
       (`az boards work-item show --id <ado_id> --query "fields.\"System.State\"" -o tsv`).
     - Move it to `ready_state` only when the current State is the
       type's starting state: the first `Proposed` state in the type's
       state list (e.g. `New`), read once per run with the same
       `workItemTypeStates` query `vc-setup` uses.
       Already `ready_state` → nothing to do. Any other State (the team
       has started, finished, or removed it) → leave it and list it in
       the summary as "marked ready locally, board is further along".
     - Collect these moves for the whole run and confirm them once with
       the user (story title, ADO id, `New -> <ready_state>`) before
       sending any. Send with
       `az boards work-item update --id <ado_id> --state "<ready_state>"`.
     - `ready_state` key missing (config written before this existed) →
       skip the move and suggest re-running `/vc:setup`. Empty → skip
       silently; the process has no ready state.

6. **Sync each story's tasks (when available)**
   - For each story just synced above, check for
     `story-<n>-task-*.md` files in this feature's
     `artifacts/epic-<epic-slug>/feature-<feature-slug>/tasks/` folder
     (written by `vc-tasks-breakdown`). None → skip that story's tasks
     silently, no error — a story can be synced long before its task
     breakdown exists.
   - Present → for each matching file whose `Status` isn't `Skipped` (a
     `Skipped` task — flagged by `vc-tasks-breakdown` as overlapping
     another story's task — is never synced, whether or not it already
     has an `ado_id`; if it does, leave that work item alone and don't
     touch it), build its Azure DevOps fields following
     `references/task-field-mapping.md` — title (stripping the leading
     `<m>. ` numbering), Description (the task's `## Notes` + `Files:`
     line + a source link back to the task file). No time estimate is
     sent — task files carry Story Points (complexity), which has no
     Task-level field in Azure DevOps.
   - `ado_id` is `null` → **create**: POST the JSON Patch body, read the
     new `id`, then add the parent relation to the **story's** `ado_id`
     (just synced above — never the feature or epic directly). Record
     `ado_id` and `last_synced` in the task's frontmatter.
   - `ado_id` already set → **update**: send the same fields via `az boards work-item update` (never `az devops invoke` PATCH — see the transport reference). No
     re-parenting check — see "Why this skill works the way it does" for
     why a task's parent never drifts. Refresh `last_synced`.

7. **Report the summary**
   - Print a plain count: epic created/updated, feature created/updated
     (and closed, when delivered), stories created/updated, requirement
     ID tags added/removed, tasks created/updated, tasks excluded for
     being marked `Skipped`, any stories skipped for having no task
     breakdown yet, and any feature re-parenting that happened. No
     further confirmation gate beyond this summary — the create-vs-update
     decision in steps 3-6 already reflects intent.

## Task-only Mode (`tasks <target>`)

Syncs only tasks — never touches epic, feature, or story content. Reached
only via a leading `tasks` token in `$ARGUMENTS` (step 1 resolves this).

1. Resolve `<target>` (the rest of `$ARGUMENTS` after `tasks`): try the
   normal feature/epic resolution first (step 1's rules); if that
   doesn't match, try a story match instead — `STORY-<feature-slug>-<n>`,
   a story's `ado_id`, or a path to its `stories-*.md` file.
2. Build the story scope: one story if `<target>` resolved to a story,
   every story under the feature if it resolved to a feature.
3. For each story in scope: if its `ado_id` is `null` (not synced yet),
   skip it and tell the user to run `/vc:sync-to-tracker` on the
   feature first — this mode never syncs a story itself, by design.
   Otherwise, run step 6's task-sync logic above for that story
   unchanged (skipping silently, same as step 6, if it has no
   `story-<n>-task-*.md` files yet).
4. Report the same summary shape as step 7, scoped to tasks only.

## Sync a Bug (`bug <target>`)

Pushes one standalone bug — never touches the Epic/Feature/Story/Task
hierarchy. Reached only via a leading `bug` token in `$ARGUMENTS` (step 1
resolves this).

1. **Resolve the bug**: `<target>` (the rest of `$ARGUMENTS` after `bug`)
   as `BUG-<bug-slug>`, a path to `artifacts/bugs/<bug-slug>.md`, or the
   bare slug. No match → tell the user to run `/vc:bug-report` first,
   and stop.
2. **Resolve the tracker**: same rule as step 1 (`--target` flag,
   otherwise `.vc/config.toml`'s `tracker`). Non-`azure-devops` →
   same stop-and-tell-the-user behavior as step 1.
3. **Find "Bug Triage" > "Inbox" — never guessed, always confirmed:**
   - Search for a work item titled containing "Bug Triage":
     ```bash
     az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.Title] CONTAINS 'Bug Triage'" --output json
     ```
   - Zero or more than one match → skip straight to asking the user
     directly for the Bug Triage Inbox work item ID (a plain ADO ID) —
     don't try to guess between ambiguous matches, and don't try a
     fuzzier search.
   - Exactly one match → list its children and look for one titled
     containing "Inbox":
     ```bash
     az boards work-item show --id <bug-triage-id> --expand relations --output json
     ```
     Filter `relations` for `rel == "System.LinkTypes.Hierarchy-Forward"`,
     extract each child's ID from its `url`, then check each child's
     title:
     ```bash
     az boards work-item show --id <child-id> --query "fields.\"System.Title\"" -o tsv
     ```
   - Zero or more than one child titled containing "Inbox" → same
     fallback as above: ask the user directly for the ID.
   - **Always confirm before using it**, every run, whether the ID came
     from search or from the user directly: show its ID and fetched
     title, and get an explicit yes before proceeding. This step never
     caches a resolved ID across runs (and this skill never writes
     `.vc/config.toml` to store one) — a fresh confirm every time is
     the point, not an optimization to skip.
4. Build the bug's Azure DevOps fields following
   `references/bug-field-mapping.md` — title, ReproSteps + SystemInfo (not Description; the five
   template fields), Severity, and the optional Related link if the bug
   file's `feature_id`/`epic_id` is set (resolved to that item's own
   `ado_id`).
5. `ado_id` is `null` → **create**: POST the JSON Patch body (Title,
   ReproSteps, SystemInfo, Severity, AreaPath, IterationPath, Tags) via
   `az devops invoke` (never `az rest`, never inline `--fields` — same
   transport rule as everything else, see
   `references/azure-devops-transport.md`), read the new `id`, add the
   hierarchical parent relation to the confirmed Inbox ID, then the
   Related link if applicable. Record `ado_id` and `last_synced` in the
   bug file's frontmatter.
6. `ado_id` already set → **update**: send the same fields via `az boards work-item update` (never `az devops invoke` PATCH — see the transport reference). Check for
   parent drift against the just-confirmed Inbox ID (same re-parenting
   reasoning as feature → epic drift) — remove the stale relation and add
   the correct one if they differ. The Related link, once set, is never
   auto-changed. Refresh `last_synced`.
7. **Ready state.** When the bug file says `status: ready` and
   `[ado].bug_ready_state` is non-empty, apply the same rule as a
   story's "Ready state" in the feature workflow's step 5, with
   `bug_ready_state` and the bug type's state list: move it only from the
   type's starting state, confirm with the user first, and leave any bug
   the team has already moved on. Key missing → suggest re-running
   `/vc:setup`; empty → skip silently.
8. Report: created or updated, the confirmed Inbox parent used, whether
   a Related link was added, and any state change.

## Safety rules

- **Never call `az rest` for Azure DevOps endpoints.** Use `az boards` /
  `az devops invoke` only — see `references/azure-devops-transport.md`.
  If the user explicitly insists on `az rest`, surface this rule and
  confirm before doing it.
- Never change a work item's **State**, with two exceptions, both
  confirmed by the user: a story's move from its starting state to
  `[ado].ready_state` (or a bug's to `[ado].bug_ready_state`), as the
  "Ready state" steps describe, and a delivered feature's move to
  `[ado].feature_closed_state` (step 4's "Delivered feature"). State transitions trigger
  board automations and may notify other people; no other State change
  is in this skill's model.
- Never delete a work item. If a story or bug file is removed from the
  vc workspace, leave the Azure DevOps item alone and flag it to the
  user.
- Never touch a work item whose ID isn't already recorded in that
  bug's/task's/story's/feature's/epic's own frontmatter, even if a title
  match suggests it's the same one — title collisions happen, frontmatter
  `ado_id` doesn't lie.
- Never guess the "Bug Triage" > "Inbox" parent, and never skip
  confirming it — this is the one place this skill asks the user to
  confirm a resolved ID before every single use, not just the first.

## Notes

- Authentication is external (`az login`), checked by `vc-setup` — this
  skill assumes it's already in place and surfaces the CLI's own error if
  not, rather than trying to detect or fix login state itself.
- `github`, `linear`, and `local` targets are recognized in config for
  forward compatibility but have no client behind them yet — don't
  implement partial/best-effort behavior for them.

## References

- `references/azure-devops-transport.md` — the JSON Patch / `az devops
  invoke` transport rule: why, exact command forms, Windows caveats.
- `references/feature-field-mapping.md` — field-by-field mapping from a
  feature's `prd.md` to Azure DevOps Feature fields, HTML conversion
  rules, title extraction, and the epic-level re-parenting flow.
- `references/story-field-mapping.md` — field-by-field mapping from a
  story file to Azure DevOps fields, HTML conversion rules, title
  parsing, and the optional Story Points field.
- `references/task-field-mapping.md` — field-by-field mapping from a
  `vc-tasks-breakdown` task file to Azure DevOps Task fields, HTML
  conversion rules, and title parsing.
- `references/bug-field-mapping.md` — field-by-field mapping from a
  `vc-bug-report` bug file to Azure DevOps Bug fields, HTML conversion
  rules, severity conversion, and the hierarchical-parent-vs-Related-link
  distinction.
