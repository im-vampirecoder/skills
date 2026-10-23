# Feature File → Azure DevOps Field Mapping

Canonical mapping used by `vc-sync-to-tracker` when pushing a feature's
`prd.md` to Azure DevOps as a Feature — the level between Epic and Story
in the backlog hierarchy.

## Field map

| Azure DevOps field | Source in the feature's `prd.md` | Notes |
|---|---|---|
| `System.Title` | The `# Feature PRD: <Title>` heading, `<Title>` only | No numbering or bracket tag to strip — features aren't numbered the way stories are. |
| `System.Description` | HTML of the `## Overview` and `## Problem / Motivation` sections | See "Description body" below. |
| `Microsoft.VSTS.Common.AcceptanceCriteria` | The `## Acceptance Criteria` bullets/checklist | Same conversion rules as a story's AC — see "Acceptance Criteria conversion" below. |
| `System.AreaPath` | `.vc/config.toml`'s `[ado].area_path` | Same value used for stories. |
| `System.IterationPath` | `.vc/config.toml`'s `[ado].iteration_path` (optional) | Omit the field entirely if blank. This is the field the backlog hierarchy rules mean by "Feature carries the target Iteration/Release" — the epic sync never sets this field at all. |
| `System.Tags` | **Not mapped.** | `[tags].story` is story-specific; no feature-level tag config exists yet. |
| Parent link (`System.LinkTypes.Hierarchy-Reverse`) | The feature's `epic_id`, resolved to that epic's `ado_id` (synced earlier in the same run) | **Never** a configured default — see "Parent resolution" below. |
| `System.State` | The `prd.md` `status`, mapped through `.vc/config.toml`'s `[ado]` Feature state keys | Moved only as "Feature State" below describes, confirmed by the user first. |

## Feature State

The target State comes from the PRD's `status`:

| `status` | Target State | Rank |
|---|---|---|
| `needs-review` | never synced: no create, no update | - |
| `draft` (legacy `synced`) | the Feature type's first state (`New`) | 0 |
| `ready` | `feature_ready_state`; empty → the first state | 1 |
| `active` | `feature_active_state` | 2 |
| `done` (legacy `delivered`) | `feature_done_state` (legacy key `feature_closed_state`) | 3 |

Read the Feature type's states and categories once per run, with the
`workItemTypeStates` query `vc-setup` uses. The board's **current rank**
comes from the work item's current State:

- equal to a configured state → that state's rank (the first state is 0);
- otherwise by category: `Proposed` → 0, `InProgress` → 2,
  `Resolved` or `Completed` → 3;
- `Removed` → no move at all; list it in the summary ("removed on the
  board, `<status>` locally").

Then:

| Case | Action |
|---|---|
| Current State equals the target | nothing to do |
| Target rank higher (forward) | collect the move; the run confirms all moves once |
| Target rank 0, current rank 1, `status: draft` (a `ready` feature revised back to `draft`) | the one backward move: confirm it on its own, naming the revision ("revised after it was ready") |
| Any other lower target (backward) | leave it; list it as "board is further along" |
| Target key empty or missing | no move; missing → suggest `/vc:setup` |

A new Feature is created in the type's first state, then moved like an
existing one. Azure DevOps refuses a move (some processes block closing
with open children) → report the error and leave the State.

## Title extraction

Input heading:

```
# Feature PRD: SSO via Entra ID
```

`System.Title` is everything after `# Feature PRD: `:

```
SSO via Entra ID
```

## Description body

Two blocks, in order:

1. The `## Overview` section's prose, rendered as HTML.
2. The `## Problem / Motivation` section's prose, rendered as HTML,
   under its own `<h4>Problem / Motivation</h4>` heading so the two
   stay visually distinct in the Azure DevOps web UI.

Use the same general markdown → HTML rules as stories (bold, inline
code, paragraphs, fenced code blocks — see `story-field-mapping.md` for
the table if needed).

## Acceptance Criteria conversion

Same rule as a story's AC: each item (numbered item, bullet, or
checklist line) becomes one `<li>`. A feature's
Definition of Done may be written as plain checklist items
(`- [ ] ...`) rather than strict Given/When/Then — in that case, drop
the checkbox syntax and render the remaining text as the `<li>` content
(the checkbox itself has no meaning once it's a tracked Azure DevOps
field; completion is the story-level work underneath, not a box to tick
here).

## Parent resolution — no configured default

A feature's parent is always the `ado_id` of the epic recorded at
`artifacts/epic-<epic-slug>/epic.md`, which `vc-sync-to-tracker` syncs
(creating or refreshing it) before touching the feature. There is no
`default_parent_epic_id`-style config value — the correct parent is
always derivable from `epic_id` in the feature's own `prd.md`
frontmatter, which `vc-propose-epic` is the sole writer of.

### Detecting drift and re-parenting

A feature can be moved between epics after it's already been synced
(via `vc-propose-epic`'s reassignment flow, which updates the
feature's `epic_id` in place). On every UPDATE:

1. Read the feature's current parent relation from Azure DevOps:
   `az boards work-item relation show --id <ado_id>` (or via
   `az devops invoke` for the relations index).
2. Compare the parent's ID to the epic's `ado_id` from this run's epic
   sync step.
3. If they match, do nothing.
4. If they differ:
   ```bash
   az boards work-item relation remove --id <ado_id> --relation-type parent --target-id <OLD_PARENT_ADO_ID>
   az boards work-item relation add --id <ado_id> --relation-type parent --target-id <NEW_EPIC_ADO_ID>
   ```
   Report this re-parent in the sync summary — it's a meaningful change,
   not routine housekeeping.

Skip this check entirely on CREATE — a freshly created feature is
parented correctly the first time, there's nothing to drift from yet.

This is the only re-parenting check left in this skill. A story's
parent (its feature) never drifts the same way — see
`story-field-mapping.md`'s "Parent resolution" section for why.
