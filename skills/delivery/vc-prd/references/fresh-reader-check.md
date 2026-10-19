# Fresh-reader check

Load this after the self-check and before the write preview. Skipped at
Quick depth.

The interview leaves the skill knowing far more than the PRD says. This
check reads the draft the way the people who build it will: with only
the file, no interview, and nobody to ask.

## 1. Put the draft where a reader can find it

Write the full draft to `prd.draft.md` in the feature's folder, next to
where `prd.md` lives or will live (for a new feature,
`artifacts/<feature-slug>/prd.draft.md`). The same file serves the
conflict pass before the preview. It is deleted after the final write,
and when the PO abandons the run. If a `prd.draft.md` is already there at
the start of a run, ask whether to resume from it or discard it.

## 2. Read it fresh

**When the environment supports subagents**, spawn the
`vc-prd-fresh-reader` subagent (`vc:vc-prd-fresh-reader` when
installed through the plugin). Give it only:

- the path to `prd.draft.md`,
- the path to `artifacts/prd.md`, when it exists,
- the path to `docs/glossary.md`, when it exists.

Never pass interview notes, answers or a summary. The point is that it
doesn't have them.

**Otherwise**, run the same pass in this session as a separate step:
re-read `prd.draft.md` from disk (plus the product PRD and glossary),
and answer only from what those files say, not from what the interview
said. Follow the reader brief below.

## Reader brief

The same rules the subagent follows:

- Act as the developer who must build this feature and the tester who
  must verify it, with only these files and nobody to ask.
- Walk each flow, requirement, error and table, asking: what would I
  have to guess to build or test this? Look for missing triggers,
  undefined words, values with no number, failures with no handling,
  statuses with no way out, roles with no stated permissions, and
  acceptance criteria no requirement backs.
- Keep only questions where a wrong guess changes what gets built or
  what a test expects. Drop style, wording and anything a sensible
  builder would settle the same way every time.
- Rank them, most damaging wrong guess first. For each: the question,
  the ID or section it is about, and one line on what goes wrong if the
  guess is wrong.
- Nothing like that left → reply exactly "nothing important left".

The reader returns either that ranked list or "nothing important left".

## 3. Sort each question

| Bucket | Meaning | What to do |
|---|---|---|
| Already answered | the interview, the product PRD or the scout findings settle it, but the draft doesn't say so | write the answer into the draft |
| Minor | a sensible builder could settle it without changing what the feature is for | settle it with the most ordinary choice, write it in, and list it under Assumed defaults |
| PO only | a wrong guess changes what gets built, and nothing on file settles it | ask the PO |

Ask all PO-only questions in one message, most important first. Apply
the vague-answer limit to the answers. Anything still open becomes
`TBD — <owner> — <date>`, a marker, or an Open Question.

## 4. One round only

Don't send the revised draft back to the reader. Go on to the write
preview, which shows what this check changed.
