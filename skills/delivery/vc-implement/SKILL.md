---
name: vc-implement
description: Implement a confirmed story's task breakdown or a standalone bug end-to-end — worktree off the target repo's fetched default branch, test-first implementation, review, tracker status update, commit, and PR. Keeps a progress file per story or bug so an interrupted run resumes from its last checkpoint. vc's developer-pipeline terminal step; built-in only, no delegation.
---

# Implement

Take a confirmed story's `story-<n>-spec.md` (written by
`vc-tasks-breakdown`) or a standalone `artifacts/bugs/<bug-slug>.md`
(written by `vc-bug-report`) and build it: worktree, test-first
implementation, review, tracker status update, commit, optional PR.
Nothing runs after this automatically.

Every run keeps a **progress file** for the story or bug it was pointed
at — `<feature folder>/tasks/story-<n>-progress.md` or
`artifacts/bugs/progress/<bug-slug>.md` — written at each checkpoint so
an interrupted run can resume where it stopped. Format, checkpoints, and
the resume check: `references/progress-file.md`.

## Workflow

1. **Resolve input & confirm understanding**
   - `$ARGUMENTS` → a story (`STORY-<feature-slug>-<n>`, its `ado_id`, or
     a path to `story-<n>-spec.md`/`stories-<n>-*.md`) or a bug
     (`BUG-<bug-slug>`, its `ado_id`, or a path to
     `artifacts/bugs/<bug-slug>.md`). Ambiguous → ask which.
   - Story: read `story-<n>-spec.md`, its task files, and the source
     story file (for `ado_id`, story-slug). Bug: read the bug file
     directly.
   - **Progress file found** (not `completed`/`ended-early`) → this is
     an interrupted run: verify it against git and the task files,
     recap, and offer "Resume from step <n>" vs. "Start over". Resuming
     skips straight to the recorded step and reuses recorded decisions.
     Full check: `references/progress-file.md`, "Resume".
   - Restate the outcome, the task list (or repro/expected/actual), any
     `## Open Questions`, and constraints. Confirm with the user before
     touching git — don't re-scout the codebase, `vc-tasks-breakdown`
     already did that.
   - The same confirmation covers marking the story or bug started
     (`status: in-progress` in its file; on Azure DevOps, a story's work
     item also moves to `[ado].active_state`, e.g. `Active`). Apply it
     right after the user confirms. Full rules:
     `references/verification-and-tracker-update.md` section 0.
   - Create the progress file at that same confirmation, then update it
     after every checkpoint in steps 2-9 — never batched to the end.

2. **Resolve target repo(s)**
   - Group the work by which `src/<repo-name>/` submodule(s) it touches.
   - **One repo** → continue with steps 3-5 directly.
   - **More than one repo** → dispatch one worker per repo in parallel
     (each owns a disjoint repo and disjoint files). A worker that hits a
     decision only the user can make stops and reports what it needs;
     relay that to the user and resume it with the answer. Collect every
     worker's report before moving to step 6.
   - Full procedure, including bug-repo resolution and worker
     dispatch: `references/resolve-target-and-worktree.md`.

3. **Fetch latest default branch, create the worktree**
   - `git fetch origin`, detect the default branch (`origin/HEAD`),
     confirm with the user if it's neither `main` nor `master` or
     detection fails.
   - Branch: `feat/<ado_id>-<story-slug>` (story) or
     `fix/<ado_id>-<bug-slug>` (bug); omit the id segment if `ado_id` is
     null.
   - Create the worktree from the fetched remote ref, never a local
     branch, under `.worktrees/` (gitignored; add + commit the ignore
     entry if missing). Run project setup and a clean-baseline test pass.
   - Full procedure: `references/resolve-target-and-worktree.md`.

4. **Implement, test-first**
   - One task (or, for a bug, one repro-to-fix slice) at a time. Before
     the first test of a task, state the seam(s) under test and confirm
     with the user.
   - Red → green → light refactor per slice: no production code without
     a failing test first; watch it fail for the right reason; minimal
     code to pass; watch it pass with no regressions.
   - Follow the conventions already noted in the task files' Notes. Full
     task scope, nothing speculative added.
   - Mark a task file's `Status:` as `Done` once its criterion is met and
     its tests are green.
   - Full loop, anti-patterns, and rationalizations to reject:
     `references/tdd-implementation-loop.md`.

5. **Review and update tracker status**
   - Invoke `/vc:code-review` against the diff and the acceptance
     criteria before calling this done. A found regression or unmet
     criterion stops here — present options via `AskUserQuestion`, never
     silently patch around it.
   - For every `Done` task (or the bug) that already has an `ado_id`,
     update its tracker state to reflect completion. Once every
     non-`Skipped` task under a story is `Done`, offer to close the
     story: `status: done` in its file, plus the tracker state when it
     has an `ado_id`. A verified bug fix gets the same offer for the bug
     file.
   - When the story just closed was the feature's last open one (every
     `stories-*.md` in the feature folder is `done` or `removed`) and the
     PRD isn't `delivered` yet, offer `/vc:prd deliver <feature>`,
     which freezes the PRD's requirements. The PO confirms delivery; on
     a no, or when the developer isn't the PO, say that the PO can run it
     later. Never deliver automatically.
   - Full procedure, including the "done" state resolution and why this
     is a deliberate exception to `vc-sync-to-tracker`'s own "never
     touch State" rule: `references/verification-and-tracker-update.md`.

6. **Ask: commit and push, or end here** (per repo, if more than one)
   - `AskUserQuestion`: "Commit, push, and consider a PR" vs. "End here,
     leave the worktree as-is."

7. **Propose the commit message**
   - Single line, under 100 characters, no AI/assistant attribution.
     Present it and wait for approval or an edit before committing.

8. **Commit, push, ask about a PR**
   - Commit with the approved message, push the branch to `origin`.
   - Ask whether to open a PR. If yes: title + description drafted from
     the story's/bug's own content, no AI attribution anywhere, against
     the default branch from step 3. Detect GitHub vs. Azure DevOps from
     the repo's own remote URL.
   - Full detail: `references/finish-commit-and-pr.md`.

9. **Ask: drop the worktree or leave it**
   - Leave it if anything is uncommitted; otherwise remove on
     confirmation, refusing (and asking) if the worktree holds files that
     exist nowhere else. Repeat steps 6-9 for each repo when more than
     one was dispatched.
   - Full detail: `references/finish-commit-and-pr.md`.

## Notes

- No delegation branch. Test-first implementation, seam confirmation, and
  the red/green loop are this skill's own built-in behavior, not a
  configurable choice.
- Never touches the submodule pointer or git state of the tracking repo —
  all git operations happen inside the target `src/<repo-name>/`
  checkout(s).
- Depends on the `vc-implement-worker` agent, shipped in the repo's
  top-level `agents/vc-implement-worker.md` and installed with the
  plugin or the file install (see
  `references/resolve-target-and-worktree.md`) — it's a plain Task-tool
  subagent, spawned only when a run spans more than one repo.
- The progress file is written only by the orchestrating run — a
  worker reports its state and the orchestrator records it. The skill
  never stages, commits, or gitignores the progress file; whether it
  goes into the tracking repo's history is the developer's call. It is
  kept after the run finishes (`status: completed`) as the run's record.
- Depends on `/vc:code-review` (step 5) and reads output from
  `vc-tasks-breakdown`/`vc-bug-report`; writes tracker state changes
  (started in step 1, finished in step 5) — a separate concern from
  `vc-sync-to-tracker`, which touches State only to push `ready`.
- This is vc's developer-pipeline terminal step. Nothing invokes this
  skill automatically, and this skill invokes nothing after itself,
  except `/vc:prd deliver <feature>` when the PO accepts step 5's
  offer after the feature's last story closes.
