---
name: vc-code-review
description: Review a worktree's changes against a story's or bug's acceptance criteria, existing tests, and repo conventions. Callable standalone or by vc-implement.
---

# Code Review

Review implementation changes against the spec they claim to satisfy —
not a general style pass.

## Workflow

1. **Resolve scope**
   - `$ARGUMENTS`: a worktree path, or a story/bug identifier (resolved
     the same way `vc-implement` does: `STORY-<feature-slug>-<n>`, an
     `ado_id`, a path to `story-<n>-spec.md`/`stories-<n>-*.md`,
     `BUG-<bug-slug>`, or a path to `artifacts/bugs/<bug-slug>.md`) plus
     the current repo.
   - Diff the worktree's current state against its branch's fork point
     (`git merge-base`).

2. **Gather the standard to check against**
   - The story's acceptance criteria (Given/When/Then), or the bug's
     Expected/Actual Result.
   - The task files' `## Notes` sections for stated conventions.
   - Existing tests and patterns in the touched files' neighborhood — the
     style already in use nearby, not an external style guide.

3. **Check**
   - Every acceptance criterion (or the bug's Expected Result) is met by
     the diff.
   - Every new or changed behavior has a test that demonstrably exercises
     it through its public interface — not a tautological assertion, not
     one that only checks a mock was called.
   - No regression at any caller of a changed function — walk them, don't
     assume.
   - No new lint/type/build errors anywhere in the repo, not only in the
     touched files.
   - Public contracts (function signatures, exported types, API
     responses, schemas, env vars, config keys) unchanged unless the
     story/bug explicitly calls for the change.
   - Follows the conventions already in use nearby (naming, error
     handling, test structure) rather than introducing a parallel style.

4. **Report**
   - Pass/fail per check above. Every failing check gets a finding: file,
     line, what's wrong, and why it fails that specific check — most
     severe first. No findings → say so plainly, don't pad the report.

## Notes

- Read-only: never edits code, never commits. A caller decides what to do
  with the findings — `vc-implement`'s step 5 stops and asks the user
  when this reports anything other than a clean pass.
- Works on whatever is currently in the worktree; re-run it after fixing
  a finding rather than assuming the fix resolved it.
