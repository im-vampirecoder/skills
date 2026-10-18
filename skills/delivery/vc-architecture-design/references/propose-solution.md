# Propose the Solution

Full procedure for the proposal that opens `vc-architecture-design`
step 6 at feature scope (including a run started from a PRD path), before
any elicitation. Its "Technical debt" rules apply at every scope. The
goal: hand the user one concrete, already-checked architecture proposal
for the PRD to confirm or push back on, instead of building it up
question by question from nothing.

## Hard boundaries

- **Architecture only, never code.** A proposal names submodules,
  ownership, contracts (what crosses a boundary and who owns it), data
  (what is stored where), integration style, and the invariants that
  keep independent work from diverging. It never contains code
  snippets, file or class names to create, function signatures, refactor
  steps, or library calls — that's `vc-tasks-breakdown` and
  `vc-implement`'s job. If the user asks for code here, say it belongs
  to those skills and stay at the architecture level.
- **Resolve the requirement, nothing more.** Every element of the
  proposal traces to a Success Criterion, Acceptance Criterion,
  Constraint, or requirement (`FR-` / `NFR-` / `BR-` / `ERR-`) in the
  PRD. NFRs are outcomes to meet: weigh every option against them. A change the PRD doesn't need, however tempting
  (a cleanup, a modernization, a pattern the code "should" use), is left
  out. If something unrelated looks broken, mention it once in the
  summary as an observation, not as part of the proposal.
- **Don't contradict what exists.** The product spine, the epic spine
  (if any), and the code as `docs/architecture.md` and the step 3
  investigation describe it are the baseline. The default proposal
  extends that baseline; it never quietly replaces a pattern, stack
  choice, or ownership boundary that's already there.
- **Don't add technical debt.** See "Technical debt" below. The
  recommended option is always one that adds none.

## 1. Draft the proposal

From steps 2-4, write a short proposal in chat, not yet in any file:

- **How it lands**: per touched submodule, what the PRD needs from it
  (extend an existing component/endpoint/table — cite `path:line` — or
  add a new one, with the reason an existing one can't carry it).
- **Contracts**: each boundary the feature crosses, what crosses it, and
  which side owns it — following the ownership and integration style
  the parent spines already fixed.
- **Data**: what the feature stores or changes, where, and whether
  existing data needs a migration or backfill.
- **Criteria map**: one line per criterion naming what serves it — this
  becomes step 8's Criteria Coverage.
- **Open points**: anything the PRD or code leaves genuinely undecided,
  each with your suggested answer. These are what step 6 interviews on.

Keep each item one or two lines. A load-bearing open point (new service
or submodule, new datastore, sync vs async, a new external integration)
gets the 2-3 options treatment from `elicit-invariants.md`.

## 2. Check it against the baseline

Before showing it, walk every item in the draft against:

- each binding `AD` and convention in the parent spines;
- the Stack, Design Paradigm, and Submodule Ownership those spines fix;
- `docs/architecture.md`'s System Boundaries, confirmed against the code
  where an item depends on it.

Anything that fits as-is stays in the proposal. Anything that would
contradict the baseline is reworked until it fits. Only when no option
that fits can meet a criterion does it become a **parent spine change**
(below) — never a local exception.

## 3. Propose parent spine changes, if any

Some PRDs genuinely need the product-level (or epic-level) architecture
to move: a capability nothing owns yet, a new cross-cutting convention a
sibling feature will need too, a stack layer the product spine doesn't
cover, or an existing `AD` that blocks a criterion outright. List each as
one entry:

- **Kind**: `add` (a new invariant at the parent), `amend` (a wording
  correction, no change of decision), or `supersede AD-<n>` (an actual
  change of a parent decision).
- **Target**: the parent spine path, and the `AD` id for amend/supersede.
- **Change**: the proposed invariant, in the same Binds / Prevents /
  Rule shape a parent `AD` uses.
- **Why the PRD needs it**: the criterion it unblocks, and why no option
  within the current spine meets it. "Would be nicer" is not a reason;
  a supersession needs a genuine technical blocker.
- **Ripple**: other features, epics, or child spines the change would
  reach (grep the child spines for the `AD` id when superseding).

Ask the user to confirm each one. This run never writes a parent spine —
parents are read-only below their own scope. Confirmed entries go into
this spine's Proposed Parent Spine Changes section with status `open`,
and are logged in this scope's `.decisions.md`. Every decision in this
spine that depends on one is marked as depending on it, so nobody builds
on a parent change that hasn't landed yet. Step 10 tells the user to run
the parent scope's Update, which picks up open proposals (step 5).

No parent change needed is the normal, preferred outcome — say so
plainly rather than inventing one.

## 4. Present and confirm

Show the checked proposal, any parent spine changes, and the technical
debt assessment (below) together. Then ask the user to:

- **Confirm** — every item becomes a decision (step 7 logs each), and
  step 6 only asks about the open points; or
- **Push back** on specific items — run step 6's interview on just
  those, one question at a time, re-checking each answer against the
  baseline (step 2 above) before accepting it.

An answer that contradicts the baseline is not accepted as a local
decision: surface it as a parent conflict (`elicit-invariants.md`) or as
a proposed parent spine change, and let the user choose.

## Technical debt

Applies to every option you put in front of the user, at every scope.

**Counts as debt** — an option that:

- adds a second way of doing something an `AD`, convention, or existing
  component already covers (a parallel auth path, a duplicate entity, a
  second error shape);
- reaches across an ownership boundary instead of going through the
  owning submodule's contract (reading another submodule's tables, a
  shared database used as an integration point the spine didn't choose);
- defers work the PRD needs to a "later" with no trigger (skipping a
  migration or backfill, a temporary shim, a hard-coded value that
  belongs in config, a manual step standing in for an automated one);
- takes a local exception to a parent invariant instead of changing the
  parent;
- picks a stack version that's unsupported or about to be, or a new
  dependency where an existing one already covers the need.

**Rules**:

- The recommended option adds no debt. If two options both meet the
  criteria, the debt-free one wins even if it's more work.
- A debt-adding option is only shown when no debt-free option meets the
  criteria (a hard deadline, a third-party limit, a parent change that
  can't land in time). Label it `[adds debt]`, and state the debt, what
  it will cost later, and the condition that should trigger paying it
  off.
- If the user still chooses it: append
  `- [<date>] ACCEPTED DEBT TD-<n>: <what> — reason: <why>; payoff trigger: <when>; binds: <scope>`
  to `.decisions.md`, and add a row to the spine's Technical Debt section.
  Suggest a `/vc:create-pbi` enabler for the payoff.
- **Existing debt the PRD touches** (found in step 3 — a duplicate
  component the feature would extend, a boundary already being bypassed
  where the feature lands): report it to the user so they know, and keep
  the proposal from building more on top of it. Fixing it is only in
  scope when a criterion can't be met otherwise; otherwise it's listed
  in the summary, not added to the proposal.
