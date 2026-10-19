---
name: vc-docs
description: Scout every code submodule under src/ and generate or refresh two whole-project brownfield docs — docs/architecture.md and docs/project-overview.md — following this skill's own bundled templates. One shared doc pair for the whole project, never one per submodule. Always auto-splits a doc that grows too long — never asks first. Every `scan` and `refresh` run also proposes candidate features guessed from the code as needs-review stub PRDs for `/vc:prd review` to complete — run standalone via `features` mode too.
---

# Docs

Document a codebase that already exists, by reading it rather than by
interviewing anyone about it. This is the only vc skill that writes
under `docs/` — a second top-level tree alongside `artifacts/` (which
holds both the po-pm pipeline's business-level content and, under each
feature's own `tasks/` folder, `vc-tasks-breakdown`'s implementation
breakdown). This skill also writes one narrow, evidence-cited thing into
`artifacts/` itself — needs-review feature stubs, via step 6 — never a
complete PRD; that interview is still `vc-prd`'s alone.

It produces exactly two files, both directly under `docs/`, never one per
submodule: `docs/architecture.md` and `docs/project-overview.md`, each
following this skill's own bundled template
(`templates/architecture.md`, `templates/project-overview.md`, next to
this `SKILL.md`) heading for heading. A tracking repo can hold several
`src/<repo-name>/` submodules, but the picture these two documents give is
of the *system as a whole* — that's the point of keeping them singular
instead of a separate architecture/overview pair per submodule.

`docs/project-overview.md`'s `Goals` and `Success Criteria` sections cite
`artifacts/prd.md` when it exists instead of re-deriving them from code —
a codebase can tell you what it *does*, never what it's *for*. Everything
else in both documents comes from the code itself, evidenced, never
invented just to fill a template heading.

## Workflow

1. **Resolve the mode**
   - Parse `$ARGUMENTS` for a token matching `scan`, `refresh`, `brief`, or
     `features`; default `scan` when none is given. This skill takes no
     repo-name argument — it always covers every submodule under `src/`
     together, never just one.
   - `scan` when `docs/architecture.md` or `docs/project-overview.md`
     already has real (non-placeholder) content: silently redirect to
     step 4 (`refresh`) instead of rebuilding from scratch — never ask.
     A from-scratch rebuild only happens on a genuinely first-ever `scan`
     (neither file exists yet, or only has placeholder content); to force
     one later, remove `docs/architecture.md` and
     `docs/project-overview.md` (or their sharded folders) first, then
     run `scan` again.

2. **Sweep every submodule**
   - Read `.vc/config.toml`'s `submodule_root` (default `src` if the
     config or field is missing). List every immediate subdirectory
     containing a `.git` entry — that's the full sweep set for this run,
     always all of them, never a chosen subset.
   - None found → stop and tell the user there's nothing under
     `<submodule_root>` to document.
   - **Exactly one submodule**: sweep it inline yourself, following the
     steps below — spawn overhead isn't worth it for one.
   - **2+ submodules**: spawn the `vc-scout` subagent (shown as
     `vc:vc-scout` when installed through the plugin) in `sweep` mode
     once per submodule, in parallel. Cap concurrency at 5 at a time;
     give each call a 3-minute timeout. A submodule whose sweep times out is skipped and logged in
     the final report as "sweep timed out — re-run to retry" rather than
     blocking the rest.
   - **What a sweep covers**, whether run inline or by `vc-scout` (its
     own definition carries the same steps, so the shape of findings is
     identical either way): walk the submodule, skipping `.git`,
     dependency/cache/build directories (`node_modules`, `vendor`,
     `dist`, `build`, `__pycache__`, `.venv`, etc.) and anything its own
     `.gitignore` excludes; per top- and second-level directory, count
     files and LOC; identify its manifest(s) (language, framework,
     dependencies) and entry point(s); read any docs/README/ADRs already
     inside it as primary evidence; note anything that looks like a call
     into, or dependency on, another submodule (a config value, base URL,
     env var, or import naming another repo), citing where it was found;
     note anything that looks like a user-facing capability surface
     (route/controller definition, page/screen component, CLI command) a
     non-technical stakeholder would recognize as something they can do,
     citing file and a short label only — no feature title or grouping at
     this step, that's `features` mode's job in step 6.
   - Once every submodule's findings are in hand (inline or delegated),
     proceed to step 3, 4, or 5.

3. **`scan` — write both documents from scratch (first run only; step 1
   redirects any later `scan` to `refresh` instead)**
   - Fill this skill's own bundled `templates/architecture.md` into
     `docs/architecture.md`, same headings as the template, every
     bracketed placeholder replaced with real, evidenced content — or,
     where the sweeps found no evidence for something the template asks
     for, an explicit note that it's unresolved rather than an invented
     answer:
     - `Stack` — one table row per real layer found. With more than one
       submodule, group rows under a `### <repo-name>` subheading per
       submodule instead of flattening everything into one ambiguous
       table.
     - `System Boundaries` — one bullet per submodule (`src/<repo-name>/`)
       stating what it owns, plus its real internal folder boundaries.
       This is also where a call/dependency on another submodule belongs
       — e.g. "calls `<other-repo>` over its REST API for X" — cited to
       the evidence a sweep found. Never infer a connection from name
       similarity alone; a submodule with no evidenced connection is
       still listed, just without one claimed.
     - `Storage Model`, `Auth and Access Model` — aggregated across every
       submodule that has one; name which submodule owns which piece
       whenever there's more than one.
     - `Invariants` — cross-cutting rules the code actually enforces
       (found in validation, guards, middleware, CI checks), never
       aspirational rules; skip any the sweeps found no real evidence
       for rather than padding the list to match the template's count.
   - Fill this skill's own bundled `templates/project-overview.md` into
     `docs/project-overview.md`, same rule (every heading kept, every
     placeholder replaced or explicitly marked as a gap):
     - Title — the project name from `artifacts/prd.md`'s own title if
       it exists, else `.vc/config.toml`'s `ado.project`, else the
       tracking repo's own folder name.
     - `Overview` — what the system actually does today, from the
       sweeps; cross-check against `artifacts/prd.md` if present, but
       describe the *as-built* system, not the aspirational one.
     - `Goals`, `Success Criteria` — if `artifacts/prd.md` exists, cite
       its Product Goals (or equivalent) instead of re-deriving them from
       code; if it doesn't exist, write "_No product goals recorded yet —
       run `/vc:prd` or add them here._" rather than guessing at intent
       from code alone.
     - `Core User Flow` — the primary route(s)/entry point(s) the sweeps
       found, traced end to end wherever there's enough evidence to trace
       it; leave a step as a gap note rather than inventing a plausible
       one.
     - `Features` — feature categories inferred from the real module/
       route/page structure the sweeps found.
     - `Scope` (`In Scope` / `Out of Scope`) — In Scope from what's
       actually implemented; Out of Scope only from explicit evidence (a
       code comment, a TODO, or the PRD's own Out of Scope) — omit the
       subsection entirely rather than invent an absence with nothing
       backing it.
   - Give both files frontmatter: `generated_at`, `mode: scan`,
     `submodules` (the list swept).
   - Apply **Auto-split** (below) to both.
   - Then run step 6 (**`features`**) using this run's sweep results —
     never a second sweep. Always, not just on request: propose candidate
     features from the evidence and write confirmed ones as needs-review
     stubs.
   - Then run step 7 (**Glossary terms**) on the same evidence.
   - Report the resulting files and a one-line summary (submodules
     swept, languages/frameworks found, anything flagged as a gap),
     followed by step 6's own feature-candidate summary and step 7's
     glossary result.

4. **`refresh` — update both after code changes**
   - Requires `docs/architecture.md` and `docs/project-overview.md` (or
     their sharded folders) to already exist; if not, tell the user to
     run `scan` first.
   - Re-sweep every submodule and diff against what's already recorded —
     a new or removed submodule, a new manifest dependency, a large LOC
     swing, a newly evidenced connection between submodules. Leave a
     section alone whose backing evidence hasn't moved.
   - Update only the affected sections/subheadings in each document (or
     the specific shard that owns that part) — append what's new,
     correct what's stale, never delete a section still backed by
     evidence just because nothing changed there this run.
   - Anything in `$ARGUMENTS` beyond the mode is an extra focus area for
     this pass (e.g. "focus on the auth boundary").
   - Apply **Auto-split** to whichever file(s) changed.
   - Then run step 6 (**`features`**) using this run's re-sweep results —
     never a second sweep. Always, not just on request: propose candidate
     features from the evidence (its own dedup against already-tracked
     features means a routine refresh with nothing new usually reports
     zero candidates) and write confirmed ones as needs-review stubs.
   - Then run step 7 (**Glossary terms**) on the same evidence.
   - Report which sections changed and why, one line each, followed by
     step 6's own feature-candidate summary and step 7's glossary result.

5. **`brief` — fast orientation pass, no file writes**
   - Runs the sweep (step 2) only. Writes nothing — doesn't touch
     `docs/architecture.md`, `docs/project-overview.md`, or their shards.
   - Answers in chat with a short summary: submodules found, language/
     framework per submodule, and anything that looks newly added since
     the last `scan`/`refresh`. For "just get me oriented fast" — run
     `scan` or `refresh` when the documents themselves need updating.

6. **`features` — propose candidate features from swept evidence**
   - Always runs at the end of `scan` and `refresh` (using that run's own
     sweep, never a second one), and is also directly invocable on its own
     (`/vc:docs features`) when you want only this, without a docs
     rebuild — same logic either way, this is the one place it's defined.
   - Aggregate every submodule's `Possible feature surfaces` findings from
     step 2's sweep.
   - Read `artifacts/prd.md`'s Features section (if it exists) and every
     existing `prd.md` title under `artifacts/` — drop any surface that
     clearly maps to an already-tracked feature; cite which existing
     feature it matches instead of re-proposing it.
   - Group the remaining surfaces into candidates, one user-recognizable
     capability each — merge multiple related surfaces into one candidate,
     keep unrelated ones separate.
   - **Present the full candidate list and wait for confirmation before
     writing anything**: title guess, one-line evidence citation, source
     submodule(s), per candidate. Let the user drop, merge, split, or
     rename any before proceeding — never write a stub the user hasn't
     seen.
   - For each confirmed candidate, generate a feature slug (same
     kebab-case + `-2`/`-3` collision rule `vc-prd` uses; same
     reserved-slug list as `vc-prd` step 7) and write `artifacts/<feature-slug>/prd.md`:
     ```markdown
     ---
     id: FEATURE-<feature-slug>
     epic_id: null
     ado_id: null
     last_synced: null
     status: needs-review
     ---

     # Feature PRD: <Title guess>

     ## Overview
     _Guessed from code — not yet reviewed. Run `/vc:prd review` to
     confirm and fill in the rest._

     <one or two sentences from the evidence, e.g. "Found in
     `src/<repo>/...`: <route/page/module list>.">

     ## Evidence
     - <surface> — `<file>` (submodule: `<repo-name>`)

     ## Problem / Motivation
     _Not yet reviewed._

     ## Target Users
     _Not yet reviewed._

     ## Success Criteria
     - _Not yet reviewed._

     ## Acceptance Criteria
     - _Not yet reviewed._

     ## Scope

     ### In Scope
     - ... (only what's confidently evidenced; omit and leave for review
       otherwise)

     ### Out of Scope
     _Not yet reviewed._

     ## Constraints
     _Not yet reviewed._

     ## Touchpoints
     - ... (submodule(s) this evidence came from)

     ## Requirements

     ## Open Questions

     ## Decisions
     ```
     `## Requirements`, `## Open Questions` and `## Decisions` stay empty
     headings: requirement IDs come only from the `vc-prd` interview
     (`/vc:prd review`), never guessed from code.
     This is deliberately a different shape from a normal completed
     feature PRD — the `## Evidence` section and the `_Not yet
     reviewed._` placeholders (instead of `...`) make a stub visually
     distinguishable from a real PRD on sight.
   - Append each to `artifacts/prd.md`'s Features section:
     `- [<Title>](./<feature-slug>/prd.md) (needs review)`. If
     `artifacts/prd.md` doesn't exist yet, bootstrap it first using
     `vc-prd`'s own product-PRD shape, but with every interview-derived
     section (Overview, Problem Statement, Target Users, Product Goals)
     filled with a gap note in the style `docs/project-overview.md`
     already uses: "_No product goals recorded yet — run `/vc:prd` or
     add them here._" — never inventing product-level content from code.
   - Report a summary: candidates written, candidates skipped as
     already-tracked, and remind the user to run
     `/vc:prd review <feature-slug>` on each new one. For a stub whose
     code is substantial, suggest `/vc:code-to-srs <feature-slug>`
     first: it documents the feature's code in depth so the review
     confirms facts instead of discovering them.

7. **Glossary terms — propose, never write silently**
   - Runs at the end of `scan` and `refresh` only (not `brief` or
     standalone `features`), on that run's evidence: code identifiers and
     docs that name a domain concept (entity and status names, route and
     page labels, README and ADR wording, PRD text under `artifacts/`).
   - Read `docs/glossary.md` (missing → skip this step and suggest
     `/vc:setup`, which creates it). Keep only domain terms the glossary
     doesn't already have as a term or as an alias to avoid: no
     requirement or work item IDs, no generic technical words (API,
     service, table, button). Also flag a word used as an alias to avoid
     in the glossary but found in new docs.
   - Nothing new → one line in the report, write nothing.
   - Otherwise show the proposed rows as a diff against the glossary
     table (`+ | <Term> | <definition from the evidence> | <aliases seen> | |`,
     with the evidence file per row) and ask via `AskUserQuestion`: add
     all, pick some, or none. Write only the approved rows, appended to
     the table, never reordering or changing existing rows. Owner stays
     blank for the user to fill.

## Auto-split (always, every mode — never a question to the user)

After writing or updating `docs/architecture.md` or
`docs/project-overview.md` (the only two files this skill ever produces):

1. Count its lines. Read `.vc/config.toml`'s `docs.max_loc` (default
   `400` if the config or field is missing).
2. If it's under the limit, leave it as a flat file.
3. If it's over the limit, shard it immediately:
   - Turn `docs/architecture.md` into `docs/architecture/` (or
     `docs/project-overview.md` into `docs/project-overview/`) containing
     an `index.md` (frontmatter, a short overview, and a linked list of
     the shards in order) plus one `NN-<section-slug>.md` per top-level
     `##` section from the template, numbered in the template's order.
   - Delete the flat file once every section has moved into a shard.
   - On a later `refresh`, edit the one shard whose section changed
     instead of touching the rest; re-shard further only if that
     individual shard itself now exceeds the limit.
4. Never ask first, and never leave an oversized flat file in place — the
   split happens as part of writing the doc, and gets one line in the
   final report ("split `architecture.md` into `architecture/` — 5
   sections").

## Notes

- Bundled templates are the source of truth for shape: this skill ships
  its own `templates/architecture.md` and `templates/project-overview.md`
  (`skills/delivery/vc-docs/templates/`). The two documents it ever writes
  follow these heading for heading — to change what this skill outputs,
  edit the templates, not the prose in this file.
- One document pair for the whole project, never one per submodule.
- Depends on the `vc-scout` agent, shipped in the repo's top-level
  `agents/vc-scout.md` and installed with the plugin or the file
  install — it's a plain Task-tool
  subagent, not another skill, shared by every `vc-*` skill that reads
  code. This skill uses its `sweep` mode: pinned to Haiku so fanning it
  out across several submodules stays cheap, and scoped narrowly enough
  (read-only, one submodule, one report, no delegating further) that it
  shouldn't get invoked outside a vc skill's scouting step.
- Reads `submodule_root` and `docs.max_loc` from `.vc/config.toml` when
  present; never writes to that file — that's `vc-setup`'s job alone.
- Never touches a submodule's git state (no commits, no pointer changes,
  not even a read-only `git log` beyond what the sweep needs) and never
  edits any file inside `src/<repo-name>/` itself, including its
  `README.md`.
- For docs content, cites `artifacts/prd.md` for `Goals`/`Success
  Criteria` but never edits it, and never writes to any feature's
  `tasks/` folder — that's `vc-tasks-breakdown`'s alone.
- `scan` and `refresh` (always) and `features` (standalone) are this
  skill's one deliberate exception to the docs/-only rule: step 6 writes
  new `artifacts/<feature-slug>/prd.md` stubs and appends to
  `artifacts/prd.md`'s Features section, always evidence-cited and always
  marked `status: needs-review` — it never writes a complete PRD itself,
  that's `vc-prd review`'s job. `brief` never triggers step 6; it writes
  nothing at all, consistent with its own definition.
- `docs/glossary.md` is edited by hand. Step 7 only appends rows the user
  approved in the diff it showed; it never edits or removes an existing
  entry and never writes the glossary without that approval.
