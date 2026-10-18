---
description: Document what the existing code does, feature by feature - an as-built pack with confidence-labelled, path:line-cited claims, plus a needs-review PRD stub for /vc:prd review
argument-hint: '[status | refresh <feature>] [<feature-slug> | <src/repo[/sub-path]>]'
---

Invoke the `vc-code-to-srs` skill now, passing `$ARGUMENTS` through
as-is. The skill's own step 0 reads the submodule config and any earlier
`artifacts/as-built-plan.json`; a leading `status` only reports progress
and stale packs, and `refresh <feature>` redrafts one feature against the
current code.
