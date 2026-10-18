# Story File → Azure DevOps Field Mapping

Canonical mapping used by `vc-sync-to-tracker` when pushing a
`stories-<n>-<description>.md` file to Azure DevOps, as whichever
story-level work item type `.vc/config.toml`'s
`[ado].story_work_item_type` names for this project — "User Story",
"Product Backlog Item", or another process-specific name. See
`vc-sync-to-tracker`'s "Story work item type" section for how that's
detected.

## Field map

| Azure DevOps field | Source in the story file | Notes |
|---|---|---|
| `System.Title` | The `# <n>. [<feature-slug>] <Story title>` heading, with the leading `<n>. ` numbering stripped | Keep the `[<feature-slug>]` bracket tag — `vc-create-user-stories` already baked it in, there's nothing to prompt for here (unlike a scheme that resolves the tag at sync time). |
| `System.Description` | HTML of the As-a/I-want/So-that block, plus a trailing source-link paragraph | See "Description body" below. |
| `Microsoft.VSTS.Common.AcceptanceCriteria` | The `## Acceptance Criteria` items | Each numbered `1. **Given** ... **When** ... **Then** ...` item (the format `vc-create-user-stories` and `vc-create-pbi` write) becomes one `<li>`; older single-line `- Given ...` bullets are accepted too. See "Acceptance Criteria conversion" below. |
| `Microsoft.VSTS.Scheduling.StoryPoints` | The story's `## Details` section's `- Story Points: <n>` bullet, when present | Written by `vc-tasks-breakdown` after generating the story's task breakdown — may not exist yet for a story that hasn't been broken down. Omit the field entirely from the sync payload when absent, same treatment as a blank `IterationPath`. |
| `System.AreaPath` | `.vc/config.toml`'s `[ado].area_path` | Backslash-separated when nested, e.g. `MyProject\Backend`. |
| `System.IterationPath` | `.vc/config.toml`'s `[ado].iteration_path` (optional) | Omit the field entirely if blank — Azure DevOps falls back to the team's default iteration. |
| `System.Tags` | `.vc/config.toml`'s `[tags].story`, plus every requirement ID on the story's `## Details` `- Implements:` bullet | `[tags].story` is applied on create only; leave it alone on update unless the user asks to change it. `[tags].story` may hold multiple tags as a comma-separated string (e.g. `vc,backlog`) — split on `,`, trim whitespace, and rejoin with `; ` (Azure DevOps' own tag delimiter) before writing `System.Tags`. Requirement IDs are kept in step on every sync — see "Requirement ID tags" below. |
| Parent link (`System.LinkTypes.Hierarchy-Reverse`) | The story's `feature_id`, resolved to that feature's `ado_id` (synced earlier in the same run) | **Never** a configured default, and never the epic directly — see "Parent resolution" below. |
| `System.State` | Set to `.vc/config.toml`'s `[ado].ready_state` only when the story file says `status: ready` and the work item is still in its starting state | The only State change a sync makes, confirmed by the user first. See the skill's step 5 "Ready state". Every other State is left alone. |
| Priority, Dependencies (the story's "Details" section) | **Not mapped (for now).** | Stay local-only; not pushed to any Azure DevOps field in this version. |

## Requirement ID tags

Each full ID on the story's `- Implements:` bullet (e.g.
`FR-checkout.pay-with-stripe`) becomes one tag, written exactly as in
the file, so a tag query in Azure DevOps finds every story that builds a
requirement. `none`, or no `Implements:` bullet → no requirement tags.

- **Create**: the `[tags].story` tags plus the requirement IDs, joined
  with `; `.
- **Update**: read the work item's current `System.Tags`, split on `;`
  and trim. Add each Implements ID that's missing. Remove a tag only when
  it has a requirement ID's shape (`FR-`, `NFR-`, `BR-` or `ERR-`, then
  `<feature-slug>.<name>`) and is no longer on the Implements bullet,
  e.g. a retired ID the story stopped citing. Every other tag, including
  ones people added on the board, stays. Nothing changed → don't send
  the field.

## Title extraction

Input heading:

```
# 3. [user-auth] Add email/password signup
```

Strip the leading `<n>. ` (a number, period, single space) to get the
`System.Title`:

```
[user-auth] Add email/password signup
```

The numbering exists for local reading order (matches the file's
`stories-<n>-...` name); it has no meaning in Azure DevOps once the
work-item ID takes over ordering, so don't carry it into the title.

## Description body

Exactly two blocks:

1. The As-a/I-want/So-that block, rendered as HTML.
2. A trailing paragraph:
   `<p><em>Source: <a href="<relative-path>"><relative-path></a></em></p>`,
   using the story file's path relative to the repo root (e.g.
   `artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md`).
   The path renders as plain text if the repo isn't browsable from
   Azure DevOps, but it's the canonical pointer back to the full story —
   the acceptance criteria's Given/When/Then detail lives there, not
   duplicated in Description.

Example:

```html
<div>
<p><strong>As a</strong> new visitor<br>
<strong>I want to</strong> create an account with email and password<br>
<strong>So that</strong> I can save my progress across sessions</p>
<p><em>Source: <a href="artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md">artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md</a></em></p>
</div>
```

## Acceptance Criteria conversion

Each item in the story's `## Acceptance Criteria` section becomes one
`<li>`. The stories skills write each criterion as a numbered item with
`**Given**`, `**When**` and `**Then**` on their own lines (hard line
breaks, a blank line between items). Join an item's lines with a space,
keep the bold keywords, and drop the leading `<n>. ` - the `<ol>` numbers
the items again.

Input:

```markdown
1. **Given** a valid email and password,  
   **When** the user submits the form,  
   **Then** an account is created and the user is signed in.

2. **Given** an email already in use,  
   **When** the user submits the form,  
   **Then** a clear inline error is shown and no account is created.
```

Output:

```html
<div>
<ol>
<li><strong>Given</strong> a valid email and password, <strong>When</strong> the user submits the form, <strong>Then</strong> an account is created and the user is signed in.</li>
<li><strong>Given</strong> an email already in use, <strong>When</strong> the user submits the form, <strong>Then</strong> a clear inline error is shown and no account is created.</li>
</ol>
</div>
```

Story files written before v1.11.1 may still use one `- Given ..., when
..., then ...` bullet per criterion. Treat each bullet as one item the
same way, bolding the `Given`/`When`/`Then` keywords where they appear.
An item ends at the next numbered item, the next bullet, or the next
`##` heading; a blank line inside the section never ends the list.

General markdown → HTML rules (fidelity over aesthetics; readers open the
work item in the Azure DevOps web UI, which renders the HTML directly):

| Markdown | HTML |
|---|---|
| `**bold**` | `<strong>bold</strong>` |
| Inline `` `code` `` | `<code>code</code>` |
| Blank line | New `<p>` paragraph |
| Fenced code block | `<pre><code>...</code></pre>`, with `<`, `>`, `&` escaped inside |

## Parent resolution — no configured default, no drift to detect

A story's parent is always the `ado_id` of the feature recorded at
`artifacts/epic-<epic-slug>/feature-<feature-slug>/prd.md`, which
`vc-sync-to-tracker` syncs (creating or refreshing it) earlier in the
same run, before touching any story. There is no `default_parent`-style
config value anywhere in this skill — the correct parent is always
derivable from `feature_id` in the story's own frontmatter.

Unlike the epic-under-a-feature relationship (which can drift — see
`references/feature-field-mapping.md`'s re-parenting section, since
`vc-propose-epic` can reassign a feature to a different epic after the
fact), a story's `feature_id` never changes after `vc-create-user-stories`
writes it: nothing in this pipeline reassigns a single story to a
different feature. So there's no re-parenting check to run here: the parent relation is set
once, at CREATE, and UPDATE never touches it at all — there's nothing
that could have drifted since.
