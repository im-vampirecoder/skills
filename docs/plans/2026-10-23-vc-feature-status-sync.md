# Plan: feature status lifecycle and tracker sync

- **Date:** 2026-10-23
- **Status:** Steps 0-6 done in the working tree (uncommitted, version 0.3.0-alpha); step 7 is the qsbn plan only
- **Depends on:** the story-readiness change in the working tree (feature `ready` gate, story `ready` set by `vc-create-user-stories` / `vc-create-pbi`, target-only gate in `vc-tasks-breakdown`, task breakdown required for sprint candidates)
- **Sources:** `fangtrack/artifacts/create-stories-from-feature/toolkit-change-note.md`, `skills/delivery/vc-sync-to-tracker/` (feature field mapping, story ready state), `skills/delivery/vc-setup/` (state questions), `skills/delivery/vc-prd/references/deliver-mode.md`, `skills/delivery/vc-implement/references/verification-and-tracker-update.md`, `skills/delivery/vc-create-sprint-release-note/`

## Goal

A feature's status in its `prd.md` and its State on the tracker always say
the same thing. A PO looking at the Azure DevOps board (and later GitHub)
sees which features are still being written, which are agreed and ready to
split, which are being built and which are finished, without opening the
tracking repo.

## What it adds over today

- Today a feature's `status` is `needs-review`, `draft`, `ready` (new, in
  the working tree) or `delivered`. Only `delivered` reaches the tracker:
  `vc-sync-to-tracker` moves the Feature to `[ado].feature_closed_state`.
  From creation until that moment the board shows the Feature in its
  first state, whatever the team is doing.
- There is no feature state for "being built". `vc-implement` moves
  stories to Active but never the Feature.
- `delivered` has no counterpart on any tracker, and its name suggests
  "in production", which it doesn't check.

This plan adds:

- Two stored feature states, `active` and `done`, replacing `delivered`.
- One tracker state per synced local state, chosen in `/vc:setup`, pushed
  by `vc-sync-to-tracker` and, for `active`, by `vc-implement` the moment
  work starts.
- Config names that don't depend on Azure DevOps, so a GitHub tracker can
  map the same states later.

## Decisions

| Topic | Decision |
|---|---|
| Local states | `needs-review → draft → ready → active → done`, stored in the `prd.md` frontmatter `status` |
| `delivered` | Renamed to `done`. Neither Azure DevOps nor GitHub has a "delivered" state; `done` is the one name every tracker shares |
| Active / Done storage | Stored in `prd.md`, not worked out from the stories at sync time |
| `needs-review` | Not synced. A stub becomes a tracker work item only once it is `draft` |
| Tracker scope now | Azure DevOps only. Config keys and the mapping are written against the local state names, so GitHub is another config block later |
| Mode and date | `/vc:prd done <feature>` (`deliver` alias for one minor version); date field `done_on` |
| Revising `active` | stays `active` |
| Release / production | `/vc:release <version>` skill, planned separately; see "Production and release notes" below |
| Agile/CMMI done state | suggest `Closed` |

## Feature lifecycle

| `status` | Meaning | Set by | Synced as |
|---|---|---|---|
| `needs-review` | stub guessed from code | `vc-docs`, `vc-code-to-srs` | not synced |
| `draft` | being written, requirements can still move | `vc-prd` (new feature, Review Mode, revision of a `ready` one) | `feature_draft_state` (`New`) |
| `ready` | team has read it, nothing blocks; stories can be written | `vc-prd-clarify` step 8 | `feature_ready_state` (`Ready`, or no move) |
| `active` | at least one story is being built | `vc-implement`, when it moves the feature's first story to `in-progress` | `feature_active_state` (`Active`) |
| `done` | every non-removed story is `done`; requirements frozen | `/vc:prd done` (today's `deliver` mode), on the PO's confirmation | `feature_done_state` (`Done` / `Closed`) |

Transitions and guards:

- **`ready → active`**: `vc-implement`, when it moves a story of a `ready`
  feature to `in-progress`. A story started on a `draft` feature (a spike
  from `vc-create-pbi`) does not change the feature's status: the feature
  isn't agreed yet.
- **`active → done`**: `vc-implement`'s existing "last story" offer, which
  invokes `/vc:prd done`. A `draft` or `ready` feature whose stories are
  all done (built before `active` existed, or started outside
  `/vc:implement`) may also go to `done`: the mode names the skipped
  status and the PO's confirmation covers it. The PO's confirmation stays, because `done`
  freezes the requirements (today's `deliver` rules unchanged).
- **Revision**:
  - `ready` → back to `draft` (already in the working tree).
  - `active` → stays `active`. Stories are being built, and the
    built-requirement freeze already protects what is `done`. The write
    preview lists the not-done stories citing a changed ID.
  - `done` → refused, as `delivered` is today (supersede or `clarify`).
- **Story writing**: `vc-create-user-stories` accepts `ready` and
  `active` features (add mode while the feature is being built); `draft`,
  `needs-review` and `done` stop as today.
- **Story removed or added** after `active`: no status change. A feature
  only goes back from `active` by hand.

## Tracker mapping (Azure DevOps)

### Config

`[ado]` in `.vc/config.toml`, next to the story keys:

```toml
feature_draft_state = "New"        # the type's first state; set automatically
feature_ready_state = ""           # "" = no ready state on this process
feature_active_state = "Active"
feature_done_state = "Closed"
```

`feature_closed_state` becomes `feature_done_state`. A config with only
`feature_closed_state` is read as `feature_done_state`; `/vc:setup`
rewrites it on its next run.

### `/vc:setup`

List the `Feature` type's states with their categories, as it does today
for the closed state, and ask one question per key, never picking for the
user:

| Question | Key | Likely default |
|---|---|---|
| Which Feature state means "ready to split into stories"? | `feature_ready_state` | a `Proposed` state after the first; "No ready state" offered |
| Which Feature state means "being built"? | `feature_active_state` | the first `InProgress` state: Agile/CMMI `Active`, Scrum `In Progress` |
| Which Feature state means "done"? | `feature_done_state` | the first `Completed` state: Agile/CMMI `Closed` (or `Resolved`), Scrum `Done` |

`feature_draft_state` is the type's first state, read from the state list,
not asked. No standard process has a Feature `Ready` state; "No ready
state" keeps a `ready` feature in the first state and suggests adding a
custom `Ready` state (Proposed category) to the inherited process, as the
story question does.

### `vc-sync-to-tracker` (feature step)

- Skip a `needs-review` feature entirely (no create, no update).
- Work out the target State from `status` and the config. Empty key → no
  move for that status.
- Read the current State. Target equal → nothing to do.
- **Forward moves** (draft → ready → active → done, by the order above):
  collect them for the whole run and confirm them once with the user,
  then send.
- **Backward moves**: only `ready → draft` after a revision is expected.
  Confirm it on its own, naming the revision. Any other backward case
  (the board is further along than the file) → leave it and list it as
  "board is further along" in the summary, as stories do today.
- Azure DevOps refuses a move (open children on some processes) → report
  the error, leave the State.
- `feature-field-mapping.md`: `System.State` row rewritten from "only
  `delivered`" to this table.

### `vc-implement`

When it moves a story to `active_state` and the feature is `ready`: set
the feature's `status: active` and, when the feature has an `ado_id` and
`feature_active_state` is set, move the Feature too, in the same
confirmation as the story. Sync reconciles anything missed.

## GitHub (later)

Same five local states, a `[github]` block with the same keys. The usual
target is a Projects v2 single-select **Status** field (`Todo`,
`In Progress`, `Done` by default, renamable), with `done` also closing the
issue. `feature_ready_state` maps to a custom Status option or stays
empty. Nothing GitHub-specific in the skills beyond the tracker step.

## Rename `delivered` → `done`

87 mentions across 33 files in this repo (skills, scripts, test fixtures).

- **Frontmatter**: `status: done`; the date field `delivered: <date>`
  becomes `done_on: <date>`. Legacy `status: delivered` and `delivered:`
  are read as `done` / `done_on` everywhere, and rewritten the next time
  the PRD is written (same pattern as legacy `synced`).
- **Mode**: `/vc:prd done <feature>`; `deliver` kept as an alias for one
  minor version, then removed. `references/deliver-mode.md` →
  `references/done-mode.md`.
- **Scripts**: `vc-requirements/scripts/requirement_state.py`,
  `shortlist_conflict_candidates.py`, `vc-prd/scripts/apply_supersessions.py`
  compare against `{"done", "delivered"}`. Fixtures gain one `done` PRD
  and keep one legacy `delivered` PRD so both paths stay tested.
- **Prose**: "delivered feature" → "`done` feature" where it means the
  status. Leave the word where it means shipping in general.
- **Kept as is**: the PRD section heading `## Changes to delivered
  features`. No script parses it, and renaming it would leave existing
  PRDs inconsistent with new ones.
- **Legacy read in scripts**: `parse_requirement_ids.feature_status()`
  maps `delivered` → `done` and `synced` → `draft` once, so every other
  script compares against the current names only.

## Production and release notes (direction agreed, separate plan)

`done` means "every story is done and the PO froze it". It does not mean
"live in production". Today nothing records that moment, and
`vc-create-sprint-release-note` reports what a sprint finished (items in
an iteration), not what users can now use.

Agreed direction:

- Keep production out of the status lifecycle: trackers have no state
  for it, and a feature can be `done` for weeks before it ships.
- Record releases separately with a `/vc:release <version>` skill: list
  `done` features (and done bugs) not yet in a release, ask which went
  out, write `release: <version>` and `released_on: <date>` in each
  `prd.md`, write `artifacts/releases/<version>.md`, and tag the tracker
  items `release-<version>` (works on every process and on GitHub).
- Add a `release <version>` mode to the release-note skill that reads
  `artifacts/releases/<version>.md` and the PRDs, with the same
  plain-language rules. The sprint mode stays as the team's recap.
- Later: read the deployed version from a git tag or the CI pipeline so
  `/vc:release` suggests the list instead of asking.

## Steps

0. **Story readiness** (working tree, done): feature `ready`, story
   `ready` at story writing, target-only task-breakdown gate, sprint
   candidates need a breakdown. Commit with this plan or before it.
1. **Rename `delivered` → `done`** (done): frontmatter, `done` mode with
   `deliver` alias, scripts with legacy read, fixtures and tests, prose
   sweep.
2. **`active` state** (done): `vc-implement` sets it; `vc-prd` revision rule for
   `active`; `vc-create-user-stories` accepts `active`; status lists in
   `vc-code-to-srs`, `vc-sync-to-tracker`, `supersession.md`,
   `requirements-section.md`.
3. **Setup** (done): the three Feature state questions,
   `feature_closed_state` read as `feature_done_state`, config template.
   Sync already reads the new key (legacy key as fallback); its state
   logic is still step 4's.
4. **Sync** (done; current State ranked by configured state, else by
   category, so Resolved/Removed and custom states are handled): skip `needs-review`; the state table, forward/backward rules,
   one confirmation per run; `feature-field-mapping.md`.
5. **Implement** (done; only from a Proposed-category state, skipped
   when the PRD has no `ado_id` or the key is missing): Feature move to `feature_active_state` with the story's.
6. **Docs** (done; 0.3.0-alpha, `deliver` alias removed in 0.4.0): delivery README, `skills/README.md`, version bump in
   `package.json` and `.claude-plugin/plugin.json`.
7. **Port to qsbn-agent-skills** (same diff, names swapped), including
   `docs/specs/qsbn-workflow-design.md`.

## Tests

- `test_requirements_scripts.py`: a `done` feature is frozen like a
  `delivered` one; a legacy `delivered` fixture still is.
- Supersession script: `done` and `delivered` targets both get banners.
- No script owns the tracker state mapping today; if step 4 adds one
  (status → target state, forward/backward), it gets its own test file.

## Settled (2026-10-23)

All five earlier open questions went with the recommendation:

1. Mode: `/vc:prd done <feature>`, `deliver` kept as an alias for one
   minor version.
2. Date field: `done_on`.
3. Revising an `active` feature keeps it `active`.
4. Releases: a `/vc:release <version>` skill (separate plan, after
   step 7), not a flag on `done`.
5. Agile/CMMI: suggest `Closed` for `feature_done_state`.
