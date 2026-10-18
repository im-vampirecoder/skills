# Finding and grouping features

Load this for steps 2-3: turning the map of the code into a confirmed
list of features.

## Feature, not module

A feature is something a user can do, named from the user's side:
`password-reset`, `place-order`, `order-history`, `admin-refunds`. A
module is a unit of code: `AuthModule`, `src/payments/`. One module can
hold several features, and one feature can span modules and
submodules.

- Too broad: a name with "management", "and" or "or" in it
  (`user-management`) is usually several features (`sign-up`, `sign-in`,
  `password-reset`, `edit-profile`). Split when each part has its own
  entry point.
- Too narrow: a single field or endpoint that only makes sense inside a
  bigger task joins that task.
- Unclear split: decide from the evidence and write a `grouping_note`;
  don't ask the user a business question.

## Signals, strongest first

1. Routes, controllers, pages, screens, CLI commands, scheduled jobs: the
   entry points (the scout's "Possible feature surfaces" plus the stack
   recipe's route listing).
2. Navigation and menus in the client: the names users actually see.
3. README and existing docs inside the submodule.
4. Migration and schema names: business concepts (`refunds`,
   `subscriptions`).

List entry points in full. A long list is the real shape of the
codebase, not noise to sample; cut work with the scope gate instead.
Describe what each surface does before deciding what feature it serves.

## Grouping by evidence

- A client surface plus the endpoints it **actually calls** (its path
  constant or request matches the server route) is one feature.
- A job, worker or consumer that reads or writes the same data as that
  endpoint joins the same feature.
- Similar names or folders are not evidence. With no call or data link,
  keep the units apart and say why in `grouping_note`.
- Cross-cutting code (sign-in guard, health checks, logging, shared UI
  kit, HTTP helpers) goes in `shared_infrastructure`: listed, cited,
  never counted as a feature.
- Suspected dead or flagged-off surfaces (recipe D) stay on the list,
  marked as suspect, so the user decides.

## Complexity flags

Set per feature from what the code shows; they tell the drafter which
sections need extra care: `oauth`, `payment`, `webhook`, `async`,
`multi-role`, `state-machine`, `throttle`, `external-redirect`.

## Matching existing features

Read `artifacts/prd.md`'s Features section and every `prd.md` under
`artifacts/` (both `artifacts/<slug>/` and
`artifacts/epic-*/feature-<slug>/`). Match by meaning: read the PRD's
Overview and Scope, don't compare slugs. A match sets `existing_prd` to
that file and reuses its slug; the table shows its status
(`needs-review`, `draft`, `delivered`).

## Slugs

kebab-case ASCII, at most 50 characters, from the user-facing name.
Collision with an unrelated feature folder → suffix `-2`, `-3`. Never a
reserved slug: `prd`, `prd-history`, `epics`, `architecture`,
`decisions`, `requirements-current`, `bugs`, `sprints`, `reviews`,
`diagrams`, `as-built-plan`, or anything starting `epic-` or `feature-`.
`as_built_plan.py validate` enforces these.

## Candidate table and scope gate

Show every candidate, then wait:

| # | Feature | Entry points | Submodule(s) | Matches | Flags | Note |
|---|---|---|---|---|---|---|

Under it, one line: candidates, submodules, code files (excluding
vendored folders), shared infrastructure items, suspect surfaces.

- The user may drop, merge, split or rename rows. Re-show the table
  after changes.
- Large run (more than about 25 candidates, more than about 1500 code
  files, or two or more submodules): say it is large, recommend working
  in batches, and ask which to do now: all, a list, or by group (sign-in
  and accounts first, then core business, then admin). The rest become
  `deferred` and a later run picks them up.
- This scope question is the only question the skill asks. Business
  unknowns become open questions in the pack.

## Order of work

Sign-in and account features first (other features depend on their
actors), then the core business features, then secondary, then admin.

## Manifest entry

```json
{
  "slug": "place-order",
  "title": "Place an order",
  "feature_id": "FEATURE-place-order",
  "sources": ["src/shop-api/Controllers/OrdersController.cs", "src/shop-app/src/screens/CheckoutScreen.tsx"],
  "complexity_flags": ["multi-role"],
  "existing_prd": null,
  "grouping_note": "",
  "status": "pending"
}
```

`sources`: up to about 8 key files, in this order: entry points,
handlers or views, services, models or schemas, guards, tests, message
catalogs, config. Tests and catalogs are sources, not extras.
