# `migrate [feature]`

Load this for `/vc:prd migrate [feature]`. It adds a `## Requirements`
section with named IDs to a feature PRD written before they existed, so
stories, test cases and later features can cite it.

1. **Pick the PRDs.** With a feature slug, take that PRD. Without one,
   list every feature PRD under `artifacts/` (both locations) that has no
   `## Requirements` section, skipping `needs-review` stubs (those go
   through `/vc:prd review`). Show title, slug and status, and ask
   which to migrate: one, several or all. Migrate them one at a time.
   Nothing to migrate → say so and stop.
2. **Read everything about the feature**: the PRD in full, its
   `stories-*.md`, `ux/ux-spec.md` and `test-cases/` when present, and
   `docs/glossary.md`.
3. **Derive the requirements** from what is already written, using the
   formats in `requirements-section.md`:
   - FRs from Overview, In Scope, Acceptance Criteria and the stories'
     own criteria; P0/P1/P2 from what the PRD and stories say about
     priority;
   - NFRs and BRs from Constraints and any rules stated anywhere;
   - ERRs from failure cases in criteria, mockups and test cases;
   - old numbered requirements (`R1`, `FR12`): give each a named ID and
     keep the number as an alias, `(P0, FR12)`.
   Note where each one came from, for the preview.
4. **Interview only for gaps**, using `interview-depth.md`'s rules at
   Quick depth (no playback, no fresh-reader check): a missing priority,
   a P0 FR that can fail with no ERR, an NFR stated as an implementation
   choice, a vague value, a word that should be a glossary term. One
   follow-up per vague answer, then `TBD` or a marker. Never re-ask what
   the PRD already says.
5. **`done` features** are frozen, so migration only restates what
   the PRD and the built stories already say. No gap interview, no new
   behaviour, no Open Questions added; gaps are listed in the console
   instead. Leave `status` and `done_on` (or legacy `delivered`) as
   they are (add `done_on: null` only to a draft that lacks the field).
6. **Keep the old Revision History** exactly as it is: not converted,
   not moved, not removed. From now on changes go through Revision Mode
   and `## Decisions`. Don't add other new sections unless a gap answer
   needs one (for example `### Anti-goals`).
7. **Preview** the full `## Requirements` section with each ID's source
   line, the assumed defaults, and any glossary proposals. Write only on
   the PO's yes.
8. **After writing**, invoke `/vc:requirements check`, then `view`,
   through the Skill tool, and fix errors in the PRD just migrated.
9. **Tell the user** which stories have no `Implements:` line yet. Story
   files belong to the story skills, so this skill doesn't add the line
   itself.
