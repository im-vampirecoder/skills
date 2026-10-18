# Test-First Implementation Loop

Full procedure for `vc-implement` step 4, run once per task (or once for
a bug's repro-to-fix slice).

## Before the first test of a task

State the seam(s) under test: the public interface/boundary you'll
observe behavior through, not internals. Confirm with the user before
writing anything — batch this across several tasks in one round if it's
faster for the user to answer once.

## The loop, per slice

1. **Red** — write one minimal test for the smallest next behavior this
   task needs. One thing, clear name, real code (no mocks unless
   genuinely unavoidable — and if a dependency's side effects aren't
   understood yet, understand them before mocking, not after).
2. **Verify red** — run it. Confirm it fails, and fails for the reason
   you expect (the behavior is missing, not a typo or setup error). If it
   passes immediately, it's testing existing behavior — fix the test, not
   the code.
3. **Green** — write the simplest code that passes. No new production
   code before its test failed first — if this order is ever violated,
   delete the code and restart from Red. Don't anticipate later tests,
   add options nothing asked for, or "improve" beyond what's needed.
4. **Verify green** — run it. Confirm it passes, every other test in the
   suite still passes, and output is clean (no stray errors/warnings).
5. **Light refactor** — remove duplication, improve names, extract an
   obvious helper. Keep everything green. Don't add behavior here.
6. Repeat for the next slice until the task's acceptance criterion
   (its `Addresses:` line) is satisfied.

## Anti-patterns — stop and re-slice if you catch yourself doing one

- **Implementation-coupled**: mocking internal collaborators, testing
  private methods, or checking a side channel instead of the public
  interface. Tell: the test breaks on refactor even though behavior
  didn't change.
- **Tautological**: the assertion recomputes the expected value the same
  way the code does, so it can't disagree with a wrong implementation.
  Expected values must come from an independent source — a known-good
  literal, a worked example, the spec's own numbers.
- **Horizontal slicing**: writing every test for the task first, then all
  the code. Work one seam, one test, one minimal implementation at a
  time — each test should respond to what the last cycle taught you, not
  to an upfront guess at the whole shape.

## Common rationalizations — none of these are reasons to skip a step

| Thought | Reality |
|---|---|
| "Too simple to test" | Simple code breaks too; the test costs seconds. |
| "I'll test after" | A test written after the code passes immediately — that proves nothing about whether it can catch a real bug. |
| "Already manually verified it" | No record of what was covered, not re-runnable, easy to miss a case under pressure. |
| "Hard to test" | Usually means the interface is hard to use — simplify the design, don't route around the test. |
| "Keep the exploration code as reference" | You'll adapt it while writing tests — that's testing after with extra steps. Throw it away, start clean. |
| "This task is different" | It isn't. Every skip is "just this once." |

## Marking a task done

Once its acceptance criterion is met and its tests are green: update that
task file's `Status:` line to `Done` (a new value alongside
`vc-tasks-breakdown`'s `New | Extend | Verify | Skipped`). Leave
`Skipped` tasks untouched — they were never in scope for this run.
