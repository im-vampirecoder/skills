# Commit, Push, PR, and Worktree Cleanup

Full procedure for `vc-implement` steps 6-9, run once per repo.

## Step 6: commit-or-end

`AskUserQuestion`, exactly two options:
- "Commit, push, and consider a PR"
- "End here — leave the worktree and changes as-is"

Choosing "end here" stops this repo's flow entirely; the worktree and its
uncommitted/committed state stay untouched.

## Step 7: commit message

Single line, no AI/assistant attribution of any kind, under 100
characters. Propose it, then wait for explicit approval or an edit — never
commit an unapproved message.

```bash
git add -A
git status   # review what's staged before committing — flag anything that looks like a secret
git commit -m "<approved message>"
git push -u origin "<branch-name>"
```

## Step 8: PR

Ask whether to open a PR. If yes, ask for nothing else the user hasn't
already given you — draft a title and description from the story's/bug's
own content (acceptance criteria / repro, what changed, which tasks),
with no AI/assistant attribution anywhere in either field.

**Detect the host from the repo's own remote, not from config:**

```bash
git remote get-url origin
```

- `github.com` in the URL → `gh pr create --title "<title>" --body "<description>" --base "<default-branch>"`
- `dev.azure.com` (or `visualstudio.com`) in the URL → `az repos pr create --title "<title>" --description "<description>" --target-branch "<default-branch>"`
- Neither → tell the user this host isn't handled yet and give them the
  pushed branch name so they can open it themselves.

Report the PR URL once created.

## Step 9: worktree cleanup

`AskUserQuestion`: "Drop this worktree now" vs "Leave it in place."

**Leave it in place** → report the path, done.

**Drop it:**

```bash
MAIN_ROOT=<the repo's own root, not this worktree>
cd "$MAIN_ROOT"
git worktree remove ".worktrees/<branch-name>"
git worktree prune
```

If removal is refused (`contains modified or untracked files`), the
worktree holds files that exist nowhere else. Never force it on your own
initiative:

```bash
git -C ".worktrees/<branch-name>" status --porcelain -uall
```

Show the user that list and ask: commit them first, move them out, or
delete them (unrecoverable). Carry out their choice, then remove the
worktree.

If a native workspace-exit capability is available in this environment
and owns this worktree, use it instead of the raw `git worktree remove`
above — the safety checks above still apply regardless of mechanism.
