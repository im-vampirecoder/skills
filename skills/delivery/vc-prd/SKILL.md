---
name: vc-prd
description: Interview the user about a feature and write its PRD with named requirement IDs (FR / NFR / BR / ERR), bootstrapping the whole-product PRD on first use. Interview depth adapts to the feature (Quick / Targeted / Deep, `--deep` forces Deep). Revises a draft feature in place; refuses to edit a `done` one and offers a superseding feature instead. Leading tokens in $ARGUMENTS pick other modes - `review` completes a needs-review stub, `done <feature>` freezes a finished feature (`deliver` is its old name), `clarify <id>` adds a clarification line to a requirement, `migrate [feature]` adds named IDs to older PRDs. Triggered by /vc:prd. Built-in only - never delegates to a third-party interview skill.
---

# PRD

Write a Product Requirements Document through an adaptive interview. This
skill always runs its own interview logic below — it never checks
`.vc/config.toml` delegation preferences and never delegates to
any third-party skill, regardless of what's installed or configured.

## What a Feature is

A feature written here must actually be Feature-shaped, per the backlog
hierarchy: an independently releasable, demoable slice — describable in
one sentence a non-technical stakeholder would recognize as "a thing that
shipped," roughly one release increment (a few sprints), with its own
stated Definition of Done. It is not a whole capability area (that's an
Epic — `vc-propose-epic`'s concern) and not a bare technical concern
with no independent user-facing value (that's a Task —
`vc-tasks-breakdown`'s concern, once a real story needs it). Step 6
runs the one-sentence test explicitly before anything gets written.

## References (load on demand)

| File | Load when |
|---|---|
| `references/interview-depth.md` | before any interview: depth, "already have / still missing", vague answers, exact values, playback, anti-goals |
| `references/requirements-section.md` | writing or revising a feature PRD: template, ID rules, line formats, wording, errors, markers, conditional tables |
| `references/fresh-reader-check.md` | step 8, after the self-check (Targeted and Deep) |
| `references/supersession.md` | Revision Mode, superseding a `done` feature, the built-requirement freeze, `## Decisions`, product history |
| `references/done-mode.md` | `done` (old name `deliver`) and `clarify` |
| `references/migrate-mode.md` | `migrate` |

## Workflow

0. **Resolve the mode**
   - First token of `$ARGUMENTS`: `review [feature]` → **Review Mode**;
     `done <feature>` (or its old name `deliver <feature>`) or
     `clarify <id>` → `references/done-mode.md`;
     `migrate [feature]` → `references/migrate-mode.md`. No mode token →
     step 1. `--deep` anywhere forces Deep interview depth.
   - A request from `/vc:requirements conflicts` carrying a chosen
     resolution (the feature, the exact change, the Decisions line and
     the PO's role) goes straight to **Revision Mode** for that feature.

1. **Check whether the product PRD exists yet**
   - Read `docs/glossary.md` when it exists. Its terms are the words to
     use in requirement names and text; its "Avoid" words are not.
   - If `artifacts/prd.md` does NOT exist, this is the first-ever run in
     this repo. Go to step 3 (product interview) before anything else.
   - If it already exists, read it as context first, then check whether
     `$ARGUMENTS` (by title match or an explicit slug/path) names a
     feature that already has a `prd.md` — unassigned
     (`artifacts/<slug>/prd.md`) or epic-assigned
     (`artifacts/epic-*/feature-<slug>/prd.md`).
     - No match: a new feature — skip to step 4.
     - A match: confirm with the user — "this looks like a change to
       `<existing feature>`, is that right, or is this a distinct new
       feature?" Never assume either way; a plausible title match isn't
       proof. Confirmed as a change → **Revision Mode**. A distinct
       feature → step 4 (its slug gets suffixed in step 7).

2. **Scout the project folder**
   - Read `.vc/config.toml`'s `submodule_root` value. If the file
     doesn't exist yet, or the field is missing/empty, skip this step —
     don't block on setup, don't guess a default path.
   - If the resolved folder exists and has content, look for what
     already exists that overlaps keywords from `$ARGUMENTS` (and
     existing feature titles from `artifacts/`), plus each project's
     language/framework from its manifest. The folder's own
     `README.md`/`docs/*.md` count as evidence too.
     - **Exactly one project**: scout it inline with `Glob`/`Grep`/`Read`.
     - **2+ projects**: spawn the `vc-scout` subagent
       (`vc:vc-scout` when installed through the plugin) in
       `focused` mode once per project, in parallel, with the keywords
       as its brief, and work from its `path:line` findings. Without
       subagent support, scout each project inline, one after another.
   - Nothing overlaps, or the folder is empty/missing → skip silently.
   - When something is found, post a 3-6 bullet summary *before* asking
     any interview question that references it. Never ask a question
     grounded in findings the user hasn't seen.

3. **Product-level interview (first run only)**
   - Ask, one question at a time: What is this product? What problem does
     it solve, and for whom? Who are the target users/personas? What are
     its top 2-4 goals?
   - Write `artifacts/prd.md`:
     ```markdown
     # Product PRD

     ## Overview
     ## Problem Statement
     ## Target Users
     ## Product Goals
     ## Features
     <!-- appended by vc-prd as features are added -->
     ```
   - Continue straight to step 4 for the feature the user asked about.

4. **Detect multi-feature requests**
   - If `$ARGUMENTS` clearly bundles several independent features, stop
     and confirm the split before any detail questions: list the
     features you'd separate it into and let the user adjust.
   - If confirmed, repeat steps 5-9 once per feature, each with its own
     slug and PRD. Otherwise continue with one feature.

5. **Feature-level interview**
   - Load `references/interview-depth.md`. Score the feature and propose
     Quick / Targeted / Deep in one line the user can override (`--deep`
     skips the proposal). Print "Already have: … · Still missing: …"
     before every question round and never re-ask an answered point.
   - Topics to satisfy, not a fixed script — skip whatever `$ARGUMENTS`,
     the stub or the scout findings already answer clearly:
     - Purpose: what can a user do after this ships that they can't now?
     - Who/scenario: who uses it, in what situation, with which role?
     - Constraints: technical, timeline, compliance, other limits.
     - Success criteria: a metric or observable behaviour.
     - Definition of Done: the feature's own acceptance criteria, as a
       short checklist or Given/When/Then — coarser than the per-story
       criteria `vc-create-user-stories` writes later. No IDs.
     - Out of scope, and anti-goals: what would make this a failure even
       if it works as specified?
     - Touchpoints: existing modules/features it touches (offer step 2's
       candidates as options).
     - The requirements themselves: each flow's trigger and result, what
       can go wrong and what the user sees, rules that limit behaviour,
       qualities the business would measure, and P0/P1/P2 per FR.
   - **One at a time vs batched.** Ask one question at a time whenever
     you offer options to pick from. Batch open-ended questions that are
     naturally answered together in one paragraph (purpose + who often
     come out together). When unsure, one at a time.
   - **No blackbox answers.** One targeted follow-up per vague answer,
     then `TBD — <owner> — <date>` or a `[NEEDS CLARIFICATION: …]`
     marker; never a third ask. Push once for exact values; never invent
     a number. **Playback** after purpose and users, scope, and each core
     flow (not in Quick). Both in `references/interview-depth.md`.
   - **Draft requirements as you go** (`references/requirements-section.md`):
     "When <trigger>, the system shall <result>" FRs, "If <condition>,
     then the system shall <handling>" failures, NFRs as measurable
     business outcomes (never implementation choices), BRs citing their
     FRs, an `ERR-` for every way a P0 FR can fail, and a conditional
     table only when its trigger comes up.
   - **Scout for conflicts while drafting.** As each requirement takes
     shape, check `artifacts/requirements-current.md` and the other
     feature PRDs for requirements sharing its signals; a disagreement
     becomes the next interview question, with both texts, the options
     and a recommendation (`references/interview-depth.md`). The PO
     decides; each choice gets a Decisions entry
     (`references/supersession.md`).
   - **Deep** also runs problem validation (written as
     `## Problem Validation`); see `references/interview-depth.md`.
   - Keep looping until every topic is concrete enough to write down
     without guessing, or is a recorded `TBD`, marker or Open Question.

6. **Feature one-sentence test (before writing anything)**
   - State the feature back in one sentence a non-technical stakeholder
     would recognize as "a thing that shipped." If you can't without
     (a) stringing together several independent capabilities, or (b)
     purely technical language with no user-facing framing, stop:
     - **Too big**: tell the user and offer to split it further — loop
       back to step 4's split flow, even if it already ran once.
     - **Too narrow/technical** (e.g. "upgrade the ORM"): tell the user
       this reads like a Task that belongs inside a story's
       implementation (`vc-tasks-breakdown`), and ask whether to
       proceed anyway. Never write it silently.
   - A check, not a rewrite — if the user confirms the shape as
     intentional, proceed to step 7.

7. **Generate the feature slug**
   - kebab-case the feature title. If it collides with an existing
     `artifacts/<slug>/` or `artifacts/epic-*/feature-<slug>/` folder,
     suffix `-2`, `-3`, etc.
   - Reject (regenerate from a fuller title, or ask the user) the
     reserved slugs, which name `artifacts/`'s root-level files and
     folders: `prd`, `prd-history`, `epics`, `architecture`,
     `decisions`, and `requirements-current` (`prd.md`,
     `prd-history.md`, `epics.md`, `architecture.md`, `.decisions.md`,
     `requirements-current.md`), plus `bugs`, `sprints`, `reviews`, and
     `diagrams` (the folders `vc-bug-report`, sprint planning, and the
     architecture skills write into), and `as-built-plan`
     (`vc-code-to-srs`'s `as-built-plan.json`). Also reject any slug starting with
     `epic-` or `feature-`. Every skill that generates a feature or epic
     slug applies this same list.
   - Requirement IDs drafted before the slug was final are renamed to
     it now (`FR-<slug>.<name>`).

8. **Check, preview and write the feature PRD**
   - **Self-check** the draft — gap, clarity, consistency, pre-mortem,
     inversion (`references/requirements-section.md`). Each finding is
     fixed in the draft or shown in the write preview.
   - **Write the draft** to `prd.draft.md` in the feature folder
     (`artifacts/<feature-slug>/prd.draft.md` for a new feature), using
     the template in `references/requirements-section.md`.
   - **Fresh-reader check** (skipped at Quick): follow
     `references/fresh-reader-check.md`.
   - **Conflict pass:** invoke `/vc:requirements conflicts <slug>`
     through the Skill tool once (it reads `prd.draft.md` in place of
     `prd.md` while the draft exists). Settle anything it raises the
     same way as during the interview.
   - **Write preview.** Show the target path, the section outline, every
     requirement ID with its one line, and then:
     - **Assumed defaults**: every value or behaviour filled in without
       the user saying it, numbered so the PO can reject each. Accepted →
       normal requirements; rejected → the PO's value or an Open Question.
     - Open markers (each answered now, or kept with a matching Open
       Question naming its ID), Open Questions, unfixed self-check
       findings, unresolved conflicts, new Decisions entries.
     - **Glossary proposals**: new domain terms the interview used that
       `docs/glossary.md` lacks (never IDs or generic tech words), as a
       diff of `| Term | Definition | Avoid | Owner |` rows. No glossary
       file yet → skip, and mention that `/vc:setup` creates it.
     Nothing the PO didn't see goes in as agreed. Write only on yes.
   - **Write** `artifacts/<feature-slug>/prd.md` from the approved draft
     with `status: draft`, plus only the glossary rows the user approved,
     then delete `prd.draft.md`. `epic_id`, `ado_id` and `last_synced`
     start `null` and are never this skill's to fill in later. Say the
     next step: `/vc:prd-clarify <feature-slug>`, where the team reads
     it and marks it `ready`; stories are written only after that.
   - **After every write** (here, Revision Mode, Review Mode, `done`,
     `clarify`, `migrate`), invoke `/vc:requirements check`, then
     `/vc:requirements view`, through the Skill tool. Fix errors it
     reports in the PRD just written and run `check` again; report
     errors in other files without touching them.
   - When the write added, retired or superseded an `FR-` or `ERR-` and
     the feature folder has an `approved` `ux/user-flow.md`, say the map
     is now out of date and suggest `/vc:define-user-flow <feature>`.

9. **Update the product PRD**
   - Append `- [<Title>](./<feature-slug>/prd.md)` under
     `artifacts/prd.md`'s **Features** section.
   - On a later run (product PRD already existed), also ask — don't
     assume — whether this feature changes anything at the product level
     (new goal, expanded target users, etc.). Edit those sections only on
     the user's confirmation, and log each confirmed change to
     `artifacts/prd-history.md` (format in `references/supersession.md`).

## Revision Mode

Revises an existing feature's PRD in place, wherever it lives. Reached
from step 1's confirmed match, or from step 0 with a conflict resolution
handed in. Load `references/supersession.md` and
`references/requirements-section.md`.

1. **Read** the PRD in full, its frontmatter `status`, and every
   `stories-*.md` in the folder (status and `Implements:`).
2. **Act on the state:**
   - `needs-review` → Review Mode instead.
   - `done` (or legacy `delivered`) → refuse the edit and say why.
     Offer `clarify <id>` when the meaning doesn't change, otherwise a
     new feature that supersedes the affected IDs: run steps 4-9 with `supersedes` and
     `## Changes to delivered features` filled in.
   - `draft` (or legacy `synced`, treated as draft) → continue.
   - `ready` → continue as for draft, but the write in step 8 sets
     `status: draft`, and the write preview lists the stories citing a
     changed, retired or replaced ID ("Revision Mode by state" in
     `references/supersession.md`).
   - `active` → continue as for draft; the status stays `active`. The
     write preview lists the not-done stories citing a changed, retired
     or replaced ID, so the team can re-check work in progress.
3. **Interview** what is changing, using step 5's rules at a depth that
   fits the size of the change. A handed-in resolution skips this: apply
   the exact change it names.
4. **Apply each change by the ID's state** ("When an ID can change" in
   `references/requirements-section.md`). A change in meaning to a cited
   ID gets a new ID, the old one retired `Replaced by <id>`. A built ID
   (a `done` story implements it) is never edited; when its replacement
   contradicts what's built, list the done stories affected and the
   not-done stories building on the old ID, and tell the user to hold
   them ("Built-requirement freeze" in `references/supersession.md`).
5. **Re-test the shape.** If the change grows the feature (a new
   capability, not a refinement), run step 6 again; step 4's split flow
   applies the same way.
6. **Conflict scout** each new or changed requirement as in step 5.
7. **Decisions.** When the PO picked between paths (here, or in the
   handed-in resolution), add the entry to `## Decisions`, newest first;
   for draft-vs-draft resolutions, in both PRDs. No other change log:
   never create or append to `## Revision History` (an older one stays
   as is).
8. **Step 8** from the self-check on: draft file, fresh-reader check
   (when the depth calls for it), conflict pass, write preview, write,
   `check` and `view`. Body sections always describe what is true now,
   never a diff. Frontmatter stays as is, except legacy `synced` →
   `draft` and `ready` → `draft`. After a `ready` → `draft` write, say
   the feature needs `/vc:prd-clarify <feature-slug>` again before more
   stories are written from it.
9. **Step 9's product-level question**, logging confirmed product
   changes to `artifacts/prd-history.md`.
10. **Architecture nudge.** Name the narrowest re-run that covers the
    change: `/vc:architecture-design <feature-slug>` when the feature
    has its own `architecture.md`, else its epic's or the whole-product
    run when one exists. `vc-architecture-design` reads `## Decisions`
    and `## Changes to delivered features` for the reason. A nudge, not
    an invocation; skip it when no spine exists at any scope.

## Review Mode (`/vc:prd review`)

Completes a `needs-review` stub PRD written by `vc-docs features` or
`vc-code-to-srs` into a real, interview-backed feature PRD, reusing
steps 5, 6, 8 and 9.

1. List every `prd.md` under `artifacts/` (both locations) with
   `status: needs-review`, or go straight to the one step 0's selector
   names. Empty → say there's nothing to review (suggest
   `/vc:docs features`) and stop.
2. Show title, slug and a one-line summary of its `## Evidence`; ask
   which one to review.
3. Treat its `## Overview` and `## Evidence` as pre-answered context:
   they count toward "Already have" and toward depth scoring. When the
   feature folder has `as-built/spec.md`, read it too: its ✅ rows are
   facts from the code, confirmed with the user in one pass rather than
   asked one by one; its 🔵 and 🟡 rows and its Open questions drive the
   interview. Its local IDs (`FR1`, `BR2`, `ERR3`) become named IDs
   (`FR-<slug>.<name>`) in the written PRD. Never edit the as-built
   pack.
4. Run steps 5 and 6 unchanged, skipping only what the evidence answers.
5. Run step 8, writing the completed template over the stub in place:
   fold `## Evidence`'s useful citations into `## Overview`/
   `## Touchpoints`, drop the stub framing, set `status: draft`.
6. Remove the ` (needs review)` suffix from its link in
   `artifacts/prd.md`, then run step 9's product-level question.

## Notes

- Output paths: `artifacts/prd.md`, `artifacts/prd-history.md`,
  `artifacts/<feature-slug>/prd.md` (new feature), an existing feature's
  `prd.md` wherever it lives (edited in place, never moved), the
  temporary `prd.draft.md` beside it, approved `docs/glossary.md` rows,
  and, through `apply_supersessions.py` on `done`, banners and
  `superseded` lists in older PRDs. Moving a feature under an epic is
  `vc-propose-epic`'s job.
- The one-sentence test runs here, not in `vc-propose-epic`, because
  this skill writes and can re-split a feature.
- Reads only `submodule_root` from `.vc/config.toml`; never writes it.
  Scouting is best-effort and silent; a product with no code is normal.
- Only `vc-docs features` and `vc-code-to-srs` write `needs-review`;
  only `done` writes `done`. This skill is the only writer of feature PRDs;
  `vc-requirements` finds problems and hands resolutions here.
