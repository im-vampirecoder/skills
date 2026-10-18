# Test Design Techniques

Used in step 5 (Plan scenarios) and step 7 (Generate).

## Risk and priority

Risk belongs to the behaviour (see `requirement-analysis.md` §6).
Priority is the order of execution:

- **P1**: critical smoke and high-risk primary paths.
- **P2**: other high and medium risks.
- **P3**: low risk.

A case inherits the highest risk level among its scenarios' risks.

## Scenarios

```json
{
  "id": "SC-<slug>-003",
  "title": "Validity hour boundaries",
  "story_id": "STORY-<slug>-1",
  "requirement_ids": ["REQ-<slug>-004"],
  "risk_ids": ["RISK-<slug>-001"],
  "techniques": ["boundary values"],
  "status": "draft",
  "source_refs": [{"source_id": "SRC-<slug>-001", "location": "BR-<slug>.validity-hours"}]
}
```

- Start from confirmed in-scope rules. Each one gets a scenario or a
  stated reason why not.
- `story_id` is the story whose AC the scenario serves; `null` for
  feature-level behaviour that no single story owns. Generation batches by
  this field.
- Extra robustness, security, or usability ideas may be added as
  scenarios linked to `proposed` rules. They never become requirements by
  being tested.
- An exploratory charter (goal, area, time box) is a scenario with
  `techniques: ["exploratory"]`. Its cases stay `needs_review` and are
  never release acceptance cases.
- `status`: `draft` until Gate B, `approved` after it, `excluded` when QC
  drops it. In `--fast` mode, mark planned scenarios `approved` yourself.

## Choosing a technique

| Technique | Use when | How |
|---|---|---|
| Equivalence classes | Inputs fall into distinct valid/invalid groups | One representative per relevant class |
| Boundary values | A limit or step is stated | The limit and the nearest value on each side; note the unit and step |
| Decision table | Several conditions combine into an outcome | One column per meaningful combination; keep every high-risk one |
| State transition | Actions depend on an entity's state | Every allowed transition, plus the refused ones the rules name |
| Pairwise | Many independent factors, too many combinations | Reduce only low-risk independent factors; keep dependent and business-rule combinations, and list what was dropped |
| Exploratory | The behaviour or oracle is still unclear | A charter, kept apart from acceptance cases |

Two conditions are enough for a decision table, and two states are enough
for a transition model. There is no minimum number of negative cases per
field. Pairwise never replaces a full security or business-rule table.

## Field and component prompts

Use these for questions and candidate scenarios on the controls that
exist, not as a list of new requirements.

| Control | Look at |
|---|---|
| Text / editor | Required, stated length, whitespace, line breaks, allowed characters, safe rendering |
| Email / phone | Stated format, missing parts, length, uniqueness only if required |
| Number / money | Range, step, precision, zero and negatives where relevant, units shown |
| Date / time / range | Real dates, ordering, past/future rules, timezone, the instant of start and end |
| Select / radio / checkbox | Options, default, selection limits, dependencies |
| File upload | Types, size and count limits, empty file, failed upload |
| Password / OTP / temporary code | Policy, expiry, reuse, failed attempts, allowed lifecycle actions |
| List / search / filter | Searchable fields, sort, paging, empty state, refresh |
| Create / edit / delete | Persistence, list and detail agree, duplicates, linked records, cancel |
| Roles / tenants | Allowed and refused actions, cross-tenant access, direct URL attempts where testable |
| Dialog / notification | Ways to close, validation, error and success feedback |
| Reliability | Double submit, session expiry, retry, interruption, concurrent edits |
| Accessibility / locale | Keyboard use and focus (observed, not assumed), language and format rules |

Test one field failure per case so a failure points at one cause. Add a
cross-field case only where a rule links the fields. An API status
assertion needs an API contract in the sources.

## Time-sensitive behaviour

Use a controlled test clock, or state the tolerance and what the case
depends on. Never assert against an unspecified "now". For a window from
start (inclusive) to end (exclusive), cover just before start, at start,
just before end, and at end.
