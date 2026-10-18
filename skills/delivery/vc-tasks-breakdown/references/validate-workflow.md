# Validate Mode Workflow

Re-verify a story's generated task breakdown
(`<feature folder>/tasks/story-<n>-*`, where the feature folder is
`artifacts/<feature-slug>/` or `artifacts/epic-<epic-slug>/feature-<feature-slug>/`)
against the current codebase, interview the user on anything uncertain,
and log the outcome — before the team commits real time to implementing
it.

## Story Resolution

1. If a story identifier follows `validate` in `$ARGUMENTS`, resolve it the
   same way step 1 of the main workflow does.
2. Otherwise, list every story under any `artifacts/*/tasks/` (unassigned)
   or `artifacts/epic-*/feature-*/tasks/` folder that has a `story-<n>-spec.md` and ask which one to validate.
3. No `story-<n>-spec.md` found at all for the resolved story → tell the
   user to run `/vc:tasks-breakdown <story>` first, and stop.

## Step 1: Read the Story's Spec

- `story-<n>-spec.md` (Approach, Tasks table, Open Questions)
- Every `story-<n>-task-<m>-*.md` (Status, Addresses, Files, Story Points, Notes, Overlaps
  if any)
- The source story file, for its Acceptance Criteria

## Step 2: Verification Pass (evidence-based)

For every task not marked `Skipped`:

- **File citations**: re-`Glob`/`Grep` every path in its `Files:` line.
  Still exists and still looks like what the task describes → `VERIFIED`.
  Missing or renamed → `FAILED`, and if a `Glob` turns up an obvious
  rename/move, note it as a candidate fix. Genuinely ambiguous →
  `UNVERIFIED`.
- **Status re-check**: for a task marked `Extend` or `Verify`, confirm the
  cited file still shows the partial/complete coverage claimed — code
  moves between generation and validation. Mismatch → `FAILED`, note what
  the code actually shows now.

For the story as a whole:

- **AC coverage**: does the union of non-`Skipped` tasks address every
  Given/When/Then criterion in the story? List any criterion with no task
  addressing it, and any task whose `Addresses:` doesn't match a real
  criterion.
- **Completeness**: does every non-`Skipped` task have a `Story Points:` line
  (and no leftover `Effort:` hours line),
  and does the story have a `Story Points:` line in its own `## Details`?

No tiering by task count — a story's task list is small enough to check
every citation, unlike a multi-phase feature plan.

## Step 3: Generate Questions

For each `FAILED`/`UNVERIFIED` finding and each open item below, write a
concrete question with 2-4 options, recommended one marked:

- A `FAILED` file citation → options built from what `Glob` actually
  found (a renamed path as the recommended fix, or "mark this task
  needing investigation" if nothing plausible turned up).
- An AC with no task addressing it → options: "add a task for it now" /
  "confirm it's covered by an existing task's Notes, just re-tag
  `Addresses:`" / "confirm it's genuinely out of scope, note why."
- Anything already sitting in `story-<n>-spec.md`'s `## Open Questions`.
- A `Status` re-check mismatch → options built from what the code
  actually shows now (e.g. "already complete — mark Verify" / "still
  partial — keep Extend, adjust Notes").

## Step 4: Interview

Before the first question, post a short recap (3-6 bullets: story title,
task count, verification summary) — this can run in a fresh session where
the spec body was never shown. Then `AskUserQuestion`, grouped up to 4 per
call. Only genuine decision points — skip a category with nothing to ask.

## Step 5: Log and Propagate

Append to `story-<n>-spec.md`:

```markdown
## Validation Log

### Session {N} — {YYYY-MM-DD}
**Trigger:** {what prompted this validation, e.g. "pre-implementation check"}

#### Verification Results
- Files checked: N — Verified: N | Failed: N | Unverified: N
- AC coverage: N/N criteria addressed
- Failures: {list, file:line or "not found"}

#### Questions & Answers
1. **[{category}]** {full question text}
   - Options: {A} | {B} | {C}
   - **Answer:** {user's choice}

#### Changes Applied
- {task file}: {what changed} — reason: {why}
```

Session number increments from the last one already in `story-<n>-spec.md`. For each answer that changes a
task, edit that `story-<n>-task-<m>-*.md` file directly (Status, Files, Addresses,
or Notes as needed) — no separate marker comment inside the task file
itself; the `## Validation Log` entry above is the record of what changed
and why.

## Step 6: Consistency Sweep

Re-read `story-<n>-spec.md` and every task file in the story's folder after
propagating. Confirm the Tasks table (Status/Story Points columns, story
complexity line) matches what the task files now say. Any task whose `Status`
changed to/from `Skipped` also needs its table row updated. Unresolved mismatch → list it and ask before recommending next
steps, don't guess.

## Output

- Verification summary (checked/verified/failed/unverified counts)
- Number of questions asked, key decisions
- Files changed
- Recommendation: ready to sync/implement, or revise first
- Readiness offer: when the recommendation is ready, no Open Questions
  remain in `story-<n>-spec.md`, and the story's `status` is `new` (missing counts
  as `new`), ask whether to mark the story ready to be put into a sprint
  - same question and same single-line `status: ready` edit as the main
  workflow's step 6.
