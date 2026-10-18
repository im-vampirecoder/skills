---
name: vc-create-ui-mockup
description: Design UI mockups for a feature PRD — UX flows, a screen inventory, and clickable hi-fi (or --wireframe) screens with every state — built on the app's extracted design system for brownfield apps, or from 2-3 chosen directions for greenfield. Changed screens show before/after. Writes to the feature's ux/ folder and the app canvas's Proposed page, optionally published to claude.ai. Triggered by /vc:create-ui-mockup.
---

# Create UI Mockup

Turn a feature PRD into screens stakeholders can click through and react
to, so feedback is about something concrete before any code is written.
The mockups follow the app's real design system when there is one, show
exactly what changes on existing screens, and surface the questions the
PRD leaves open.

## Ground rules

- **Repo first.** Everything is written to files; the claude.ai canvas is
  a mirror, published only after asking.
- **Follow the baseline.** When `docs/design-system/<app>/` exists, use its
  tokens, components and patterns as they are. New visual ideas belong to
  greenfield work or an explicit request, never slipped into brownfield
  screens.
- **The PRD is the scope.** Design what the PRD asks for. Anything the
  design needs that the PRD doesn't answer becomes a PO/BA question, not
  an invented requirement.
- **Real structure, sample data.** Realistic sample values in the shape
  of real data; no invented metrics, testimonials, or customer names
  presented as real; labelled placeholders for widgets that can't be
  mocked faithfully.
- **Never edits the PRD or app code.** Only touches a story's `Design:`
  line, and only after the user confirms (step 10).

## Workflow

0. **Resolve the PRD and any earlier run**
   - `$ARGUMENTS` → a feature slug, `FEATURE-<slug>`, or a path to a
     `prd.md`, unassigned (`artifacts/<slug>/`) or under an epic. Strip
     `--wireframe` first. Empty → list feature PRDs and ask.
   - `status: needs-review` stub → stop; point to `/vc:prd review`.
   - Read the PRD, `artifacts/prd.md`, any `stories-*.md` in the feature
     folder, and `clarification-questions.md` if `vc-prd-clarify` saved
     one.
   - **User-flow map.** Invoke `/vc:define-user-flow status <feature>`
     through the Skill tool and act on its answer:
     - `approved` → read `ux/user-flow.md`; step 3 builds from it.
     - `missing` or `draft` → suggest `/vc:define-user-flow <feature>`
       first, so screens and branches are agreed before drawing. The user
       can run it (stop here) or continue; continuing keeps step 3's own
       derivation.
     - `stale` → stop and show what changed. Ask the user to confirm the
       current flow: yes → use the map as it is now; no → point to
       `/vc:define-user-flow <feature>` to revise it, and stop.
   - `<feature folder>/ux/ux-spec.md` already exists → show its status and
     ask: revise it, start over, or stop. Revising keeps everything the
     user didn't ask to change.

1. **Resolve the app and the route**
   - Which frontend does this feature touch? Use the PRD's Touchpoints,
     else `docs/design-system/*/`, else ask. `<app>` is that app's slug.
   - **`docs/design-system/<app>/DESIGN.md` exists → follow-baseline.**
     Read `DESIGN.md` (brand book, component guidelines, rules for new
     pages), `tokens.json`, the `Components.dc.html` board, and the
     baseline boards of screens this feature touches.
   - **No baseline, but the app has frontend code under `src/`** → say
     the mockups will match the real app much better after
     `/vc:extract-design-system`, and ask: run that first (stop here),
     or continue as greenfield.
   - **No frontend yet → greenfield.**

2. **Fill the UX gaps the PRD leaves (short interview)**
   - Only what the PRD, baseline and user-flow map don't answer: devices
     and contexts of use (skip when the map's `devices` is set), who uses each screen and how often, information density,
     existing screens that must be reused, accessibility needs beyond the
     baseline. One question at a time when offering options; skip
     anything already answered. Same "no blackbox answers" rule as
     `vc-prd`.

3. **Flows and screen inventory**
   - **With a map from step 0:** take its flows, screens (numbers, names,
     new/changed) and transitions as given; don't add, drop or regroup
     screens. Only add each screen's states and the criteria coverage
     below. Error states come from the map's `ERR-` transitions. A gap
     the mockups reveal in the map goes to the user as a suggestion to
     revise it with `/vc:define-user-flow`, not as a silent change.
   - **Without a map:** from the PRD's users, scenarios, acceptance
     criteria and scope, derive the user flows: entry points, steps,
     decisions, success, errors and recovery.
   - List the screens: each **new** or **changed** (naming the baseline
     screen it changes), with the states it needs — default, loading,
     empty, error, success, disabled, permission-denied where they apply —
     and the PRD criteria it covers.
   - Every acceptance criterion maps to at least one screen or state; a
     criterion with no screen is flagged.
   - **Exact wording per state.** For every error, success and info state,
     write the exact text the user sees. An error state cites the
     `ERR-<feature-slug>.<name>` entry it shows (from the PRD's
     `### Errors` table) and uses its "The user sees" wording word for
     word. A user-facing `ERR-` with no screen state is flagged; an error
     state with no `ERR-` behind it, or an `ERR-` whose wording is `TBD`,
     becomes a PRD gap (step 9) with the placeholder text the mockup used.
     Success and info text comes from the PRD where it has some, else is
     marked as the mockup's default for the PO to confirm. Cite live IDs
     only: skip any marked retired or superseded (in the PRD or
     `artifacts/requirements-current.md`).
   - Show the flows and inventory and confirm before building. Note every
     PRD gap found so far (step 9).

4. **Visual direction**
   - **Follow-baseline:** skip — the baseline is the direction. Write its
     brief into `ux-spec.md` from `DESIGN.md`.
   - **Greenfield:** follow `references/design-brief-and-directions.md`:
     2-3 distinct briefs, each with one preview of the most important
     screen in `ux/directions/`. The user picks one or combines them. The
     chosen tokens seed `docs/design-system/<app>/` so later features
     follow the same system.

5. **Build the mockups** (`references/mockup-build-and-check.md`)
   - One self-contained HTML file per screen and state in
     `<feature folder>/ux/mockups/`, plus `index.html` showing the flows
     and linking every screen. Screens link to each other, so the set is
     clickable; with a map, links follow its Transitions table and nothing
     else.
   - Hi-fi from the tokens and components by default; `--wireframe`
     builds grey-box layouts with the same structure and spacing scale.
   - **Changed screens** start from the baseline board; the change is
     applied and marked (numbered markers, toggled by a "Show changes"
     control), and the matching change list goes in `ux-spec.md`.

6. **Check the rendered result**
   - Render each mockup at 375, 768 and 1440 with the Playwright CLI
     (Edge), review against the checklist in
     `references/mockup-build-and-check.md`, fix, and re-check once. At
     most two rounds. Anything that couldn't be rendered or checked is
     marked unverified in `ux-spec.md`.
   - Add `artifacts/**/ux/checks/` to the tracking repo's `.gitignore` if
     missing.

7. **Add the mockups to the app canvas**
   - Convert each checked mockup into a board under
     `docs/design-system/<app>/canvas/project/proposed/<feature-slug>/`,
     following
     `../vc-extract-design-system/references/canvas-board-build.md`
     (writing one board, making it interactive) and the baseline's
     "Rules for new pages" on `Main.dc.html`.
   - In `canvas.json`, place them on the **Proposed** page: a title note
     for the feature, one row per flow, each changed screen's "after"
     board next to a copy of its baseline board labelled "Before".
   - Greenfield with no canvas yet: create
     `docs/design-system/<app>/` with the seeded `tokens.json`, a canvas
     holding only the Proposed page, and a `DESIGN.md` marked
     `origin: proposed` (see `references/ux-spec-template.md`).
   - Set up or refresh the local preview, including a `support.js` copy
     in `proposed/<feature-slug>/`
     (`../vc-extract-design-system/references/local-preview.md`), and
     give the user the command to view the boards.
   - Never touch boards outside `proposed/<feature-slug>/`.

8. **Write `ux-spec.md`** from `references/ux-spec-template.md`: brief,
   flows, screen inventory with states and criteria coverage, the
   wording table (exact text per state, with the `ERR-` ID it shows),
   change lists, components used (and any new component proposed, flagged for
   the design system), responsive and accessibility notes, open
   questions, and the board/mockup paths.

9. **PRD gaps → PO/BA questions**
   - List every gap found while designing ("what does the list show with
     0 results?", "who can edit after approval?"), with the default
     assumption the mockup used.
   - Offer a PO/BA questionnaire using
     `../vc-prd-clarify/references/questionnaire-format.md`, shown in the
     console; save to `<feature folder>/ux/clarification-questions.md`
     only if the user wants.

10. **Link stories** (only when `stories-*.md` exist)
    - Map screens to stories by the acceptance criteria they cover; show
      the mapping and ask before writing.
    - On yes, set each story's `- Design:` line to its mockup path(s)
      relative to the story file. Change nothing else in the story.

11. **Offer to publish**
    - Summarize: screens and states built, fidelity, what was checked,
      open questions.
    - Ask whether to publish the Proposed boards to the app's claude.ai
      canvas. Yes → follow
      `../vc-extract-design-system/references/claude-design-sync.md`,
      sending only this feature's boards and `canvas.json`. The canvas
      link comes from the app's `DESIGN.md`, so the whole team publishes
      to the same canvas.

## Approval

The mockups stay `status: draft` in `ux-spec.md` until the user says the
PO (or the stakeholder named in the PRD) approved them; then set
`status: approved` with who and when. A rerun after approval asks before
changing anything and resets the status to `draft` if screens change.

## Notes

- Writes only to `<feature folder>/ux/`, the feature's boards under the
  app canvas's `proposed/<feature-slug>/`, `canvas.json`'s Proposed page,
  stories' `Design:` lines (after confirming), and — greenfield only — a
  new `docs/design-system/<app>/`.
- `ux/` lives in the feature folder, so `/vc:propose-epic`'s folder move
  carries it along; canvas boards are keyed by feature slug and don't
  move.
- `/vc:extract-design-system refresh` never touches the Proposed page.
- Mobile apps are out of scope, same as `vc-extract-design-system`.
