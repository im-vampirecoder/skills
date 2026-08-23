# Conflict Resolution During Forward Cherry-Pick

Used in step 10 of the main process when a cherry-picked commit touches content already changed earlier in the rewrite.

1. Attempt the cherry-pick normally: `git cherry-pick -x <hash>`.
2. If it reports a conflict, don't resolve it silently. Show the user:
   - the conflicting hunks (the `<<<<<<<` / `=======` / `>>>>>>>` markers)
   - the incoming commit's own diff, for context on what it originally intended
3. Auto-merge what git can resolve on its own, and combine the two sides for the conflicting hunks where the merge is mechanically obvious (e.g. both sides add non-overlapping lines). Don't guess when the conflict is semantic, not textual.
4. Show the user the full resulting diff of the merged commit - not just the conflict markers, the complete picture of what this commit would become.
5. Ask the user to choose:
   - **Save** - continue the cherry-pick (`git cherry-pick --continue`) and commit, preserving the original commit's author and date per step 10.
   - **Discard everything** - abort the cherry-pick and unwind the whole rewrite using the discard sequence in the main SKILL.md's Safety notes (`git cherry-pick --abort`, switch to `<target>`, delete `rewrite-<target>-in-progress`, reapply any step-3 WIP patches). Don't try to salvage a partial rewrite - the target branch was never touched, so any named source commits are still exactly where they were and any uncommitted changes come back exactly as they were.
6. There is no partial-save option. It's the full merged commit or nothing - a half-applied splice is worse than no splice, since it silently drops part of either the original commit or the source diff.
