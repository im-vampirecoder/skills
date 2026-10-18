---
description: Draw a scope's architecture as interactive HTML + SVG diagrams — as-is from the code, to-be from the architecture spine, changes highlighted — whole-product with no argument, one epic or feature with an argument
argument-hint: "[epic-slug | EPIC-<slug> | feature-slug | FEATURE-<slug>]"
---

Invoke the `vc-create-architecture-diagrams` skill now, passing
`$ARGUMENTS` through as-is. No arguments means whole-product; an epic or
feature slug or id means that scope — the skill's own step 1 resolves
this the same way `vc-architecture-design` does.
