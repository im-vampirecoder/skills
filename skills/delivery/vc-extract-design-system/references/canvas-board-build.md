# Canvas Board Build

Loaded by `vc-extract-design-system` steps 5-6, and by
`vc-create-ui-mockup` when it turns mockups into boards. Every board is
written straight as a canvas file (`.dc.html`) under
`docs/design-system/<app>/canvas/project/`. There is no intermediate
plain-HTML copy: the board itself is the replica. The local preview
(`local-preview.md`) and, once published, the canvas's Play mode make
the set a clickable prototype.

The board format belongs to the claude.ai Design type. At publish time
`claude-design-sync.md` re-reads the type's instructions and `format.md`;
where they differ from this page, the type wins and the boards are fixed
before sending.

## The board set

Laid out in rows, one `title1` note above each row (see "Layout" below).

| Row | Board | What it holds |
|---|---|---|
| Foundations & components | `Main.dc.html` (title "Foundations") | The design system at a glance: color swatches grouped by role (brand, surfaces and text, status), each with token name, value and usage; the type scale rendered in the real font; spacing, radius and shadow steps drawn to size; the icon set; a closing **Rules for new pages** section (below). |
| | `Components.dc.html` | Every shared component, one labelled section each, showing all variants and states side by side: buttons, badges, form controls, table + pagination, cards, dialogs, feedback (toast, alert, empty state), navigation items, page header, and the app-specific ones. |
| | `Flows.dc.html` | The flow map: every included screen as a labelled box grouped by feature area, arrows for navigation, a marker on guarded routes. Built from placed elements, not one big `<svg>`. Each box links to its screen board. |
| One row per feature area | `<area>-<screen>.dc.html` | One full page per route, inside the real app shell. |
| Dialogs & overlays | `<area>-<overlay>.dc.html` | Dialogs, drawers, menus, lightboxes over a dimmed backdrop. Related states sit side by side on one board (form → success; edit → confirm delete). |
| Auth & system pages | `auth-<screen>.dc.html`, `system-pages.dc.html` | Login, reset password and similar; 404, 403 and the app's loading screen together on one board. |

Only boards that exist in the app: no invented screens, no screen
without a route or a component behind it.

### Rules for new pages

The last section of `Main.dc.html`, and the reason the canvas is useful
for later work. Short, concrete rules a designer or `/vc:create-ui-mockup`
follows to add a page that fits, each naming tokens and components:
page anatomy (shell, header, content padding, footer), the primary-action
style and where it sits, how lists/tables/forms/detail views are built,
spacing between sections, how status is shown, and the do-nots seen in
the UI debt list.

## Writing one board

The skeleton (keep the `support.js` line exactly):

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title><Screen name></title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<style>
/* @font-face for the app's fonts (uploaded), or a Google Fonts css2 <link> */
body{margin:0}
a{color:<link color>}a:hover{color:<link hover>}
button,input,select,textarea{font-family:inherit}
</style>
</helmet>
<!-- the screen's markup, every style inline -->
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":1440,"height":<page height>}}'>
class Component extends DCLogic {
renderVals() { return {}; }
}
</script>
</body>
</html>
```

All boards sit flat in `canvas/project/` (no subfolders), so the
`./support.js` line and every link between boards stay plain filenames.

Rules:

- **Markup from the source.** Rebuild each screen from the captured DOM
  snapshot when there is one, otherwise from the route's component tree
  in code. Same sections, order, columns, labels and copy as the app.
- **Styles inline.** Every rule's declarations go on the element as
  `style="…"`, with `var(--token)` replaced by the token's resolved value.
  That's what the canvas's properties panel edits. Only font loading,
  `body{margin:0}`, link colors and the form-font reset stay in
  `<helmet><style>`. A value used in the app but in no token is written
  literally and listed as UI debt; never invent a token for it.
- **Real shell on every page.** Each screen board repeats the app's
  sidebar/header/footer exactly as the app renders them, with the current
  item marked (`aria-current="page"`) and the right page title.
- **Pages are fluid.** Screen boards get `"expand": "fill"` in
  `canvas.json`, a fluid root (`max-width` container, `%`/`rem`/`fr`),
  `$preview` width 1440 and the page's height at that width. Side menu
  plus content is a `flex-wrap: wrap` row with the content
  `flex: 999 1 560px; min-width: 0`, so the menu stacks at phone width.
  Toolbars wrap; wide tables sit in an `overflow-x: auto` box. Overlay
  boards and the system-pages board use a fixed root at their `w`×`h`.
- **Controls are real.** `<button>`, `<a href>`, `<input>` with a
  `<label>`, `aria-label` on icon-only buttons, headings in order. Never a
  clickable `<div>`.
- **Fonts and icons are the app's own.** Font files and logos live in
  `docs/design-system/<app>/assets/`; boards reference them by relative
  path (`../../assets/fonts/<file>.woff2`) until the first publish, which
  uploads them and swaps in `/_blob/<id>` (`claude-design-sync.md`). The
  local preview resolves both forms. Icons are inline stroke SVG of the
  same icon set the app uses, never emoji or a substitute set.
- **Placeholders, not data.** Text that is user data is a bracketed
  placeholder in the shape of the real field: `[User name 1]`,
  `[user1@example.com]`, `[date, time]`, `[total]`. Enum-like values the
  app defines itself (statuses, roles, plan names) are written as they
  are in code, so every variant shows. Never copy a value from a capture.
- **Unbuildable widgets** (charts, maps, rich-text editors, video,
  third-party embeds) become a box of the same size with a label such as
  `[Chart: monthly revenue, line]`.
- **No network** except a Google Fonts `css2` link and uploaded files. No
  `<iframe>`, no script that builds UI (`innerHTML`, `appendChild`).

## Making it interactive

The aim: someone presses Play and clicks through the app as it works.

- **Navigation between boards.** Every sidebar item, breadcrumb, row
  link, "View"/"Back" link and post-action destination points at the
  target board with a relative `href` (`<a href="users-detail.dc.html">`).
  Style the `<a>` itself as the button; a `<button>` inside an `<a>`
  swallows the click. A destination that wasn't built points to `#`.
- **Repeated rows from data.** Tables, lists and card grids use
  `<sc-for list="{{rows}}" as="row" hint-placeholder-count="6">` with
  the rows built in `renderVals()`, one row per variant the app has (each
  status, each role, an empty optional field, a long name). Per-row
  styles (status chip colors) are computed in `renderVals()` and bound
  as `style="{{row.statusStyle}}"`.
- **In-page behavior with state.** Where the app switches content on
  the same page, keep it working: tabs, segmented controls, accordions,
  dropdown menus, a filter that opens, a toggle, and opening a dialog
  from its trigger. Keep the choice in `state`, handlers come from
  `renderVals()` (`onClick="{{ openCreate }}"`), and each branch sits in
  `<sc-if value="{{ isOpen }}" hint-placeholder-val="{{ false }}">`.
  Holes are dotted lookups only; compute everything in `renderVals()`.
- **Read-only, like the capture rules.** Nothing pretends to save or
  submit data. A submit button on a form may move to the board that shows
  its result state, never more.
- Mark every board with working handlers or inputs
  `"is_interactive": true` in its `canvas.json` entry. Pure link-only or
  static boards leave it off.
- **Tweaks:** none by default. Copy stays literal markup so people can
  retype it in place.

## Layout in `canvas.json`

- `pages`: one page per feature area plus an empty **Proposed** page
  (reserved for `/vc:create-ui-mockup`); foundations, components and
  flows sit on the first page, or all boards on one page for a small app.
- Frames 80px apart in a row, rows 120px apart plus room for the row
  title: a `title1` note ≥223px above each row, `maxW` = the row's width.
- `order`: `Main.dc.html` first, then `Components.dc.html`, `Flows.dc.html`,
  then screens row by row.
- Each entry has `title` (the screen's name as people say it, e.g.
  "User detail"), `w`/`h` matching the board's `$preview`, `expand`,
  `is_interactive` where it applies.
- `launch`: `{"view":"canvas"}`.

## Large apps

A canvas holds at most 512 files. With 40+ screens, step 1 of the skill
asks which areas to include. Write boards one at a time; never hold the
whole set in one message.
