---
name: history-surgery
description: Rewrites git commit history to fold uncommitted working-directory changes and/or specific existing commits back into the historical commits they belong to, preserving original authorship and dates, with a confirmation gate before every destructive step and before any force-push.
disable-model-invocation: true
---

# History Surgery

Rewrites a branch's commit history so that changes the user identifies - uncommitted work-in-progress, one or more existing commits on the branch, or both together - land in the historical commits they actually belong to, instead of sitting on top as separate commits. The rewrite always happens on a disposable branch; the target branch is never touched until the final force-push, and every destructive step requires explicit confirmation.

**This is destructive and ends in a force-push.** Never proceed past step 7 (the backup) without the user's explicit go-ahead, and ask again before the force-push in step 12 even if everything earlier was already confirmed.

## Process

1. **Pick the target branch.** Ask which branch to rewrite (default: the current branch). Tell the user this is a destructive rewrite that requires a force-push afterward, and that walking commit-by-commit through history (steps 5, 9, 10) is token-intensive - ask them to make sure they have sufficient token budget available before continuing. Confirm they understand both before proceeding.

2. **Identify the source of the change.** Ask the user what contains the work to fold into history: uncommitted working-directory changes, one or more existing commits already on `<target>` (collect exact hashes), or both. For any commit hashes given, confirm each is actually reachable from `<target>`'s tip (`git merge-base --is-ancestor <hash> <target>`) - reject anything that isn't on this branch.

3. **Build the combined source diff.**
   - If existing commits were named: create a disposable scratch branch off the parent of the oldest named commit, `git cherry-pick` the named commits onto it in chronological order (this resolves each commit against a real tree instead of blindly concatenating patches), then take `git diff <scratch-base> <scratch-tip>` as their combined diff. Delete the scratch branch once the diff is captured.
   - If uncommitted changes are part of the source, also capture `git diff` / `git diff --staged`, and snapshot them so they can be restored exactly if the rewrite is later discarded: `git diff --staged > .git/history-surgery-staged.patch` and `git diff > .git/history-surgery-unstaged.patch`. Untracked files need no snapshot - switching branches never touches them.
   - The **source diff** for the rest of this process is the combination of whichever of these applies. Combine this with whatever the user has already said in this conversation about what the changes are for - don't guess intent from the diff alone.

4. **Confirm the understood intent.** Summarize, in a sentence or two, what the source diff does and which target branch it'll be folded into. Get an explicit yes before going further.

5. **Find the commits to rewrite.** From the touched file paths - and touched function/symbol names where identifiable from the diff hunks - search history: `git log --oneline -- <paths>` for file-level hits, `git log -G'<symbol>' -- <paths>` for symbol-level hits. Exclude any commits already named as a source in step 2 - they're being folded in, not searched. Present a table:

   | Hash | Date | Message | Files touched |
   |---|---|---|---|

6. **Confirm the rewrite.** Point out which commit in the table is the farthest one that needs changing, and ask the user to confirm before mutating anything.

7. **Back up the target branch.** `git branch backup/<target>-<timestamp> <target>`. Tell the user this backup exists and name it.

8. **Create the working branch.** `git switch -c rewrite-<target>-in-progress <target>`. Since the new branch starts at the same tip as `<target>`, any uncommitted files carry over untouched - do not stash them; any named source commits are still present on this branch too, to be dropped in step 10. Before making any commits, confirm the author/committer identity to use: read `git config user.name` / `user.email` and ask the user to confirm it's correct.

9. **Rewrite the farthest commit.** Isolate just that commit's content: check out its parent, then `git cherry-pick <farthest-hash> --no-commit` to stage only that commit's own diff. Layer the relevant hunks of the source diff (step 3) on top and show the user the combined result - this step is manual and judgment-heavy, don't auto-merge blindly. Confirm a commit message (one line, under 100 characters) with the user, then commit preserving the original author and date:
   ```
   GIT_AUTHOR_DATE="<original author date>" GIT_COMMITTER_DATE="<original author date>" \
     git commit --author="<original author>" --date="<original author date>" -m "<confirmed message>"
   ```

10. **Cherry-pick forward.** For each subsequent original commit, oldest to newest, from `<farthest-hash>` up to the target's original tip:
    - If the commit is one of the source commits named in step 2, **skip it** - its content was already folded into the rewritten commit in step 9, so replaying it would duplicate the diff.
    - Otherwise: `GIT_COMMITTER_DATE="<original committer date>" git cherry-pick -x <hash>`, then drop the auto-added `(cherry picked from ...)` trailer if the history should read clean. A commit with no overlap picks cleanly. A commit that touches content already altered by the rewrite needs conflict handling - see `references/conflict-resolution.md`.
    - After each commit lands or is skipped, report progress: how many commits processed so far and how many remain to the original tip.

11. **Verify before touching the target branch.** Once `rewrite-<target>-in-progress` reaches the original tip's content (minus the dropped source commits), ask the user to verify the result - build, test, whatever the project's own verification commands are - before anything is force-pushed.

12. **Publish or hold.** Ask explicitly: force-push `rewrite-<target>-in-progress` onto `<target>` now, or stop here and leave both branches plus the backup in place for the user to inspect and push later. Never force-push without this explicit ask.

## Safety notes

- Nothing destructive happens to `<target>` before step 12 - every step through step 11 happens on the disposable `rewrite-<target>-in-progress` branch. Since `<target>` is never touched, any named source commits from step 2 still sit exactly where they originally were on it, untouched, for the entire process.
- **Discarding a rewrite mid-flight** must put the user back exactly where they started: on `<target>`, with its original commits intact and any uncommitted files restored, not lost inside a deleted branch. The sequence is:
  ```
  git cherry-pick --abort   # only if a cherry-pick is in progress
  git switch <target>
  git branch -D rewrite-<target>-in-progress
  git apply --cached .git/history-surgery-staged.patch   # if that patch exists and is non-empty
  git apply .git/history-surgery-unstaged.patch           # if that patch exists and is non-empty
  rm -f .git/history-surgery-staged.patch .git/history-surgery-unstaged.patch
  ```
  If the source was purely named commits with no uncommitted changes, there's nothing to reapply - `<target>` already has everything. Because `<target>` was never touched, this fully restores the pre-invocation state - the `backup/*` branch from step 7 is a second safety net, not the primary way back.
- Don't skip a confirmation step because earlier steps were already confirmed - each one gates a different, harder-to-reverse action.
