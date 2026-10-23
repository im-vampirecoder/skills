---
description: Turn a `ready` user story into an implementation task breakdown, or validate one
argument-hint: <ado-ticket-id | story-id | story-file | feature-id> | validate [story-id]
---

Invoke the `vc-tasks-breakdown` skill now, passing `$ARGUMENTS` through
as-is. A leading `validate` token routes to Validate Mode instead of the
breakdown path — the skill's own step 0 resolves this. Otherwise
`$ARGUMENTS` is the identifier to resolve — a story directly, or a feature
to pick a story from if it has more than one.
