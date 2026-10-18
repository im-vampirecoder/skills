---
name: vc-create-architecture-diagrams
description: Draw a scope's architecture as interactive diagrams — as-is from the existing code, to-be from the architecture spine, with what changes highlighted. Whole-product with no argument, one epic or one feature with an argument, matching vc-architecture-design's scopes. Writes a typed JSON source plus a compiled self-contained HTML reader and SVG per diagram into a diagrams/ folder beside the spine. Triggered by /vc:create-architecture-diagrams; built-in only, needs Node 18+.
---

# Create Architecture Diagrams

Turn an architecture spine and the code it lands on into diagrams a team
can click through: system topology, the key cross-submodule flows, and
any status lifecycles — each drawn **as-is** (what the code does today)
and **to-be** (what the spine decides), with the difference called out.

Every diagram is authored as typed JSON and compiled by the bundled
compiler (`scripts/compiler/`): the compiler owns layout and routing, so this skill only describes what is
connected to what, never coordinates. Output is a self-contained HTML
reader (search, focus, route tracing, guided chapters, light/dark) plus a
static SVG.

This skill draws what's already decided — it never makes an
architecture decision. A diagram that needs a decision the spine doesn't
hold is a gap to report, not one to fill.

## Workflow

1. **Resolve the scope and check prerequisites**
   - Resolve `$ARGUMENTS` exactly as `vc-architecture-design` step 1
     does: empty → product (`artifacts/`), an epic → its folder, a
     feature → its folder, a bare slug matching both → ask.
   - Run `node --version`. Missing, or older than 18: stop and tell the
     user Node 18+ is required — don't hand-draw SVG as a fallback.

2. **Gather the to-be (the spine)**
   - Read this scope's `architecture.md` and `.decisions.md`, and its
     parent spines for inherited ids. Follow only current `AD`s — never
     one marked `Status: Superseded`.
   - No spine at this scope: there's no to-be. Say so, offer
     `/vc:architecture-design` first, and continue only if the user
     wants as-is diagrams alone.
   - Read the in-scope PRDs for the flows worth drawing: feature scope
     uses its Criteria Coverage rows; product and epic scope use each
     feature's Touchpoints.

3. **Gather the as-is (the code)**
   - Read `.vc/config.toml`'s `submodule_root` (default `src`) and, if
     present, `docs/architecture.md` as the starting map.
   - Confirm it against the code for the submodules in scope.
     **One submodule**: read it inline yourself. **2+ submodules**: spawn
     the `vc-scout` subagent in `focused` mode, one per submodule, in parallel. Brief:
     components and entry points, datastores, outbound calls to other
     submodules or external services, and any status/state fields the
     to-be lifecycle touches — each with `path:line`.
   - Every submodule empty or missing (greenfield): no as-is; draw to-be
     only and say so.

4. **Choose the diagram set**
   - Pick from the catalog in `references/diagram-catalog.md` — one
     topology per scope, plus only the flows and lifecycles that earn a
     picture. Present the planned list (name, archetype, what it shows,
     as-is/to-be) and let the user add, drop, or rename before drawing.

5. **Author the IR**
   - Write one JSON file per diagram per state, following
     `references/ir-authoring.md`: `<name>.as-is.json` and
     `<name>.to-be.json`, or a single `<name>.json` when only one state
     exists. Every node and edge traces to evidence — an `AD`, an
     inherited id, a Criteria Coverage row, or a scout `path:line` — kept
     in the item's `description`.
   - Mark the difference in the to-be file: `(new)` / `(changed)` label
     suffixes and a "What changes" chapter, per `references/ir-authoring.md`.

6. **Compile**
   - From this skill's directory, per IR file:
     ```
     node scripts/compiler/compile.mjs --input <ir.json> --format html --out <same-name>.html
     node scripts/compiler/compile.mjs --input <ir.json> --format svg --out <same-name>.svg
     ```
   - A validation error names the bad field — fix the IR and re-run;
     never edit the compiled output by hand.

7. **Self-review**
   - Check each diagram against its evidence, not just that it compiled:
     every spine `AD` that binds a connection or ownership shows up on
     the topology, no edge exists that nothing evidences, as-is shows
     nothing the code doesn't have, and labels read in the user's
     vocabulary (submodule and component names from the code and
     spine, not invented ones).
   - Look at each rendered diagram when you can view images: screenshot
     it in a real browser, after the ~8 s entrance animation, e.g.
     `npx playwright screenshot --wait-for-timeout 9000 --viewport-size
     "1400,900" file://<abs-path>.svg <scratch>.png`, then read the PNG.
     Don't use `rsvg-convert` or similar converters — they don't run the
     SVG's CSS variables or animation and render it blank. Fix clipped
     edge labels, crowding, or unreadable text by shortening labels or
     splitting the diagram, then recompile. No browser available: say
     visual quality is unverified — the compiler guarantees no overlaps,
     not legibility.

8. **Summarize**
   - List every diagram with its HTML and SVG paths, which state(s) it
     shows, and what it highlights as changing. List any gaps: a flow or
     ownership the diagrams needed that the spine doesn't decide, and
     as-is findings that contradict the spine. Suggest
     `/vc:architecture-design` (Update) for those — a nudge, not an
     automatic invocation.

## Output

All files go in a `diagrams/` folder beside this scope's
`architecture.md`: `artifacts/diagrams/`, `artifacts/epic-<slug>/diagrams/`,
or `<feature folder>/diagrams/`. As-is diagrams drawn with no spine at
the product scope go in `docs/diagrams/` instead. Per diagram:

- `<name>[.as-is|.to-be].json` — the source; edit and recompile, never
  edit the HTML or SVG.
- `<name>[.as-is|.to-be].html` — self-contained interactive reader.
- `<name>[.as-is|.to-be].svg` — static vector.

A re-run overwrites files with the same name and leaves others alone; a
diagram dropped from the set is listed in the summary as stale rather
than deleted.

## Notes

- Never writes `architecture.md`, `.decisions.md`, PRDs, or any code —
  diagrams only.
- No PNG export and no Mermaid output — the HTML and SVG are the
  deliverables.
- The compiled output's `vc-*` CSS class names and attribute order are
  the reader runtime's contract (`assets/reader.js`); change them only
  in the compiler, the assets, and the reader together.
- The compiled HTML is fully offline: no CDN, fonts, or telemetry, so it
  can be attached to a work item or opened from a file share as is.
- The SVG is styled with CSS variables and plays a short entrance
  animation, so it needs a browser to display — it shows blank in
  converters and some image viewers. Point people at the HTML first.
