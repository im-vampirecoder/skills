---
description: Configure the tracker connection, submodule layout, story tag, team members, and secret protection for this repo, or migrate old task-breakdown output
argument-hint: '[] | reinit | migrate | secure | members'
---

Invoke the `vc-setup` skill now, passing `$ARGUMENTS` through as-is. A
leading `reinit`, `migrate`, `secure`, or `members` token routes to that
mode instead of the normal configure flow — the skill's own step 0
resolves this.
