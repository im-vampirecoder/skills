---
name: vc-architecture-design
description: Interview the user to design a project's architecture — tech stack per layer, design paradigm, submodule ownership, cross-feature conventions, foundational work — grounded in the existing code for brownfield and in the PRDs for greenfield. Whole-product scope with no argument, epic scope with an epic argument, feature scope with a feature argument or a PRD path (each inheriting the spines above it). At feature scope it first proposes a solution for the PRD, checked so it doesn't contradict the existing architecture, plus any product- or epic-level spine changes the PRD needs, then interviews only on what's open; it flags any technical debt an option would add and never recommends one that adds debt. Architecture only, never code changes. Writes a short architecture.md spine plus an append-only decision log, then lints it and runs parallel reviewer subagents before marking it reviewed (`review` re-runs only that gate). Triggered by /vc:architecture-design; built-in only.
---

# Architecture Design

Help the user actively design the project's architecture, not just record
decisions after the fact: interview them on the choices a project needs
early — tech stack per layer, design paradigm, submodule ownership,
cross-feature conventions — proposing informed suggestions grounded in
the product's scope rather than open-ended questions with no anchor.
Fix only what would let two things built independently diverge; file
layout and per-story implementation choices stay out of this document,
that's `vc-tasks-breakdown`'s call.

Three scopes, same skill, each inheriting every spine above it:

- **Whole-product** (`$ARGUMENTS` empty): the invariants that should bind
  *every* epic — output is `artifacts/architecture.md`. This is the
  common case, and the one to reach for first on a project of any size:
  one shared spine, written once and updated as the product grows.
- **Epic** (`$ARGUMENTS` names an epic): the invariants specific to one
  epic, on top of whatever the product spine already fixed — output is
  `artifacts/epic-<epic-slug>/architecture.md`. Reach for this only when
  an epic needs decisions the product spine doesn't cover: it spans
  multiple submodules, or has a real cross-feature consistency risk the
  product spine is silent on.
- **Feature** (`$ARGUMENTS` names a feature, or is a path to its
  `prd.md`): how one feature's PRD lands
  on the architecture — which submodules it touches, the contracts and
  data it adds or changes, and how each of its success/acceptance
  criteria is served — output is `architecture.md` in the feature's own
  folder. Reach for this when a feature is big or risky enough that
  `vc-tasks-breakdown` shouldn't be deciding its shape story by story.
  This scope starts with a proposed solution for the PRD (step 6)
  rather than a blank interview, and can propose changes to the epic or
  product spine when the PRD genuinely needs them.

At every scope the skill stays at the architecture level and on the
requirement in front of it: it never suggests code changes, never adds
work the PRDs don't need, and never recommends an option that adds
technical debt (`references/propose-solution.md`, "Technical debt").

Optional at every scope: a small product, epic, or feature can skip
straight to `/vc:create-user-stories` without running this at all.

## Workflow

0. **Resolve the mode**
   - A leading `review` token in `$ARGUMENTS`: Review Mode — resolve the
     scope from the rest of `$ARGUMENTS` as step 1 does, then run only
     step 9's review gate against that scope's existing spine
     (`references/review-gate.md`, Review Mode). No `review` token →
     continue with step 1.

1. **Resolve the scope**
   - `$ARGUMENTS` empty: whole-product scope. Target root is `artifacts/`.
   - `EPIC-<slug>`, or a slug matching `artifacts/epic-<slug>/`: epic
     scope. The epic must have at least one assigned feature — if no
     epic exists yet, tell the user to run `/vc:propose-epic` first.
     Target root is `artifacts/epic-<epic-slug>/`.
   - `FEATURE-<slug>`, or a slug matching `artifacts/<slug>/prd.md`
     (unassigned) or `artifacts/epic-*/feature-<slug>/prd.md`
     (assigned): feature scope. Target root is that feature's folder.
     An unassigned feature is fine — `vc-propose-epic`'s `git mv`
     carries the spine along when it's assigned later.
   - A path to a PRD file: `artifacts/prd.md` is whole-product scope;
     a `prd.md` inside a feature folder (`artifacts/<slug>/` or
     `artifacts/epic-*/feature-<slug>/`) is that feature's scope. A PRD
     outside `artifacts/` has no folder for its spine to live in: stop
     and tell the user to bring it in with `/vc:prd` first.
   - A bare slug matching both an epic and a feature: ask which scope
     the user means. Matching nothing: stop and say so.

2. **Read context**
   - Always read the product `artifacts/prd.md`.
   - Whole-product scope: read every `epic.md` and assigned feature
     `prd.md` under every `artifacts/epic-*/`, plus any unassigned
     `artifacts/<feature-slug>/prd.md` — the spine has to hold across all
     of them, not just the ones already in an epic.
   - Epic scope: read this epic's `epic.md` and every assigned feature's
     `prd.md` (and any `stories-*.md` already written) under it.
   - Feature scope: first run `/vc:requirements conflicts <feature>`
     (through the Skill tool), so the architecture isn't designed on
     contested requirements. It walks the PO through any conflict it
     finds; the user chooses to resolve them now or continue. Continuing
     → every unresolved conflict is carried as open (both IDs and the
     one-line reason) into the spine's Open Requirement Conflicts and the
     step 10 summary, and no decision may silently pick a side. No
     `## Requirements` section in the PRD → skip the check and say so.
   - Feature scope: read this feature's `prd.md`, any `stories-*.md` and
     `ux/` already written under it, and its epic's `epic.md` if
     assigned. List its Success Criteria and Acceptance Criteria — every
     one of them must be accounted for in step 8's Criteria Coverage.
     Also list its live `NFR-` entries (skip retired or superseded IDs):
     each NFR is a business outcome (wait time, availability, retention,
     who can see what) and is a decision input — options are weighed
     against it, and each NFR gets its own Criteria Coverage row. An NFR
     holding `TBD` is an open point to raise, never a number to assume.
     Read the PRD's `## Decisions` and, when present,
     `## Changes to delivered features`: settled product choices this
     design must respect, and the `done` features' requirements this feature
     replaces.
   - Use each PRD's Touchpoints and Constraints sections as the first
     hint for which submodules are in play.

3. **Investigate the existing codebase (brownfield)**
   - Read `.vc/config.toml`'s `submodule_root` (default `src`).
   - Make sure the code-derived docs are there and current, using the
     `vc-docs` skill rather than mapping the codebase from scratch:
     - `docs/architecture.md` (or `docs/architecture/`, if `vc-docs`
       auto-split it) missing, and at least one submodule has code: ask
       the user to run `vc-docs` `scan` now (it writes `docs/` and may
       propose feature stubs), and invoke it on a yes.
     - Present but older than the newest commit in any in-scope
       submodule (compare `git log -1 --format=%cs` on the doc against
       `git -C <submodule_root>/<repo-name> log -1 --format=%cs`): offer
       `vc-docs` `refresh`, focused on the in-scope submodules.
     - The user declines either: carry on, and say in the summary that
       the docs were missing or stale.
   - Read `docs/architecture.md` first — its System Boundaries and Stack
     are a code-derived starting map. Treat it as a pointer, not proof:
     confirm anything load-bearing against the code itself.
   - For each `<submodule_root>/<repo-name>/` submodule the in-scope
     features plausibly touch (from step 2's hints, or ask), find out
     the following. **One submodule**: read it inline yourself.
     **2+ submodules**: spawn the `vc-scout` subagent
     (`vc:vc-scout` when installed through the plugin) in `focused`
     mode, one per submodule, in parallel, with this as its brief:
     what patterns/paradigm are already in use, what user-facing
     journeys or capabilities already exist there that overlap the
     in-scope PRDs, and what's genuinely missing (no auth wiring, no
     shared package for X, etc.), plus any `docs/architecture.md` claim
     about that submodule to confirm or refute, and any existing
     technical debt where the in-scope work would land (duplicated
     components, bypassed boundaries, temporary shims). Feature scope narrows the
     brief to the feature's criteria — the existing component, endpoint,
     or table each one would extend. Cite `path:line` either way; with
     scouts, read a cited file yourself only where a decision hinges on
     detail the finding doesn't give.
   - If a submodule is empty or doesn't exist yet, it's greenfield for
     that submodule — nothing to ratify there.
   - Ratify what's already there, don't invent something new. Don't
     maintain this as a standing catalog inside `architecture.md` — it
     goes stale the moment the code moves; every skill that needs it
     (including this one, next run) re-reads the code fresh.

4. **Load the parent spines**
   - Whole-product scope: skip to step 5, there's no parent.
   - Epic scope: the parent is `artifacts/architecture.md`.
   - Feature scope: the parents are the feature's epic spine
     (`artifacts/epic-<epic-slug>/architecture.md`, assigned features
     only) and the product spine — the epic's own Inherited Invariants
     already carry the product's, so take each id from whichever spine
     defines it.
   - No parent exists: proceed standalone, and tell the user at the end
     that running `/vc:architecture-design` at the higher scope first
     would let this one inherit shared invariants instead of redeciding
     them locally — but don't block on it.
   - Parent exists: load it and its `.decisions.md`. Its `AD-n`
     decisions, conventions, and paradigm are **binding and read-only**
     here — carry them into this spine's Inherited Invariants table by
     their **original** ids, never renumbered, and don't re-elicit
     anything they already settle. Carry only the ones that actually
     constrain this scope, not the whole parent.

5. **Create or update**
   - `architecture.md` doesn't exist yet at this scope's target root:
     this is a Create run — go to step 6.
   - It exists: this is an Update run. Read it and this scope's
     `.decisions.md`, summarize what's already decided, and ask the user
     what changed (a new epic or feature landed, a new constraint, a
     feature's PRD was revised, the feature moved to a different epic)
     before eliciting anything new. Check what `vc-prd` records, newest
     entry first: each in-scope feature `prd.md`'s `## Decisions` and
     `## Changes to delivered features` sections, and
     `artifacts/prd-history.md` for the product PRD (product and epic
     scope). An older PRD that still has a `## Revision History` section
     (from before named requirement IDs) is read the same way. Any entry
     dated after this `architecture.md`'s `updated` date — or a PRD with
     no dated entry but a newer file modification, or a parent spine with
     a newer `updated` date — is a likely trigger: surface it rather than
     making the user recall it. Only revisit the sections the change actually
     touches.
   - Whole-product or epic scope (Create or Update): grep every spine
     below this one for a Proposed Parent Spine Changes row targeting
     this spine with status `open`. Walk each with the user — accept it
     (it goes through step 6 like any other decision) or reject it with
     a reason — and in the child spine flip that row's status to
     `applied (AD-<n>)` or `rejected — <reason>`. That status cell is
     the only edit this skill makes to a spine outside its own scope.

6. **Propose, then elicit the invariants**
   - Feature scope starts with a proposal, not a blank interview: draft
     one concrete architecture for the PRD from steps 2-4 — how it lands
     per submodule, the contracts and data it adds, a
     criterion-by-criterion map, and the open points — check every item
     against the parent spines and the existing code so it contradicts
     neither, add any parent spine changes the PRD truly needs, assess
     technical debt for every option, then ask the user to confirm or
     push back. Full procedure, including the never-code and no-debt
     rules: `references/propose-solution.md`.
   - One question at a time. Skip anything already answered by steps
     2-4. Whole-product and epic scope cover stack (greenfield
     submodules only), design paradigm, submodule ownership,
     foundational work, and consistency conventions. Feature scope
     covers how the feature lands: touched submodules and their contract
     changes, data it adds or changes, reuse vs new components, and
     anything only this feature needs — limited to the open points and
     pushed-back items from the proposal, not the whole list again.
   - Every option offered carries the technical debt assessment:
     the recommended one adds none, and a debt-adding one the user picks
     anyway is logged as `ACCEPTED DEBT` (`references/propose-solution.md`).
   - Full procedure — what to propose per topic, options for
     load-bearing calls, the litmus test, parent conflicts, and
     supersessions: `references/elicit-invariants.md`.

7. **Log each decision as it's confirmed**
   - Append one line to this scope's `.decisions.md` (next to its
     `architecture.md`) the moment each decision is confirmed — don't
     batch this until the end. Line formats (normal and supersession):
     `references/elicit-invariants.md`.
   - This file is append-only and never rewritten by this skill.

8. **Distill `architecture.md`**
   - Write (Create) or amend (Update) at this scope's target root,
     following the template and the `AD-n` id rules in
     `references/spine-template.md`. Cut any section that would be
     empty.
   - Feature scope: before writing, check that every criterion and NFR
     listed in step 2 maps to an `AD`, an inherited invariant, or an
     existing component in Criteria Coverage. Anything left unmapped goes back to
     the user as a gap — never silently dropped.
   - Confirmed parent spine changes go in Proposed Parent Spine Changes,
     accepted debt in Technical Debt — both cut when empty.

9. **Review the spine**
   - Lint it with `scripts/lint_spine.py`, then run the
     `vc-architecture-reviewer` agent once per lens (`evidence`,
     `divergence`, `failure-modes`) in parallel, then triage blockers with
     the user one at a time — fix or accept, both logged to
     `.decisions.md`. Set `status: reviewed` once no blocker is open.
   - Full procedure, including which lenses a small Update run can skip:
     `references/review-gate.md`.

10. **Summarize**
   - List the decisions made, the submodule ownership map, the Technical
     Prerequisites (if any), and anything under Deferred. If step 4
     loaded a parent, also list what was inherited. Feature scope: also
     list any criteria flagged as gaps. List any supersessions from this
     run explicitly (`AD-<old> → AD-<new>: <why>`), and the review
     outcome: blockers fixed, risks accepted, should-fix items left open,
     and the `reviews/` folder path. Feature scope: also list every
     requirement conflict left open in step 2, with
     `/vc:requirements conflicts <feature>` as the way to settle it.
   - **Technical debt**: every `TD-n` accepted this run with its payoff
     trigger (suggest a `/vc:create-pbi` enabler for each), and any
     existing debt step 3 found where this work lands. Say plainly when
     none was added.
   - **Proposed parent spine changes** (feature or epic scope): list
     each open one and tell the user to run `/vc:architecture-design`
     at that parent's scope to apply or reject it — decisions here that
     depend on one shouldn't be built until it lands.
   - **Whole-product or epic scope, when this run superseded an AD**:
     grep every spine below this one (`artifacts/epic-*/architecture.md`
     and every feature folder's `architecture.md` for product scope;
     this epic's `feature-*/architecture.md` for epic scope) for the
     superseded id in its Inherited Invariants table, and list any hits
     as spines that are now stale and should get their own Update run.
     This is a nudge in the summary, not an automatic cascade — nothing
     gets rewritten in those spines by this run.
   - For each Technical Prerequisite, suggest its home:
     `/vc:create-pbi` for a technical enabler larger than a task, or a
     dependency `/vc:tasks-breakdown` picks up as a task otherwise —
     never a non-demoable story (`vc-create-user-stories` rejects
     those).
   - Mention `/vc:create-architecture-diagrams` with the same scope
     argument to draw this spine as interactive as-is/to-be diagrams.
   - Tell the user `/vc:tasks-breakdown` and `/vc:implement` read
     whichever spine is most specific to each story (feature, then epic,
     then product) — its Submodule Ownership table decides which repo a
     story's work lands in.

## Notes

- Architecture, never code: no snippets, file or class names, function
  signatures, or refactor steps in a proposal, a question, or the
  spine. Stay on what the PRDs require — unrelated improvements are at
  most an observation in the summary.
- Never syncs to a tracker, and never touches `epic.md`'s Features
  section or `artifacts/epics.md` — those stay `vc-propose-epic`'s job.
- Running this skill at any scope is a recommendation, never a hard
  gate: every consumer treats the spine as optional context and falls
  back to `docs/architecture.md` when it's absent.
- A `Status: Superseded` block is history, not current guidance — any
  consumer reading Decisions follows whichever `AD` superseded it, never
  the superseded one. It stays in the document only so a reader can see
  *why* the current rule is what it is.
- The review gate reports and asks; it never rewrites a decision on its
  own. Review files under `reviews/` hold the latest run only — the
  lasting record of what was fixed or accepted is `.decisions.md`.
- Only this skill writes `architecture.md` and `.decisions.md`. To fold
  later technical calls back into a spine, re-run this skill's Update
  path at whichever scope.
- Step 3's codebase investigation is what makes this skill work for
  brownfield products, epics, and features, not just greenfield ones:
  ratify the stack and paradigm already there rather than propose a
  change nobody asked for. Don't skip it just because things feel
  familiar — the point is to check, not to assume.
- Spines nest by altitude: a parent binds read-only, a
  conflicting local decision gets surfaced rather than silently
  overriding, and each spine's own `AD-n` numbering is a fresh local
  sequence. Cite a decision from outside its own spine by path and id
  (`epic-billing/architecture.md#AD-3`) when a bare id would be
  ambiguous.
