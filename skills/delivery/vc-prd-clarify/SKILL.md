---
name: vc-prd-clarify
description: Interview a TA, SM, DEV, or QA on a feature PRD so they actually read and understand it, rather than relying on an LLM summary — quiz them section by section, compare each answer to the PRD text, collect the gaps, then offer a clarification questionnaire for the PO/BA. Triggered by /vc:prd-clarify. Console-only by default; writes files only when the user opts in.
---

# PRD Clarify

Make sure the person who has to build, test, plan, or architect a feature
understands its PRD the way the PO/BA wrote it — and surface where the PRD
itself is unclear. The user reads the PRD; this skill quizzes them on it,
reveals what the PRD actually says after each answer, and records every
gap between the two.

This is an interview, not a summary service. The skill never hands over
section content before the user has answered a question on it — reading
the PRD is the user's job, checking it is the skill's.

## Ground rules

- **Input is a PRD in `artifacts/` only.** An external file (`.docx`,
  `.pdf`, a URL, pasted text, meeting notes) is out of scope — stop and
  tell the user to turn it into a PRD first, e.g.
  `/vc:prd Read <file-path>, it contains the feature design from my
  meeting with stakeholders, and write a new PRD (or edit the existing one
  if it matches/extends one)`, then re-run this skill on the result.
- **Console only by default.** The running gap log lives in the
  conversation. Nothing is written to disk unless the user says yes at one
  of the explicit offers (steps 6, 7 and 8, or when pausing early).
- **Never sends anything.** No email, no tracker comment, no wiki page —
  the questionnaire is shown and, optionally, saved; sending it is the
  user's call.
- **Never edits the PRD's content.** Gaps go to the PO/BA; updating the
  PRD afterwards is `vc-prd`'s job. The only edit is the PRD's
  frontmatter `status: ready` line from step 8.

## Workflow

0. **Resolve the PRD**
   - `$ARGUMENTS` → a feature slug (resolve `artifacts/<slug>/prd.md` or
     `artifacts/epic-*/feature-<slug>/prd.md`), `FEATURE-<slug>`, or a path
     to a `prd.md` under `artifacts/`. Strip `--quick` first (see step 3).
   - Empty → list every feature `prd.md` under `artifacts/` (title, slug,
     `status`) and ask which one. None found → tell the user to run
     `/vc:prd` first and stop.
   - Anything that isn't a PRD under `artifacts/` → apply the ground rule
     above and stop.
   - A `status: needs-review` stub → warn that it's an unconfirmed guess
     from code (`/vc:prd review` completes it) and ask whether to
     continue anyway.
   - Also read `artifacts/prd.md` (product PRD) if present, as context
     only — never quiz on it.

1. **Ask the user's role**
   - `AskUserQuestion`, single select: TA (Technical Architect), SM (Scrum
     Master), DEV, QA. The role shifts which questions get asked — see
     `references/question-design.md`'s role lens table. It never changes
     the classification rules.

2. **Silent analysis (not shown to the user)**
   - Split the PRD into its sections.
   - For each section, list the checkable facts: rules, flows, roles,
     thresholds/limits/numbers, scope edges, acceptance criteria. The
     `## Requirements` section counts as one section per subsection that
     has entries (Functional, Non-functional, Business rules, Errors, and
     any State transitions / Interrupted flows / Scenarios table), each
     fact tied to its full requirement ID.
   - Separately, note your own suspected PRD gaps: undefined terms,
     missing edge cases or error paths, contradictions between sections,
     untestable criteria, unstated NFRs. In the Requirements section also
     look for: a P0 FR that can fail with no `ERR-`, an `ERR-` whose
     "The user sees" text is `TBD`, an NFR that isn't measurable or holds
     a `TBD` value, a BR no FR applies, and every open
     `[NEEDS CLARIFICATION: …]` marker. Skip IDs marked retired or
     superseded. Keep these private until step 5 — showing them early
     primes the user's answers.

3. **Show a map, not a summary**
   - Print a table: section name, a one-line statement of *what the
     section covers* (never what it says — "describes the refund approval
     flow", not "refunds over $500 need manager approval"), and a rough
     reading time.
   - Ask which sections to cover (default: all) and the depth: `--quick`
     ≈ 2 questions per section, default ≈ 3-5, scaled to how much a
     section actually contains. A thin section can get one question.
   - When the PRD has a `## Requirements` section, the default selection
     always includes its Business rules, Non-functional and Errors
     subsections, each with at least one question even in `--quick`;
     those are where builders and testers most often guess.

4. **Interview loop — one section at a time**
   - Tell the user to read the section now ("Read §<n> <name> and tell me
     when you're done") — don't paste it.
   - Ask questions **one at a time**, free text, built from the question
     types and role lens in `references/question-design.md`. Small batches
     only for simple open-ended recall, same pacing rule as `vc-prd`.
   - After each answer: quote what the PRD actually says (section + short
     verbatim excerpt, or "the PRD doesn't say"), then classify it with
     the result table in `references/question-design.md` and add it to the
     running gap log as `CLR-<nnn>`, naming the requirement ID the
     question was about when there is one.
   - **No blackbox answers.** A vague or hedged answer ("probably",
     "something like") gets one targeted follow-up on exactly the unclear
     part before it's classified.
   - **Shortcut requests.** "Just summarize it" / "just tell me" → decline
     once, briefly, and offer a hint pointing at where in the section to
     look. If they still want to move on, accept a **skip** — log the item
     as ⏭️ Not verified, never as understood.
   - After each section, print a one-line tally (✅ n · ❌ n · ❓ n · ⚠️ n ·
     ⛔ n · 💭 n · ⏭️ n) and move on.
   - **Pausing early.** If the user stops mid-interview, offer to save the
     partial gap log (same format and location as step 6) or suggest
     `/vc:handoff` so another session can continue.

5. **Reveal your own findings**
   - Show the suspected gaps from step 2 that the interview did *not*
     already surface, each with its section and why it looks like a gap.
   - For each, ask the user: real gap (add to the log as ❓/⚠️/⛔), not
     a gap, or unsure (log as ⚠️ with "flagged by review, not confirmed").

6. **Scorecard**
   - Print, in the console: a per-section table of the result counts, the
     full gap log grouped by section (template in
     `references/questionnaire-format.md`), and a **Re-read** list built
     from every ❌ Misread and ⏭️ Not verified item, with the section to
     revisit.
   - Ask whether to save the gap log. Yes → write
     `<prd-folder>/clarifications.md` (overwrite only after confirming if
     it already exists). No → leave it in the console.

7. **Offer the PO/BA questionnaire**
   - Ask whether to generate one. No → step 8.
   - Yes → build it from the ❓, ⚠️, ⛔, and 💭 items only (❌ and ⏭️ are
     the reader's own homework, not the PO's), using
     `references/questionnaire-format.md`: grouped by section, ranked
     🔴 Blocking / 🟡 Important / ⚪ Nice-to-have, each question standalone
     with PRD context, options where they help, and a default assumption.
     Each question names the requirement IDs it touches. End it with
     **Proposed Open Questions**: one line per question, worded for the
     PRD's `## Open Questions` list (no IDs of its own, naming the
     requirement IDs in full), for the PO/BA to add through `/vc:prd`.
     This skill never writes them into the PRD itself.
     Print it in the console first.
   - Then `AskUserQuestion`: don't save, markdown, email-ready HTML, or
     both. Save to `<prd-folder>/clarification-questions.md` and/or
     `<prd-folder>/clarification-questions.html` (confirm before
     overwriting). Report the path(s) written.

8. **Offer to mark the feature ready**
   - `ready` is the gate for `vc-create-user-stories`: stories are
     written only for a `ready` feature (later `active`, once building
     starts). Runs only when the PRD's frontmatter
     `status` is `draft` (or legacy `synced`). Already `ready` → say so
     and skip. `needs-review`, `active` or `done` → skip silently.
   - **Not offered while something blocks the split**, naming each item:
     - any ⛔ item, or any questionnaire item ranked 🔴 Blocking, still in
       the log;
     - any open `[NEEDS CLARIFICATION: …]` marker in the PRD;
     - an Open Question in any feature PRD naming one of this feature's
       IDs together with an ID from another feature (a conflict deferred
       by `/vc:requirements conflicts`);
     - a section selected out in step 3, or skipped (⏭️) in step 4: the
       whole PRD has to be read before the feature is ready.
     Say the feature can be marked ready once the PO/BA has answered and
     `vc-prd` has updated the PRD, by running this skill again.
   - Otherwise ask via `AskUserQuestion` whether the feature is ready to
     be split into stories ("Not yet" / "Mark ready").
   - Mark ready → set `status: ready` in the PRD's frontmatter and touch
     nothing else in it. Report the file changed and name the next step,
     `/vc:create-user-stories <feature-slug>`. On an Azure DevOps
     project, say the board is unchanged until `/vc:sync-to-tracker`
     pushes the new state.
   - Story readiness is no longer set here: `vc-create-user-stories`
     offers it right after it writes the stories.

## Notes

- `<prd-folder>` is the folder holding the resolved `prd.md`, whether
  it's still `artifacts/<slug>/` or already moved under an epic.
- The skill never touches the tracker; the next `/vc:sync-to-tracker`
  moves the Feature to `[ado].feature_ready_state` once the PRD says
  `ready`. It's a reading-comprehension and gap-finding step that
  can run at any point after a PRD exists, and it is the step that
  makes a feature `ready` for story writing.
- A ❌ Misread means the PRD is clear and the reader got it wrong — it's
  a learning moment, shown back plainly but without judgement, and never
  turned into a PO question.
