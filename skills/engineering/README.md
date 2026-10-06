# Engineering

General-purpose skills for daily code work.

## User-invoked

- **[history-surgery](./history-surgery/SKILL.md)** - Rewrite git commit history to fold uncommitted changes and/or specific existing commits into the historical commits they belong to, with a confirmation gate at every destructive step.
- **[prompt-enhancer](./prompt-enhancer/SKILL.md)** - Expand a quick, rough prompt into a detailed, codebase-grounded one before sending it as a real request.
- **[vc-handoff](./vc-handoff/SKILL.md)** - Write a redacted handoff document to `.handoff/` (auto-created and git-ignored) so another agent session can continue the current work.
- **[vc-resume-handoff](./vc-resume-handoff/SKILL.md)** - Load a handoff document, check it against the repo, confirm it with the user, then continue the work.

## Model-invoked

- **[draft-user-story](./draft-user-story/SKILL.md)** - Turn a rough feature request into a structured user story with requirements and acceptance criteria, and confirm it with you before planning or implementing. Triggers on natural phrasing like "write a user story for this" or "refine my requirement"; `/draft-user-story` also works.
