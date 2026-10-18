# Delivery

A PRD-to-shipped backlog and delivery pipeline for PO/PM, architect, developer, and QA work, backed by local files or Azure DevOps. The skills share `.vc/config.toml` (written by `vc-setup`) and the `agents/vc-*` subagents at the repo root, so install them together. Each runs as `/vc:<name>` or `/vampirecoder:<name>`.

## Model-invoked

All of these are model-invoked so their command shims can reach them, but each `description` names its `/vc:` command: they are meant as deliberate pipeline steps, not auto-triggers.

### core — shared foundation used by every other role

- **[vc-setup](./vc-setup/SKILL.md)** - Configure tracker connection, submodule layout, story tag, sprint states, and (Azure DevOps) team members; protect secrets with deny rules and a PreToolUse hook. Run once per repo; `reinit` re-clones the configured submodule repos after a fresh checkout, `secure` adds only the secret protection, `members` refreshes the team roster.
- **[vc-docs](./vc-docs/SKILL.md)** - Scout every code submodule and generate or refresh `docs/architecture.md` and `docs/project-overview.md` for the whole project, one pair of documents, never one per submodule.
- **[vc-code-to-srs](./vc-code-to-srs/SKILL.md)** - Document what a brownfield codebase already does, feature by feature, before the PO interview: an as-built pack per feature under `<feature folder>/as-built/` (spec with every claim labelled ✅ stated by code / 🔵 corroborated / 🟡 inferred and cited to `path:line`, plus evidence, flows, states, ERD, use cases), mined from routes, validators, tests, message catalogs and dead-code checks, with a cold audit and a script check. Writes or links a `needs-review` stub so `/vc:prd review` starts from evidence. Resumable across runs (`artifacts/as-built-plan.json`); `status` reports progress and stale packs.
- **[vc-extract-design-system](./vc-extract-design-system/SKILL.md)** - Extract an existing frontend's tokens, components, screens and flows into an interactive design canvas under `docs/design-system/<app>/` (foundations board, component sheet, clickable screen boards, rules for new pages), viewable locally with no publish (`preview`), and optionally published as a claude.ai Design canvas the team keeps editing (`publish`/`pull` keep repo and canvas in sync).
- **[vc-requirements](./vc-requirements/SKILL.md)** - Check the named requirement IDs (FR / NFR / BR / ERR) every feature PRD defines, rebuild the generated `artifacts/requirements-current.md` (what the product does now, what cites each ID, coverage gaps), and find conflicts between features' requirements for the PO to resolve. Never edits a PRD.
- **[vc-prd-clarify](./vc-prd-clarify/SKILL.md)** - Quiz a TA, SM, DEV, or QA on a feature PRD section by section so they read it themselves, collect the gaps between their understanding and the PRD, and offer PO/BA clarification questions. Console-only unless the user chooses to save.

### po-pm — PRD -> user flow -> UI mockups -> user stories -> epic -> sync-to-tracker pipeline (stories may come before or after the epic), plus bug reporting

- **[vc-prd](./vc-prd/SKILL.md)** - Interview the user about a feature at the depth it needs and write its PRD with named requirement IDs, bootstrapping the whole-product PRD on first use. Revises drafts in place, refuses to edit delivered features (a new superseding feature instead), and has `deliver`, `clarify` and `migrate` modes.
- **[vc-define-user-flow](./vc-define-user-flow/SKILL.md)** - Map a feature's screens and the moves between them before mockups: a Mermaid flow with happy, error and edge branches, screens, flows and a transitions table, tied to the PRD's `FR-` / `ERR-` IDs. Independently reviewed, PO sign-off, script-checked and hashed; writes `ux/user-flow.md`. `status` reports whether the map is approved or stale.
- **[vc-create-ui-mockup](./vc-create-ui-mockup/SKILL.md)** - Design clickable UI mockups for a feature PRD: flows, a screen inventory, every state, hi-fi on the app's extracted design system (or `--wireframe`), before/after for changed screens, 2-3 directions for greenfield. Writes the feature's `ux/` folder and the app canvas's Proposed page; can link stories' `Design:` lines and publish to claude.ai.
- **[vc-propose-epic](./vc-propose-epic/SKILL.md)** - Match a feature to an existing epic or propose a new one, then move it there (or reassign it later).
- **[vc-create-user-stories](./vc-create-user-stories/SKILL.md)** - Write INVEST-checked user stories with Given/When/Then acceptance criteria for a feature, assigned to an epic or not yet. Tracker sync still needs `/vc:propose-epic` first.
- **[vc-create-pbi](./vc-create-pbi/SKILL.md)** - Same as vc-create-user-stories (epic optional), minus the demoable/deliverable requirement, for spikes, research, and technical enablers that are still larger than a task.
- **[vc-bug-report](./vc-bug-report/SKILL.md)** - Interview the user through the bug-triage template and severity rubric, then write a local bug file.
- **[vc-sync-to-tracker](./vc-sync-to-tracker/SKILL.md)** - Create or update a feature's epic, feature, stories, and tasks in the configured tracker (Epic -> Feature -> Story -> Task), plus a standalone bug mode. Azure DevOps only for now.
- **[vc-sync-to-ado](./vc-sync-to-ado/SKILL.md)** - Sync a feature's epic, feature, stories, tasks, or a bug to Azure DevOps specifically. Alias over vc-sync-to-tracker.
- **[vc-plan-sprint-candidates](./vc-plan-sprint-candidates/SKILL.md)** - Prepare sprint planning: a draft outcome goal, ready stories fitted to the SM's published capacity and the team's story throughput, and carryover up for decision, written to `artifacts/sprints/<sprint-slug>/candidates.md`. `settle` records the scope the team agreed. Local files or Azure DevOps.
- **[vc-create-sprint-release-note](./vc-create-sprint-release-note/SKILL.md)** - Draft (and optionally publish) a non-technical Sprint Release Note grouped by feature/epic, as an Azure DevOps wiki page, an email-ready HTML file, or both.

### architect — design the architecture spine the developer skills build against

- **[vc-architecture-design](./vc-architecture-design/SKILL.md)** - Interview the user on stack, design paradigm, submodule ownership, and cross-feature conventions, grounded in the existing code (brownfield) or the PRDs (greenfield). Writes `architecture.md` plus an append-only `.decisions.md` at product (`artifacts/`), epic (`artifacts/epic-<slug>/`), or feature scope (the feature's folder, with a criteria-to-architecture coverage map). Feature scope also takes a PRD path and starts from a proposed solution checked against the existing architecture, proposes product/epic spine changes only when the PRD needs them, and flags any tech debt an option would add (never recommending one). Architecture only, no code suggestions.
- **[vc-create-architecture-diagrams](./vc-create-architecture-diagrams/SKILL.md)** - Draw a scope's architecture as interactive diagrams (topology, key flows, lifecycles) — as-is from the code, to-be from the spine, changes highlighted. Compiles typed JSON into a self-contained HTML reader plus SVG in a `diagrams/` folder beside the spine. Needs Node 18+.

### developer — turn a confirmed user story into an implementation task breakdown, implement it, and review it

- **[vc-tasks-breakdown](./vc-tasks-breakdown/SKILL.md)** - Turn one confirmed user story into an implementation task breakdown (epic optional), scoped to the code that already exists.
- **[vc-implement](./vc-implement/SKILL.md)** - Implement a confirmed story's task breakdown, or a standalone bug, end-to-end: worktree, test-first implementation, review, tracker status update, commit, PR. Keeps a per-story/bug progress file so an interrupted run can resume.
- **[vc-code-review](./vc-code-review/SKILL.md)** - Review a worktree's changes against a story's or bug's acceptance criteria, existing tests, and repo conventions.

### qa — turn a feature's PRD and stories into reviewed manual test cases

- **[vc-create-test-cases](./vc-create-test-cases/SKILL.md)** - Draft manual test cases for a feature (one combined set) or one of its stories: requirement analysis, risk-based scenarios, then detailed cases, with QC review gates A and B (`--fast` skips them) and a final approval. State in `<feature>/test-cases/.state.json` lets a later session resume; a changed PRD or story sends the affected scope back through review. Writes `test-cases.json` (canonical, ready for a later Azure DevOps sync) plus rendered `analysis.md`, `scenarios.md`, `test-cases.md`. Never runs tests or touches the tracker.
