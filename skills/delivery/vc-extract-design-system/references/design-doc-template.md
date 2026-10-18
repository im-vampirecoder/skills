# DESIGN.md Template

Loaded by `vc-extract-design-system` step 8. Written to
`docs/design-system/<app>/DESIGN.md`. Every fact cites its evidence
(`file:line`, or `capture:<area>-<screen>` for a running-app finding);
anything not found is `unknown`, never guessed.

```markdown
---
app: <app-slug>
source: <submodule_root>/<repo-name>
stack: <framework + UI library + styling approach, as detected>
capture: <none | local | staging | production>   # environment captured
captured_at: <ISO-8601 or null>
generated_at: <ISO-8601>
local_preview:
  runtime_from: <canvas url the Design runtime was downloaded from, or null>
  runtime_version: <version the read reported, or null = built-in only>
  runtime_fetched_at: <ISO-8601 or null>
claude_design:
  canvas_url: null
  owner: null
  last_published: null
  last_pulled: null
generated:          # sha256 of each file as this skill last wrote it; used to spot canvas edits
  tokens.json: <hash>
  canvas/project/Main.dc.html: <hash>
  canvas/project/<area>-<screen>.dc.html: <hash>
---

# Design System: <App name>

## Overview
Stack, how the UI is built, how many tokens / components / screens,
which feature areas are included, and fidelity (captured vs code-only).

## Foundations
### Color
Table per theme: token, value, usage, evidence.
### Typography
Families, scale (name, size, line height, weight), evidence.
### Spacing, radius, shadow, breakpoints, motion
One table each.
### Iconography and imagery
Icon set, sizes, stroke, how icons are loaded; logos in `assets/brand/`.
### Content tone
How the UI writes: labels, buttons, empty and error messages, with real
examples from the code.

## Components
| Component | Variants | States | Used on | Guidelines | Source |
|---|---|---|---|---|---|

Guidelines: when to use it, what the caller provides, what not to do.
Shown visually on `canvas/project/Components.dc.html`.

## App shell and layouts

## Screens
| Area | Screen | Route | Guard / roles | Fidelity | Interactive | Board |
|---|---|---|---|---|---|---|

Fidelity is `captured` or `code-only`; Interactive lists what works in
Play beyond links (tabs, menu, dialog). Per screen, any "board differs
from capture" notes.

## Flows
Per feature area: entry points, main paths, redirects, guarded routes.
Link to the flow map board (`canvas/project/Flows.dc.html`).

## Rules for new pages
The same rules as the last section of `canvas/project/Main.dc.html`:
page anatomy, primary action, lists/tables/forms/detail views, section
spacing, status display, do-nots. Each names tokens and components.

## UI Debt
| # | Issue | Where | Evidence | Suggested fix |
|---|---|---|---|---|

## Not captured / known gaps
Screens or states not reached, placeholders used, values marked unknown.

## Viewing the design
Local: `node docs/design-system/<app>/canvas/local/serve.mjs`, then open
`http://127.0.0.1:4321/`. claude.ai: the canvas link (or "not published
yet"), who owns it, and how teammates get edit access.
```
