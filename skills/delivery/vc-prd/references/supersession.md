# Feature states, the built-requirement freeze, supersession and Decisions

Load this in Revision Mode, when a new feature replaces requirements of a
`done` feature, and when applying a conflict resolution.

## Feature states

| `status` | Who sets it | What can change |
|---|---|---|
| `needs-review` | `vc-docs features` | everything; completed through Review Mode |
| `draft` | this skill (new feature, Review Mode, and any revision of a `ready` feature) | edited in place, no change log, subject to the freeze below |
| `ready` | `vc-prd-clarify` (step 8), once the team has read it and nothing blocks it | same as draft, but any revision sets it back to `draft` (Revision Mode below); stories are written only for a `ready` or `active` feature |
| `active` | `vc-implement`, when the first story of a `ready` feature starts | same as draft (the freeze protects what is built); a revision keeps it `active` |
| `done` (legacy `delivered`, read as `done`) | `/vc:prd done` | nothing in the body except `> Superseded by` and `> Clarified on` lines; frontmatter only through `done` and `apply_supersessions.py` |

A legacy `status: synced` (written by sync before v1.11.1) means draft.
Rewrite it to `draft` the next time the PRD is written.

## Revision Mode by state

**Ready.** Revise it exactly like a draft, then set `status: draft`:
the team has to re-read what changed before more stories are written
from it. Before writing, list the stories (any status but `removed`)
whose `Implements:` cites an ID this revision changes, retires or
replaces, with their status, so the PO can re-check them. Stories keep
their own status; this skill never edits a story file. Name
`/vc:prd-clarify <feature-slug>` as the way back to `ready`.

**Active.** Revise it exactly like a draft and keep `status: active`:
stories are being built, and the built-requirement freeze below already
protects what is `done`. Before writing, list the stories that are not
`done` or `removed` whose `Implements:` cites an ID this revision
changes, retires or replaces, with their status, so the team can
re-check work in progress. This skill never edits a story file.

**Draft.** Edit the body in place so it describes what is true now.
There is no change log: what changed is in git, and why is in
`## Decisions` when the PO picked between paths. Every requirement
touched follows the "When an ID can change" table in
`requirements-section.md`, and built requirements follow the freeze
below.

**Done.** Refuse the edit and say why: the feature is frozen
because it describes what was shipped, and stories, test cases and the
tracker point at it. Then offer the route that fits:

- the requirement was unclear, not wrong, and the built system's
  behaviour doesn't change → `/vc:prd clarify <id>` (`done-mode.md`);
- anything else → a new feature that supersedes the affected IDs. Run
  the normal new-feature flow (SKILL.md step 4 onward) with the change as
  its description, `supersedes` filled in and a
  `## Changes to delivered features` entry per target (below).

**Needs review.** Go to Review Mode instead.

## Built-requirement freeze

An ID is frozen as soon as any story implementing it (`Implements:` in
a `stories-*.md` file) has `status: done`, even while the feature is
still `draft`. A frozen ID's text is never edited; `check` reports it as
`frozen-edited`.

A change to a frozen requirement:

1. Write the new behaviour as a **new requirement with a new ID** in the
   same feature.
2. Retire the old one: `Retired. Replaced by <new-id>.` at the end of its
   line (`requirements-section.md`).
3. Decide whether the new requirement **contradicts what is already
   built** (the built system would have to behave differently), rather
   than only adding to it. If it contradicts, search every `stories-*.md`
   under `artifacts/` for the old ID in `Implements:` and show:

   ```
   FR-checkout.pay-with-stripe is built and is being replaced by
   FR-checkout.pay-with-saved-card.

   Done stories that built the old behaviour (need rework):
   - STORY-checkout-1 Pay by card (done)

   Not-done stories that build on the old ID (hold these):
   - STORY-checkout-4 Retry a declined card (in-progress)
   - STORY-checkout-5 Card receipt email (new)

   Hold the not-done stories until the rework is planned, so nothing more
   gets built on behaviour that is about to change.
   ```

   This skill never edits story files; holding and replanning the stories
   is the team's call (`/vc:create-user-stories` for the rework
   stories). Stories that point at a retired ID show up as
   `retired-but-cited` in `check` until they are pointed at the
   replacement.

A small fix that leaves the built behaviour the same (clearer wording, a
missing detail) is a `> Clarified on` line, not a new ID.

## Superseding a `done` feature

The new feature's frontmatter lists every target, as a single-line list:

```yaml
supersedes: [FR-checkout.pay-with-stripe, ERR-checkout.card-declined]
```

To replace a whole `done` feature, use its feature ID:
`supersedes: [FEATURE-checkout]`.

The new PRD then gets a `## Changes to delivered features` section, one
bullet per target, in exactly one of these forms:

```markdown
## Changes to delivered features
- FR-checkout.pay-with-stripe: replaced by FR-paypal-checkout.pay-with-paypal — why: lower fees per order
- FR-checkout.guest-pay: changed, replaced by FR-paypal-checkout.guest-pay-with-paypal — guests now pay through PayPal only — why: one provider
- ERR-checkout.card-declined: removed — why: no card entry left in checkout
- FEATURE-checkout: replaced as a whole — why: checkout rebuilt on PayPal
```

`apply_supersessions.py` reads the `replaced by <id>` part of each bullet;
a target with no replacement is marked as superseded by the new feature
itself.

Only requirements of `done` features are superseded. A conflict with a draft
feature is settled by changing or retiring requirements in the drafts
(Decisions entry in both), and a change to a built requirement in a
draft feature follows the freeze above.

Supersession takes effect when the new feature is `done`. Until then
the old ID is still the current truth, and `requirements-current.md`
shows it as "being replaced by FEATURE-<new> (draft)". At `done`, the
`done` mode runs the script, which adds `> Superseded by <id> on <date>`
under each target and the target to the old PRD's `superseded: [...]`.
Never write those lines by hand.

## Decisions log

`## Decisions` is the last section of the feature PRD, newest entry on
top. Add an entry only when the PO or BA picks between paths: two ways to
build something, a conflict resolution, a scope trade-off. Never for
routine edits.

```markdown
## Decisions
- [2026-10-17] Saved cards replace one-off card entry — options: keep one-off entry / saved cards only / both — why: repeat customers abandon at card entry — by: PO
- [2026-10-12] not a conflict: FR-checkout.guest-pay vs BR-accounts.login-before-purchase — why: the login rule applies to the loyalty store only — by: PO
```

Format: `- [<date>] <decision> — options: <A / B> — why: <reason> — by:
<role>`. A dismissed conflict uses `not a conflict: <id> vs <id>` as the
decision, so it is never raised again. A draft-vs-draft resolution gets
the same entry in both PRDs. Whenever the interview reaches a choice
between paths, ask the PO for the why and the role in the same message
as the choice, then write the entry. Never edit or delete an older entry;
a reversed decision is a new entry on top.

## Product PRD history

Edits to `artifacts/prd.md`'s Overview, Problem Statement, Target Users
or Product Goals are logged in `artifacts/prd-history.md`, never inside
`prd.md`. Create it on the first logged change:

```markdown
# Product PRD — Revision History

- [<date>] <what changed> — reason: <why>
```

New entries go directly under the heading. Adding a feature link to
`## Features`, or the ` (done)` / ` (needs review)` suffixes, isn't
logged. Never edit or delete an older entry.
