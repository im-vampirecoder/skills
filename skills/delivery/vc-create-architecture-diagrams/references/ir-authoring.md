# IR Authoring

How `vc-create-architecture-diagrams` step 5 writes each diagram's
typed JSON. The compiler (`scripts/compiler/validate-ir.mjs`) is the
final authority — when it rejects a field, it says which one.

## Envelope (every diagram)

```json
{
  "schema_version": 1,
  "diagram_type": "architecture",
  "meta": {
    "title": "Share Notes — Topology (to-be)",
    "subtitle": "FEATURE-share-notes · from architecture.md, 2026-10-08",
    "description": "One-sentence summary for screen readers",
    "visual_preset": "classic",
    "theme": "light",
    "views": []
  }
}
```

- `title` names the scope, the diagram, and the state.
- `subtitle` names the scope id and the spine's `updated` date (to-be)
  or "from code, <date>" (as-is), so a stale diagram is visible.
- Use `visual_preset: "classic"` and `theme: "light"` unless the user
  asks otherwise — the reader toggles dark mode itself. Presets:
  `classic`, `signal-flow`, `blueprint`, `editorial`.
- IDs match `^[a-zA-Z0-9_-]{1,64}$` and must be unique; reuse the same id
  for the same component across every diagram in the set. Text fields
  max 512 characters.

## Archetypes — fields and enums

**architecture** — `components[]` (1-250, required), `connections[]`,
`boundaries[]`.
- component: `id`, `label`, `role` (`frontend` | `backend` | `database` |
  `cache` | `queue` | `storage` | `gateway` | `auth` | `external` |
  `worker`), optional `description`, `layer` (0-10, left-to-right
  column; omit to let the compiler rank).
- connection: `from`, `to`, optional `label`, `protocol`, `kind`
  (`sync` | `async` | `stream` | `fallback` | `bi-directional`).
- boundary: `id`, `label`, `role` (`cloud` | `vpc` | `cluster` |
  `trust-boundary` | `private-network` | `external-zone`), `components`
  (member ids).

**sequence** — `participants[]` (2-50): `id`, `label`, `role` (`client` |
`service` | `database` | `gateway` | `external` | `queue`).
`messages[]` (1-500): `from`, `to`, `label` (required), `kind`
(`sync-call` | `async-signal` | `return` | `self-call` | `error`). A
`sync-call` opens an activation bar closed by the next `return`.

**dataflow** — `stages[]`: `id`, `label`, `order`. `nodes[]` (1-250):
`id`, `label`, `role` (`source` | `transform` | `store` | `sink` |
`consumer` | `filter` | `governance`), `stage`, optional
`classification` (`public` | `internal` | `confidential` | `pii` |
`restricted`). `flows[]`: `from`, `to`, `label`.

**lifecycle** — `states[]` (1-250): `id`, `label`, `kind` (`initial` |
`active` | `waiting` | `failure-recoverable` | `failure-fatal` |
`terminal-success` | `terminal-cancelled`). `transitions[]`: `from`,
`to`, `event`, optional `kind` (`normal` | `retry` | `timeout` |
`cancel` | `fail`).

**workflow** — `lanes[]`: `id`, `label`, `role` (`user` | `frontend` |
`orchestrator` | `worker` | `approver` | `system`). `steps[]` (1-250):
`id`, `label`, `lane`, `kind` (`start` | `action` | `decision` | `wait` |
`subprocess` | `terminal-success` | `terminal-failure`).
`transitions[]`: `from`, `to`, optional `condition`, `kind` (`normal` |
`branch-true` | `branch-false` | `retry` | `exception`).

## Evidence in `description`

Every component, participant, node, and state carries its evidence in
`description` — it shows in the reader on focus:

- to-be: the `AD` (`AD-3`, or `epic-billing/architecture.md#AD-3` when
  inherited) or Criteria Coverage row it comes from.
- as-is: the scout `path:line` it was found at.

Connections have no `description`; put the `AD` id at the end of the
`label` when a decision fixes that connection (`"REST · AD-4"`), as long
as the label stays within the length limit below.

## Marking what changes (to-be only)

The compiler has no change field, so mark it in text and chapters:

- Label suffix: `" (new)"` for a component, participant, node, or state
  that doesn't exist as-is; `" (changed)"` for one whose role, owner, or
  contract the spine changes.
- Connections get no marker in the label — edge labels sit in a narrow
  gap between nodes and a prefix gets clipped. List new and changed
  connections in the "What changes" chapter's `narrative` instead.
- Something removed: leave it out of the to-be, and name it in the
  "What changes" chapter's `narrative`.
- Chapters (`meta.views`, max 5): first `"overview"` (no focus — the
  whole picture), then `"what-changes"` with `focus_nodes` set to every
  new or changed id and a `narrative` listing additions, changes, and
  removals with their `AD` ids. Optional further chapters walk one flow
  each via `highlight_route` (`[start-id, end-id]`).

## Size and legibility

- Node labels: 2-4 words; put detail in `description`, not the label.
- Edge labels (connections, messages, flows, transitions): about 16
  characters at most — longer ones get clipped where the edge meets a
  node. Put the protocol in `protocol`, not the label.
- Topology past ~25 components or a sequence past ~15 messages: split it
  (one diagram per submodule group, or one flow per scenario) rather than
  shrinking text.
