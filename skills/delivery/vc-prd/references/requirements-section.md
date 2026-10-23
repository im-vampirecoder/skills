# Feature PRD template and the Requirements section

Load this when writing or revising a feature PRD (step 8, Revision Mode,
Review Mode, `migrate`). It holds the full feature PRD layout, the ID
rules, the wording rules, the error catalogue, the ambiguity markers and
the conditional tables. `/vc:requirements check` enforces these rules;
the line formats below are exactly what its parser reads, so don't vary
them.

## Feature PRD template

```markdown
---
id: FEATURE-<feature-slug>
epic_id: null
ado_id: null
last_synced: null
status: draft
done_on: null
---

# Feature PRD: <Title>

## Overview
...

## Problem / Motivation
...

## Target Users
...

## Success Criteria
- ...

## Acceptance Criteria
- Given ..., when ..., then ...

## Scope

### In Scope
- ...

### Out of Scope
- ...

### Anti-goals
- <what would make this a failure even if it works as specified>

## Constraints
- ...

## Touchpoints
- ...

## Requirements

### Functional
- **FR-<feature-slug>.<name>** (P0): When <trigger>, the system shall <result>.

### Non-functional
- **NFR-<feature-slug>.<name>:** <measurable business outcome>.

### Business rules
- **BR-<feature-slug>.<name>:** <rule>. Applies to FR-<feature-slug>.<name>.

### Errors
| ID | If | The user sees | For |
|---|---|---|---|
| ERR-<feature-slug>.<name> | <condition> | "<exact text>" | FR-<feature-slug>.<name> |

## Problem Validation

## Open Questions
- ...

## Changes to delivered features

## Decisions
- [<date>] <decision> — options: <A / B> — why: <reason> — by: <role>
```

Section rules:

- **Frontmatter.** `epic_id`, `ado_id`, `last_synced` start `null` and are
  never written by this skill afterwards (`vc-propose-epic` and
  `vc-sync-to-tracker` own them). `status` moves
  `draft → ready → active → done` (who sets each: "Feature states" in
  `supersession.md`); `done_on` is set only by the `done` mode.
  `supersedes: [...]` is added only when this feature replaces
  requirements of `done` features, and `superseded: [...]` is written
  only by `apply_supersessions.py`. Both are single-line lists and are
  omitted when empty. See `supersession.md`.
- **Acceptance Criteria** is the feature's own Definition of Done,
  coarser than any story's criteria. It has no IDs: test cases cite the
  FR, BR or ERR they verify.
- **Anti-goals** sits under Scope next to In and Out of Scope. Omit the
  heading only when the PO said there are none.
- **Touchpoints**: omit when none were identified.
- **Requirements** subsections with nothing in them are omitted, except
  Functional, which every feature has. State transitions, Interrupted
  flows and Scenarios go at the end of `## Requirements`, only when
  triggered (see below).
- **Problem Validation**: Deep depth only (see `interview-depth.md`).
- **Open Questions**: a plain list, no IDs. Remove an entry once it is
  answered and the answer is written into the PRD.
- **Changes to delivered features**: only with `supersedes`.
- **Decisions**: only once the PO has picked between paths. Newest first.
- An older PRD keeps its `## Revision History` exactly as it is. Never
  append to it and never create one.

## Requirement IDs

Format: `<TYPE>-<feature-slug>.<name>`, for example
`FR-checkout.pay-with-stripe`.

| Type | Use for |
|---|---|
| `FR` | something the system does for a user or another system |
| `NFR` | a quality the business can measure: speed, availability, retention, access, volume |
| `BR` | a business rule that limits or decides behaviour |
| `ERR` | a failure the user can hit, and what they see |

- `<feature-slug>` is the feature's own slug (the folder name, minus
  `feature-` once the feature sits under an epic). The dot separates it
  from the name, because slugs contain hyphens.
- `<name>` is kebab-case, at most 40 characters, built from glossary
  words (`docs/glossary.md`), and says what the requirement is about.
  Never a number or position (`fr-1`, `step-two`).
- **Unique within the feature, never reused**, including retired IDs.
- **Only the feature's own PRD defines its IDs.** Another feature that
  depends on one cites it.
- **Always cite in full**, even inside the defining PRD (never a short
  form like `FR.pay-with-stripe`), so one grep finds every citation.
- An imported numbered requirement keeps its old number as an alias
  next to the priority: `- **FR-pmc.solution-mapping** (P0, FR12): ...`.
  The alias is a label only; nothing new is ever given one.

### When an ID can change

| The ID is | Wording fix, same meaning | Change in meaning |
|---|---|---|
| Uncited, in a draft feature | edit freely; rename or delete freely | edit freely |
| Cited (story, test case, mockup, another PRD, tracker tag), not built | edit, keep the ID | new ID; retire the old one |
| Built (a `done` story implements it) or the feature is `done` | never edit the text; add a `> Clarified on` line instead | new ID (`done` feature: in a new superseding feature); retire or supersede the old one |

**Retiring** keeps the original text and adds a marker at the end of the
line: `Retired. Replaced by <new-id>.`, or just `Retired.` when nothing
replaces it. In an Errors row the marker goes at the end of the `If`
cell. A retired ID is never deleted and never reused.

```markdown
- **FR-checkout.pay-with-stripe** (P0): When the customer confirms the order, the system shall charge the card through Stripe. Retired. Replaced by FR-checkout.pay-with-saved-card.
```

## Line formats

Each requirement is exactly one line. Notes about it go on `>` lines
directly under it, and only these two kinds exist:

```markdown
> Superseded by <id or FEATURE-slug> on <date>
> Clarified on <date>: <detail> — <source>
```

The first is written only by `apply_supersessions.py`; the second only by
`clarify` (see `done-mode.md`). Any other text under a requirement
ends it, so never put sub-bullets or wrapped lines there.

| Type | Line |
|---|---|
| FR | `- **FR-<slug>.<name>** (P0): <text>` with P0, P1 or P2 |
| NFR | `- **NFR-<slug>.<name>:** <text>` |
| BR | `- **BR-<slug>.<name>:** <text>. Applies to FR-<slug>.<name>.` |
| ERR | a row of the Errors table: `\| ERR-<slug>.<name> \| <if> \| <the user sees> \| <FR id> \|` |

Priorities apply to FRs: **P0** the feature can't be released without
it, **P1** expected in this release but release can go ahead without it,
**P2** worth doing if there is room.

## Wording

- **Behaviour (FR):** "When <trigger>, the system shall <result>." State
  that holds all the time: "While <state>, the system shall <result>."
  Plain prose only when neither form fits.
- **Failure (FR or ERR):** "If <condition>, then the system shall
  <handling>." In the Errors table the `If` cell is just the condition.
- **One obligation per FR.** Two results joined by "and" are two FRs.
- **Testable.** A tester can say pass or fail without asking anyone. No
  "fast", "easy", "user-friendly", "appropriate", "etc.".
- **Glossary words.** Use the glossary's term, never a word listed under
  its "Avoid" column. A new domain word is proposed for the glossary (see
  SKILL.md).
- **NFRs are business outcomes**, measured where the business feels
  them: "The customer sees the payment result within 3 s at peak (500
  orders/hour)", "Card data is visible to the finance role only and kept
  for 7 years". Never an implementation choice ("use a cache", "store it
  in table X", "run on two servers"): if the user names one, ask what
  outcome it is for and write that.
- **BRs** name the FRs they apply to. A BR no FR uses is a warning in
  `check`.
- **Unknown values** are written as `TBD — <owner> — <date the answer is
  needed by>`, never as an invented number.

## Error catalogue

Every P0 FR that can fail has at least one `ERR-` row. Something can fail
when it depends on user input, another system (payment, email, identity,
an API), permissions, time (expiry, timeouts), or something that may
already exist (duplicates, concurrent edits).

- **If:** the condition, in the user's terms where possible.
- **The user sees:** the exact message in quotes, or what happens on
  screen ("returned to the cart with the card field cleared"), or
  `TBD — <owner> — <date>` when nobody has decided.
- **For:** the full ID of the FR it belongs to.

## Ambiguity markers

A small open detail inside an otherwise writable requirement goes inline:
`[NEEDS CLARIFICATION: <question>]`. At the write preview each marker is
either answered (the marker is removed and the answer written in) or kept
with a matching Open Questions entry that names the ID. A requirement
with an open marker blocks its stories from being `ready` in sprint
planning, so keep markers few and specific. A question too big for one
requirement goes to Open Questions only.

## Conditional tables

Add each table only when the interview detects its trigger. Rows cite
the IDs they illustrate; the tables never define new IDs.

**State transitions**: an entity has a status or lifecycle (order,
invoice, request, subscription). The first column is always `Entity`.

```markdown
### State transitions
| Entity | From | Event | To | Allowed for | Requirement |
|---|---|---|---|---|---|
| Order | pending | payment succeeds | paid | system | FR-checkout.pay-with-stripe |
```

Ask about every status pair the user didn't mention: can it go back, can
it be cancelled from here, what happens to a stuck one.

**Interrupted flows**: the flow leaves the product or waits on something
(external redirect, payment, webhook, email link, background job). Cover
at least: the browser is closed mid-way, the link or session expires, the
callback fails or arrives late, the user starts the same thing twice.

```markdown
### Interrupted flows
| Step | Interruption | What the system does | Requirement |
|---|---|---|---|
| Card payment | customer closes the browser before the bank answers | order stays pending; payment result applied when it arrives | FR-checkout.pay-with-stripe |
```

**Scenarios**: two or more roles, or inputs that change the outcome
(guest vs signed in, empty vs full cart, first vs repeat customer).

```markdown
### Scenarios
| Scenario | Role | Starting state | Expected outcome | Requirement |
|---|---|---|---|---|
| Guest pays | guest | cart with 1 item | order created, receipt by email | FR-checkout.guest-pay |
```

## Self-check before writing

Run on the draft before the fresh-reader check. Fix what you can; show
the rest in the write preview.

- **Gap:** every success criterion and acceptance criterion is backed by
  at least one FR; every P0 FR that can fail has an `ERR-`.
- **Clarity:** every FR and NFR is testable; one obligation per FR; no
  unquantified "fast", "secure", "simple".
- **Consistency:** no FR contradicts an Open Question or another FR;
  every BR is cited by an FR; glossary terms used, "Avoid" words not;
  every ID carries the feature's final slug.
- **Pre-mortem:** "It failed after release — why?" Start from the
  anti-goals, then the riskiest flow.
- **Inversion:** "How would a user break this?" Misuse, duplicates,
  abandoning half-way, the wrong role, two people at once.
