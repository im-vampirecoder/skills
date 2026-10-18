---
name: vc-bug-report
description: Interview the user through the bug-triage report template and severity rubric, then write a local bug file. Never syncs to a tracker itself — that's a separate `/vc:sync-to-tracker bug [bug-id]` step.
---

# Bug Report

Interview the user to file a bug, following the template and severity
rubric in the project's bug-triage process, then write it as a local
file. This skill never talks to Azure DevOps — syncing is
`vc-sync-to-tracker`'s job, run separately once the report is written.

## Workflow

1. **Interview**
   - Cover these topics, one question at a time — rephrase, reorder, or
     skip any `$ARGUMENTS` already answers clearly, same flexibility rule
     `vc-prd` applies to its own interview:
     - Title: a short description of the issue.
     - Steps to Reproduce: numbered, concrete steps.
     - Expected Result: what should happen.
     - Actual Result: what actually happens.
     - Environment: browser, OS, deployment slot, API version — whichever
       actually apply; skip a sub-field that doesn't fit this bug (e.g. no
       "Browser" for a pure backend/API bug).
     - Screenshots/Logs: optional — a file path, a pasted log snippet, or
       a description of what evidence exists. Never block on this being
       empty.
     - Feature/Epic this affects (optional): ask if there's a product
       Feature or Epic this bug relates to; a standalone bug with no
       named parent is a normal, valid answer, never required.
     - Requirement behind the expected result (only when a feature was
       named and its `prd.md` has a `## Requirements` section): find the
       live `FR-` / `BR-` / `ERR-` entry the Expected Result relies on and
       quote it back. If the feature is `status: delivered` and the
       requirement's text supports both the expected and the actual
       behaviour (unclear rather than wrong), note it for step 6.
   - **No blackbox answers.** Same rule `vc-prd` uses: a vague, hedged,
     or partial answer ("probably the login page, not sure") gets one
     targeted follow-up before moving on, never gets written in verbatim.

2. **Severity — ask via `AskUserQuestion`, using the project's own rubric**
   - Present the four levels with their real definitions and examples
     from the bug-triage doc, not a generic guess:
     - **Critical** — System down, data loss, no workaround (e.g. login
       broken for all users, messages lost, platform unreachable).
     - **High** — Major feature broken, workaround exists (e.g. chat
       export fails but data accessible via API, bot responses delayed
       >30s).
     - **Medium** — Minor feature issue, low user impact (e.g. sorting
       not working on one column, tooltip shows wrong text).
     - **Low** — Cosmetic, typo, nice-to-have fix (e.g. misaligned icon,
       spelling error in settings page).
   - Frame it as the reporter's best judgment, not a final call — per the
     doc, this gets sanity-checked by the SM and a dev before it drives
     any Fast Path/Weekly Triage routing. This skill doesn't simulate
     that check, it just records the initial severity.

3. **Fast Path nudge (Critical/High only)**
   - If the chosen severity is Critical or High, tell the user in plain
     text: per the bug-triage process, also ping the SM directly (Teams)
     for a suspected Critical/High bug — don't wait for standup. This
     skill has no Teams integration; it's a reminder, not an action.

4. **Generate the bug slug**
   - kebab-case the title. If it collides with an existing
     `artifacts/bugs/<slug>.md`, suffix `-2`, `-3`, etc.

5. **Write the bug file**
   - Path: `artifacts/bugs/<bug-slug>.md` (create `artifacts/bugs/` if
     needed) — its own folder, not nested under an epic/feature, since a
     bug may be standalone.
   - Content:
     ```markdown
     ---
     id: BUG-<bug-slug>
     epic_id: null
     feature_id: null
     ado_id: null
     last_synced: null
     severity: Critical | High | Medium | Low
     status: new
     iteration: null
     ---

     # Bug: <Title>

     **Steps to Reproduce:**
     1. ...
     2. ...

     **Expected Result:** ...

     **Actual Result:** ...

     **Environment:** ...

     **Screenshots/Logs:** ...

     **Severity:** <Critical | High | Medium | Low>
     ```
   - `epic_id`/`feature_id`: set to `EPIC-<epic-slug>`/`FEATURE-<feature-slug>`
     when step 1 named one (resolve it the same way other vc skills
     resolve a feature identifier); otherwise leave both `null`. These
     become an optional Related link at sync time — never the bug's
     hierarchical parent, see `vc-sync-to-tracker`'s own bug-sync
     section for that distinction.
   - `ado_id`/`last_synced` start `null` — this skill never syncs.
   - `status`/`iteration` are the same sprint-tracking fields stories
     carry (see `vc-create-user-stories` step 6 for the values). Always
     `new` / `null` here. Only a `ready` bug can be planned into a sprint
     by `vc-plan-sprint-candidates`; a bug-triage skill will make that
     call later, until then the PO sets `status: ready` by hand.

6. **Report and offer the handoff**
   - Give the file path, the bug's `id`, and its severity. Then ask via
     `AskUserQuestion` what to do next — never invoke any of these
     automatically:
     - "Sync this bug to the tracker
       (`/vc:sync-to-tracker bug BUG-<bug-slug>`)" (Recommended)
     - "Fix it now (`/vc:implement BUG-<bug-slug>`)"
     - "Done for now"
   - When step 1 found the bug traces to an unclear requirement of a
     delivered feature, also suggest
     `/vc:prd clarify <requirement-id>` in the report, so the PO can
     settle what the requirement means (a `> Clarified on` line when the
     built behaviour stays, a superseding feature when it changes) before
     anyone fixes toward a guess. A suggestion only; never invoke it.

## Notes

- Writes only under `artifacts/bugs/` — never touches `docs/`,
  `specs/`... there is no `specs/` tree anymore, and never any
  `epic-*/feature-*/` folder either, since a bug isn't part of the
  Epic → Feature → Story → Task hierarchy those trees hold.
- No delegation branch — always runs its own interview, same as
  `vc-prd` and `vc-create-user-stories`.
- Never creates or updates anything in Azure DevOps. `vc-sync-to-tracker`
  owns that, including finding (and always confirming) the "Bug Triage" >
  "Inbox" parent every bug gets filed under.
