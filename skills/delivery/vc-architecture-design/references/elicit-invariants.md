# Elicit the Invariants

Full procedure for `vc-architecture-design` steps 6-7.

## Ground rules

- One question at a time. Skip anything already answered by the PRDs,
  the codebase read, or (epic scope) a parent invariant — don't re-ask
  what's already known or already settled above this scope.
- Propose, don't poll: every question carries a concrete suggestion
  grounded in the PRDs or the code, with brief reasoning, and the user
  confirms or picks an alternative.
- **Load-bearing calls get options.** For a call that's expensive to
  reverse — a greenfield stack or paradigm, a new service or submodule
  boundary, a new datastore, sync vs async integration — present 2-3
  concrete options instead of one suggestion. For each, name the
  assumption it leans on hardest and the condition under which it fails
  first, then recommend the smallest one that meets the criteria, or
  the cheapest to back out of. Everything else gets a single suggestion.

## Topics — whole-product and epic scope

- **Stack** (greenfield submodules only — a brownfield submodule's stack
  is whatever the codebase read found there; ratify it, don't re-decide
  it): for each layer the in-scope features actually need — frontend,
  backend, a persistence/database engine if anything needs to be stored
  durably, and any other layer the scope clearly calls for (cache,
  queue, search) — propose a concrete stack grounded in what the PRDs
  describe, not a generic default. State the reasoning briefly (e.g.
  "these features read as a typical CRUD web app with moderate write
  volume and relational data — Postgres fits well; SQLite would fit
  instead if this is meant to run single-user/embedded, MySQL/MariaDB if
  the team already standardizes on one of those, MSSQL if the hosting
  environment is already SQL Server-based") and let the user confirm or
  pick an alternative — never just assert a choice unexamined. Don't ask
  about a layer nothing in scope needs. Once chosen, this stack is what
  every future feature in scope is expected to use — it isn't
  re-litigated per feature. Changing it later is a supersession (below),
  and the reason has to be a genuine technical blocker (the chosen stack
  can't achieve a specific goal something now needs), not preference
  drift or "the newer option looked nicer."
- **Design paradigm**: propose one based on what the codebase read found
  if the submodule isn't empty (ratify it — don't propose something
  different just because it's not your first choice) or on the shape of
  what's in scope if it's greenfield (e.g. "these features read as CRUD
  over one datastore — layered? or do you want hexagonal for
  testability here?"). Let the user confirm or override either way.
- **Submodule ownership**: list every `<submodule_root>/<repo-name>/` the
  scope plausibly touches (from the codebase read, or ask directly for
  anything it didn't cover). For each pair of submodules a feature
  crosses, ask what owns the shared contract and how they integrate (API
  call, shared package, event/queue, etc.). This is the decision a
  single-repo architecture doc never has to make — vc can span
  independently-versioned submodules, so the boundary between them is
  itself an invariant, not a per-story detail.
- **Foundational / unavoidable technical work**: from what the codebase
  read found missing (no auth wiring, no shared client for an
  integration, a migration something depends on), name the groundwork
  that has to exist before anything in scope can be demoed, and can't
  itself be reframed as user-facing. This becomes the spine's Technical
  Prerequisites section — a `/vc:create-pbi` enabler or a task, never
  a story of its own.
- **Consistency conventions**: naming, id/data formats, error shapes,
  auth — only where two things in scope could plausibly pick
  differently.

## Topics — feature scope

Stack, paradigm, and conventions are inherited, not re-asked — a feature
that seems to need a different stack is a parent conflict (below), not a
local decision. Instead, walk the feature's criteria and settle how it
lands:

- **Touched submodules and contract changes**: for each submodule the
  feature touches, what it adds or changes there, and for each pair it
  crosses, the contract between them (new endpoint, event, shared type,
  schema field) — and which side owns it.
- **Data**: entities, fields, or tables the feature adds or changes,
  where each lives, and any migration or backfill existing data needs.
- **Reuse vs new**: for each criterion, the existing component,
  endpoint, or table it extends (brownfield) or the new one it needs.
  Default to extending what the codebase read found; a new component
  needs a reason.
- **Feature-only needs**: a layer, integration, or constraint (cache,
  queue, third-party API, rate limit, permission) nothing above this
  scope covers and only this feature needs. If a sibling feature will
  plausibly need it too, say so — it may belong in the epic spine
  instead.
- **Foundational work**: the same as at broader scopes, limited to what
  this feature alone depends on.

**Litmus test** for everything above, at every scope: would two things
in scope, built independently, diverge on this? At feature scope, "two
things" means two stories of this feature, or this feature and the code
it extends. If no, it doesn't belong here — leave it to
`vc-tasks-breakdown`.

## Conflicts with a parent spine (epic and feature scope)

If a decision here would contradict or weaken an invariant inherited
from a parent spine, that's a **conflict to surface**, not a local
override — stop, tell the user which parent `AD` it conflicts with, and
let them resolve it (change the local decision, or record a proposed
parent spine change per `propose-solution.md` for the parent scope to
apply) rather than silently picking one. A local exception to a parent
invariant is technical debt, never the recommended option.

## Superseding this spine's own prior decision

A different case from a parent conflict: if a decision here changes what
an existing `AD-n` in this same spine already settled, that's a
deliberate, sanctioned change. Confirm with the user this is
intentional, then **require a reason** — a decision without one isn't
useful history. If the trigger was a PRD change recorded by `vc-prd` —
a feature `prd.md`'s `## Decisions` entry or `## Changes to delivered
features` row (an older PRD's `## Revision History` entry), or the top
entry of `artifacts/prd-history.md` for a product-level change —
reference it directly as the reason rather than re-deriving one.

## Decision log line formats

Append to this scope's `.decisions.md`, next to its `architecture.md`
(`artifacts/.decisions.md` whole-product,
`artifacts/epic-<epic-slug>/.decisions.md` per-epic, or the feature
folder's own `.decisions.md` per-feature — create it if missing), one
line per confirmed decision:

```
- [<date>] <what was decided> — binds: <scope>; prevents: <the divergence>
```

A supersession carries the reason and points at what it replaces:

```
- [<date>] SUPERSEDES AD-<old>: <new decision> — reason: <why, citing the triggering PRD's Decisions entry if there was one>; binds: <scope>; prevents: <the divergence>
```

A proposed parent spine change (`propose-solution.md`) and knowingly
accepted technical debt each get their own line:

```
- [<date>] PROPOSED PARENT CHANGE P-<n> (<kind>) to <parent spine path>: <change> — unblocks: <criterion>; status: open
- [<date>] ACCEPTED DEBT TD-<n>: <what> — reason: <why>; payoff trigger: <when>; binds: <scope>
```
