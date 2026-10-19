---
name: vc-code-to-srs
description: Document what a brownfield codebase already does, feature by feature, before the PO interview - an as-built pack per feature (spec with every claim labelled ✅ stated by code / 🔵 corroborated / 🟡 inferred and cited to path:line, plus evidence trace, flows, states, ERD and use cases), mined from routes, validators, tests, message catalogs and dead-code checks across the configured submodules. Writes <feature folder>/as-built/ and a needs-review PRD stub (or links an existing stub) so /vc:prd review starts from evidence. Never edits code, a real PRD or the tracker. Triggered by /vc:code-to-srs.
---

# Code to SRS

On a brownfield project, write down what the code already does before
anyone interviews the PO. Each feature gets an as-built pack under its
feature folder, and a `needs-review` stub PRD that points at it, so
`/vc:prd review` confirms facts instead of discovering them.

## Ground rules

- **Code is the evidence; the user is not asked about the business.**
  What the code doesn't say becomes an open question in the pack. The
  only questions this skill asks are where to read (when there is no
  config), which features to do now (step 3), and whether to write
  (step 6).
- **Labels are asymmetric.** Code proves *how*, never *why* or *for
  whom*: `references/labels-and-framing.md`. Never upgrade intent to ✅
  because the code was read.
- **Business words.** Code names appear only in citations and in
  `evidence.md`.
- **Read-only code.** Read inside `submodule_root` (`.vc/config.toml`,
  default `src`) only; never write there, run, build or test anything,
  or touch submodule git state beyond `git rev-parse`. Env variable
  names only, never values; never open `.env` files.
- **Local IDs only.** The pack numbers its own items `FR1`, `NFR1`,
  `BR1`, `ERR1`, `OQ1`. Named `FR-<slug>.<name>` IDs are minted only by
  `/vc:prd review`, so `/vc:requirements check` never sees the pack's
  items as dangling requirements.
- **Self-contained output.** Pack files never name this skill, a tool, a
  vendor, or how they were produced.
- **Never edits** application code, a `draft` or `delivered` PRD,
  stories, or the tracker.
- **Scripts.** `<skill-dir>` is this skill's folder; run from the
  tracking repo root:
  `python3 <skill-dir>/scripts/as_built_plan.py <command>` (manifest:
  `init --from <file>`, `validate`, `set-status`, `next-batch`,
  `status`, `commits`, `folder <slug>`) and
  `python3 <skill-dir>/scripts/check_as_built.py check <pack-dir>`.
- **Language.** Discuss in the user's language; write the pack in
  English, quoting UI and error text as the code has it.

## `status` (read-only)

Run `as_built_plan.py status` and report per feature: status, pack
path, a leftover `.draft/` (a `partial` feature, not a finished pack),
and stale packs (a submodule's commit moved since the pack was
written). Suggest `refresh <feature>` for stale ones and a plain run for
`pending` / `deferred` ones. Writes nothing.

## Workflow

0. **Resolve the run**
   - First token `status` → the mode above, then stop. `refresh
     <feature>` → steps 4-7 for that one feature (its manifest entry must
     exist), diffing against the current pack in step 6.
   - Read `.vc/config.toml`. No config, or no cloned repo under
     `submodule_root` → stop and point to `/vc:setup` (or `vc-setup
     reinit` after a fresh checkout).
   - The rest of `$ARGUMENTS`: empty → every cloned submodule; a path
     under `submodule_root` → only that repo or sub-folder; a feature slug
     → that feature only (from the manifest, or found in step 2).
   - `artifacts/as-built-plan.json` exists → run `as_built_plan.py
     validate`; `pending` entries are offered first ("continue the N
     pending features, or look for new ones too?"). A `done` feature
     whose submodule commits haven't moved is reported "up to date" and
     skipped unless named.

1. **Map the code**
   - One submodule: sweep it in this session. Two or more: spawn one
     `vc-scout` subagent per submodule in `sweep` mode, in parallel
     (shown as `vc:vc-scout` when installed through the plugin);
     without subagent support, sweep each inline, one after another.
   - Per submodule, note the stack and load the matching recipe file:
     `references/recipes-dotnet.md`, `references/recipes-js-ts.md`,
     `references/recipes-mobile.md`, always with
     `references/recipes-cross-stack.md`. No match → the cross-stack
     file's "Unknown stack" route, and say coverage is lower.
   - Nothing recognisable (no manifest, no entry point, no route or
     screen) → stop and say what was searched.

2. **Find the candidates** — `references/feature-clustering.md`: list
   every entry point with the stack recipe, group by call and data
   evidence across submodules, set complexity flags, separate shared
   infrastructure and suspect (dead or flagged-off) surfaces, and match
   each candidate to existing features by meaning.

3. **Confirm the list (hard stop)**
   - Show the candidate table and the size line from
     `feature-clustering.md`; apply its scope gate on a large run. Wait
     for the user's edits and choice.
   - Write the confirmed list to a temporary JSON file and run
     `as_built_plan.py init --from <file>`; fix and re-run until it
     validates (slug, reserved names, collisions, sources). Chosen
     features are `pending`, the rest `deferred`. Delete the temporary
     file.

4. **Draft, a batch at a time**
   - `as_built_plan.py next-batch --size 3`. For each feature, spawn the
     `vc-srs-drafter` subagent (in parallel within the batch), giving
     it the manifest entry, the recipe files for its stacks, the
     templates in `references/templates/`, `labels-and-framing.md`, and
     `docs/glossary.md`. Without subagent support, draft each feature in
     this session, one at a time, from the same inputs.
   - The drafter returns every pack file as text and writes nothing.
     Stage the files in `<feature folder>/as-built/.draft/` (folder from
     `as_built_plan.py folder <slug>`), with `sources` in the spec
     frontmatter taken from `as_built_plan.py commits` (only the
     submodules the pack cites) and `generated_at` today.
   - Run `check_as_built.py check <.draft dir> --no-compile`. Errors →
     send the findings back for one redraft. Still failing → set the
     feature `partial` (`as_built_plan.py set-status`), keep the
     `.draft/`, report it, and go on to the next feature.

5. **Audit** — `references/audit-rubric.md`: the `vc-srs-auditor`
   subagent per drafted feature (in parallel), or a separate cold pass
   in this session. Apply its changes to the staged draft, update the
   label and open-question counts, and re-run the check. A `fail`
   verdict gets one redraft; then the same `partial` rule as step 4.

6. **Preview and write (hard stop per batch)**
   - In plain language, per feature: one or two lines on what the code
     shows, the label counts (✅ / 🔵 / 🟡), the number of open questions,
     anything suspect (dead paths, skipped tests, unresolved wording), and
     what happens to its PRD (new stub, link added to an existing stub,
     or none because a real PRD exists). For `refresh`, show the diff
     against the current pack instead.
   - Write only on an explicit yes. Then: replace `as-built/` with the
     draft (move the files, delete `.draft/`); write or update the PRD
     stub per `references/prd-stub.md` (show the diff first for an
     existing file); set the feature `done`.
   - Ask whether to continue with the next batch or stop. Stopping keeps
     the rest `pending`, resumable by a later run.

7. **Verify and report**
   - Run `check_as_built.py check <feature folder>/as-built` on each
     written pack (with the Mermaid compile). Fix and re-check at most
     twice. Report each level on its own line as the script prints it:
     structure, citations, ids, renderer, self-containment, compile
     (`skipped (no Node)` is not OK, say so), business correctness
     (always "not machine-checked").
   - Then a summary: features written (each with its label counts),
     `partial` and `deferred` counts, stubs created and updated,
     cross-repo hops found, open questions waiting for the PO.
   - Next step: `/vc:prd review <feature>` for each stub (it reads the
     pack, confirms the ✅ facts in one pass and interviews on the rest).
     A remaining `deferred` or `pending` count → run `/vc:code-to-srs`
     again to continue.

## Notes

- Files: `<feature folder>/as-built/` (`spec.md`, `evidence.md`,
  `flows.md`, `states.md`, `erd.md`, `use-cases/index.md`,
  `use-cases/uc-<slug>.md`), the feature's `prd.md` stub,
  `artifacts/prd.md` (one Features line per new stub) and
  `artifacts/as-built-plan.json`. `states.md` / `erd.md` are omitted, with
  the reason in the spec, when the code has no multi-state entity / no
  stored data.
- The pack lives inside the feature folder, so `/vc:propose-epic`
  moving the feature carries it along.
- `/vc:docs features` also writes stubs from a lighter sweep; both
  skills match existing features by meaning, so a stub from one is
  adopted by the other rather than duplicated.
- The pack is never promoted or edited by other skills; `/vc:prd
  review` reads it and writes the PRD. Re-running this skill on a
  feature replaces only its `as-built/` folder.
