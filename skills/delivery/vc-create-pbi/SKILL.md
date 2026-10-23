---
name: vc-create-pbi
description: Write a Product Backlog Item or User Story with Given/When/Then acceptance criteria for a feature (assigned to an epic or not), with no requirement that it be independently demoable — covers research, spikes, and technical enablers as well as ordinary value stories. Built-in only — never delegates to a third-party story-writing skill.
---

# Create PBI

Break a feature's PRD into backlog items at the story level, same as
`vc-create-user-stories`, but without that skill's hard demoable/deliverable
requirement. Use this instead of `/vc:create-user-stories` for a feature that
needs a research spike, a technical/architecture investigation, or any
other item too large for a single task but with no direct end-user demo —
`vc-create-user-stories` rejects those by design (see its Demoable-AC check);
this skill is the escape hatch for the cases that check exists to catch
everywhere else. Always runs its own logic below — never checks
`.vc/config.toml` preferences and never delegates to `/user-story`,
`bmad-create-epics-and-stories`, or any other third-party skill, regardless
of what's installed.

Output is identical in shape to `vc-create-user-stories`' — same file naming,
same frontmatter, same `STORY-<feature-slug>-<n>` id scheme — so
`vc-tasks-breakdown`, `vc-implement`, `vc-code-review`, and
`vc-sync-to-tracker` all pick it up unchanged, whether the target
project's process template calls this level "User Story" or "Product
Backlog Item." This skill doesn't need to know which one a given project
uses — it writes the same artifact either way.

## What this skill produces

Per the backlog hierarchy rules, an item written here is still a
**story-level backlog item**: bigger than a Task, INVEST-checked where
INVEST applies, one file per item. Two shapes are allowed:

- **Value story** — same definition as `vc-create-user-stories`: a vertical
  slice that's independently demoable and testable on its own, format "As
  a [role], I want [goal], so that [benefit]," where "so that" is
  user/business value. Draft and check these exactly as
  `vc-create-user-stories` does.
- **Non-demoable item** (spike, research, technical enabler) — no
  end-user demo, but still a bounded, story-sized unit of work with a
  concrete Definition of Done: a documented decision, a written finding,
  a working proof-of-concept, a resolved risk/unknown. "As a [role], I
  want [to investigate/resolve X], so that [the team can then do Y]" is
  fine here even though the "so that" names a technical/process outcome —
  that's the one hard rule this skill relaxes from `vc-create-user-stories`.

A Task (a technical step with no independent value, e.g. "add a PUT
endpoint") is still never written as its own item here — that's
`vc-tasks-breakdown`'s concern once an item is approved, same as
`vc-create-user-stories`.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as a path to a feature's `prd.md` or a feature
     slug. Resolve it the same way `vc-create-user-stories` does —
     `artifacts/<feature-slug>/prd.md` (unassigned) or
     `artifacts/epic-<epic-slug>/feature-<feature-slug>/prd.md`
     (assigned); epic assignment is not required. The folder holding
     that `prd.md` is the **feature folder**.
   - Read the feature's `prd.md` (including its `## Acceptance Criteria`
     — the feature's own Definition of Done), plus its epic's `epic.md`
     when the feature is epic-assigned.
   - Read the PRD's `## Requirements` section and work out which IDs are
     live exactly as `vc-create-user-stories` step 1 does (reads
     `artifacts/requirements-current.md` when present; never cites a
     retired or superseded ID; no Requirements section → suggest
     `/vc:prd migrate <feature>` and continue without `Implements:`
     lines).
   - List any existing `stories-<n>-*.md` files already under this
     feature (from a prior `vc-create-user-stories` or `vc-create-pbi` run)
     and note the highest `<n>` in use — new items continue that same
     sequence rather than restarting at 1, since both skills write into
     one shared numbering space per feature.

2. **Draft candidate items**
   - Ask the user (if not already clear from context) whether this run is
     for ordinary value stories, non-demoable items, or a mix — this
     determines which checks apply per candidate in step 3.
   - Decompose the feature into story-sized units, each completable in
     roughly 1-3 days, each delivering end-to-end value or a concrete
     finding on its own.
   - **Splitting method**: split by workflow step, business rule, data
     variation, happy-path vs. edge-case, or — for a non-demoable item —
     by distinct question/unknown being resolved. Never split by
     technical layer (DB / API / UI) or by CRUD verb alone — those
     produce task-slices, not story-level items.
   - Apply INVEST where it applies: Independent, Negotiable, Valuable
     (business or team value — see "What this skill produces" above),
     Estimable, Small, Testable. Format: "As a [persona], I want to
     [action], so that [benefit]."
   - Note which live requirement IDs each value story implements (its
     FRs plus the BRs, ERRs and NFRs that apply to them), as
     `vc-create-user-stories` step 4 does. A spike or enabler builds no
     requirement itself, so it implements none unless it delivers part
     of one.

3. **Run the hard-rule checks on every candidate — reject and re-slice
   before writing anything**
   - **Value stories**: run `vc-create-user-stories`' full check set unchanged
     — Demoable-AC check, "So that" test (a technical benefit clause
     fails), and Vertical-slice check.
   - **Non-demoable items**: run these instead —
     - **Concrete-outcome check**: the item must name a specific artifact
       or resolved question as its Definition of Done (a decision
       recorded, a report/finding written, a proof-of-concept built and
       evaluated, a risk closed) — not an open-ended "investigate X" with
       no defined end state. Fails → tighten the scope until there's a
       checkable finish line.
     - **Size check**: still roughly 1-3 days, same bar as a value story.
       A genuinely task-sized technical step (no independent value, fits
       inside another item's implementation) doesn't get its own file —
       flag it as a dependency in step 7 instead, the same treatment
       `vc-create-user-stories` gives a technical prerequisite.
     - **Vertical-slice check**: a non-demoable item still must stand on
       its own — if it only produces something useful combined with a
       sibling, merge them or re-split along a different axis per step
       2's splitting method.
   - Re-run the relevant checks after any re-slice. Only candidates that
     pass move on to step 4.

4. **Write acceptance criteria per item**
   - Given/When/Then format, 3-7 criteria per item. Each criterion is one
     numbered list item (`1.`, `2.`, ...), in order; break `Given`/`When`/
     `Then` onto their own line inside that item (hard line break, i.e.
     trailing two spaces), with `**Given**`, `**When**`, `**Then**`
     bolded, and a blank line between each numbered item — see the
     template in step 6.
   - Value story: cover the happy path, at least one edge case, and at
     least one error state, same as `vc-create-user-stories`, with
     edge-case and error-state criteria drawn from the applicable `BR-`
     and `ERR-` entries (exact limits, exact "The user sees" wording,
     nothing invented).
   - Non-demoable item: cover what's investigated/built, what the
     concrete output is, and how it's verified (reviewed by whom, or what
     test/measurement confirms the finding) — the "Then" describes the
     produced artifact or decision, not a user-facing behavior.

5. **Add item metadata**
   - Priority: must-have, should-have, or nice-to-have.
   - Dependencies on other items from this same feature, if any.
   - Design: link to a wireframe/mockup if one already exists for this
     item's UI, else "n/a". Never required, never fabricated. Check
     `<feature folder>/ux/ux-spec.md` for mockups first, as
     `vc-create-user-stories` does.
   - Implements: the full requirement IDs from step 2, comma-separated,
     live IDs only; `none` for a spike or enabler that builds no
     requirement.
   - Type: `story` or `spike` — local-only note for readers and for
     `vc-tasks-breakdown`, not synced to the tracker (see Notes).

6. **Write one file per item**
   - Path: `<feature folder>/stories-<n>-<short-description>.md`,
     `<n>` continuing the sequence found in step 1, `<short-description>`
     a few kebab-case words.
   - Content:
     ```markdown
     ---
     id: STORY-<feature-slug>-<n>
     feature_id: FEATURE-<feature-slug>
     ado_id: null
     last_synced: null
     status: new
     iteration: null
     ---

     # <n>. [<feature-slug>] <Item title>

     **As a** <persona>
     **I want to** <action>
     **So that** <benefit>

     ## Acceptance Criteria

     1. **Given** ...,  
        **When** ...,  
        **Then** ...

     2. **Given** ...,  
        **When** ...,  
        **Then** ...

     3. ...

     ## Details

     - Priority: must-have | should-have | nice-to-have
     - Dependencies: <story IDs, or "none">
     - Design: <wireframe/mockup link, or "n/a">
     - Implements: <full requirement IDs, comma-separated, or "none">
     - Type: story | spike
     ```
   - Same `id`/`feature_id` scheme as `vc-create-user-stories` (prefix
     `STORY-`, not e.g. `PBI-`) — deliberate, not an oversight:
     `vc-tasks-breakdown` and `vc-sync-to-tracker` resolve items by
     this id and by the `stories-<n>-*.md` filename, so a different
     scheme would make a non-demoable item invisible to both.
   - Same `status: new` / `iteration: null` sprint-tracking fields as
     `vc-create-user-stories` (see its step 9 for the values and who
     changes them). A spike needs to be `ready` before task breakdown
     and a sprint too.

7. **Offer to mark items ready, then summarize**
   - First the readiness offer, exactly as `vc-create-user-stories`
     step 10: the feature's `status: new` items, multi-select, "None yet"
     included; set `status: ready` on the chosen ones and nothing else.
     `/vc:tasks-breakdown` only runs on `ready` items.
   - After writing all files, list them with a one-line description each
     (tagging `[spike]` next to any non-demoable item), the suggested
     implementation order, and which items form the MVP subset (deliver
     the core value with the fewest items).
   - List any Task-level dependency flagged in step 3 (technical
     prerequisites with no item of their own), naming which item each one
     belongs under.
   - Same coverage warning as `vc-create-user-stories` step 11: every
     live P0 `FR-` that no item in the feature folder implements is named,
     with an offer to draft one. A spike never counts as covering an FR.
   - Suggest `/vc:requirements check` so the new `Implements:`
     citations are verified.

## Notes

- This skill never syncs to a tracker — `ado_id` and `last_synced` stay
  `null` until `vc-sync-to-tracker` runs.
- `vc-sync-to-tracker` doesn't distinguish a spike from a value story —
  both sync as whatever work item type `.vc/config.toml`'s
  `[ado].story_work_item_type` names for this project ("User Story",
  "Product Backlog Item", or another process-specific name — `vc-setup`
  detects it once at setup time). The `Type` field from step 5 is local
  documentation only, never pushed anywhere.
- This skill never touches `epic.md`'s Features section, a feature's own
  `prd.md`, or `artifacts/epics.md` — those stay `vc-propose-epic`'s
  (and `vc-prd`'s) responsibility.
- Items written for an unassigned feature follow the same rule as
  `vc-create-user-stories`: they move with the feature folder when
  `/vc:propose-epic` assigns it; tasks breakdown works without it, but
  tracker sync still needs that assignment first.
- There is no reassignment flow for a single item to a different feature
  — an item's `feature_id` is fixed at creation, same as
  `vc-create-user-stories`.
- Prefer `vc-create-user-stories` for ordinary feature work. Reach for this
  skill specifically when a candidate keeps failing that skill's
  Demoable-AC or "So that" check and re-slicing genuinely can't produce a
  demoable story — a real research spike or technical enabler, per "What
  this skill produces" above, not a shortcut around that skill's rigor.
