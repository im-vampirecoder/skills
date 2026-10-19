---
name: vc-requirements
description: Check named requirement IDs (FR / NFR / BR / ERR) across every feature PRD, rebuild the generated artifacts/requirements-current.md view, or find conflicts between features' requirements and walk the PO through resolving them. Never edits a PRD. Triggered by /vc:requirements, and invoked by other vc skills after a PRD write or before feature-scope architecture design.
---

# Requirements

Keeps the requirement IDs that feature PRDs define trustworthy for every
skill that cites them: stories (`Implements:`), test cases, mockups,
architecture. Three modes:

- `check` — find broken IDs. Read-only.
- `view` — rebuild `artifacts/requirements-current.md`, the one place to
  read what the product does now and what each ID means.
- `conflicts [feature]` — find requirements in different features that
  disagree, and get the PO to pick a resolution.

## Ground rules

- **Never edits a PRD.** The only file this skill writes is
  `artifacts/requirements-current.md`. Every conflict resolution is
  handed to `vc-prd` Revision Mode, which is the one writer for PRDs.
- **Deterministic work runs in scripts.** Parsing, checking, rebuilding
  the view and shortlisting conflict candidates are Python 3 stdlib
  scripts in this skill's `scripts/` folder. Run them from the tracking
  repo root; `<skill-dir>` is this skill's folder:
  `python3 <skill-dir>/scripts/<script>.py --root .`
- **Other skills call this one through the Skill tool**
  (`/vc:requirements check`, `view`, `conflicts <feature>`), never by
  reaching into this folder's script paths, so plugin and file installs
  behave the same.
- **ID rules** are defined in `vc-prd`'s
  `references/requirements-section.md`. This skill enforces them; it
  doesn't redefine them.

## Mode resolution

Parse `$ARGUMENTS`: first token `check`, `view` or `conflicts`; anything
after `conflicts` is a feature slug (`<slug>` or `FEATURE-<slug>`). No
token → run `check`, then `view`.

If `artifacts/` has no feature PRD with a `## Requirements` section, say
so, suggest `/vc:prd migrate` for older PRDs or `/vc:prd` for a new
feature, and stop.

## `check`

1. Run `python3 <skill-dir>/scripts/check_requirement_ids.py --root .`
   (add `--json` when another skill needs the findings to act on).
2. Show the result grouped by level. Errors first, each with the file and
   line and a one-line fix:

   | Check | Meaning | Fix |
   |---|---|---|
   | `duplicate` | same ID defined twice | rename one, in the PRD that defined it later |
   | `wrong-feature` | a PRD defines another feature's ID | move the definition to its own PRD, cite it here |
   | `malformed` | not `<TYPE>-<feature-slug>.<name>`, or name over 40 chars | rewrite the ID; if already cited, add a new ID and retire this one |
   | `dangling` | cited but defined nowhere | fix the citation or add the requirement |
   | `retired-but-cited` | an open story still implements a retired ID | point the story at the replacement |
   | `frozen-edited` | text changed after the ID froze | restore the old text; record the change as a new ID with `Replaced by` |
   | `bad-supersedes` | `supersedes` names an ID or feature that doesn't exist | fix the frontmatter |

   Warnings (retired ID still cited by a test case or mockup, a BR linked
   to no FR, an error case naming no FR, glossary aliases and glossary
   candidates) are shown after the errors and never block anything.
   `INFO [needs-clarification]` lines count open markers per feature.
3. Exit code 1 means errors. When called from `vc-prd` after a write,
   hand the errors back to it; this skill fixes nothing itself.

## `view`

1. Run `python3 <skill-dir>/scripts/build_requirements_view.py --root .`
2. Report the file path, the feature and ID counts, and the coverage gaps
   line from the top of the file (P0 FRs with no story, error cases with
   no test case).

The view lists, per feature, every ID with type, priority, a one-line
summary, its state (current / being replaced by a draft feature /
superseded / retired), whether it is frozen and why, and what cites it.
It ends with a hidden baseline of frozen requirement texts; `check`
compares against it to catch edits under a frozen ID. Never edit the file
by hand. If someone did, rebuilding overwrites their edit; the baseline
is kept.

## `conflicts [feature]`

Read `references/conflict-check.md` before running this mode. In short:

1. **Shortlist (script).** `python3 <skill-dir>/scripts/shortlist_conflict_candidates.py --root . [--feature <slug>]`
   returns candidate pairs, delivered-vs-delivered `bug_candidates`, and
   on an unscoped run over 50 pairs, `needs_scope: true` with per-feature
   counts. Then ask which features to audit and rerun scoped. Never cap
   and continue.
2. **Judge.** Read each shortlisted pair in full and classify it. For a
   large audit, use one read-only judge per group of feature pairs (the
   `vc-conflict-judge` subagent when the environment supports
   subagents, otherwise judge the groups one after another yourself).
   Also check each feature in scope against `artifacts/prd.md` for
   product misfit.
3. **Resolve.** Show the PO one real conflict at a time with both texts,
   the options from the reference and a recommended option. The PO
   decides. Hand each decision to `vc-prd` Revision Mode for the
   affected draft feature (via the Skill tool, `/vc:prd` with the
   change), which writes the change and the Decisions entry and reruns
   `check` and `view`.
4. **Report.** One console summary: found, resolved, deferred (now Open
   Questions), dismissed (now `not a conflict` Decisions entries), and
   delivered-vs-delivered pairs listed as `/vc:bug-report` candidates.
   No report file.

## Called by

- `vc-prd`: `check` then `view` after every write; `conflicts <feature>`
  once more before the write preview.
- `vc-architecture-design` at feature scope: `conflicts <feature>`
  first; unresolved conflicts are listed as open in the spine.
- The user by hand: any mode, including the whole-project audit
  (`/vc:requirements conflicts`).

Conflict checks run only on demand, never on a schedule or as part of a
sync.
