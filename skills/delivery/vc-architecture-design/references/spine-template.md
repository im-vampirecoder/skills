# Architecture Spine Template

Full template and id rules for `vc-architecture-design` step 8. Cut any
section that would be empty — the template is a shape, not a form to
fill.

## Template

```markdown
---
scope: product | epic | feature
epic_id: EPIC-<epic-slug>          # epic scope, or an assigned feature
feature_id: FEATURE-<feature-slug> # feature scope only
status: draft | reviewed            # reviewed once no review blocker is open
updated: <date>
---

# Architecture — <Product name, Epic Title, or Feature Title>

## Stack
<product and epic scope only — a feature inherits its stack. Cut this
section at feature scope unless the feature adds a layer nothing above
it covers, and then list only that layer.>
<SEED — the concrete tech choice per layer, verified current at
authoring; the code owns this in detail once it exists. One row per
submodule the choice applies to; a shared choice across submodules can
list them together. Noted as "ratified from existing code" or "new,
greenfield" the same way Design Paradigm is below. Cut a row for a layer
nothing in scope needs.>

| Layer | Submodule(s) | Choice | Version |
| --- | --- | --- | --- |
| Frontend | | | |
| Backend | | | |
| Persistence | | | |

## Design Paradigm
<named pattern, mapped to submodules/directories — noted as "ratified
from existing code" or "new, greenfield" per submodule>

## Inherited Invariants
<epic and feature scope only, and only when a parent spine exists. The
parents' ADs/conventions/paradigm that actually bind here, by their
ORIGINAL ids — read-only, never renumbered, not re-derived. "From" names
the spine that defines the id.>

| Inherited | From | Binds here |
| --- | --- | --- |
| {AD-id / convention} | artifacts/architecture.md | {what it constrains in this scope} |

## Submodule Ownership
<at feature scope, only the submodules this feature touches, and what it
adds or changes in each>

| Submodule (`<submodule_root>/<repo-name>`) | Owns | Integrates via |
| --- | --- | --- |

## Criteria Coverage
<feature scope only. One row per Success Criterion and Acceptance
Criterion in the feature's prd.md, quoted or closely paraphrased, in PRD
order, then one row per live NFR, cited by its full ID
(`NFR-<feature-slug>.<name>: <outcome>`). "Served by" names an AD in this spine, an inherited id, or an
existing component/endpoint/table (with its path). A criterion with no
architectural impact still gets a row ("no change — UI copy only"). A
row marked GAP is an open question for the user, never left silently.>

| Criterion | Served by | Submodule(s) | New / extends |
| --- | --- | --- | --- |

## Open Requirement Conflicts
<feature scope only, and only when the user continued past unresolved
conflicts from `/vc:requirements conflicts <feature>`. Cut otherwise.
No decision above may rely on either side until it's settled.>

| Requirement | Conflicts with | Kind | Why |
| --- | --- | --- | --- |

## Decisions
<this scope's own new decisions only — never the parent's; those live in
Inherited Invariants above. Numbering is local to this spine, starting
at AD-1, even when a parent spine's own numbering is already past AD-1.>

### AD-1 — <decision>
- **Binds:** <scope, or `all`>
- **Prevents:** <the divergence this stops>
- **Rule:** <the enforceable constraint>
- **Supersedes:** <AD-n, if this decision replaces an earlier one — omit
  this field otherwise>

### AD-2 — <a decision later retired by AD-5>
- **Binds:** <scope, or `all`>
- **Prevents:** <the divergence this stopped>
- **Rule:** <the constraint that applied while this was current>
- **Status:** Superseded by AD-5, <date> — <the reason it changed,
  citing the PRD's Decisions entry, Changes to delivered features, or
  older Revision History when that's what triggered it>. Omit
  this field entirely for a still-current decision — its absence *is*
  "current."

## Technical Prerequisites
<non-demoable groundwork that must exist before anything in scope can be
demoed, and why it can't be reframed as user-facing. Each one becomes a
`/vc:create-pbi` enabler or a task, never a story.>

## Proposed Parent Spine Changes
<epic and feature scope only. Changes to a parent spine this scope's PRD
genuinely needs, confirmed with the user but not yet applied — this
skill never writes a parent spine from below. The parent scope's next
run applies or rejects each one and updates its Status. Kind is `add`,
`amend AD-n`, or `supersede AD-n`.>

| # | Kind | Target spine | Proposed change | Unblocks | Status |
| --- | --- | --- | --- | --- | --- |
| P-1 | {kind} | artifacts/architecture.md | {Binds / Prevents / Rule} | {criterion} | open |

## Technical Debt
<only debt the user knowingly accepted, each also logged as ACCEPTED
DEBT TD-n in .decisions.md. Cut this section when none was accepted —
an empty section is the expected outcome.>

| Id | Debt | Why accepted | Payoff trigger |
| --- | --- | --- | --- |

## Conventions
| Concern | Convention |
| --- | --- |

## Deferred
- <thing intentionally left to a lower altitude's judgment, and why>
```

## `AD-n` id rules

`AD-n` ids are stable forever within their own spine — tasks, PBIs, and
later epic spines cite them. An Update run touches an existing one in
exactly two ways; don't blur them together:

- **Amend in place**: only for a correction that doesn't change the
  actual decision (a typo, a clarified wording of the same Rule).
- **Supersede**: for an actual change of decision. Never edit the old
  `AD-n`'s Rule to say the new thing — add the next `AD-n` with
  `Supersedes: AD-<old>`, and add `Status: Superseded by AD-<new>,
  <date> — <reason>` to the old one. The old block's Rule text stays
  exactly as it was when it was current; that's the historical record.

Never renumber or reuse a retired id either way. A parent's ids never
change just because a child inherits them.
