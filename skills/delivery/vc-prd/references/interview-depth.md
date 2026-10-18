# Interview depth and question rules

Load this before the feature-level interview (step 5), and in Revision
Mode, Review Mode and `migrate` when they interview. It sets how deep the
interview goes and the rules every question round follows.

## Choosing the depth

Score two things.

**Size**, from what the description, scout findings and stub say:

| Size | Signals |
|---|---|
| small | one role, one main flow, no other system involved, nothing with a status |
| medium | two roles or a few flows, or one other system, or one entity with a status |
| complex | money or payment, an external redirect or webhook, personal or regulated data, roles with different permissions, an entity lifecycle with several statuses, data migrated from an old flow, or changes across several existing modules |

Any one complex signal makes the feature complex.

**How much is already known**: *much* when the description, scout
findings or stub already answer purpose, users and the main flow; *little*
when it's a one-line idea.

| | much known | little known |
|---|---|---|
| small | Quick | Targeted |
| medium | Targeted | Deep |
| complex | Deep | Deep |

Propose the result in one line the user can override, then start:

> This looks medium (two roles, one external system) and your
> description covers purpose and users, so I'll run a Targeted
> interview. Say "quick" or "deep" to change it.

`--deep` forces Deep and skips the proposal line. If the interview turns
up a signal that raises the size (a payment step nobody mentioned), say
so in one line and move up a level. Never move down without the user
asking.

## What each depth does

| | Quick | Targeted | Deep |
|---|---|---|---|
| Topics | all, batched into as few rounds as possible | all, follow-ups only on gaps | all, plus the extra questions below |
| Playback | skipped | yes | yes |
| Conditional tables | when triggered | when triggered | when triggered, and every trigger is probed |
| Conflict scouting | yes | yes | yes |
| Self-check | yes | yes | yes, pre-mortem and inversion asked aloud |
| Fresh-reader check | skipped | yes | yes |
| Assumed defaults in preview | yes | yes | yes |

**Deep adds:**

- Problem validation: "What isn't working today that this solves, and
  what happens if we don't build it?" Record the answer, plus each
  assumption raised and its risk if wrong, as `## Problem Validation`.
  Also triggered at any depth when the description names a technical
  mechanism instead of a user outcome (a sign the solution was picked
  before the problem was stated).
- Every NFR category walked once: response time, availability,
  retention, access, volume. Skip any the user rules out.
- The pre-mortem and inversion questions from the self-check asked to
  the user directly, not only answered by the skill.

## "Already have / still missing" line

Before every question round, print one line:

> Already have: purpose, users, main flow, success metric · Still
> missing: errors on payment, anti-goals, retention

Build it from the topic list in SKILL.md step 5 plus whatever the
feature triggered (errors, tables, NFRs). Never ask again about a point
listed under "Already have". When a new answer seems to contradict an
earlier one, ask about the contradiction itself, quoting both; that is
not a re-ask.

## Vague-answer limit

A vague, hedged or partial answer ("some users I guess", "fast enough",
"the usual checks") gets one follow-up aimed at the unclear part only:
offer concrete options or ask for the number. If the second answer is
still vague, stop asking. Write the point as `TBD — <owner> — <date>`
(ask who owns the answer and by when, in the same message, or take the
PO and the end of the next sprint as defaults and list them under
Assumed defaults) or as an inline `[NEEDS CLARIFICATION: <question>]`
marker, and move on. Never a third ask on the same point.

## Exact values

When an answer has a quantity or a message in it, push once for the
exact value:

- "fast" → how many seconds, measured where, at what load?
- "a few retries" → how many, over what time?
- "recent orders" → from how far back?
- "show an error" → what exactly does the message say? (or `TBD`)
- "admins" → which role, by its name in the product?

Write the value the user gives. If they don't know, it's `TBD — <owner>
— <date>`, never a number the skill made up. A number the skill proposes
and the user doesn't confirm is an assumed default.

## Playback

Skipped in Quick. Once a part is understood, describe it back in a short
paragraph before moving to the next part, and end with "What's wrong or
missing?". The parts, in order:

1. purpose and users,
2. scope (in, out, anti-goals),
3. each core flow, one at a time, including its failures.

Anything in the playback the user didn't actually say is marked
`(assumed)`. An assumption the user lets stand goes into the write
preview's Assumed defaults, not straight into the PRD as agreed.

## Anti-goals

Ask at every depth (in Quick, fold it into the scope round): "What would
make this a failure even if it works exactly as specified?" Prompt with
an example when the user is stuck: "checkout gets faster, but
declined-card support tickets double". Answers go under `### Anti-goals`
in `## Scope`, and the self-check's pre-mortem starts from them.

## Conflict scouting while drafting

At every depth, as each requirement takes shape, look for existing
requirements that share its signals: a glossary term (aliases count), the
same entity or status, the same touchpoint, the same NFR category
(response time, availability, retention, access), or the same ID name.
Look in `artifacts/requirements-current.md` when it exists, and open the
owning PRDs for the full text.

When one disagrees (a contradiction, an NFR clash, a rule clash, or a
duplicate), make it the next interview question while the PO still has
the context. Quote both texts, then give the options with a
recommendation:

- change the new requirement to fit;
- narrow both to the conditions where each applies;
- the other one is delivered: supersede it (`supersession.md`);
- the other one is a draft: change or retire it instead (its PRD is
  revised in the same run, with a Decisions entry in both);
- a duplicate: cite the existing ID and drop the new one;
- not a conflict: record `not a conflict: <id> vs <id>` in Decisions.

The PO decides; the skill never picks. Plain overlap (two features touch
the same screen without disagreeing) is not raised.
