---
name: vc-plan-sprint-candidates
description: Prepare sprint planning for the PO or SM - a draft sprint goal written as an outcome, candidate user stories and bugs (only `ready` ones with a task breakdown, from local files or Azure DevOps) fitted to the SM's published capacity and the team's story throughput, and carryover listed for an explicit decision - written to artifacts/sprints/[sprint-slug]/candidates.md. A leading `settle` token records the scope the team agreed in planning by setting the stories' iteration path. Invoked as /vc:plan-sprint-candidates [settle] [sprint-slug].
---

# Plan Sprint Candidates

Get the PO (or SM) to sprint planning with a proposal, not a blank board:
a draft goal, the ready stories that serve it, sized against capacity the
SM has already published, and every unfinished story from the current
sprint up for a conscious decision.

Everything this skill writes is a proposal. The whole team agrees the
goal and the scope in planning; how the work gets done is the
Developers' call. Capacity is the SM's number and priority is the PO's;
this skill reads both and decides neither.

## Ground rules

- **Only `ready` stories and bugs are candidates, and a story also needs
  a task breakdown** (`tasks/story-<n>-spec.md`). See
  `references/readiness-checks.md` for what ready means per tracker and
  the checks run on top of it.
- **No capacity, no plan.** The SM publishes
  `artifacts/sprints/<sprint-slug>/capacity.md`
  (`references/capacity-file-contract.md`). Missing or broken → stop and
  say so; never estimate it.
- **No story points.** Fit uses story throughput (stories Done per
  sprint) scaled by available hours. A story's points may be shown, never
  summed.
- **Nothing rolls over by itself.** Every carryover story gets a
  decision, made by the PO/SM.
- **Writes one file**, `candidates.md`, and only after the user agrees.
  Never touches story files or the tracker in this mode.

## Workflow

0. **Resolve the mode**
   - `$ARGUMENTS` starts with `settle` → follow
     `references/settle-to-iteration.md` and stop here.
   - Otherwise the rest of `$ARGUMENTS` is an optional sprint slug
     (default: the next sprint).

1. **Fetch the data**
   - Run, from the tracking repo root:
     ```
     python3 <skill-dir>/scripts/fetch_sprint_planning_data.py --root . [--sprint <slug>]
     ```
     (`<skill-dir>` is this skill's directory; `python` on Windows).
     Tracker comes from `.vc/config.toml`.
   - Azure DevOps: needs the `az` CLI logged in (as for
     `vc-sync-to-tracker`) and `[ado]` filled by `/vc:setup`,
     including `team`, `ready_state`, and `bug_ready_state`. Sprints are
     the team's iterations; the capacity file stays local. The run can
     take a minute or more on a large project: run it in the background
     and read the output when it finishes.
   - `problems` non-empty → show them plainly with the fix (usually: the
     SM publishes capacity) and stop.
   - Show `warnings` and continue.

2. **Show the starting point**
   - One short block: sprint name and dates, available hours and who
     published them, the capacity notes, and throughput (median done per
     sprint, scaled number, core and full limits) or why there is none.

3. **Carryover decisions**
   - Apply the carryover part of `references/readiness-checks.md` to
     `carryover` and `stale_in_past_sprint`.
   - Ask the PO/SM per story via `AskUserQuestion` (up to four stories
     per call): keep / backlog / split / drop, recommended option first,
     plus "Decide in planning". Record the answers; "decide in planning"
     leaves the decision empty.
   - None → say "No carryover." and move on.

4. **Check readiness**
   - Run the checks in `references/readiness-checks.md` on
     `backlog_ready`, including check 9: a story isn't ready while a
     requirement it implements still has a `[NEEDS CLARIFICATION]`
     marker or sits in a deferred conflict (an Open Question naming it
     with another feature's ID). Keep ok and concern stories as
     candidates; set blocked ones aside with their reason.
   - Pick out the not-ready stories worth naming (same reference).

5. **Draft the goal**
   - Build two or three options per `references/sprint-goal-guide.md`,
     each with the stories it would focus on.
   - Ask the PO via `AskUserQuestion` to pick one or write their own.
     Check a written goal against the guide's reject list; say once if it
     fails and offer a rewrite. The PO's wording wins.

6. **Fit the candidates**
   - Order: kept carryover first, then candidates that serve the goal, in
     backlog order (`backlog_ready` is already ordered; the PO may
     reorder).
   - With a throughput number: **core** fills up to `core_limit`
     (including kept carryover), **supporting** up to `full_limit`,
     **stretch** is the next one to three goal stories beyond that. Kept
     carryover alone above `full_limit` → say so and suggest a recovery
     goal.
   - Without one: propose the smallest set that reaches the goal as core,
     a few more as supporting and stretch, and say the team judges fit in
     planning.
   - A ready story that does not serve the goal is not a candidate
     unless the PO asks for it; then it is supporting, noted "outside the
     goal".
   - **Slip test**, in prose: if the one or two core stories most at risk
     slip (largest, most concerns, most dependencies), does the goal still
     hold? If not, say what would make it hold: a smaller goal or a
     different core.
   - Feature roll-up: for each feature with candidates, whether the
     sprint finishes or advances it; features with no ready stories are
     listed as gaps.

7. **Write `candidates.md`**
   - Show a short summary (goal, counts per role against the limits,
     blocked stories, slip test result) and ask before writing.
   - Target: `artifacts/sprints/<sprint-slug>/candidates.md`, filled from
     `references/candidates-template.md` with `status: draft`.
   - Already exists → show its `status`. `agreed` or `settled` means the
     team already planned from it: warn, and overwrite only on an explicit
     yes. `draft` → confirm before overwriting.

8. **Next steps**
   - Share the file with the team before planning.
   - In planning: edit the goal, the `In sprint` column, and carryover
     `Decision` to match what the team agrees; set `status: agreed`.
   - Then `/vc:plan-sprint-candidates settle` records it (PO or SM can
     run it, and again whenever scope changes).
   - The not-ready list is the PO's refinement to-do for the next sprint.

## Notes

- Candidates are stories (including PBIs and spikes) and bugs. Features
  are derived from the stories' parents, never selected directly. A bug
  is ready when the PO sets `status: ready` (a bug-triage skill will take
  this over).
- This skill never sets or clears `ready`; that is the user's call at the
  offers in `vc-create-user-stories` and `vc-create-pbi`.
- Local sprints are the folders under `artifacts/sprints/` that hold a
  `capacity.md`; the sprint dates come from that file. On Azure DevOps
  they are the team's iterations, and `capacity.md` must sit at
  `artifacts/sprints/<slug of the iteration name>/`.
- Azure DevOps items without a local file appear as `ADO-<id>`. Backlog
  order is the board's own order.
- The SM's capacity skill (SM-04, `vc-plan-team-capacity`) is planned;
  until then the SM writes `capacity.md` by hand from the contract.
