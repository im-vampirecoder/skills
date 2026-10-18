# Sprint Capacity File Contract

The shared contract between the Scrum Master's capacity skill (SM-04,
`vc-plan-team-capacity`), which writes the file, and
`vc-plan-sprint-candidates`, which reads it. Until the SM skill exists,
the SM writes the file by hand against this contract.

Capacity is the SM's number. `vc-plan-sprint-candidates` never computes,
estimates, or negotiates it: it reads the file, checks it, and uses it to
scale the team's story throughput. No file means no candidate plan.

## Location

```
artifacts/sprints/<sprint-slug>/capacity.md
```

Relative to the tracking repo root (the folder holding `.vc/config.toml`).
`candidates.md` for the same sprint is written beside it.

### Sprint slug

Derived from the sprint's name - the last segment of the iteration path
(`MyProject\Release 3\Sprint 42` -> `Sprint 42`):

1. Lowercase.
2. Replace every run of characters other than `a-z` and `0-9` with one `-`.
3. Trim leading and trailing `-`.

`Sprint 42` -> `sprint-42`; `2026 Q4 / Sprint 3` -> `2026-q4-sprint-3`.
Both skills apply the same rule, so the folder is found without asking.

## Frontmatter

```yaml
---
sprint: Sprint 42
iteration_path: MyProject\Release 3\Sprint 42
start_date: 2026-10-12
finish_date: 2026-10-23
working_days: 10
members:
  - name: Anna de Vries
    id: 6f1c2d0e-0000-0000-0000-000000000001
    hours_per_day: 6
    time_off_hours: 8
  - name: Ravi Patel
    hours_per_day: 6
    time_off_hours: 0
available_hours: 112
published_by: Sam Jansen
published_at: 2026-10-09
---
```

| Field | Required | Meaning |
|---|---|---|
| `sprint` | yes | Sprint name exactly as the tracker shows it. |
| `iteration_path` | yes | Azure DevOps: the work item Iteration Path of the team's sprint (`MyProject\Sprint 42`, without the `\Iteration\` node segment). Local: the same value stories carry in their `iteration:` field. |
| `start_date`, `finish_date` | yes | ISO dates (`YYYY-MM-DD`), inclusive. |
| `working_days` | yes | Working days in the sprint after team-wide non-working days (weekends, public holidays). |
| `members` | yes | One entry per Developer contributing to the sprint. |
| `members[].name` | yes | Display name as the tracker shows it. |
| `members[].id` | no | The person's Azure DevOps identity id. Take name and id from `.vc/config.toml`'s `[[team_members]]` (saved by `/vc:setup`), so the roster stays the same sprint to sprint. |
| `members[].hours_per_day` | yes | Hours this person can give to sprint work on a normal day. Whether ceremonies and support duty are already taken out is the SM's call; say which in the body. |
| `members[].time_off_hours` | yes | Registered time off inside the sprint, in hours. `0` when none. |
| `available_hours` | yes | Team total; see the formula below. |
| `published_by` | yes | Who published the figure (normally the SM). |
| `published_at` | yes | ISO date the figure was published. |

### Formula

```
member hours    = max(0, hours_per_day x working_days - time_off_hours)
available_hours = sum of member hours
```

Team-wide days off reduce `working_days`; one person's leave goes in their
`time_off_hours`. Never count the same day in both.

## Body

Free markdown below the frontmatter, for the assumptions behind the number:
whether ceremonies are already deducted, support rotation, a new joiner
ramping up, a known release freeze. Shown to the PO as is; never parsed.

## Reader checks

`vc-plan-sprint-candidates` applies these when it loads the file:

| Condition | Action |
|---|---|
| File missing | Stop. Tell the user capacity has not been published for this sprint and point to the SM's capacity skill (or this contract, until it exists). |
| Frontmatter unparseable or a required field missing | Stop and name the field. |
| `sprint` or `iteration_path` does not match the sprint being planned | Stop: the file is for another sprint. |
| `available_hours` differs from the recomputed formula | Warn, show both values, and use the recomputed one. |
| `published_at` is after `start_date` | Warn: capacity was published after the sprint started, so it was likely negotiated in planning. Continue. |
| A member has `hours_per_day` of 0 | Warn (probably someone who should be left out). Continue. |

## Usual capacity (for throughput scaling)

Throughput is scaled by this sprint's `available_hours` against the team's
usual hours. The usual hours are the median `available_hours` from the
`capacity.md` files of the past sprints used for throughput. For a past
sprint with no file, use the current file's members at full time
(`hours_per_day x working_days`, no time off) and label the result as an
assumption in the candidate plan.

## Azure DevOps team capacity

ADO stores the same shape per team and iteration: capacity per day per
member (split by activity) and days off per member. A future version of the
SM skill may read or write it there; the file stays the contract either way.
