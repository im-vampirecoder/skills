---
feature_id: FEATURE-<feature-slug>
status: as-built
generated_at: <YYYY-MM-DD>
sources: [<repo>@<short-sha>, <repo>@<short-sha>]
asserted: <count of ✅ claim rows>
corroborated: <count of 🔵 claim rows>
inferred: <count of 🟡 claim rows>
open_questions: <count of OQ rows>
---

# <Feature title> - as built

## Confidence legend

| Label | Meaning |
|---|---|
| ✅ | Stated by the code or by an active test at the cited line |
| 🔵 | Inferred, backed by two or more independent places in the code |
| 🟡 | Inferred; the code doesn't say. Needs confirmation |

## Scope

| Statement | Label | Source |
|---|---|---|
| <what a user can do with this feature> | ✅ | S1:<line> |

## Actors

| Actor | Can do | Label | Source |
|---|---|---|---|
| <role in business words> | <actions> | ✅ | S1:<line> |

## Functional

| ID | When | The system | Label | Source |
|---|---|---|---|---|
| FR1 | <trigger> | <result the user sees or the system keeps> | ✅ | S1:<line> |

## Non-functional

| ID | Requirement | Label | Source |
|---|---|---|---|
| NFR1 | <measurable behaviour the code enforces: timeout, rate limit, retention> | ✅ | S1:<line> |

## Business rules

| ID | Rule | Applies to | Label | Source |
|---|---|---|---|---|
| BR1 | <rule with its real value> | FR1 | ✅ | S1:<line> |

## Errors

| ID | If | The user sees | For | Label | Source |
|---|---|---|---|---|---|
| ERR1 | <condition> | "<exact wording from the catalog>" | FR1 | ✅ | S1:<throw line>, S2:<catalog line> |

## State transitions

| Entity | From | To | Trigger | Label | Source |
|---|---|---|---|---|---|
| <entity> | <state> | <state> | <what causes it> | ✅ | S1:<line> |

## Success criteria

| Statement | Label | Source |
|---|---|---|
| <observable outcome the code guarantees> | ✅ | S1:<line> |

## Entities

| Entity | Holds | Label | Source |
|---|---|---|---|
| <business name> | <what it records, in business words> | ✅ | S1:<line> |

Details: [erd.md](erd.md).

## Flows

| Flow | Summary | Label | Source |
|---|---|---|---|
| <flow-slug> | <one line> | ✅ | S1:<line> |

Details: [flows.md](flows.md).

## Screens

| Screen | Purpose | Label | Source |
|---|---|---|---|
| <screen name> | <what the user does there> | ✅ | S1:<line> |

## Constraints & dependencies

| Statement | Label | Source |
|---|---|---|
| <external service, platform limit, sign-in requirement> | ✅ | S1:<line> |

## Sources

| ID | Path | Lines | What it covers |
|---|---|---|---|
| S1 | <submodule_root>/<repo>/<path> | <a>-<b> | <one line> |

## Open questions

| ID | Question | About | Why the code can't answer |
|---|---|---|---|
| OQ1 | <question for the PO> | <FR1, BR1, actor or entity> | <what was searched, or why code can't show intent> |

## Gaps & conflicts

| Kind | Detail | Search run |
|---|---|---|
| Gap | <what is missing or unclear> | `<pattern and scope searched>` |
| Conflict | <two places in the code that disagree> | `<path:line>` and `<path:line>` |
