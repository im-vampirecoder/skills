---
name: vc-propose-epic
description: Match a feature's PRD against existing epics (or propose a new one), then move the feature folder under the confirmed epic. Also handles moving an already-assigned feature to a different epic.
---

# Propose Epic

Assign a feature to an epic, creating the epic if none fits, and physically
move the feature's folder there. Never merges a feature into an epic
without the user explicitly confirming — no silent matching.

## What an Epic is

Per the backlog hierarchy rules, an Epic is a large, stable **capability**
area — spans a quarter or more, named for the capability itself ("User
Authentication"), never for a release or a batch of work ("Q3 Auth
Work"). It carries a goal statement and success metric, not acceptance
criteria, and it never carries a target Iteration — that belongs on the
Feature, one level down. An Epic that's actually scoped to a single
release is a mislabeled Feature, not an Epic; step 4's shape check below
is where that gets caught, whenever this skill is the one proposing a
brand-new epic.
`vc-prd` already checked the *feature* itself is Feature-shaped before
this skill ever runs — this skill's own job is making sure any epic it
creates is actually Epic-shaped, not re-litigating the feature.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as a PRD description, a path to a feature's
     `prd.md`, or a feature slug. Locate its folder: either
     `artifacts/<feature-slug>/` (unassigned) or
     `artifacts/epic-*/feature-<feature-slug>/` (already assigned — this
     is the reassignment case, go to step 5 after finding candidates in
     step 2).
   - Read the located `prd.md`'s frontmatter `status`. If `needs-review`,
     stop and tell the user to run `/vc:prd review <feature-slug>`
     first — don't propose or assign an epic for an unreviewed guess.

2. **Find candidate epics**
   - Read `artifacts/epics.md` and every `artifacts/epic-*/epic.md` for
     title and any topic/domain hints in their body. Compare against the
     feature's PRD (title, overview, problem statement).
   - Present the best 1-3 candidates (or none) to the user, each with a
     one-line reason it might fit, plus an explicit "none of these — make
     a new epic" option.

3. **Confirm with the user**
   - Wait for the user to pick an existing epic, or confirm creating a
     new one. Never auto-select the top match.

4. **New epic (if chosen)**
   - Ask for the epic's title if not obvious from the feature. Generate
     `<epic-slug>` (kebab-case, same collision-suffix rule as feature
     slugs: `-2`, `-3`, ...).
   - **Epic-shape check, before writing anything:** does the proposed
     title/scope name a durable capability, or does it read as scoped to
     one release (a quarter/sprint qualifier, or "the work for X" rather
     than "the capability of X")? If it reads release-scoped, stop and
     tell the user — this is a Feature-sized epic, not a real one. Two
     ways forward, their choice: rename it around the underlying
     capability (e.g. "Q3 Auth Work" → "User Authentication"), or skip
     creating a new epic and reconsider whether an existing one already
     fits (back to step 2) — a release-scoped batch of work usually isn't
     a new capability at all.
   - Create `artifacts/epic-<epic-slug>/epic.md`:
     ```markdown
     ---
     id: EPIC-<epic-slug>
     ado_id: null
     last_synced: null
     title: <Title>
     status: draft
     ---

     # Epic: <Title>

     ## Features
     ```
   - Append a row to `artifacts/epics.md` (create the file with a header
     row if it doesn't exist yet):
     ```markdown
     | ID | Title | Status | Link |
     | --- | --- | --- | --- |
     | EPIC-<epic-slug> | <Title> | draft | [epic.md](./epic-<epic-slug>/epic.md) |
     ```

5. **Move the feature folder**
   - First-time assignment: `git mv artifacts/<feature-slug>/
     artifacts/epic-<chosen-epic-slug>/feature-<feature-slug>/`.
   - Reassignment: `git mv artifacts/epic-<old-epic-slug>/feature-<feature-slug>/
     artifacts/epic-<new-epic-slug>/feature-<feature-slug>/`.
   - If the destination epic folder doesn't exist yet (new epic case),
     `git mv` still works once step 4 has created `epic.md` inside it.
   - Either way, update the moved `prd.md`'s own frontmatter: set
     `epic_id: EPIC-<chosen-or-new-epic-slug>`. This is the field
     `vc-sync-to-tracker` reads to parent the feature's Azure DevOps
     work item to the right epic — the folder move alone isn't enough,
     the frontmatter has to say so explicitly.

6. **Update the epic(s)' Features sections**
   - Add a line to the chosen epic's `## Features` section:
     `- [<Title>](./feature-<feature-slug>/prd.md)`.
   - Reassignment only: also remove the corresponding line from the old
     epic's `## Features` section.

7. **Update the product PRD link**
   - In `artifacts/prd.md`'s Features section, update the feature's link
     to its new path (`epic-<epic-slug>/feature-<feature-slug>/prd.md`).

8. **`artifacts/epics.md` stays untouched on a move**
   - It indexes epics only, not features, so reassigning a feature
     between epics never requires editing it. Only editing an epic's
     title or status (not covered by this skill) would.

## Notes

- A feature folder may already hold `stories-<n>-*.md` files —
  `vc-create-user-stories` and `vc-create-pbi` allow writing stories
  before an epic exists. The `git mv` in step 5 carries them along as-is;
  they store only `feature_id`, so no story file needs editing. The same
  goes for a `tasks/` folder from `vc-tasks-breakdown`, which also runs
  before an epic exists — task files store only `story_id`.
- A feature folder may also hold a feature-scope `architecture.md` and
  `.decisions.md` from `vc-architecture-design`; the `git mv` carries
  them too. Set the moved spine's `epic_id` frontmatter the same way as
  `prd.md`'s. Its Inherited Invariants were taken from the old epic's
  spine (or none), so tell the user to re-run
  `/vc:architecture-design <feature-slug>` to re-check it against the
  new epic's spine — a nudge, not something this skill rewrites.

- This skill never syncs to a tracker. `epic.md`'s `ado_id` and
  `last_synced` fields, and the feature's own `ado_id`/`last_synced`, are
  populated by `vc-sync-to-tracker`, not here — this skill only ever
  writes `epic_id`.
- A reassignment (step 5) changing a feature's `epic_id` after it's
  already been synced is exactly what `vc-sync-to-tracker` checks for
  on its next run (feature-level re-parenting) — nothing needs to happen
  here beyond writing the new `epic_id` correctly.
- Reject the reserved slugs from `vc-prd` step 7 as epic slugs too
  (`prd`, `prd-history`, `epics`, `architecture`, `decisions`, `bugs`,
  `sprints`, `reviews`, `diagrams`, and any slug starting with `epic-` or
  `feature-`), so an epic folder name never collides with a root-level
  file or folder or doubles its prefix.
