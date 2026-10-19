---
name: vc-extract-design-system
description: Extract the design system of an existing (brownfield) frontend from its code, and from the running app when available — tokens, components, every screen and the navigation flows — into an interactive design canvas (foundations board, component sheet, one clickable board per screen, rules for new pages) plus tokens under docs/design-system/[app]/, viewable locally with no publish, and optionally published as a claude.ai Design canvas the team builds new pages on. Modes scan, refresh, preview, publish, pull. Triggered by /vc:extract-design-system.
---

# Extract Design System

Capture what an existing app already looks like and how its screens
connect, so later design work (`/vc:create-ui-mockup`) builds on the
real thing instead of starting from nothing.

**The repo is the record.** Everything is written under
`docs/design-system/<app>/`:

- the **design canvas** (`canvas/project/`): a Foundations board (tokens
  shown visually, plus rules for new pages), a Components sheet (every
  variant and state), a flow map, and one board per screen, dialog and
  system page. Boards link to each other and keep tabs, menus and
  dialogs working, so they click through like the real app.
- `tokens.json`, `assets/` (the app's own fonts, logos, icons) and
  `DESIGN.md` (the written brand book, inventory and UI debt).

**View it locally**, no claude.ai needed: a small server and overview page
render every board with claude.ai's own Design runtime, downloaded fresh
on each run (`references/local-preview.md`).

**Publishing is optional**: the same boards can be mirrored to one
claude.ai Design canvas for comments and editing, and `pull` brings those
edits back into the repo as a git diff.

## Ground rules

- **Code is always scanned.** The running app is recommended, never
  required: without it the boards come from code alone, and `DESIGN.md`
  says so.
- **Never invent.** Token names and values come from the source as they
  are; a value the scan can't find is written `unknown`, not guessed.
  Widgets that can't be rebuilt faithfully (charts, maps, rich-text
  editors, third-party embeds) become labelled placeholders.
- **Placeholders, not data.** Boards show user data as bracketed
  placeholders (`[User name 1]`, `[date, time]`); app-defined values like
  statuses and roles stay as in code. Never copy real data from a running
  app. Screenshots stay in `captures/`, which is git-ignored.
- **Read-only against the app.** Navigate and open things; never submit a
  form, save, delete, or click anything that changes data.
- **Never publish without asking.** `publish`, and the offer at the end
  of `scan`/`refresh`, always ask first.
- **Mobile apps are out of scope** (React Native, Flutter, MAUI, native).
  Say so and stop if that's the only frontend found.

## Workflow

0. **Resolve the mode and the app**
   - Parse `$ARGUMENTS` for `scan` (default), `refresh`, `preview`,
     `publish`, or `pull`, followed by an optional app slug.
   - Read `.vc/config.toml`'s `submodule_root` (default `src`). Find the
     frontend(s) among its submodules using
     `references/framework-detection-hints.md` — work the stack out from
     what's actually there; the hints are a starting point, not a list of
     what's supported.
   - One web frontend → use it. Several → ask which. None → stop and say
     so.
   - `<app>` = a kebab-case slug of the submodule name. Output always goes
     to `docs/design-system/<app>/`, even for a single app, so a second
     frontend later never needs a move.
   - Every mode first refreshes the local Design runtime
     (`references/local-preview.md` → "The real runtime").
   - `preview` → refresh the preview files and give the run command
     (`references/local-preview.md`). Never scans.
   - `publish` / `pull` → go to `references/claude-design-sync.md`. They
     never scan.
   - `refresh` with no `docs/design-system/<app>/DESIGN.md` yet → run as
     `scan`.
   - A `DESIGN.md` with `origin: proposed` was seeded by
     `/vc:create-ui-mockup` before the app existed: treat the run as a
     first `scan`, replace the seeded system with the extracted one, keep
     the canvas's Proposed page and the canvas link, and drop
     `origin: proposed`.

1. **Static scan (always)**
   - Inventory, with `file:line` evidence for each item:
     - **Tokens:** colors (every theme), type (families, sizes, weights,
       line heights), spacing, radii, shadows, breakpoints, z-index, motion
       durations. Sources: CSS custom properties, SCSS/Less variables,
       theme objects, utility-framework config, design-token files.
     - **Fonts and icons:** font files or hosted families; the icon set
       and how it's loaded.
     - **Components:** shared/reusable components, each with its variants,
       states, and where it's used.
     - **App shell and layouts:** header, navigation, sidebars, footers,
       page templates.
     - **Screens:** every route, with its layout, guards (which roles see
       it) and the main components it uses.
     - **Flows:** navigation links, menus, redirects, guards, and
       post-action navigation (e.g. "after save → detail page").
   - Small apps: sweep inline. Large apps (roughly 30+ routes or several
     feature areas): spawn the `vc-ui-scout` agent (`vc:vc-ui-scout`
     through the plugin) once per feature area, in parallel, then merge
     their reports.
   - Show the user a short summary: stack, counts (tokens, components,
     screens), feature areas. With 40+ screens, ask which areas to
     include this run — a canvas holds at most 512 files.

2. **Running-app capture (recommended)**
   - Ask once: "Is the app running somewhere I can open (local or
     staging)? It makes the screens much closer to the real thing." No
     → skip to step 3 and record `capture: none` in `DESIGN.md`.
   - Yes → follow `references/running-app-capture.md`: the user logs in
     themselves in a visible Edge window; for each included screen record
     the page structure, computed styles and screenshots at 375, 768 and
     1440px.

3. **Reconcile**
   - Real values win: where the running app's computed styles differ from
     a token in code, record the rendered value and note the drift.
   - Build the **UI debt** list: hard-coded values that bypass tokens,
     near-duplicate tokens, one-off components that duplicate a shared
     one, inconsistent spacing or type steps, missing states (no
     empty/error/loading), contrast failures. Each with evidence.

4. **Write the foundation files** → `docs/design-system/<app>/`
   - `tokens.json` in the list shape described in
     `references/claude-design-sync.md` → "File shapes"; keep the source's
     own token names, converting map-shaped token files to lists.
   - `assets/`: fonts the app ships as files (`assets/fonts/`), logos and
     icon files (`assets/brand/`, `assets/icons/`), copied as-is, never
     redrawn. A hosted font (Google Fonts) is named, not copied.
   - The brand book and component guidelines go in `DESIGN.md` (step 8),
     and visually on the Foundations and Components boards (step 5).

5. **Build the canvas boards** (`references/canvas-board-build.md`),
   straight as canvas files in `docs/design-system/<app>/canvas/project/`,
   one file at a time:
   - `Main.dc.html` — Foundations: color by role, type scale in the real
     font, spacing/radius/shadow drawn to size, icons, and **Rules for
     new pages**.
   - `Components.dc.html` — every shared component with all its variants
     and states.
   - One page board per screen inside the real app shell; dialogs and
     overlays grouped with their states; auth and system pages
     (404/403/loading).
   - Interactive: links between boards follow the real navigation,
     tables and lists render from `sc-for` rows, and tabs, menus, toggles
     and dialog triggers work through state.
   - With captures, take structure from the DOM snapshot and values from
     the computed styles; record any part that still differs from the
     screenshots under the screen in `DESIGN.md`. Without captures, mark
     the screen `fidelity: code-only`.

6. **Build the flow map and the canvas index**
   - `Flows.dc.html`: every included screen as a labelled box linking to
     its board, grouped by feature area, arrows for navigation, a marker
     on guarded routes.
   - `canvas.json`: rows titled per area (foundations & components,
     each feature area, dialogs & overlays, auth & system), one page per
     feature area plus an empty **Proposed** page reserved for
     `/vc:create-ui-mockup`, `is_interactive` on boards with working
     controls.

7. **Set up the local preview** (`references/local-preview.md`): copy
   `support.js`, `index.html` and `serve.mjs` into place, write
   `blob-map.js`, and give the user the command to run it.

8. **Write `DESIGN.md`** from `references/design-doc-template.md`:
   stack, capture status, brand book, inventory, screens and flows, rules
   for new pages, UI debt, known gaps, and the `claude_design` block in
   its frontmatter (`canvas_url` stays `null` until the first publish).

9. **Offer to publish**
   - Summarize what was written (paths, counts of boards and
     components, fidelity: captured or code-only, widget placeholders
     used).
   - Ask whether to also publish the canvas to claude.ai now. Yes → run
     the publish flow in `references/claude-design-sync.md`. No → stop;
     the local preview has everything, and `publish` can run later.
   - Add `docs/design-system/*/captures/` and
     `docs/design-system/*/canvas/local/artifact-type/` to the tracking
     repo's `.gitignore` if missing, and tell the user.

## `refresh` mode

1. Run `pull` first when `canvas_url` exists, so canvas edits are in the
   repo before anything is compared. If `pull` fails, ask whether to
   continue without it.
2. Re-run steps 1-3 (step 2 only if the user wants a new capture).
3. Update only what changed in code: changed tokens, new/removed
   components, new/removed/changed screens and flows. A token or
   component change also updates `Main.dc.html`, `Components.dc.html` and
   the screen boards that use it; a navigation change updates the links
   on both boards and `Flows.dc.html`. Never rebuild untouched files.
4. **Conflicts:** a file that changed in code *and* was edited on the
   canvas (its last pulled version differs from what this skill last
   generated, per `DESIGN.md`'s `generated` hashes) is not overwritten.
   List each conflict with both sides and ask: keep the canvas edit, take
   the code version, or skip.
5. Never touch the **Proposed** page or anything under it.
6. Refresh the local preview files (step 7), update `DESIGN.md`, then
   offer to publish (step 9).

## Notes

- Writes only under `docs/design-system/<app>/`, plus two `.gitignore`
  lines. Never edits app code, `artifacts/`, or `.vc/config.toml`.
- Reads one config field, `submodule_root`, like `vc-prd` and
  `vc-docs`.
- Complements `vc-docs`: that skill documents architecture; this one
  documents the UI. If `docs/architecture.md` exists, read it for the
  frontend's structure before scanning.
- Depends on the `vc-ui-scout` agent (top-level `agents/`), installed
  with the plugin or the file install.
- Publishing, pulling and downloading the real Design runtime need a
  Claude Code session signed in to claude.ai. Team members without one
  still get the repo files and the local preview, on its built-in
  runtime.
