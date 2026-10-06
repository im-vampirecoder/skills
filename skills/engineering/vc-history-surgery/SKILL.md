---
name: vc-history-surgery
description: Rewrites git commit history to fold uncommitted working-directory changes and/or specific existing commits back into the historical commits they belong to, preserving original authorship and dates, with a confirmation gate before every destructive step and before any force-push.
disable-model-invocation: true
metadata:
  internal: true
---

# History Surgery

Rewrites a branch's commit history so that changes the user identifies - uncommitted work-in-progress, one or more existing commits on the branch, or both together - land in the historical commits they actually belong to, instead of sitting on top as separate commits. The rewrite always happens on a disposable branch; the target branch is never touched until the final force-push, and every destructive step requires explicit confirmation.

**This is destructive and ends in a force-push.** Never proceed past step 7 (the backup) without the user's explicit go-ahead, and ask again before the force-push in step 12 even if everything earlier was already confirmed.

**Every resulting commit must look like it was made properly at the time, not like history was manipulated afterward.** Two invariants enforce this and apply to every commit the rewrite produces, no exceptions:

- **Committer date always equals that commit's own author date.** Never let a committer date default to whenever the rewrite happens to run.
- **No commit message anywhere may reference the rewrite process.** Strip any `(cherry picked from ...)` trailer and any other cherry-pick/rebase/rewrite wording, including wording already present in an original message before this skill ran.

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

9. **Rewrite the farthest commit.** Isolate just that commit's content: check out its parent, then `git cherry-pick <farthest-hash> --no-commit` to stage only that commit's own diff. Layer the relevant hunks of the source diff (step 3) on top and show the user the combined result - this step is manual and judgment-heavy, don't auto-merge blindly. Confirm a commit message (one line, under 100 characters) with the user. Pull the original commit's author identity and date directly from git - never retype or guess a date string - then commit with it as both author date and committer date:
    ```
    AUTHOR_IDENT=$(git show -s --format='%an <%ae>' <farthest-hash>)
    AUTHOR_DATE=$(git show -s --format=%ad --date=iso-strict <farthest-hash>)
    GIT_AUTHOR_DATE="$AUTHOR_DATE" GIT_COMMITTER_DATE="$AUTHOR_DATE" \
      git commit --author="$AUTHOR_IDENT" --date="$AUTHOR_DATE" -m "<confirmed message>"
    ```
    Verify immediately with `git log -1 --format='author=%ai committer=%ci'` - both dates must equal `$AUTHOR_DATE`. Fix before moving on if they don't; a mismatch here defeats the entire point of the skill.

10. **Cherry-pick forward.** For each subsequent original commit, oldest to newest, from `<farthest-hash>` up to the target's original tip:
    - If the commit is one of the source commits named in step 2, **skip it** - its content was already folded into the rewritten commit in step 9, so replaying it would duplicate the diff.
    - Otherwise: `git cherry-pick --committer-date-is-author-date <hash>` - never pass `-x`, since that flag is exactly what stamps the `(cherry picked from ...)` trailer the invariants above forbid. `--committer-date-is-author-date` is required, not optional - plain `git cherry-pick` preserves the author date but stamps the committer date as the moment the cherry-pick runs.
    - If git reports the pick is now empty ("The previous cherry-pick is now empty"), check whether the *original* commit actually touched files: `git show --stat <hash>`.
      - If it did, its content was already absorbed by an earlier splice or conflict-merge in this rewrite. Skip it: `git cherry-pick --skip`. Report it as "folded away," distinct from both a clean pick and a step-2 source-commit skip. Never commit it empty - a no-op commit is itself an obvious sign history was rewritten, breaking the "looks naturally made" invariant.
      - If the original commit was already empty in the source history (rare - e.g. a deliberate `--allow-empty` commit), that emptiness isn't caused by the rewrite, so preserve it rather than dropping it: `git cherry-pick --keep-redundant-commits --committer-date-is-author-date <hash>`.
    - Even on a clean, non-empty pick, check the resulting message: if the original commit's message already contains cherry-pick/rebase/rewrite wording from some earlier, unrelated history operation, strip it with `git commit --amend -m "<cleaned message>"`. Otherwise leave a clean pick's message untouched - its diff didn't change, so it's already an accurate, naturally-written description.
    - A commit that touches content already altered by the rewrite needs conflict handling - see `references/conflict-resolution.md`. That path always ends with the message rewritten to match the commit's actual final diff, confirmed with the user, and free of any rewrite-process wording.
    - After each commit lands or is skipped, verify with `git log -1 --format='author=%ai committer=%ci'` that both dates match, and that the message contains no cherry-pick/rewrite wording. Stop and investigate before continuing if either check fails - don't let a violation propagate through the rest of the rewrite.
    - Report progress: how many commits processed so far and how many remain to the original tip.

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

## Common mistakes

- **Committer date silently defaults to "now."** Plain `git cherry-pick` and plain `git commit` only preserve the *author* date automatically - the committer date is stamped at run time unless told otherwise. Always use `--committer-date-is-author-date` (step 10) or an explicit `GIT_COMMITTER_DATE` pulled from `git show` (step 9), and verify with `git log -1 --format='author=%ai committer=%ci'` after every commit. A skill whose entire purpose is preserving original dates that quietly stamps today's date is a failed run, not a cosmetic issue.
- **`-x` leaves a `(cherry picked from ...)` trailer.** Never pass `-x` to `git cherry-pick` in this skill - it's the single most obvious tell that history was rewritten, and it directly contradicts the goal of making every commit look like it happened naturally at the time.
- **A stale message survives a content change.** When conflict resolution alters a commit's diff (`references/conflict-resolution.md`), leaving its original message in place makes the commit describe content it no longer contains. Rewrite the message to match the actual final diff whenever the diff itself changed.
- **An empty cherry-pick halts the walk if it's not handled.** Once earlier splices/merges in the rewrite absorb a later commit's content, cherry-picking that commit produces nothing to apply and git stops rather than silently continuing. Check `git show --stat <hash>` on the *original* commit to tell "already folded away" (skip it, don't commit empty) from "was genuinely empty in the source history" (preserve it with `--keep-redundant-commits`) - see step 10.
