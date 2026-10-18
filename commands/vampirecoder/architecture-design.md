---
description: Design the architecture spine — tech stack, design paradigm, submodule ownership, conventions — whole-product with no argument, one epic with an epic argument, one feature with a feature argument or a path to its PRD (proposes a solution first, flags tech debt, never suggests code)
argument-hint: "[review] [epic-slug | EPIC-<slug> | feature-slug | FEATURE-<slug> | path/to/prd.md]"
---

Invoke the `vc-architecture-design` skill now, passing `$ARGUMENTS`
through as-is. No arguments means a whole-product run; an epic slug or
id means an epic-scoped run; a feature slug or id, or a path to a
feature's `prd.md`, means a feature-scoped run — the skill's own step 1 resolves this, including asking when a bare
slug matches both. A leading `review` token instead re-runs only the
review gate against that scope's existing spine.
