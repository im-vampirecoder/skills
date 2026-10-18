# Sprint Goal Guide

How `vc-plan-sprint-candidates` drafts sprint goal options. The skill
proposes; the PO chooses or rewrites; the whole team agrees the goal in
planning. The skill never presents a goal as decided.

## What a sprint goal is

One sentence that says why this sprint is worth doing: the outcome a user
or stakeholder gets when it is reached. The stories are how the team
plans to get there; the goal is what stays fixed when the plan changes.

A good goal:

- names who benefits and what they can do or know afterwards;
- can be reached in more than one way, so a slipped story does not sink
  it;
- can be checked at the sprint review with a yes or no;
- links to the bigger picture: the feature or epic it advances, and the
  product goals in `artifacts/prd.md` when that file states any.

## Shapes to reject

| Shape | Example | Why it fails |
|---|---|---|
| A list of stories | "Do stories 3, 4 and 7" | No reason to prefer one story over another when time runs short |
| A technical layer | "Finish the notes API" | Says what is built, not what anyone gets |
| Everything | "Make progress on voice notes and sharing and offline" | Not one objective; nothing to protect |
| Unmeasurable | "Improve the recording experience" | No yes/no at the review |
| A copy of the feature title | "Create notes by voice" | Usually bigger than one sprint, so it is never reached |

When the PO writes a goal in one of these shapes, say which one, once, and
offer a rewrite. The PO has the final word.

## Drafting the options

Offer two or three options, each from a different angle, built from the
script's data:

1. **Finish a feature**: a feature whose remaining ready stories fit the
   sprint (`features` roll-up). "Users can <feature outcome> end to end."
2. **Advance the top of the backlog**: the highest-ordered ready stories
   share a feature or user. "<User> can <first slice of value>, so we can
   learn <what> before building the rest."
3. **Recover**: when kept carryover is large, a goal about landing it.
   "Users get <carryover outcome> that slipped last sprint, without
   leaving it half done again."

Use the story's "So that" lines for the benefit wording, not the titles.
Each option gets a one-line note on which stories it would focus the
sprint on.

Format:

```
By the end of this sprint, <who> can <do or know what>, <so that / which means> <why it matters>.
```

The format is a help, not a rule: a goal the PO words differently is fine
if it passes the checks above.

## Examples

| Weak | Better |
|---|---|
| Implement voice recording and transcription | Mobile users can turn a spoken thought into a saved note without typing |
| Stories STORY-share-1 to STORY-share-4 | A user can share a note with a teammate, who sees it in their own list |
| Offline support | Users who lose signal mid-recording keep what they said and get the note once they are back online |
