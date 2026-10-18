# Preview, review and sign-off

Loaded by SKILL.md steps 4-6.

## Plain-text preview (step 4)

Show the map without Mermaid first, so the user reacts to the flow, not
the syntax:

```text
Flow: pay   (happy, error, edge)
  [1] Cart --taps Checkout--> [2] Payment --taps Pay--> Card accepted?
      Yes ............................ [3] Order confirmed (end)
      No, tries left ................. [4] Card declined  ERR-checkout.card-declined
                                        --Try another card--> [2]
      No, limit reached .............. [5] Locked: try later  ERR-checkout.too-many-tries
                                        --Back to cart--> [1]

Screens: 5 (5 new, 0 changed) · Devices: mobile, desktop
Covered: FR-checkout.review-cart, FR-checkout.pay-with-card, ERR-checkout.card-declined, ...
Not on the map yet: none
Open questions: 1
```

Ask: does this match how users move through the feature? Apply the
answer and show the preview again. At most 3 rounds; after the third,
list what's still disputed as open questions and continue.

## Independent review (step 5)

Run the review on the agreed preview's full map (all five sections as
they would be written). Use the read-only `vc-flow-reviewer` subagent
when the environment supports subagents; give it the map, the PRD path
and the paths below. Otherwise, run the same review yourself as a
separate pass: re-read the PRD and the map from the top as someone who
didn't draw it, and work through each lens in order before changing
anything.

Inputs: the draft map, the feature PRD, `artifacts/prd.md`,
`docs/glossary.md`, `clarifications.md` / `clarification-questions.md`
when present.

### Lenses

| Lens | Look for |
|---|---|
| Case coverage | a decision with only the happy exit; a PRD error, limit, timeout or interruption with no branch |
| Flow integrity | dead ends, loops with no exit, orphan branches, a temporary state with no way out, back paths missing where a user would expect one |
| Screen inventory | a step that needs its own screen but has none (confirmation, empty state, permission denied), or two nodes that are really one screen |
| Grouping | flows split where users don't see a break, or one flow mixing unrelated goals |
| Requirement coverage | a P0 FR not on any screen or transition; a user-facing `ERR-` with no branch; a cited ID that is retired, superseded or from another feature |
| Consistency with the PRD | behaviour, order or rules the PRD and clarifications don't support; anything out of scope or listed as an anti-goal |
| Words | screen names or labels not using the glossary term, or using a word under Avoid |
| UX anti-patterns | messages that reveal whether an account exists, destructive actions with no confirm or undo, no way back from a step, a user stuck waiting with no feedback |

### Findings

Each finding: severity, lens, where (node or table row), what's wrong,
and the smallest fix.

- **BLOCKING**: the map would send a user somewhere wrong or nowhere, or
  misses a P0 FR or user-facing `ERR-`.
- **WARNING**: likely wrong or confusing; fix unless the PO disagrees.
- **SUGGESTION**: optional.

Also a **missing screens and branches** checklist: each item the map
should add, with the PRD line or ID that calls for it.

### Applying review

- Apply every BLOCKING finding and every missing screen or branch the
  PRD supports.
- A finding that needs a business value or rule the PRD doesn't give
  (how long a lock lasts, who may cancel) becomes an open question with
  the assumption used, plus a PRD gap (step 9). Never decide it.
- WARNING and SUGGESTION: apply the ones that are clearly right; list the
  rest for the user at sign-off.
- At most 2 review rounds. Run the second only when the first changed
  the structure (nodes or edges); after it, list anything still open.

## Sign-off (step 6)

A hard stop. Show:

1. the final plain-text preview,
2. what review changed (added, removed, renamed, each with its reason),
3. findings not applied and why,
4. open questions and PRD gaps.

Ask for an explicit yes to write. Anything else (a change, "maybe",
silence) is not a yes: apply changes and show the sign-off again, or stop
with nothing written.
