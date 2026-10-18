# Local Preview

Loaded by `vc-extract-design-system` (step 7 and the `preview` mode)
and by `vc-create-ui-mockup` when it adds boards. Lets anyone view and
click through the canvas from the repo, with no publish to claude.ai.

## Files

Copied from this skill's `assets/local-preview/`, overwriting older
copies (they belong to the skill, never edited by hand):

| Repo path (under `docs/design-system/<app>/`) | From | Role |
|---|---|---|
| `canvas/project/support.js` | `support.js` | The line every board loads. Uses the real Design runtime when it's downloaded and the page is served; otherwise a small built-in runtime |
| `canvas/project/proposed/<feature-slug>/support.js` | `support.js` | Same, for boards in a Proposed subfolder (each folder needs its own copy) |
| `canvas/index.html` | `index.html` | The overview: every board laid out from `canvas.json`, page tabs, zoom, click a name to open the board |
| `canvas/local/serve.mjs` | `serve.mjs` | Local server (Node 18+, no dependencies) |
| `canvas/local/blob-map.js` | written by the skill | Maps upload ids to local files, so `/_blob/<id>` keeps working locally |
| `canvas/local/artifact-type/dc-runtime.js` | downloaded, git-ignored | The real Design runtime |

## The real runtime — refreshed on every run

Every `scan`, `refresh`, `publish`, `pull` and `preview` run downloads
the current runtime first, so the local view tracks claude.ai's own
renderer. This is a read; nothing is published.

1. Source: `DESIGN.md`'s `claude_design.canvas_url` if set. Otherwise
   any Design canvas the user owns: Artifact `list` with
   `type: "Design"`, take the first. Every Design canvas serves the same
   runtime release.
2. Artifact `read` that url with `path: "artifact-type/dc-runtime.js"`
   and `out_dir: docs/design-system/<app>/canvas/local` (it lands at
   `canvas/local/artifact-type/dc-runtime.js`). Saving into the repo asks
   the user once; that's expected.
3. Record the source url and the version the read reports in
   `DESIGN.md`'s `local_preview` block.
4. No canvas to read from, not signed in to claude.ai, or the read fails:
   say so in one line and carry on. The built-in runtime covers the
   board subset this skill writes, and the next run tries again.

Add `docs/design-system/*/canvas/local/artifact-type/` to the tracking
repo's `.gitignore` if missing: it's claude.ai's file, fetched fresh by
each person, never committed.

## `blob-map.js`

```js
window.__vcBlobMap = {
  "948073035162e3c1304c49e8ece96705": "assets/fonts/TTCommonsPro-Regular.woff2"
};
```

Keys are upload ids, values are paths relative to
`docs/design-system/<app>/`. The publish step adds one entry per upload
(`claude-design-sync.md`). Before the first publish it's an empty map,
since boards still point at the local files directly.

## Running it

Tell the user, after any run that wrote boards:

```bash
node docs/design-system/<app>/canvas/local/serve.mjs   # optional port, default 4321
```

then open `http://127.0.0.1:4321/` (the overview). Boards marked ▶ have
working controls; links between boards click through like the canvas's
Play mode. A single board also opens straight from disk
(double-click the `.dc.html`), using the built-in runtime.

Never start the server unasked; give the command.

## Publish and pull leave these alone

- Publish sends only `canvas/project/**/*.dc.html` and
  `canvas/project/canvas.json`. Never `support.js`, `index.html` or
  anything in `canvas/local/`: on claude.ai the canvas serves its own
  `support.js`.
- Pull reads only the files the live canvas lists under `project/`,
  which never include `support.js`.
