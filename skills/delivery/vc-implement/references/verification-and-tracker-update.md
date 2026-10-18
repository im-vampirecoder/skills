# Review and Tracker Status Update

Full procedure for `vc-implement` step 5, plus the story-started update
from step 1 (section 0).

## 0. Story started (step 1)

Runs once, right after the user confirms the restated story or bug in
step 1. Tasks keep their current behavior.

**Story or bug file:** set `status: in-progress` in its frontmatter (add
the line if missing) when it is `new` or `ready` (missing counts as
`new`). Already `in-progress` → nothing to do. `done` or `removed` →
leave it and tell the user the file says the item is already closed.
The local status is what `vc-plan-sprint-candidates` reads for the
sprint board and throughput, for bugs as much as for stories.

**Azure DevOps** (stories only, and only when the story has a non-null
`ado_id`; a bug's work item state is left alone at start):

- Target state: `.vc/config.toml`'s `[ado].active_state`. Key missing
  (config older than this) → ask the user once which state means work
  has started (offer `Active`, `Committed`, free text), use it for this
  run, and suggest re-running `/vc:setup` to store it.
- Read the current State
  (`az boards work-item show --id <ado_id> --query "fields.\"System.State\"" -o tsv`).
  Move it only when it is still in a `Proposed`-category state (`New`,
  or `[ado].ready_state`). Already `active_state` → nothing to do. Any
  later state (resolved, closed, removed) → leave it and tell the user.
- `az boards work-item update --id <ado_id> --state "<active_state>"`.
- A story that was never marked ready is still moved, but say so: the
  team pulled it into work without the readiness offer.

Report the change (work item id, old→new state) with the rest of the
run's record.

## 1. Review

Invoke `/vc:code-review`, scoped to this worktree's diff against the
branch's fork point, passing the story's acceptance criteria (or the
bug's Expected/Actual Result) and the task files' Notes as context.

If it reports an unmet criterion, a regression, or a side effect: stop.
Present it to the user via `AskUserQuestion` with concrete options (e.g.
"fix it now", "accept as a known trade-off and note it", "revert this
task and re-approach") — never silently patch around a finding without
the user choosing how.

Clean report → continue to step 2.

## 2. Tracker status update

This is a deliberate exception to `vc-sync-to-tracker`'s own "never
change a work item's State" rule — that rule protects *sync* operations
(create/update field pushes) from accidentally tripping board automations
on every metadata refresh. This step is different: it fires once, when
work is genuinely finished, which is exactly what a State transition is
for.

**Scope:** only work items that already have a non-null `ado_id` — never
touch tracker items that haven't been synced yet, and never sync one here
just to then close it (that's `vc-sync-to-tracker`'s job, run
separately if needed).

**Resolving the "done" state value:** Azure DevOps' state names for
"finished" vary by process template (e.g. `Closed` under Basic/Agile,
`Done` under Scrum-derived templates). The first time this step needs to
update a state in a given run, ask the user once via `AskUserQuestion`
which value their project uses (offer `Closed`, `Done`, `Resolved`, and a
free-text option) — then reuse that same answer for every other item in
this run. Don't persist it to `.vc/config.toml`; that file is
`vc-setup`'s to write.

**Per task marked `Done` in step 4, with a non-null `ado_id`:**

```bash
az boards work-item update --id <ado_id> --state "<resolved-done-state>"
```

Never `az rest` for this — same transport rule the rest of this repo
follows.

**Story-level:** once every non-`Skipped` task under the story is `Done`,
ask whether the story as a whole is finished. On a yes, set `status: done`
in the story file's frontmatter (the local record
`vc-plan-sprint-candidates` counts as throughput) and, when the story
has a non-null `ado_id`, update its tracker state the same way as the
tasks. Don't do it automatically — a story can have tasks this run didn't
touch (a partial implementation across multiple runs), and only the user
knows whether the story as a whole is actually finished.

**Feature delivery offer:** after a story is set `done`, check the
other `stories-*.md` files in the same feature folder. Every one `done`
or `removed`, and the feature's `prd.md` not already `status: delivered`
→ tell the user this was the feature's last story and ask whether the PO
confirms the feature is delivered. Yes → invoke `/vc:prd deliver
<feature>` through the Skill tool; it freezes the requirements, writes
supersession banners and asks its own confirmation. No, or the PO isn't
here → say the PO can run `/vc:prd deliver <feature>` later. Never set
`delivered` yourself, and never move the ADO Feature's State:
`vc-sync-to-tracker` closes it on its next run once the PRD says
`delivered`.

**Bug:** once its fix is verified, ask whether the bug is finished. On a
yes, set `status: done` in the bug file's frontmatter (same reason as
for a story: it is the local record sprint planning counts) and, when
the bug file has a non-null `ado_id`, update its tracker state the same
way as the tasks.

Report every state change made (work item id, old→new state) so the user
has a record of what just happened in the tracker.
