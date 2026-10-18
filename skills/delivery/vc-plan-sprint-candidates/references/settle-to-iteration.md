# Settle: Record the Agreed Scope

`/vc:plan-sprint-candidates settle [sprint-slug]`. Run by the PO or SM
after the whole team has agreed the sprint scope in planning. It records
that agreement by setting each item's iteration; it does not make the
decision and it does not lock anything. Run it again whenever the scope
changes during the sprint.

## Rules

- **Source of truth is `candidates.md`**: the carryover `Decision` and
  candidates `In sprint` columns, keyed by `Item`
  (`references/candidates-template.md`). Edit the file to match what the
  team agreed before settling.
- **Only the iteration changes.** Local: the item file's `iteration:`
  frontmatter line. Azure DevOps: the work item's Iteration Path
  (`az boards work-item update --iteration`); taking an item out of the
  sprint sets the team's backlog iteration. Local files are not changed
  on Azure DevOps. Status is never changed (`vc-implement` moves an
  item to `in-progress` when work starts).
- **Only ready items join.** An item with `In sprint` = `yes` that is not
  `ready` (or already `in-progress`) stops the run. Make it ready first
  (`vc-prd-clarify`, `vc-tasks-breakdown`, or by hand for a bug), or
  set it to `no`.
- **Unlisted items are never touched**, even when they sit in the sprint;
  they are reported as warnings.
- **Every decision is made.** An empty carryover `Decision` stops the run.
- Azure DevOps: confirming the moves is mandatory, because each one
  updates a shared board other people watch.

| Row | Move |
|---|---|
| Candidates, `In sprint` = `yes` | iteration = this sprint |
| Candidates, `In sprint` = `no` | iteration cleared, only if it is in this sprint now |
| Carryover, `keep` | iteration = this sprint |
| Carryover, `backlog` | iteration cleared |
| Carryover, `split` | no move; follow-up: write the remaining part as a new story (`vc-create-user-stories`), then close this one |
| Carryover, `drop` | no move; follow-up: the PO sets `status: removed` |

## Workflow

1. **Plan the moves** (writes nothing):
   ```
   python3 <skill-dir>/scripts/set_iteration.py plan --root . [--sprint <slug>]
   ```
   Without `--sprint`, it settles the next sprint's `candidates.md`, or
   the current sprint's once the next one has none (a mid-sprint change).
   - `problems` → show each with its fix and stop.
   - `file_status` is `draft` → ask via `AskUserQuestion` whether planning
     is done. No → stop. Yes → continue (the file is set to `settled`
     at the end).
   - Show `warnings`.

2. **Confirm**
   - Show a table of `moves` (item, title, from, to, reason) and the
     `followups`. No moves → say the tracker already matches the file,
     still offer to record the settle, and skip to step 3 on a yes.
   - Ask via `AskUserQuestion`: apply all / leave some out / cancel.
     Leave some out → multi-select which to exclude.

3. **Apply**
   ```
   python3 <skill-dir>/scripts/set_iteration.py apply --root . [--sprint <slug>] \
     --by "<name>" [--exclude <ID> ...]
   ```
   `<name>` is the person running it (`git config user.name` in the
   tracking repo, or ask). The script recomputes the same plan, refuses if
   anything changed into a problem, sets each `iteration:` line, sets
   `candidates.md` to `status: settled`, and appends a dated record under
   `## Settle record`.

4. **Report**
   - Each move with its result (`done`, `excluded`, or `failed: ...`).
   - The follow-ups, as the PO's to-do.
   - Remind: scope can change during the sprint; edit `candidates.md`,
     set `status: agreed`, and settle again.
