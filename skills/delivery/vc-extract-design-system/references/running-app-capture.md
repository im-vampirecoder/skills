# Running-App Capture

Loaded by `vc-extract-design-system` step 2. Uses the Playwright CLI
with Microsoft Edge in a visible window.

## Before starting

- Confirm the URL with the user and whether it's local, a dev/staging
  environment, or production. **Production → ask again** and recommend
  staging or local instead; if they still choose production, keep strictly
  to the read-only rules below.
- Ask the user to use a test account where possible, since screens may
  show real data.

## Open and log in

```bash
npx playwright-cli open --browser msedge --headed "<app-url>"
```

- If the app needs a login, tell the user the window is open and ask them
  to sign in themselves. Never type, store, or ask for credentials in the
  conversation.
- If a bot check or CAPTCHA appears, stop and ask the user to solve it in
  the window; continue only after they confirm.
- After login, take a `snapshot` to confirm you're inside the app.

## Read-only rules

- Navigate by URL (`goto`) wherever possible.
- Allowed clicks: opening menus, tabs, accordions, dialogs, dropdowns, and
  hover/focus states — anything that only changes what's shown.
- Never click submit, save, delete, approve, send, pay, or anything whose
  label or handler suggests a change. If unsure, skip it and note the
  state as not captured.
- Never type into fields except to reveal a validation/empty state on a
  form you will not submit; clear it afterwards.

## Per screen

For each included route:

1. `goto` the route. If it needs an ID, use one from a list screen
   captured earlier; if none is reachable, note it and move on.
2. For each viewport — 375×812, 768×1024, 1440×900:
   - resize, wait for the page to settle (network idle, no spinners);
   - save a full-page screenshot to
     `docs/design-system/<app>/captures/<area>-<screen>-<width>.png`.
3. At 1440 only, record:
   - a DOM snapshot of the main content (structure, text, roles);
   - computed styles of representative elements — page background, body
     text, headings, primary/secondary buttons, inputs, cards/panels,
     table rows, nav items, links — color, background, font family,
     size, weight, line height, letter spacing, padding, margin, gap,
     border, radius, shadow;
   - the CSS custom properties defined on `:root` and theme roots, with
     their resolved values.
4. Capture reachable states: an open dialog or menu, a hover and focus
   state on a primary control, and empty/error states where they show
   without changing data.

Save the recorded structure and styles as
`docs/design-system/<app>/captures/<area>-<screen>.json` so the board
build can use them without reopening the browser.

## Finish

- `npx playwright-cli close`.
- Note in `DESIGN.md`: the environment captured (local / staging /
  production), the date, the viewports, and any screens or states not
  captured and why.
- `captures/` is git-ignored: screenshots may contain real data.
