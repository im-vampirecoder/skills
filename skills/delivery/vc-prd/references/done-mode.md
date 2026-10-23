# `done` and `clarify`

Load this for `/vc:prd done <feature>` and `/vc:prd clarify <id>`.
`deliver <feature>` is the old name of `done` and still works until
0.4.0 (added in 0.3.0): run `done` and tell the user the new name.

## `done <feature>`

The lock point. A feature is `done` when all its stories are `done`
and the PO confirms. `vc-implement` offers this after it closes the
last story; the user can also run it by hand. `done` means built and
frozen, not "live in production": releases are recorded separately.

1. **Find the feature.** `<feature>` is a slug or `FEATURE-<slug>`. Look
   in `artifacts/<slug>/prd.md` and `artifacts/epic-*/feature-<slug>/prd.md`.
   Not found → say so and stop. Already `done` (or legacy `delivered`)
   → say when (the `done_on` date, or the legacy `delivered` one) and
   stop. `needs-review` → refuse; it has to go through `/vc:prd review`
   and stories first. `active` is the normal state here. `draft` or
   `ready` (a feature built before `active` existed, or whose stories
   were started outside `/vc:implement`) → say which status it skips and
   continue; the PO's confirmation in step 4 covers it.
2. **Check the stories.** Read every `stories-*.md` in the feature
   folder. No stories → stop: there is nothing to say was built. Any
   story not `done` (ignore `removed`) → list them with their status and
   stop.
3. **Check what freezes.** Invoke `/vc:requirements check` through the
   Skill tool. Errors in this feature's PRD block `done`: fix them
   first through Revision Mode. Then show:
   - open `[NEEDS CLARIFICATION]` markers: these block `done`, because
     a `done` PRD can't be edited to answer them. Resolve each through
     Revision Mode first;
   - Open Questions still listed: ask the PO to answer them now (Revision
     Mode) or confirm they stay as a record of what was never decided;
   - P0 FRs with no story implementing them.
4. **Show what `done` does** and ask the PO to confirm:
   - the feature and its story count,
   - that every requirement in it freezes: later changes need a new
     superseding feature, or `clarify` when the meaning doesn't change,
   - when the frontmatter has `supersedes`: run
     `python3 <skill-dir>/scripts/apply_supersessions.py --root . --feature <slug> --dry-run`
     and show which IDs in which PRDs it would mark.
   Only an explicit yes from the PO continues. Anything else stops with
   nothing written.
5. **Write the frontmatter.** `status: done` and `done_on: <today>`; a
   legacy `delivered:` line is replaced by `done_on`. Nothing else in the
   PRD changes.
6. **Apply supersessions** when `supersedes` is present:
   `python3 <skill-dir>/scripts/apply_supersessions.py --root . --feature <slug>`.
   `<skill-dir>` is this skill's folder; run from the tracking repo root.
   It is idempotent, so a rerun after a failure is safe.
7. **Mark it in the product PRD.** Append ` (done)` to the feature's
   link line under `## Features` in `artifacts/prd.md` (once; not logged
   in `prd-history.md`).
8. **Refresh the requirements.** Invoke `/vc:requirements check`, then
   `/vc:requirements view`, through the Skill tool.
9. **Tell the user** what was frozen and marked, and that the next
   `/vc:sync-to-tracker <feature>` moves the tracker Feature to its
   done state.

## `clarify <id>`

For a requirement that turned out unclear, not wrong: a bug or a
question showed two readings, and the built system's intended behaviour
stays the same. Allowed in a `done` PRD and on a built requirement in
a draft one. An uncited, unbuilt requirement in a draft is just edited
in Revision Mode instead.

1. **Find the requirement.** The feature slug is the part of the ID
   between the type and the dot. Read that feature's PRD and find the
   definition line. Not found → say so, suggest
   `/vc:requirements check`, and stop. Retired or superseded → say so
   and name its replacement; clarify the replacement instead.
2. **Show it** with any lines already under it, and ask what was unclear
   and where it came from (a bug ID such as `BUG-<slug>`, a test case, a
   person and role).
3. **Ask:** "Does this change what the built system should do?"
   - **Yes** → it isn't a clarification. `done` feature: offer a new
     superseding feature (`supersession.md`). Draft feature with a built
     ID: Revision Mode, new ID, retire the old one, and the hold-stories
     check.
   - **No** → continue.
4. **Write one line** directly under the requirement, after any existing
   `>` lines:

   ```markdown
   > Clarified on <date>: <detail> — <source>
   ```

   The detail is one sentence and states how to read the requirement,
   never a new behaviour. The original text is never edited.
5. Invoke `/vc:requirements check`, then `view`, through the Skill tool.
6. **Tell the user** the ID is unchanged, stories citing it stay valid,
   and test cases citing it will be flagged for review the next time
   `/vc:create-test-cases` runs (through `changed_sources`).
