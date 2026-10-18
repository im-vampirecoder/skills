# Task File → Azure DevOps Field Mapping

Canonical mapping used by `vc-sync-to-tracker` when pushing a
`task-<m>-<task-slug>.md` file (written by `vc-tasks-breakdown`) to
Azure DevOps as a Task.

## Field map

| Azure DevOps field | Source in the task file | Notes |
|---|---|---|
| `System.Title` | The `# <m>. <Task title>` heading, with the leading `<m>. ` numbering stripped | Same stripping rule as a story's title — the number is for local reading order only. |
| `System.Description` | The task's `## Notes` section, plus its `Files:` line, plus a trailing source-link paragraph | See "Description body" below. |
| `System.AreaPath` | `.vc/config.toml`'s `[ado].area_path` | Same as story/feature. |
| `System.IterationPath` | `.vc/config.toml`'s `[ado].iteration_path` (optional) | Omit if blank. |
| `System.Tags` | `.vc/config.toml`'s `[tags].story` | Reused as-is — no separate task-tag config. Same split-on-`,`/rejoin-with-`; ` conversion as story/feature. |
| Parent link (`System.LinkTypes.Hierarchy-Reverse`) | The task's `story_id`, resolved to that story's `ado_id` | **Never** a configured default, and never the feature or epic directly — see "Parent resolution" below. |
| `System.State` | **Not mapped.** | Never touched by a sync. |
| Story Points | **Not applicable at this level.** | Azure DevOps' Task work item type has no native Story Points field — that's a User Story-level field. The task file's `Story Points:` line stays local. See `references/story-field-mapping.md`. |
| `Microsoft.VSTS.Scheduling.OriginalEstimate` | **Not mapped.** | Estimates are complexity (Story Points), never hours. |

## Title extraction

Same rule as a story: strip the leading `<m>. ` from

```
# 2. Add duplicate-email check to signup handler
```

to get the `System.Title`:

```
Add duplicate-email check to signup handler
```

## Description body

Two or three blocks:

1. The task's `## Notes` content, rendered as HTML (same markdown → HTML
   rules as `references/story-field-mapping.md`: bold, inline code,
   paragraphs, fenced code blocks).
2. `<p><strong>Files:</strong> <task's Files: line></p>`, when the task
   has one.
3. A trailing paragraph:
   `<p><em>Source: <a href="<relative-path>"><relative-path></a></em></p>`,
   using the task file's path relative to the repo root (e.g.
   `artifacts/epic-checkout/feature-user-auth/tasks/story-3-task-2-duplicate-email-check.md`).

## Parent resolution — no configured default, no drift to detect

A task's parent is always the `ado_id` of the story named by the task's
own `story_id` frontmatter field — the same story synced earlier in this
run (or, in Task-only Mode, already on record from a prior run). Nothing
in this pipeline reassigns a task to a different story after
`vc-tasks-breakdown` writes it, so — same reasoning as a story's
`feature_id` — there's no re-parenting check: the parent relation is set
once, at CREATE, and UPDATE never touches it.
