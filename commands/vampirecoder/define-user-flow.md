---
description: Map a feature's screens, flows and transitions (happy, error and edge branches tied to PRD requirement IDs) before mockups
argument-hint: '[status] <feature-slug | feature-id | prd-file>'
---

Invoke the `vc-define-user-flow` skill now, passing `$ARGUMENTS`
through as-is. The skill's own step 0 resolves the feature PRD and any
earlier map; a leading `status` only reports whether the map is missing,
draft, approved or stale.
