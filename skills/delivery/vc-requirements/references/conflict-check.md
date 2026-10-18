# Conflict check

How `/vc:requirements conflicts [feature]` finds and settles
requirements in different features that disagree.

## What counts

| Kind | Example | Not a conflict when |
|---|---|---|
| Contradiction | `FR-checkout.guest-pay` lets guests pay; `BR-accounts.login-before-purchase` requires sign-in | both are limited to conditions that can't apply at the same time |
| NFR clash | payment result within 3 s in one feature, 5 s in another, same flow | different flows or different load levels |
| Rule clash | retry limit 3 per card vs 5 per card | one rule is explicitly narrower and says so |
| Product misfit | the feature targets users or goals the product PRD excludes | the product PRD already lists them |
| Duplicate | two features define the same behaviour under different IDs | never a contradiction; settled by citing the earlier ID |

Plain overlap, where two features touch the same screen or entity
without disagreeing, is not reported.

## Shortlist

`shortlist_conflict_candidates.py` pairs live requirements (not retired,
not superseded) from different features that share at least one signal. When a feature folder holds a `prd.draft.md` (vc-prd is mid-write),
the draft stands in for that folder's `prd.md`; `check` and `view` ignore
drafts. Signals:

- `term:<t>`: the same glossary term in the ID name or text. Aliases
  listed under "Avoid" count as the term. In projects with 30 or more
  requirements, a term found in more than half of them is ignored.
- `nfr:<category>`: two NFRs in the same category (response time,
  availability, retention, access).
- `touchpoint:<t>`: the same `## Touchpoints` entry.
- `entity:<e>`: the same entity in `### State transitions` tables.
- `same-name`: identical ID names, the strongest duplicate hint.

The script skips pairs already settled: any `## Decisions` line in either
PRD that names both IDs, including `not a conflict: <id> vs <id>`.
Delivered-vs-delivered pairs are returned as `bug_candidates` and never
judged, because a contradiction between two shipped features is a product
bug. Pairs involving a delivered feature come after draft-vs-draft pairs.

An unscoped run with more than 50 pairs returns `needs_scope: true`, the
pair count and per-feature counts instead of pairs. Show those counts
(drafts first) and ask which features to audit, then rerun with
`--feature` for each. There is no progress file and no partial run. The
threshold is `--max-pairs`; adjust it once real projects show a better
number.

## Judge

Read both requirement texts in full, plus the owning PRDs' Scope and
Constraints when the texts alone don't settle it. Classify each pair:
`contradiction`, `nfr-clash`, `rule-clash`, `duplicate` or `none`, with
one line of reasoning that quotes both texts. When unsure, choose `none`
and say why. A false alarm costs the PO more time than a missed edge
case, which the next scoped run can still catch.

**Product misfit** is checked once per feature in scope: its Overview,
Target Users and Scope against `artifacts/prd.md`'s goals, users and
scope.

**Large audits:** split the shortlist into groups by feature pair and
give each group to a read-only judge: the `vc-conflict-judge` subagent
when available, otherwise one group after another in this session. Each
judge returns findings only, never edits.

## Resolve

Show one real conflict at a time with both texts, the kind, the options
below and a recommended option with a one-line reason. The PO decides;
the skill never picks.

| Situation | Options |
|---|---|
| New or draft vs delivered | supersede the delivered ID (the new feature adds `supersedes` and a `## Changes to delivered features` entry), or change the new requirement to fit |
| Draft vs draft | keep A and change or retire B; keep B and change or retire A; or narrow both to their conditions. A Decisions entry goes in both PRDs |
| NFR clash | keep the stricter value for both, or scope each value to its flow. Decisions entry |
| Rule clash | retire one rule, or narrow both to their conditions. Decisions entry |
| Product misfit | change the feature, or change the product PRD (logged to `prd-history.md`) |
| Duplicate | the later feature cites the earlier ID and retires its own |
| Not a conflict | `- [date] not a conflict: <id> vs <id> — why: … — by: <role>` in the newer feature's Decisions, so it's never raised again |
| Can't decide yet | an Open Question in both PRDs naming the other ID; stories implementing either ID aren't ready for sprint planning until it's answered |

Each chosen option goes to `vc-prd` Revision Mode for the affected
draft feature, together with the exact change, the Decisions line and the
PO's role. A delivered feature is never edited. The change always lands
in the draft or new feature (for example, the new feature supersedes the
delivered ID).

## Output

A console summary per run: found, resolved, deferred, dismissed, and any
`bug_candidates` with a suggestion to run `/vc:bug-report`. There is no
report file: every outcome lands in a PRD as a changed requirement, a
Decisions entry or an Open Question, so `requirements-current.md` stays
the one place to read.
