# Azure DevOps Transport — CLI Only, Never `az rest`

All Azure DevOps API calls in this skill go through the Azure DevOps CLI
extension — `az boards ...` for short, simple field operations and
`az devops invoke ...` for anything that needs to carry HTML content.
**Do not use `az rest` for Azure DevOps endpoints.**

## Why this matters

- **Auth path divergence.** `az rest` resolves tokens via the MSAL cache
  populated by `az login`. The `az devops` extension uses a separate
  cached credential (PAT or AAD token kept by the extension). On a
  machine where `az boards work-item show` works but `az login` hasn't
  been refreshed against the current cloud tenant, `az rest` fails with
  `User '<email>' does not exist in MSAL token cache. Run 'az login'.`
  while the extension keeps working. The extension is the path that
  survives normal day-to-day auth state.
- **Windows `cmd.exe` argument length cap.** On Windows, `az` runs
  through `az.cmd`, which goes through `cmd.exe`. The full command line
  is capped at ~8,191 characters. A single story's or feature's
  Description + Acceptance Criteria HTML routinely exceeds this. Passing
  it inline via
  `az boards work-item create --description "..." --fields
  "Microsoft.VSTS.Common.AcceptanceCriteria=..."` fails with `The
  command line is too long.` even though the strings are individually
  valid. The fix is a JSON Patch document loaded from a file via
  `az devops invoke --in-file ...`, which is exactly what the work-items
  REST API accepts.
- **Quoting hazards in `--fields`.** `--fields "key=value"` becomes
  unreadable for multi-kilobyte HTML containing `&`, `<`, `>`, backticks,
  and emoji — inline quoting mangles different characters differently
  across PowerShell/cmd/bash. A JSON Patch body file removes all of
  this; the JSON encoder handles escaping once, deterministically.

## Rule of thumb

| Operation | Use |
|---|---|
| Read a work item, list relations, query by WIQL, add/remove a parent link, simple field tweak (short title, tag) | `az boards work-item show` / `relation add` / `relation remove` / `update` / `az boards query` — direct, no body file needed |
| Create a story, feature or bug with full HTML fields | `az devops invoke --area wit --resource workitems --http-method POST --in-file <body>.json --media-type application/json-patch+json` |
| Update a story, feature or bug with full HTML fields | `python.exe -IBm azure.cli boards work-item update --fields ...` (see UPDATE — `invoke` PATCH fails with `KeyError: 'type'`) |
| Any work-item CREATE where the inline command would exceed ~7,000 chars | `az devops invoke` with `--in-file` |
| Azure DevOps REST endpoints, ever | **Never** `az rest` |

If a future call has no `az boards` equivalent, fall back to
`az devops invoke`, never to `az rest`. If the user explicitly requests
`az rest`, surface this rule and ask them to confirm before proceeding.

## Building the JSON Patch body

```jsonc
// body.json — JSON Patch (RFC 6902) consumed by the work-items REST API
[
  { "op": "add", "path": "/fields/System.Title",                             "value": "<TITLE>" },
  { "op": "add", "path": "/fields/System.AreaPath",                          "value": "<area_path>" },
  { "op": "add", "path": "/fields/System.IterationPath",                     "value": "<iteration_path>" },
  { "op": "add", "path": "/fields/System.Description",                       "value": "<HTML_DESCRIPTION>" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria", "value": "<HTML_AC>" },
  { "op": "add", "path": "/fields/System.Tags",                              "value": "<tags.story>" }
]
```

- Omit the `System.IterationPath` line if `.vc/config.toml`'s
  `[ado].iteration_path` is blank — Azure DevOps falls back to the
  team's default iteration.
- `[tags].story` may be a comma-separated list (e.g. `vc,backlog`).
  Split on `,`, trim whitespace from each tag, and rejoin with `; `
  before putting it in `<tags.story>` above — `; ` is the delimiter
  Azure DevOps itself uses for `System.Tags`, not `,`.
- For UPDATE, all of the above are optional to include — send only the
  fields that changed. Title/Description/AcceptanceCriteria are the
  typical set.
- Write the file as UTF-8 without BOM.
- Use HTML entities (e.g. `&#128077;` for 👍) for anything above ASCII
  inside the HTML strings, keeping the JSON body itself pure ASCII —
  this sidesteps Windows console cp1252 encoding issues when `az` prints
  the response.

## CREATE

```bash
az devops invoke \
  --area wit --resource workitems \
  --route-parameters project=<project> type="<work-item-type>" \
  --api-version 7.1 \
  --media-type application/json-patch+json \
  --http-method POST \
  --in-file <body.json> \
  --out-file <response.json>
```

- `project=<project>` **must** be passed as a `--route-parameters`
  entry. `az devops configure --defaults project=...` only applies to
  top-level `--project` flags, not to invoke route placeholders —
  omitting it makes the extension fall back to an org-scoped route
  template that doesn't exist for this endpoint, producing `The
  controller for path '/_apis/wit/workItems/<id>' was not found ...
  404`.
- `type` is the plain string for whichever work item type is being
  created, no leading `$` — the extension supplies the `$` from the URL
  template itself. Passing `$User Story` double-prefixes and 404s. `Epic`
  and `Feature` are fixed names across process templates; the story
  level is not — it's `.vc/config.toml`'s `[ado].story_work_item_type`
  (`"User Story"`, `"Product Backlog Item"`, or whatever that project's
  process template calls it — see `vc-sync-to-tracker`'s "Story work
  item type" section for how it's detected). With `project=` supplied
  correctly, the extension URL-encodes a space in the type name (e.g.
  `User%20Story`) and the call succeeds regardless.
- Read the response's `id` field. If the response is hard to parse
  because `az` printed warnings into the output stream, fall back to:
  ```bash
  az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.Title] = '<TITLE>' ORDER BY [System.Id] DESC" --output json
  ```
  and take the highest `id` matching the title just created.
- Add the parent relation as a separate call (not part of the JSON
  Patch body) — the epic's `ado_id` when creating a feature, or the
  feature's `ado_id` when creating a story:
  ```bash
  az boards work-item relation add \
    --id <NEW_ID> \
    --relation-type parent \
    --target-id <parent-ado-id>
  ```

## UPDATE

**Do not use `az devops invoke ... --http-method PATCH` with
`--route-parameters project=... id=...`.** The extension resolves the
`workitems` resource to the create-style route template (which needs
`type`) and fails with `KeyError: 'type'`. Use `az boards work-item
update` instead, bypassing `az.cmd` so the `cmd.exe` length cap doesn't
apply (the limit becomes the ~32,767-char `CreateProcess` limit):

```powershell
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe" -IBm azure.cli `
  boards work-item update --id <WORK_ITEM_ID> `
  --fields "System.Title=$title" "Microsoft.VSTS.TCM.ReproSteps=$repro"
```

- Pass only the fields that changed, one `Field=value` per `--fields`
  entry. Read the HTML from files into variables first
  (`$repro = Get-Content -Raw -Encoding utf8 repro.html`) rather than
  pasting it inline, so quoting is handled by the shell once.
- Locate the interpreter from `az` itself if the path above differs:
  `(Get-Command az).Source` sits next to `..\CLI2\python.exe`.
- If a single update would still exceed ~30,000 characters, split it
  across several `update` calls, each carrying a subset of the fields.
- The JSON Patch body file is only used for CREATE.
