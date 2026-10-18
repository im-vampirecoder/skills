---
description: Interview the user to file a bug report following the bug-triage template and severity rubric
argument-hint: []
---

Invoke the `vc-bug-report` skill now, passing `$ARGUMENTS` through as
any initial context already given (e.g. a rough description of the bug) —
the rest comes from the interview. This command never syncs to a tracker;
that's `/vc:sync-to-tracker bug <bug-id>`, run separately.
