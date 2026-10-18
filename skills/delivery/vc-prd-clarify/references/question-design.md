# Question Design and Answer Classification

Loaded by `vc-prd-clarify` step 4. How to build questions that prove the
user read and understood a PRD section, and how to classify each answer.

## Question types

Mix these per section; don't run the same type twice in a row when the
section supports another.

| Type | Shape | Example |
|---|---|---|
| Recall in own words | "In your own words, what happens when ...?" | "What does the system do when a refund request comes in?" |
| Scenario / edge case | A concrete situation, user predicts the PRD's outcome | "A customer on an expired plan tries to export a report. What should happen?" |
| Numbers / limits | Ask for a value the PRD states (or should) | "How long does a reset link stay valid?" |
| Scope boundary | Is a specific thing in or out? | "Is bulk import part of this feature?" |
| Actor / permission | Who can do it, who can't | "Which roles can approve a refund?" |
| Cross-section | How two sections interact | "How does the approval rule in §3 apply to the bulk flow in §5?" |
| Done / acceptance | How we'd know it works | "What would you check to call this feature done?" |
| Business rule (`BR-`) | A case at or just past the rule's limit | "The same card fails for the third time in ten minutes. What happens on the fourth try?" |
| Non-functional (`NFR-`) | The outcome and the condition it holds under | "How long may a customer wait for the payment result, and at what load does that apply?" |
| Error case (`ERR-`) | The failure, what the user sees, and which flow it belongs to | "The bank declines the card. What does the customer see, and what can they do next?" |

When the PRD has a `## Requirements` section, every covered section of it
gets at least one question of the matching type, and the reveal names the
full requirement ID (`📄 BR-checkout.max-retry-per-card: "..."`). A
`TBD` value or a `[NEEDS CLARIFICATION]` marker is never ✅: the PRD is
silent there, so the answer is ❓ or 💭.

## Rules for good questions

- **Free text only.** Never offer multiple choice for comprehension
  questions — the options leak the answer. `AskUserQuestion` is for
  meta choices only (role, sections, depth, save options).
- **No yes/no questions**, and no question whose wording contains its
  own answer ("Refunds need manager approval, right?").
- **Answerable from the section the user just read** — except
  cross-section questions, which name both sections.
- **Probe likely gaps on purpose.** Some scenario questions should target
  an edge case you suspect the PRD doesn't cover (from step 2's silent
  analysis) — the user's answer reveals whether *they* noticed, and the
  reveal turns it into a ❓ item if the PRD is silent.
- **One concept per question.** Split compound questions.
- Never paste the section before the answer. After the answer, quote only
  the short excerpt needed to compare.

## Role lens

The role from step 1 sets the emphasis, not an exclusive filter — every
role still gets core recall questions on each section.

| Role | Lean toward |
|---|---|
| TA | Integrations and dependencies, data flow and ownership, NFRs (performance, security, scale, retention), constraints, touchpoints with existing modules |
| SM | Scope boundaries, dependencies on other teams/features, Definition of Done, sequencing and releasability, what's explicitly out of scope |
| DEV | Business rules (`BR-`), flows and state changes, validation, error cases (`ERR-`) and their wording, edge cases, data shapes |
| QA | Acceptance criteria and how to verify them, `BR-` boundary values, every `ERR-` as a negative path, NFRs that can't be measured, permissions, untestable criteria |

## Answer classification

Compare the user's answer to the PRD text, then assign exactly one result.

| Result | When | Goes to PO/BA? |
|---|---|---|
| ✅ Aligned | Answer matches what the PRD clearly states | No |
| ❌ Misread | PRD is clear, answer contradicts or misses it | No — add to Re-read |
| ❓ PRD silent | PRD doesn't address it at all | Yes |
| ⚠️ PRD ambiguous | PRD text supports more than one reasonable reading (including the user's) | Yes |
| ⛔ PRD contradicts itself | Two places in the PRD disagree | Yes |
| 💭 User assumption | User states something plausible the PRD never says — the PRD is silent and the user filled it in | Yes, as "confirm this assumption" |
| ⏭️ Not verified | User skipped | No — add to Re-read |

Tie-breakers:
- Partly right → ✅ for the part that matches, but if a key detail is
  wrong, it's ❌; mention the correct detail in the reveal.
- The PRD is silent and the user just says "I don't know" → ❓, not ⏭️.
- The PRD is silent and the user confidently fills it in → 💭, so the
  assumption gets confirmed rather than silently built.
- The user's reading is wrong but *defensible* from the wording → ⚠️, not
  ❌ — the PRD needs fixing, not the reader.

## Reveal format (after every answer)

```
📄 PRD §<n> <section>: "<short verbatim excerpt>"   (or: the PRD doesn't say)
<result emoji> <Result> — <one sentence on why>
```

Keep it short and neutral. A ❌ is stated plainly, without judgement.

## Anti-patterns

- Summarising the section "to get started" — defeats the purpose.
- Asking questions answered in the map from step 3.
- Accepting "probably X" as ✅ without a follow-up.
- Logging ⏭️ items as ✅ to keep the tally clean.
- Turning a ❌ Misread into a PO question — the PRD was clear.
