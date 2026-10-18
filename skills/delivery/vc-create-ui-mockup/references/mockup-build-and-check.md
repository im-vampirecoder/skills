# Mockup Build and Check

Loaded by `vc-create-ui-mockup` steps 5-6.

## Files

- `<feature folder>/ux/mockups/<flow>-<screen>.html`, and
  `<flow>-<screen>--<state>.html` for each extra state.
- `<feature folder>/ux/mockups/index.html`: the flows as a simple map
  (one row per flow, screens as linked thumbnails or labelled boxes, with
  arrows), so a reviewer can start anywhere.
- Each file is self-contained: `<!doctype html>`, charset and viewport
  metas, one `<style>` block, no build step, no external scripts except a
  pinned icon or font source the baseline already uses.

## Building

- Start the `<style>` with the tokens as CSS custom properties, using the
  design system's own names, and style only through them. A value the
  design needs that no token covers is a proposal: add it to the
  "Components and tokens proposed" list in `ux-spec.md` instead of
  hard-coding it silently.
- Reuse baseline components exactly (structure, spacing, states). A new
  component gets a name, a reason, and an entry in the proposed list.
- Real structure: page header, navigation and app shell as in the
  baseline; one primary action per view; labels and copy in the product's
  voice, taken from the PRD's wording where it has some.
- Sample data in the shape of real data (lengths, formats, counts),
  including an awkward case — a long name, a large number, an empty
  optional field.
- Links between screens follow the flows, so the set is clickable from
  `index.html`.
- Responsive: the layout re-composes at 768 and 375 (columns stack,
  tables scroll in their own box or turn into lists, toolbars wrap); it
  doesn't just shrink.

## States

Each screen covers the states it needs, as separate files when they
change the layout and inline when they don't: default, loading
(skeletons that match the final layout), empty (what it is and the next
action), error (what went wrong and how to fix it), success feedback,
disabled, validation errors on forms, and permission-denied where roles
matter. Interactive elements show hover, focus-visible and active styles.
Error, success and info messages use the exact text from the wording
table in `ux-spec.md`; an error state shows the PRD's `ERR-` wording word
for word, and the mockup file carries the ID in an HTML comment
(`<!-- ERR-<feature-slug>.<name> -->`) next to the message, so a search
for the ID finds the screen.

## Changed screens: before and after

- Start from the baseline board for the screen
  (`docs/design-system/<app>/canvas/project/<area>-<screen>.dc.html`):
  take the markup inside its `<x-dc>`, with its inline styles and any
  `sc-for` rows expanded to plain markup, as the mockup's starting HTML,
  and apply the feature's change to it.
- Mark each change with a small numbered marker placed next to it, and
  add a "Show changes" toggle (a button in a fixed corner) that shows or
  hides markers and a subtle outline on changed regions. Markers are off
  in screenshots for the canvas "after" board unless the user asks
  otherwise.
- List the same numbers in `ux-spec.md` with what changed and why (PRD
  criterion or decision).
- No baseline board for that screen → build it from the baseline
  tokens and components and say the "before" is approximate.

## Wireframe mode (`--wireframe`)

Same files, structure, states and flows, but grey-box: neutrals only, one
system font, real labels and copy, boxes for images and charts, no
shadows or brand color. Spacing still follows the scale, so a later hi-fi
pass keeps the layout.

## Accessibility floor

- Real `<button>`, `<a href>`, `<label>` + `<input>`, headings in order,
  landmarks (`header`, `nav`, `main`).
- Contrast 4.5:1 for text, 3:1 for large text, icons, borders of
  controls and focus rings.
- Touch targets at least 44×44px on the 375 layout.
- Color is never the only signal (pair it with text or an icon).
- Any motion respects `prefers-reduced-motion`.

## Check (step 6)

1. For each file, screenshot at 375×812, 768×1024 and 1440×900 with the
   Playwright CLI (`--browser msedge`), into
   `<feature folder>/ux/checks/` (git-ignored like the extract skill's
   captures).
2. Review each screen against this list, writing one line of evidence for
   anything that fails:
   - matches the brief (character, density, color strategy);
   - follows the baseline: same components, spacing and type as the
     baseline boards around it, and the "Rules for new pages";
   - clear hierarchy — the most important thing and the primary action
     are obvious;
   - spacing from the scale, tighter inside groups than between them;
   - alignment on a grid; numbers right-aligned in tables;
   - all needed states exist and look designed;
   - no overflow, clipping, overlapping or horizontal scroll at 375;
   - accessibility floor above;
   - copy is specific, consistent with the PRD, free of placeholder names;
   - every error, success and info message matches the wording table, and
     every error state cites its `ERR-` ID;
   - every acceptance criterion it maps to is visibly covered.
3. Fix the failures, re-check once. Stop after two rounds; record what is
   still open in `ux-spec.md`.

If the Playwright CLI or Edge isn't available, say so, skip the render
check, review from the code only, and mark the screens unverified.
