# Requirement Analysis

Used in step 3 (Analyze). The result is the Gate A snapshot: sources,
rules, questions, risks, and scope inside `test-cases.json`.

## 1. Source inventory

One `sources` entry per file actually read or looked for:

| type | Where |
|---|---|
| `prd` | `<feature folder>/prd.md` (always) |
| `story` | each `stories-<n>-*.md` in scope |
| `clarifications` | `clarifications.md`, `clarification-questions.md` (from `/vc:prd-clarify`) |
| `ux` | `ux/ux-spec.md` and the mockups it lists |
| `architecture` | the feature/epic/product `architecture.md`; `docs/architecture.md` (Auth and Access Model, Invariants) |
| `design-system` | `docs/design-system/<app>/DESIGN.md`, only for field formats and labels |
| `other` | anything the user hands over in the conversation (record it as `path: null`) |

Fields: `id`, `type`, `path` (repo-relative), `access`
(`read` / `unreadable` / `missing`), `revision` (from
`file_fingerprint`; see `state-resume-and-revisions.md`), `purpose`.

## 2. Scope

`scope.summary` (one paragraph: goal, actors), `scope.story_ids` (the
feature's stories; for a story input, still all of them, see SKILL.md),
`scope.environment` (only what the user or sources state; never inferred
from the project name), `scope.roles`, `scope.exclusions`.

## 3. Rules

Split behaviour into rules that can each be checked on their own. One rule
per limit, per transition, per permission, per validation. A story AC that
packs three outcomes becomes three rules.

```json
{
  "id": "REQ-<slug>-004",
  "statement": "Validity is a whole number of hours from 1 to 48 inclusive",
  "status": "confirmed",
  "in_scope": true,
  "story_ids": ["STORY-<slug>-1"],
  "prd_ids": ["BR-<slug>.validity-hours", "ERR-<slug>.validity-out-of-range"],
  "source_refs": [{"source_id": "SRC-<slug>-001", "location": "BR-<slug>.validity-hours"}],
  "coverage_override": null
}
```

- `prd_ids`: the full PRD requirement IDs (`FR-`, `NFR-`, `BR-`, `ERR-`)
  this rule checks, from the PRD's `## Requirements` section. Live IDs
  only: when `artifacts/requirements-current.md` exists, skip any it
  shows as retired or superseded and cite the replacement instead. A
  rule drawn only from a story AC, a clarification or a mockup still
  names the PRD ID behind it when there is one; `[]` when there is none
  (e.g. a proposed robustness rule), or when the PRD has no
  `## Requirements` section yet. Every `ERR-` in scope gets at least one
  rule, so `/vc:requirements view` can show it as covered.

- `status`: confirmed / proposed / observed / unresolved (see
  `qa-core-rules.md`). Confirmed means written down by an authority, not
  that the system passes.
- `coverage_override`: `{"status": "deferred", "reason": "..."}` only
  when QC agrees a rule gets no case this round.
- A revised rule keeps its ID. A dropped rule gets `"retired": true`;
  never delete it, never reuse its number.

## 4. Inventories that feed scenarios

Kept in your working notes, not in the JSON. Each one surfaces rules and
questions:

- **Fields:** type, required, limits, format, default, options,
  dependencies, uniqueness, messages, timezone, units. Unstated means
  unknown, not "none".
- **Role × action × state:** allowed, refused, unknown. Keep tenant
  limits apart from role limits.
- **Flows:** happy, alternate, failure, at a high level, plus links to
  other features.

## 5. Questions

```json
{
  "id": "Q-<slug>-002",
  "topic": "Duplicate codes",
  "question": "AC allows creating a code but does not say what happens when the student already has an active one. Replace, refuse, or allow both?",
  "requirement_ids": ["REQ-<slug>-007"],
  "source_refs": [{"source_id": "SRC-<slug>-002", "location": "STORY-<slug>-1 AC3"}],
  "blocking": true,
  "owner": "PO",
  "status": "open",
  "resolution": null
}
```

- Ask only what changes scope or an expected result. Name the gap or the
  conflict, the rules it touches, and what it does to testing.
- `blocking` means the expected outcome for those rules cannot be written
  yet. It blocks only those rules, never unrelated scope.
- Before adding a question, check `clarifications.md` /
  `clarification-questions.md`: reuse an answered item as a source
  (`location: CLR-<nnn>`), and do not ask the same thing twice.
- Never answer your own question as if it were a requirement.

## 6. Risks

```json
{
  "id": "RISK-<slug>-001",
  "description": "Off-by-one at the 48-hour limit lets a code live too long",
  "requirement_ids": ["REQ-<slug>-004"],
  "impact": 3,
  "likelihood": 2,
  "level": "high",
  "rationale": "Expired access is an auth exposure; limit logic is hand-written",
  "test_focus": "Values 0, 1, 48, 49 and a decimal"
}
```

Impact and likelihood are each 1-3. Level follows the score: 1-2 low,
3-4 medium, 6-9 high. QC may override; record the reason in
`override_reason`.

## 7. Readiness before Gate A

| Situation | What to do |
|---|---|
| Clear rules, reliable outcomes | Ready for scenarios |
| Some outcomes open | Ready for the confirmed part; propose excluding the rest |
| Nothing checkable | Stop; point the user at `/vc:prd-clarify` and the PO |
| Optional design missing, rules sufficient | Continue; record the missing evidence |
| Essential source unreadable | Pause the behaviour that depends on it; say what is needed |

A missing formal "Acceptance Criteria" heading is not by itself a reason
to stop. "Works correctly" is never an acceptable expected outcome.
