# Readiness Checks

How `vc-plan-sprint-candidates` decides which stories may be proposed,
and what it says about the ones that may not. Works on the JSON from
`scripts/fetch_sprint_planning_data.py`.

## The gate

Only a **ready** story or bug can be a candidate, and a ready story only
once it has a task breakdown (check 10). Nothing else gets in, however
high it sits in the backlog.

| Tracker | Ready means |
|---|---|
| `local` | Story frontmatter `status: ready` (the script's `backlog_ready`) |
| `azure-devops` | Work item State equals `.vc/config.toml`'s `[ado].ready_state` (stories) or `[ado].bug_ready_state` (bugs), both chosen in `/vc:setup`. When it is empty (a process with no ready state, e.g. Agile), `status: ready` in the local file matched by `ado_id` decides instead |

`ready` is set only by the user, at the readiness offer in
`vc-create-user-stories` (step 10) or `vc-create-pbi` (step 7), right
after the stories are written. A story is broken into tasks only once
it is `ready`. This skill never sets or clears it.

## Checks on ready stories

Ready is the team's earlier judgment; things can change after it. Run
these on every ready story and give each a result: **ok**, **concern**
(stays a candidate, the concern is shown next to it), or **blocked** (left
out of the candidates, with the reason).

| # | Check | Source | Result when it fails |
|---|---|---|---|
| 1 | Has acceptance criteria | script flag `no acceptance criteria` | blocked |
| 2 | Criteria are testable: each states an observable result, not "works well" or "is fast" | read the story's Acceptance Criteria | concern |
| 3 | Parent feature exists | script flag `parent feature ... has no prd.md` | concern |
| 4 | Dependencies are done | script flag `depends on X (..., not done)` | ok if X is also a candidate placed earlier in this sprint; blocked otherwise |
| 5 | Title is an outcome, not a technical layer ("API for...", "DB schema for...", "Frontend of...") | the story title | concern; suggest re-slicing with `vc-create-user-stories` |
| 6 | Fits in one sprint: the story-size bar is roughly 1-3 days of work (`vc-create-pbi`) | the story's task breakdown (`tasks/story-<n>-spec.md`) when it exists: more than ~8 non-skipped tasks, or more than ~8 criteria | concern; suggest splitting |
| 7 | No open blocking questions | `## Open Questions` in the story's spec, 🔴 Blocking items in the feature's `clarification-questions.md` | blocked when the question is blocking, otherwise concern |
| 8 | Spike states its question and timebox | `Type: spike` stories only | concern |
| 9 | Requirements it implements are settled | the story's `- Implements:` IDs, looked up in the feature PRD's `## Requirements` and in every feature PRD's `## Open Questions` | blocked when an implemented ID still has an inline `[NEEDS CLARIFICATION: …]` marker, or an Open Question in any feature PRD names an implemented ID together with an ID from another feature (a conflict deferred by `/vc:requirements conflicts`); concern when an implemented ID is retired or superseded |
| 10 | Has a task breakdown (stories only, not bugs) | the story's `breakdown` in the script output (`null` when `tasks/story-<n>-spec.md` doesn't exist) | blocked |

Story points are never part of these checks. When a check reads a file
that does not exist (no clarification file, or no breakdown for check 6),
the check passes; do not invent a concern. Check 10 is the one
exception: a missing breakdown blocks.

A blocked ready story or bug is not moved back to `new`. Say what blocks
it and which skill clears it; the user decides.

### Bugs

Ready bugs (`artifacts/bugs/*.md`, `status: ready`) are candidates too,
ordered with the stories by severity (critical with must-haves, high with
should-haves, and so on). Until a bug-triage skill exists, the PO marks a
bug ready by hand. Checks on a ready bug:

| # | Check | Source | Result when it fails |
|---|---|---|---|
| B1 | Has numbered steps to reproduce | script flag `no steps to reproduce` | blocked |
| B2 | States expected and actual result | script flag `expected/actual result missing` | blocked |
| B3 | Has a severity | script flag `no severity` | concern |

A not-ready bug high in the order is named like a story, with "triage
the bug (fill in steps, expected/actual, then set `status: ready`)" as
the next step.

## Not-ready stories worth naming

List the not-ready stories that sit high in the backlog: those in the
order ahead of, or among, the last candidate, up to about one sprint's
worth beyond it. For each, name what is missing and the skill that makes
it ready:

| Missing | Next step |
|---|---|
| Not marked ready | `/vc:create-user-stories <feature>` offers mark-ready after it writes (or reviews) the stories |
| Ready, no task breakdown | `/vc:tasks-breakdown <story>` |
| Breakdown has open questions | answer them, then `/vc:tasks-breakdown validate <story>` |
| An implemented requirement has a `[NEEDS CLARIFICATION]` marker | the PO answers it through `/vc:prd <feature>` |
| An implemented requirement is in a deferred conflict | the PO resolves it with `/vc:requirements conflicts <feature>` |
| An implemented requirement is retired or superseded | point the story at the replacement (`/vc:requirements check` names it) |
| The feature isn't `ready`, so no stories can be agreed yet | `/vc:prd-clarify <feature>` (offers to mark the feature ready at the end) |
| No or weak acceptance criteria | `/vc:create-user-stories` or edit the story, then one of the above |
| Unknown status value | fix the story's `status` field |

Do not list the whole backlog; this list is the PO's refinement to-do
before the next planning (PO-03).

## Carryover

For every story in the script's `carryover` (unfinished in the current
sprint):

- Show its status and progress: tasks `Done` out of non-skipped tasks
  from its breakdown when there is one.
- Recommend one option with a one-line reason, and leave the decision to
  the PO/SM:
  - **keep**: still serves the new goal and is close to done.
  - **backlog**: no longer serves the goal, or blocked for reasons
    outside the team.
  - **split**: part is done and valuable on its own; the rest becomes a
    new story (written with `vc-create-user-stories`, not here).
  - **drop**: no longer wanted (`status: removed` is set by the PO, not by
    this skill).
- Nothing rolls over by default. A kept story counts against the fit
  limits like any candidate.

Also show the script's `stale_in_past_sprint` stories (left open in a
sprint before the current one) with the same options; they were missed
at an earlier planning.
