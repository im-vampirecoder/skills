# Diagram Catalog

Which diagrams `vc-create-architecture-diagrams` step 4 picks per
scope, and what each one draws from. Fewer, sharper diagrams beat a full
set: draw a flow or lifecycle only when it answers a question the
topology can't.

## Per scope

| Diagram | Archetype | Product | Epic | Feature | Drawn from |
| --- | --- | :---: | :---: | :---: | --- |
| `topology` | architecture | always | always | always | Submodule Ownership, Stack, `AD`s on boundaries and integration; as-is from `docs/architecture.md` + scouting |
| `flow-<slug>` | sequence | 1-3 | 1-3 | 1 per cross-submodule criterion, max 3 | `AD`s fixing a contract between submodules; feature Criteria Coverage rows that span 2+ submodules |
| `data-<slug>` | dataflow | rare | when data moves between stores | when the feature adds a migration, backfill, import, or export | `AD`s on data ownership; Data decisions; scout findings on stores |
| `lifecycle-<entity>` | lifecycle | rare | when an entity's status crosses features | when the feature adds or changes a status field | PRD acceptance criteria naming states; status enums found by scouting |
| `workflow-<slug>` | workflow | — | when a process hands off between roles or systems | when a criterion is a multi-step, multi-actor process | PRD scenario and acceptance criteria |

## What each diagram must show

- **topology** — one boundary per `<submodule_root>/<repo-name>`
  submodule (`role: "cluster"`), externals in an `external-zone`
  boundary, every datastore and queue as its own component. A
  connection's `protocol` comes from the Submodule Ownership "Integrates
  via" column. Feature scope: only the submodules the feature touches,
  plus the one component on each untouched neighbour it calls. Product
  scope: the whole system, collapsed to one or two components per
  submodule when it passes ~25 components.
- **flow** — the happy path first, then at most one `error` message for
  the failure the spine or PRD actually addresses. Participants are
  components from the topology, with the same ids.
- **data** — stages in the order data actually moves; mark `pii` or
  `confidential` where the spine or PRD says so, never by guess.
- **lifecycle** — only states the PRD or the code names; `initial` and
  terminal kinds where the code or criteria make them explicit.
- **workflow** — one lane per actor (user, each system, approver);
  decisions only where a criterion branches.

## As-is vs to-be

- Topology: draw both whenever an as-is exists and the to-be differs.
  If they're identical, draw one `topology.json` and say "no structural
  change" in the summary.
- Flows, data, lifecycles, workflows: draw the to-be; add an as-is only
  when the flow already exists in the code and the spine changes it.
- Greenfield (no code): to-be only. No spine: as-is only.

## Arrow meaning

Keep arrow kinds consistent across every diagram in a set:

| Relationship | Architecture `kind` | Sequence `kind` |
| --- | --- | --- |
| Request/response call | `sync` | `sync-call` + `return` |
| Event, message, job | `async` | `async-signal` |
| Continuous feed | `stream` | `async-signal` |
| Degraded path | `fallback` | `error` |
| Mutual dependency | `bi-directional` | — |

## Naming

kebab-case, scope-free (the folder already carries the scope):
`topology`, `flow-checkout`, `data-order-backfill`,
`lifecycle-invoice`. Keep a name stable across re-runs so links to it
keep working.
