# <Feature title> - evidence

## Entry points

| Entry point | Kind | Source |
|---|---|---|
| <route, screen, command or job> | <HTTP endpoint / screen / job / message handler> | `<submodule_root>/<repo>/<path>:<line>` |

## Validation

| Field | Rule | Source |
|---|---|---|
| <field> | <rule with values> | `<path>:<line>` |

## Errors

| Code or key | Wording | Throw site | Catalog |
|---|---|---|---|
| <key> | "<exact wording>" | `<path>:<line>` | `<path>:<line>` |

## Rules and constants

| Rule | Value | Source |
|---|---|---|
| <constant, guard, option or tested rule> | <value> | `<path>:<line>` |

## Entities

| Entity | Stored as | Source |
|---|---|---|
| <entity> | <class, table, model, migration> | `<path>:<line>` |

## Cross-repo hops

| From | To | Through | Source (from) | Source (to) |
|---|---|---|---|---|
| <action in one submodule> | <what it triggers in another> | <HTTP call, queue, shared storage> | `<path>:<line>` | `<path>:<line>` |

## Gaps

| Gap | Search run | Scope |
|---|---|---|
| <what wasn't found> | `<pattern>` | <submodules searched> |
