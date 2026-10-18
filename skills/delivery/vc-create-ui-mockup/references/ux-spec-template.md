# ux-spec.md Template

Loaded by `vc-create-ui-mockup` step 8. Written to
`<feature folder>/ux/ux-spec.md`.

```markdown
---
prd: ../prd.md
feature_id: FEATURE-<slug>
app: <app-slug>
route: <follow-baseline | greenfield>
fidelity: <hi-fi | wireframe>
status: draft            # draft | approved
approved: null           # { by: <name>, at: <ISO-8601> } once approved
generated_at: <ISO-8601>
canvas_boards: docs/design-system/<app>/canvas/project/proposed/<feature-slug>/
---

# UX Spec: <Feature title>

## Brief
Context / Character / Density / Color strategy / Type / Shape and depth /
Signature — from the baseline's DESIGN.md or the chosen direction.

## Flows
Per flow: entry point, steps, decisions, success, errors and recovery.
Link to `mockups/index.html`.

## Screens
| Flow | Screen | New / changed | Baseline screen | States | Criteria covered | Mockup | Board |
|---|---|---|---|---|---|---|---|

### Changes to <baseline screen>
| # | Change | Why (criterion / decision) |
|---|---|---|

## Acceptance criteria coverage
| Criterion | Screen(s) / state(s) |
|---|---|
Criteria with no screen are listed with the reason.

## Wording per state
| Screen | State | Kind (error / success / info) | Exact text | Requirement |
|---|---|---|---|---|
Error rows cite the full `ERR-<feature-slug>.<name>` ID and copy its "The
user sees" wording exactly. Text the PRD doesn't give is marked
"(mockup default)" and listed under Open questions.

## Components and tokens
- Used from the design system: …
- Proposed (new component or token, with reason): …

## Responsive and accessibility notes

## Open questions (PRD gaps)
| # | Question | Default assumption in the mockup |
|---|---|---|

## Check results
Rounds run, what was fixed, anything still open or unverified.
```

## Greenfield: seeded `DESIGN.md`

When step 7 creates `docs/design-system/<app>/` for an app with no
extracted baseline, write a minimal `DESIGN.md` with the same frontmatter
shape `vc-extract-design-system` uses (see its
`references/design-doc-template.md`), plus:

```yaml
origin: proposed        # seeded from <feature-slug>'s chosen direction, not extracted from code
```

and only the Foundations section filled. When the app is built and
`/vc:extract-design-system` runs, it replaces this with the real
baseline and keeps the Proposed page.
