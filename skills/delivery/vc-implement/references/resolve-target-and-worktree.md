# Resolve Target Repo(s) and Create the Worktree

Full procedure for `vc-implement` steps 2-3.

## 1. Resolve which `src/<repo-name>/` submodule(s) are in scope

**Story input:** read every task file listed in `story-<n>-spec.md`'s
`## Tasks` table. Each task's `Files:` line names paths; the first path
segment under `.vc/config.toml`'s `submodule_root` (default `src`) is
that task's repo. Group tasks by repo. A task with no `Files:` line
(shouldn't happen post-`vc-tasks-breakdown`, but if it does) — ask the
user which repo it belongs to rather than guessing.

**Bug input:** the bug file has no scouted `Files:` list.
- If the bug names a Feature/Epic (its `feature_id`/`epic_id` frontmatter
  isn't null), read that scope's `architecture.md` (feature-level, then
  epic-level, then product-level) or `docs/architecture.md`'s System Boundaries
  section — same resolution `vc-tasks-breakdown` uses — and match the
  bug's description against it.
- Neither resolves it → ask the user directly which `src/<repo-name>/`
  submodule this bug belongs to.

## 2. Branch on repo count

- **Exactly one repo** → continue with section 3 below inline, scoped to
  every task (or the one bug).
- **More than one repo** → spawn the `vc-implement-worker` agent (shown
  as `vc:vc-implement-worker` when installed through the plugin):
  - Dispatch one worker per repo, in parallel (each owns a disjoint repo
    and disjoint files — safe to run together). Give each worker: the
    repo's path, its slice of the task list (or the bug), the shared
    story/bug context (acceptance criteria, constraints, Open Questions),
    and this reference file plus `tdd-implementation-loop.md`.
  - A worker that hits a decision only the user can make (a seam to
    confirm, an ambiguous default branch, anything needing user input)
    stops and reports exactly what it needs instead of guessing. Relay
    that question to the user yourself, then resume the worker with the
    answer.
  - Collect every worker's report — branch name, worktree path, files
    changed, task statuses — before moving to `vc-implement`'s step 5.

## 3. Fetch and create the worktree (per repo)

```bash
cd <submodule_root>/<repo-name>
git fetch origin
git remote set-head origin --auto 2>/dev/null
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
```

If `$DEFAULT_BRANCH` is empty, or is neither `main` nor `master`, confirm
it with the user before proceeding — never guess silently.

**Branch name:**
- Story: `feat/<ado_id>-<story-slug>`
- Bug: `fix/<ado_id>-<bug-slug>`
- Omit the `<ado_id>-` segment entirely if `ado_id` is `null`.

**Directory:** `.worktrees/<branch-name>`, inside this repo (not the
tracking repo). Verify it's ignored, adding it if not — this must happen
before creating the worktree, and on whichever branch is currently
checked out:

```bash
git check-ignore -q .worktrees || {
  echo ".worktrees/" >> .gitignore
  git add .gitignore
  git commit -m "chore: ignore .worktrees/"
}
```

**Create the worktree from the fetched remote ref — never from a local
branch:**

```bash
git worktree add ".worktrees/<branch-name>" -b "<branch-name>" "origin/$DEFAULT_BRANCH"
cd ".worktrees/<branch-name>"
```

If a native worktree-creation capability is available in this
environment, prefer it over the raw `git worktree add` above — it
handles placement and cleanup bookkeeping; the branch source and naming
rule above still apply regardless of which mechanism creates it.

## 4. Project setup and clean baseline

```bash
[ -f package.json ] && npm install
[ -f Cargo.toml ] && cargo build
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f pyproject.toml ] && poetry install
[ -f go.mod ] && go mod download
```

Run the project's test suite. Report ready with the worktree path and
baseline result. Tests failing at baseline → report failures and ask
whether to proceed or investigate first; don't silently start
implementing on a dirty baseline.
