---
description: Interview the user about a feature and write its PRD with named requirement IDs, revise a draft feature in place, complete a needs-review stub with `review`, freeze a finished feature with `deliver`, add a clarification to a requirement with `clarify`, or add named IDs to older PRDs with `migrate`
argument-hint: <feature-description | change to an existing feature> [--deep] | review [feature-slug] | deliver <feature> | clarify <requirement-id> | migrate [feature]
---

Invoke the `vc-prd` skill now, passing `$ARGUMENTS` through as-is. A
leading `review`, `deliver`, `clarify` or `migrate` token routes to that
mode instead of the feature description path — the skill's own step 0
resolves this. Otherwise, if `--deep` is present, strip it from the
description and pass it through as the flag that forces Deep interview
depth.
