# Candidates File Template

The file `vc-plan-sprint-candidates` writes to
`artifacts/sprints/<sprint-slug>/candidates.md`, beside the sprint's
`capacity.md`. The PO/SM edits it before and during planning; the team's
agreement is recorded in it; `settle` reads it to set iteration paths.

Two columns are the contract `settle` reads, so keep their names and
values exact:

Both tables identify rows by the **`Item`** column: a story id
(`STORY-...`) or bug id (`BUG-...`) from the local file, or `ADO-<id>`
for an Azure DevOps work item with no local file.

- **Carryover table, `Decision`**: `keep`, `backlog`, `split`, `drop`, or
  empty (undecided - `settle` refuses to run while any row is empty).
- **Candidates table, `In sprint`**: `yes` or `no`. Core and supporting
  rows start as `yes`, stretch rows as `no`. The team flips them in
  planning; rows can be added by hand with the story id.

Everything else is for people and is never parsed.

## Template

```markdown
---
sprint: <sprint name>
iteration_path: <iteration path>
sprint_slug: <sprint-slug>
status: draft
prepared_by: <name>
prepared_at: <YYYY-MM-DD>
available_hours: <recomputed hours from capacity.md>
throughput: <scaled_throughput, or "not available">
core_limit: <n, or null>
full_limit: <n, or null>
---

# Sprint candidates: <sprint name>

> Proposal for sprint planning, prepared by <name>. The whole team agrees
> the scope in planning; change this file to match what was agreed, set
> `status: agreed`, then run `/vc:plan-sprint-candidates settle`.
> Scope can still change during the sprint; run settle again after.

## Sprint goal (draft)

**<chosen goal, one sentence, an outcome>**

Options considered:
1. <option> - <what it would focus on>
2. <option>
3. <option>

## Capacity

Published by <published_by> on <published_at>: **<available_hours> hours**
over <working_days> working days.

| Member | Hours/day | Time off (h) | Hours |
|---|---|---|---|
| <name> | <n> | <n> | <n> |

<capacity notes from capacity.md, verbatim>

<warnings from the capacity check, if any>

## Throughput

| Sprint | Stories done | Available hours |
|---|---|---|
| <sprint> | <n> | <n> |

Median <n> stories, scaled by <available_hours> / <usual_hours> hours =
**<scaled_throughput>**. Core up to <core_limit>, full up to
<full_limit>.

<or: "Not available: <reason>. The team judges fit in planning.">

## Carryover

| Item | Title | Status | Progress | Recommendation | Decision |
|---|---|---|---|---|---|
| <STORY-id or BUG-id> | <title> | <status> | <done>/<total> tasks | <keep/backlog/split/drop> - <reason> | |

<"None." when empty>

## Candidates

Kept carryover counts toward the limits: <kept> kept + <core> core +
<supporting> supporting = <total> of <full_limit>.

| # | Item | Type | Title | Feature | Role | Serves the goal by | Concerns | In sprint |
|---|---|---|---|---|---|---|---|
| 1 | <STORY-id> | story | <title> | <feature title> | core | <one line> | <none / concern> | yes |
| 2 | <BUG-id> | bug | <title> | <linked feature or -> | supporting | <one line> | | yes |
| 3 | <STORY-id> | story | <title> | <feature title> | stretch | <one line> | | no |

## Slip test

If <the 1-2 core stories most at risk> slip, the goal <still holds
because ... / no longer holds - consider ...>.

## Features this sprint

| Feature | Stories in sprint | Result if all done |
|---|---|---|
| <feature title> | <n> of <total> | finishes / advances |

Features with no ready stories: <list, or "none">.

## Not ready, high in the backlog

| Item | Title | Missing | Next step |
|---|---|---|---|
| <STORY-id> | <title> | <what> | <skill> |

## Risks and dependencies

- <dependency or risk, and which stories it touches>

## Questions for planning

- <question the team should answer in the session>

## Settle record

<filled by settle: date, who ran it, each iteration move>
```

## Rules for filling it

- `status` moves `draft` -> `agreed` (the PO/SM sets it after planning)
  -> `settled` (set by `settle`). Editing after `settled` is fine; set it
  back to `agreed` and run settle again.
- One row per item; an item never appears in both tables. `Type` is
  `story`, `spike`, or `bug`.
- `Role` is `core`, `supporting`, or `stretch` (see the fit rules in
  `SKILL.md`). It is a planning aid, never a commitment level.
- Empty sections stay, with "None.", so the team sees they were checked.
- Write titles as they are in the item's file; the id is what settle
  uses.
