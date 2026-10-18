# Progress File

A per-run record of where a `vc-implement` run stands, so an
interrupted run (session ended, context lost, a worker died, a different
agent picking it up) can resume from the last checkpoint instead of
rebuilding state from git and re-asking the user.

## Location

One file per target the user pointed the skill at:

- Story → `<feature folder>/tasks/story-<n>-progress.md`, beside
  `story-<n>-spec.md` (the feature folder is `artifacts/<feature-slug>/`
  or `artifacts/epic-<epic-slug>/feature-<feature-slug>/`; it moves with
  the folder on `/vc:propose-epic`).
- Bug → `artifacts/bugs/progress/<bug-slug>.md` — a subfolder, so it
  never shows up in the `artifacts/bugs/*.md` listing that sprint
  planning reads as bugs.

The skill writes it but never stages, commits, or gitignores it — the
developer decides whether it belongs in the tracking repo's history.

## Single writer

Only the orchestrating `vc-implement` run writes this file. A
`vc-implement-worker` never touches it; it reports its state back, and
the orchestrator records that report under the worker's repo section.
Parallel writers to one file would overwrite each other.

Consequence: a worker interrupted mid-slice leaves no checkpoint of its
own beyond its task files' `Status: Done` and its git state — which is
exactly what the resume check below re-reads, so nothing is lost that
can't be recovered.

## Format

```markdown
---
target: STORY-<feature-slug>-<n> | BUG-<bug-slug>
status: in-progress | blocked | ended-early | completed
current_step: <1-9>
started: <YYYY-MM-DD HH:MM>
updated: <YYYY-MM-DD HH:MM>
---

# Implement progress: <story or bug title>

Source: <relative path to story-<n>-spec.md or the bug file>

## Repos

### <repo-name>
- Branch: <branch-name>
- Worktree: <submodule_root>/<repo-name>/.worktrees/<branch-name>
- Base: origin/<default-branch> @ <short sha>
- Baseline: green | failing (user chose to proceed)
- Step: <n> — <label, e.g. "4 implement">
- Current task: TASK-<feature-slug>-<n>-<m> — seam confirmed | red | green | refactor | none
- Review: not run | clean | findings (see Decisions)
- Commit: <short sha> | none
- Pushed: yes | no
- PR: <url> | declined | none
- Worktree after run: kept | removed

## Decisions
- <YYYY-MM-DD> — <question> → <answer>

## Tracker updates
- <ado_id> (<story | task | bug>): <old state> → <new state> — <YYYY-MM-DD>

## Log
- <YYYY-MM-DD HH:MM> — <event>
```

Task completion is **not** duplicated here — each task file's own
`Status:` stays the source of truth. The progress file only holds what
lives nowhere else: per-repo branch/worktree, the in-flight task's
phase, review/commit/push/PR outcome, user decisions, tracker moves.

Record under **Decisions** every answer a resumed run would otherwise
have to ask again: confirmed seams, a non-`main`/`master` default
branch, a failing-baseline go-ahead, review-finding choices, the "done"
state value chosen for this run, and the story/bug close answer.

## Checkpoints — when to write

Write (and bump `updated`, `current_step`, append a Log line) right
after each of these, never batched to the end:

| Step | Checkpoint |
|---|---|
| 1 | User confirmed — create the file (`status: in-progress`), record the start tracker move |
| 2 | Repos resolved — one `### <repo-name>` section each |
| 3 | Worktree created, baseline result |
| 4 | Seams confirmed; each task's phase change; each task marked `Done` |
| 5 | Review outcome; each tracker update; story/bug close answer |
| 6 | Commit-or-end choice (`ended-early` when every repo chose end) |
| 7-8 | Commit sha, push, PR url or declined |
| 9 | Worktree kept/removed |

A worker's report (multi-repo runs) is a checkpoint too — record it as
soon as it arrives, including a worker stopped on a question
(`status: blocked`, the pending question in the Log).

Run finishes (every repo through step 9, or ended at step 6) → set
`status: completed` (or `ended-early`) and keep the file as the record
of the run. Never delete it.

## Resume — checked at step 1

After resolving the target, look for its progress file.

- **None** → normal run; create it at step 1's confirmation.
- **`completed`/`ended-early`** → say so with a one-line summary from
  the file. Running again (e.g. the story had tasks a prior run left) →
  set `status: in-progress`, `current_step: 1`, append a "Run reopened"
  Log line, and continue as a normal run that keeps the existing
  Decisions/Tracker history.
- **`in-progress`/`blocked`** → verify before trusting it, per repo:
  - Worktree path exists and is on the recorded branch.
  - Missing worktree but the branch exists locally or on `origin` (e.g.
    resuming on another machine after a push) → offer to recreate the
    worktree from that branch — the one exception to step 3's "always
    from the default branch" rule, since the work lives on the branch.
  - Branch gone everywhere → that repo's work is lost; say so and offer
    to restart that repo from step 3.
  - Recorded commit/push/PR still match (`git log`, `git ls-remote`).
  - Task files' `Status: Done` match what the Log says was finished.
  - In-flight task at `red`/`green`/`refactor` → re-run the test suite
    in the worktree to re-establish the real phase; don't trust the
    recorded one.

  Then post a short recap (target, per-repo step, last Log entry, any
  mismatch found) and ask via `AskUserQuestion`: "Resume from step <n>"
  (Recommended) vs. "Start over" — start over resets each repo section
  and `current_step` but keeps Decisions, Tracker updates, and the Log,
  appending a "Restarted" line. A recorded worktree/branch still
  present blocks step 3 from recreating it — handle it with step 9's
  cleanup rules (ask, never force, never discard unpushed work silently)
  before starting over. Resuming reuses recorded Decisions instead of
  re-asking them.
