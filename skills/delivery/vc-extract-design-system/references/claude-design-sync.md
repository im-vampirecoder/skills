# Claude Design Sync: Publish and Pull

Loaded by `vc-extract-design-system` for `publish`, `pull`, and the
offer at the end of `scan`/`refresh`. One claude.ai artifact mirrors the
repo: the app's **Design canvas** (claude.ai "Design" type), from
`docs/design-system/<app>/canvas/project/`.

The repo is the record and the local preview (`local-preview.md`) is how
the team views it day to day. Publishing is optional: it's for people who
want to comment on or edit the canvas in claude.ai.

## Shared link — one canvas per app, for the whole team

`DESIGN.md`'s frontmatter holds the team's link:

```yaml
claude_design:
  canvas_url: https://claude.ai/artifact/<id>   # or null
  owner: <name of the person who created it>
  last_published: { at: <ISO-8601>, by: <name> }
  last_pulled: { at: <ISO-8601>, by: <name> }
```

- **A URL is set → always publish to that URL.** Never create a second
  canvas for the same app, even if publishing to it fails.
- If a publish is refused because the person running it can't edit the
  canvas: stop and tell them to ask `<owner>` to share it with them with
  **Can edit** (claude.ai → the canvas → Share). Never fall back to
  creating a new one.
- After creating the canvas for the first time, write its URL into
  `DESIGN.md` immediately and tell the user to commit it, so teammates
  publish to the same canvas. It's private until the owner shares it
  with the team.

## Publish

1. **Ask first.** "Publish the `<app>` design canvas to claude.ai?" Say
   whether this creates a new canvas or updates the existing one. No →
   stop.
2. **Pull first** when the URL exists (see Pull), so nobody's canvas
   edit is overwritten. Resolve conflicts as `refresh` step 4 does.
3. **Create if missing** (no URL in `DESIGN.md`): one Artifact publish
   with only `type_url` = the Design type
   `https://claude.ai/artifact/QKN21svewxgyPb6SYRqWnd` and
   `title` = `<App name> Design`. Record the returned URL in `DESIGN.md`
   straight away.
4. **Read the type's current instructions** from the create or read
   result, plus `artifact-type/reference/format.md` via `read` with
   `path` on the canvas's URL. They are the authority on board and
   `canvas.json` shapes; if they differ from what this skill wrote, fix
   the repo files first, then send.
5. **Uploads.** Upload each font, logo and image the boards use
   (`publish` with `asset: true` to the canvas URL), one file per call or
   several with `file_paths`. For each, add `"<id>": "<path under
   docs/design-system/<app>/>"` to `canvas/local/blob-map.js`, and swap
   the board's relative path for the returned `/_blob/<id>`. A file
   already in `blob-map.js` and unchanged is not uploaded again.
6. **Send the boards** with `root: docs/design-system/<app>/canvas`,
   paths `project/…`. Only `*.dc.html` and `canvas.json` — never
   `support.js`, `index.html` or `canvas/local/`. First publish:
   `canvas.json` with `Main.dc.html`, then the other boards in `order`, a
   few per call. Later publishes: only changed boards, `canvas.json` only
   when boards were added, removed or moved, and then read again right
   before sending, keeping every key you didn't change.
7. **Refused because someone saved meanwhile:** pull the files it names,
   redo the change on them, try once more; a second refusal → tell the
   user and stop.
8. Update `last_published` in `DESIGN.md`, plus the `generated` hash of
   every file sent (see `design-doc-template.md`), and give the user the
   link.

## Pull

1. Needs `canvas_url` in `DESIGN.md`; none → say there's nothing to pull
   and offer `publish`.
2. List the canvas's files (`list` with `scope: "files"`), then `read`
   the `project/` files with `paths` and
   `out_dir: docs/design-system/<app>/canvas`. Saving outside the
   scratchpad asks the user once; that's expected.
3. Never pull the type's own files (anything outside `project/`), and
   never overwrite `canvas/project/support.js`.
4. Pulled boards use `/_blob/<id>` URLs. An id not in `blob-map.js` (an
   image someone added on the canvas): `read` it by id with
   `out_dir: docs/design-system/<app>/assets/canvas`, then add it to
   `blob-map.js` so it shows locally.
5. Show what changed (`git diff --stat docs/design-system/<app>/`) and a
   short summary per changed board.
6. Boards added on the canvas by people (not in `generated`) are kept and
   listed as "added on canvas"; boards on the **Proposed** page belong to
   `/vc:create-ui-mockup` and are left alone.
7. Update `last_pulled` in `DESIGN.md` and remind the user to commit.

## File shapes known so far

Re-check against the type at publish time (step 4); the type wins.

- **`tokens.json`** (repo only, `docs/design-system/<app>/tokens.json`,
  never published): every family except `type` is
  `{"tokens": [{"name", "value", "usage"}]}` — a list, never a
  name→value map. `color` also has `themes: [{id, name}]`, and a color
  `value` is `{<themeId>: <value>}`, primary theme first. Names match
  `[A-Za-z0-9][A-Za-z0-9_.-]{0,63}`, unique across families. Color values:
  hex, `rgb()`, `hsl()`, `oklch()` or an alias `"{other-token}"` — never
  named colors, `var()` or `color-mix()` (convert or flag them). `type`
  has `fonts` (with `file` paths under `assets/fonts/`), `families` and
  `groups` of named styles. Every token gets a `usage` note. Keeping this
  shape means the file can seed a claude.ai Design System later without
  rework.
- **Canvas index** `project/canvas.json`: `v: 3`, `createdOnFiles`,
  `title`, `launch`, `pages` (one per feature area, plus `Proposed`),
  `boards` keyed by file path with `x, y, w, h`, `title`, `page`,
  `expand: "fill"` for screens and `is_interactive: true` for boards with
  working controls; `order`; `notes` (row titles as `kind: "title1"`);
  `designSystems: []`. Keep any key you don't change.
