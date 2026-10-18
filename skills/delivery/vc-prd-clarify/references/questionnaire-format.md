# Gap Log and PO/BA Questionnaire Formats

Loaded by `vc-prd-clarify` steps 6-7. The same markdown is printed in
the console and, if the user opts in, written to disk.

## Gap log (step 6)

Saved as `<prd-folder>/clarifications.md` only when the user says yes.

```markdown
---
prd: <relative path to prd.md>
feature_id: FEATURE-<slug>
reviewer_role: <TA | SM | DEV | QA>
date: <YYYY-MM-DD>
status: <complete | partial>
sections_covered: [<section names>]
---

# PRD Clarifications: <Feature title>

## Scorecard

| Section | ✅ | ❌ | ❓ | ⚠️ | ⛔ | 💭 | ⏭️ |
|---|---|---|---|---|---|---|---|
| §<n> <name> | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Gap Log

### §<n> <section name>

- **CLR-001** ❓ PRD silent
  - Question asked: ...
  - Reader's understanding: ...
  - PRD says: "<excerpt>" (or: nothing)
  - Source: interview | review finding

## Re-read

- §<n> <section> — CLR-<nnn>: <what to look at again>
```

`status: partial` when the user paused before covering every selected
section; list only the sections actually covered.

## PO/BA questionnaire (step 7)

Built from ❓, ⚠️, ⛔, and 💭 items only.

### Priority

| Priority | Meaning |
|---|---|
| 🔴 Blocking | Can't design, build, plan, or test the affected part without the answer |
| 🟡 Important | Work can start on a stated assumption, but rework is likely if it's wrong |
| ⚪ Nice-to-have | Polish or wording; a sensible default is low-risk |

⛔ contradictions are 🔴 by default unless clearly cosmetic.

### Writing each question

- **Standalone.** The PO/BA reads it without the interview — include the
  PRD context (section + short quote), never "as discussed".
- **One decision per question.**
- **Offer options** (A / B / other) when the answer space is small.
- **State a default assumption** — what the team will do if no answer
  comes back — so silence still leads somewhere explicit.
- **Neutral tone.** It's a clarification request, not a critique of the
  PRD. Never mention the reader's score or ❌ items.

### Markdown template

Saved as `<prd-folder>/clarification-questions.md` when chosen.

```markdown
# Clarification Questions: <Feature title>

PRD: <relative path or title> · From: <reviewer role> · Date: <YYYY-MM-DD>

<N> questions — 🔴 <n> blocking · 🟡 <n> important · ⚪ <n> nice-to-have

## §<n> <section name>

### Q1 🔴 <short title> (CLR-<nnn>)

**Requirement:** <full IDs, e.g. ERR-checkout.card-declined, or "none">

**Context:** §<n> says "<excerpt>". (or: §<n> doesn't cover <topic>.)

**Question:** <one precise question>

**Options:**
- A) ...
- B) ...

**Default assumption if unanswered:** ...
```

Order sections as in the PRD; within a section, 🔴 before 🟡 before ⚪.

The questionnaire ends with the lines the PO/BA can add to the PRD's
`## Open Questions` list (through `/vc:prd`, never by this skill). No
IDs of their own; requirement IDs always in full:

```markdown
## Proposed Open Questions

- What does the customer see when the card is declined? (ERR-checkout.card-declined, wording TBD)
- Does the 3-try limit count per card or per customer? (BR-checkout.max-retry-per-card)
```

### HTML template (email-ready)

Saved as `<prd-folder>/clarification-questions.html` when chosen. Same
content and order as the markdown. Constraints so it survives pasting
into Outlook/Gmail:

- One self-contained file: inline `style=""` attributes only, no
  `<style>` block reliance, no external CSS, fonts, scripts, or images.
- Table-based layout, max width ~680px, system font stack
  (`Segoe UI, Arial, sans-serif`), dark text on white.
- Priority shown as a coloured pill with its text label (🔴 Blocking etc.),
  never colour alone.
- Header block: feature title, PRD reference, reviewer role, date, and
  the priority counts. A short neutral intro line, e.g. "While reviewing
  the PRD we found a few points we'd like to confirm before work starts."
- UTF-8 (`<meta charset="utf-8">`), no BOM.
