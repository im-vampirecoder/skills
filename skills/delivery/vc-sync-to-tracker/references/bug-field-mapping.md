# Bug File → Azure DevOps Field Mapping

Canonical mapping used by `vc-sync-to-tracker` when pushing an
`artifacts/bugs/<bug-slug>.md` file (written by `vc-bug-report`) to
Azure DevOps as a Bug.

## Field map

| Azure DevOps field | Source in the bug file | Notes |
|---|---|---|
| `System.Title` | The `# Bug: <Title>` heading, with the leading `Bug: ` stripped | |
| `Microsoft.VSTS.TCM.ReproSteps` | Steps to Reproduce + Expected Result + Actual Result | See "Field bodies" below. Bugs do not use `System.Description`. |
| `Microsoft.VSTS.TCM.SystemInfo` | Environment + Screenshots/Logs | See "Field bodies" below. Omit the field if both are empty. |
| `Microsoft.VSTS.Common.Severity` | The bug file's `severity:` frontmatter | Value format varies by process template — Agile/Scrum/CMMI typically use `"1 - Critical"`, `"2 - High"`, `"3 - Medium"`, `"4 - Low"`. If unsure the org's template matches this, check an existing Bug's actual value first: `az boards work-item show --id <existing-bug-id> --query "fields.\"Microsoft.VSTS.Common.Severity\""` — never guess blindly. |
| `System.AreaPath` | `.vc/config.toml`'s `[ado].area_path` | Same as story/feature/task. |
| `System.IterationPath` | `.vc/config.toml`'s `[ado].iteration_path` (optional) | Omit if blank. |
| `System.Tags` | `.vc/config.toml`'s `[tags].story` | Reused as-is — no separate bug-tag config, same split-on-`,`/rejoin-with-`; ` conversion as story/feature/task. |
| Hierarchical parent (`System.LinkTypes.Hierarchy-Reverse`) | The confirmed "Bug Triage" > "Inbox" work item ID — see `SKILL.md`'s "Sync a Bug" section | Never guessed, always confirmed with the user first, every run. |
| Related link (`System.LinkTypes.Related`) | The bug file's `feature_id`/`epic_id` frontmatter, when set, resolved to that item's `ado_id` | Optional — only added when the bug names a product Feature/Epic it affects, per the bug-triage doc's own linking rule. A `null`/missing `feature_id`/`epic_id` means no Related link, not an error. |
| `System.State` | Set to `.vc/config.toml`'s `[ado].bug_ready_state` only when the bug file says `status: ready` and the work item is still in its starting state | The only State change a bug sync makes, confirmed by the user first. See the skill's bug workflow step 7. Every other State is left alone. |

## Title extraction

Input heading:

```
# Bug: Signup form accepts duplicate email addresses
```

Strip the leading `Bug: ` to get the `System.Title`:

```
Signup form accepts duplicate email addresses
```

## Field bodies

Split across two fields, matching how existing Azure DevOps Bugs are laid
out. Omit a block whose field is empty rather than rendering an empty
heading.

`Microsoft.VSTS.TCM.ReproSteps`:

```html
<div>
<p><strong>Steps to Reproduce:</strong></p>
<ol>
<li>...</li>
<li>...</li>
</ol>
<p><strong>Expected Result:</strong> ...</p>
<p><strong>Actual Result:</strong> ...</p>
</div>
```

`Microsoft.VSTS.TCM.SystemInfo`:

```html
<div>
<p><strong>Environment:</strong> ...</p>
<p><strong>Screenshots/Logs:</strong> ...</p>
</div>
```

Never put any of this in `System.Description`. Before the first bug sync
in a project, optionally compare against an existing Bug's
`ReproSteps`/`SystemInfo` (`az boards work-item show --id <bug-id>`) to
confirm the split matches the team's convention.

Same general markdown → HTML rules as `references/story-field-mapping.md`
(bold, inline code, paragraphs, fenced code blocks).

## Severity conversion

| Bug file `severity:` | `Microsoft.VSTS.Common.Severity` sent (default process template) |
|---|---|
| `Critical` | `1 - Critical` |
| `High` | `2 - High` |
| `Medium` | `3 - Medium` |
| `Low` | `4 - Low` |

## Parent resolution — two distinct relationships, never conflated

- **Hierarchical parent** (`System.LinkTypes.Hierarchy-Reverse`): every
  bug gets one, always the confirmed "Bug Triage" > "Inbox" work item —
  this is what makes a filed bug show up in the SM's daily Inbox review.
  Resolved and confirmed fresh on every sync run (see `SKILL.md`), never
  cached or reused silently, and never a configured default in
  `.vc/config.toml` — `vc-sync-to-tracker` never writes that file.
- **Related link** (`System.LinkTypes.Related`): optional, only present
  when the bug names a product Feature/Epic it affects. This is a
  traceability link, not a hierarchy link — a bug parented under Inbox
  can still relate to a Feature elsewhere in the backlog. Added as a
  separate relation call, same as any other parent-relation add in this
  skill (never part of the JSON Patch body itself).
- On UPDATE, re-check the hierarchical parent against what's currently
  confirmed (same re-parenting reasoning `references/feature-field-mapping.md`
  already documents for Epic → Feature drift) — remove the stale relation
  and add the correct one if they differ. The Related link, once set, is
  never re-checked or removed automatically; changing which Feature/Epic
  a bug relates to is a manual edit to the bug file plus a manual
  Azure DevOps relation change, out of scope for this skill.
