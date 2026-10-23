# PRD stub for a feature documented from code

New feature: write `<feature folder>/prd.md` exactly in the stub shape that
`vc-docs` step 6 defines (`skills/delivery/vc-docs/SKILL.md`, "features"), with
these differences only:

- `## Overview` one-to-two-sentence evidence line names the submodules
  and the main entry points found.
- `## Evidence` lists the main surfaces (`- <surface> — `<path>`
  (submodule: `<repo>`)`) and ends with:
  `- As-built spec — [as-built/spec.md](as-built/spec.md)`
- `### In Scope` lists only what the spec's ✅ Scope rows state.
- `## Requirements`, `## Open Questions`, `## Decisions` stay empty
  headings: requirement IDs and open questions move into the PRD only
  through `/vc:prd review`.

Then add `- [<Title>](./<slug>/prd.md) (needs review)` under
`## Features` in `artifacts/prd.md`. When `artifacts/prd.md` doesn't
exist, bootstrap it the way `vc-docs` step 6 does (the product-PRD
shape with gap notes in every interview-derived section), never
inventing product-level content from code.

Existing `needs-review` stub: add only the `- As-built spec — ...` line
to its `## Evidence` (show the diff first). `draft`, `ready`, `active` or `done`
PRD: leave it untouched.
