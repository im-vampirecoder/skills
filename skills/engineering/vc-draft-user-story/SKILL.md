---
name: vc-draft-user-story
description: Use when the user asks to write, draft, or refine a user story or requirement, e.g. "write a user story for this", "refine my following requirement", "turn this into a user story", "clarify these requirements", "write acceptance criteria", or pastes a rough feature idea and wants it spelled out before planning or implementing. Also runs as /draft-user-story.
---
# Draft User Story

Turns a rough feature request into a user story the user can approve or
revise before any planning or implementation starts. The write-up is the
deliverable. Do not plan, design, or code in this skill.

## When to use

- The user asks for a user story, refined requirements, or acceptance
  criteria, in any wording, with or without `/vc-draft-user-story`.
- The user asks to refine, clarify, or spec a feature idea before building.

Do not use when the user asks to implement, plan, or fix something directly
and has not asked for a write-up first.

## Process

1. **Capture the input.** Use the skill argument if given, otherwise the
   requirement the user supplied in their message (inline, pasted, or
   referenced in the preceding message). If no requirement can be found, ask
   the user for it and stop.
2. **Ground it lightly.** If the request names existing UI, screens, or
   behavior, glance at the codebase (Glob/Grep/Read) so the Background and
   requirements use the product's real names. Skip this when the request is
   self-contained. Never invent behavior the request or the code doesn't
   support.
3. **Check the size.** Before drafting, test the request against the split
   signals below. If any signal holds, do not draft yet: follow "When the
   request is too big". Otherwise continue.
4. **Write the story** using the template below, in this order. Use the
   user's own vocabulary for UI elements and states.
5. **Surface gaps as assumptions.** Anything the request doesn't state but the
   story depends on (persistence, confirmation on the reverse action, other
   code paths, accessibility) goes under "Assumptions to Confirm", phrased as
   what the story currently assumes. Do not silently decide it in the
   requirements and do not interrupt with questions before drafting.
6. **Confirm.** After the write-up, ask the user whether they agree or want
   changes before moving on to planning or implementing. Offer three
   choices: approve as-is, edit (they say what to change), or resolve the
   listed assumptions. Use `AskUserQuestion` when available.
7. **Iterate.** On edits, revise the story and ask again. Stop only when the
   user approves. Then tell them the next step is planning or implementing,
   and do not start it unless they ask.

## When the request is too big

Split signals (any one is enough):

- The request touches more than one distinct area: separate screens,
  features, user roles, or data domains.
- Some acceptance criteria you would write share no state or flow with the
  others, so they could not be verified together.
- The request has more than one independent "so that" benefit.
- You expect more than about 8 acceptance criteria.

When a signal holds:

1. Tell the user the request looks too big for a single story and name which
   signal(s) fired.
2. Propose a split: state the number of stories and give each a title plus
   one line of scope. Each proposed story must be independently deliverable
   and verifiable, and together they must cover the whole request.
3. Ask whether to split as proposed, adjust the split, or keep it as one
   story. Use `AskUserQuestion` when available.
4. Draft only the stories the user approved, each with the template below,
   and present them together. Cross-story dependencies go under
   "Assumptions to Confirm". Then confirm as in step 6.

## Template

```markdown
# User Story: <Short Title>

## Story

**As a** <role>,
**I want** <capability>,
**so that** <benefit>.

## Background

<2-3 sentences: current behavior and the problem this solves.>

## Requirements

### <State or flow name>

- <Observable behavior, one per bullet. Numbered when order matters.>

## Acceptance Criteria

1. **Given** <state>
   **When** <action>
   **Then** <observable result>

---

2. **Given** <state>
   **When** <action>
   **Then** <observable result>

## Assumptions to Confirm

- **<Topic>:** <what this story assumes and why it needs a decision.>

## Out of Scope

- <Adjacent thing this story deliberately excludes.>
```

## Rules for the content

- Group requirements by state or flow (default state, each action, resulting
  state, reversal), not by implementation layer.
- Every requirement must be observable by a user. No component names, APIs,
  or storage details.
- Write acceptance criteria as a numbered list, not a table, with a `---`
  line (blank line above and below) between items.
- Every acceptance criterion maps to a requirement, and every requirement is
  covered by at least one criterion. Include the cancel/negative path when
  the flow has a confirmation step.
- List an assumption only if a different answer would change the
  requirements. Keep it to 4 or fewer, each written as a statement, not a
  question.
- Every acceptance criterion must test something no other criterion already
  covers.
- Keep Out of Scope to real neighbors of the request, not a generic list.

## Example

See the input/output pair in the repo's `.tmp/new-skill.md` for the target
level of detail (a title-locking feature).
