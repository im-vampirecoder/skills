# Reviewing existing stories and splitting one

Load this in step 2 when the feature folder already has `stories-*.md`
files, and again in step 9 when the user approved a split.

## Which stories are reviewed

Every `stories-<n>-*.md` in the feature folder except `status: removed`
ones. A missing `status` counts as `new`.

## Checks per story

Run the same checks a new candidate gets, against the story as written:

| Check | Fails when |
|---|---|
| INVEST | the story is not Independent, Negotiable, Valuable, Estimable, Small or Testable |
| Demoable-AC (step 5) | it can't be demoed on its own to a stakeholder |
| "So that" test (step 5) | the benefit clause names a technical concern |
| Vertical slice (step 5) | it only becomes demoable together with a sibling |
| Too big | more than ~7 acceptance criteria, more than one workflow step or business-rule variation that could stand alone, or clearly more than 1-3 days of work |
| Overlaps a sibling | it implements the same FR as another story for the same flow, data variation or path (happy vs. edge), so building both would build the same thing twice |
| Cites dead IDs | an `Implements:` ID is retired or superseded |

Then the feature-level check: list every live P0 `FR-` that no reviewed
story implements.

## Which stories may be split

Only a story with `status: new` **and** `ado_id: null`. Every other
story is **locked**: report its findings, but never offer to split or
rewrite it, and say why:

- `ready`, `in-progress`, `done`: the team has already accepted it for
  task breakdown or is building it.
- a non-null `ado_id`: it is on the tracker board, and rewriting it
  would rewrite the work item.

For a locked story that is too big, the way forward is a new story for
the missing part (add mode), not a split.

## Reporting

Print one table, nothing written:

| Story | Status | Findings | Can split? |
|---|---|---|---|
| `STORY-<feature-slug>-<n>` <title> | new | too big: two flows (pay by card, pay by voucher) | yes |
| `STORY-<feature-slug>-<m>` <title> | ready | overlaps n on FR-<feature-slug>.<name> | no (ready) |

Follow it with the uncovered P0 FRs, one line each. No findings at all →
one line saying the existing stories pass, then move on.

## Applying an approved split (step 9)

- **Rewrite the original file in place** with the first part of the
  split: same file path, same `<n>`, same `id`, `feature_id`,
  `ado_id: null`, `last_synced: null`, `status: new`, `iteration: null`.
  Title, the As a / I want / So that lines, the acceptance criteria and
  the Details bullets change to describe only that part. If the title's
  short description no longer fits, keep the file name anyway: other
  files point at it by path.
- **Every other part is a new story** numbered after the highest `<n>`
  in the folder, written like any other new story.
- Never edit a sibling story to follow the split. When a sibling's
  `Dependencies:` names the original story and the part it depends on
  moved to a new number, list that sibling in step 11's summary so the
  user can fix the line.
