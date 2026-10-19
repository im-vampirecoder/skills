# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh [dir]            # symlink every skill, command shim, and agent into <git root or dir>/.claude for local testing
scripts/link-skills.sh --unlink [dir]   # remove those links again
python3 -m unittest discover -s tests -p "test_*.py"   # tests for skill scripts, against tests/fixtures/
```

There is no build or lint step - skills are Markdown files with YAML frontmatter, not code that compiles or runs standalone. Only skill `scripts/` have tests, under `tests/` at the repo root (Python 3 stdlib `unittest`, one `test_<area>_scripts.py` per skill or skill group, fixture repos under `tests/fixtures/`). A test imports its scripts by path (`skills/<bucket>/<skill>/scripts`), so moving or renaming a skill means updating that path. Add or update a test whenever a skill's `scripts/` changes.

## Architecture

This is a Claude Code [Agent Skills](https://code.claude.com/docs/en/skills) repository: a flat collection of `skills/<bucket>/<skill-name>/SKILL.md` files, each one an independent, self-contained unit Claude Code can discover, invoke, or auto-trigger.

**Bucket layout.** Skills are grouped under `skills/` by bucket - general-purpose (`engineering/`, `productivity/`) or tech-specific (`dotnet/`), see `skills/README.md` for the current list and when to add a new one. Buckets exist for human navigation; tooling treats them alike, except that the plugin manifest lists each bucket by path (see Packaging) and `deprecated/` is skipped by `link-skills.sh` and the setup scripts. Each bucket folder should carry its own `README.md` listing its skills, one line each, split into User-invoked / Model-invoked.

**`SKILL.md` frontmatter contract:**

```yaml
---
name: skill-name
description: What it does and, for model-invoked skills, when to reach for it.
disable-model-invocation: true   # omit unless the skill must be user-invoked only
---
```

- **Model-invoked** (default - omit `disable-model-invocation`): Claude can trigger it automatically when the task fits, and other skills can invoke it. The `description` needs rich trigger phrasing ("Use when the user wants..., mentions...") since that's what drives auto-invocation.
- **User-invoked** (`disable-model-invocation: true`): reachable only when a human explicitly types the skill's own name (`/vc-<name>`). The `description` is a plain human-facing one-liner - no trigger phrasing needed, nothing else fires it automatically. The flag also blocks the Skill tool, so its `/vc:<name>` shims can't reach it - keep it for skills that must never run without a human asking by name (only `vc-history-surgery` today).
- **Model-invoked, command-driven**: a skill meant to run as a deliberate `/vc:<name>` step (the `delivery/` set, `vc-handoff`, `vc-prompt-enhancer`) stays model-invoked so its shims work, but its `description` names the `/vc:` command rather than trigger phrasing for loosely related requests.

A user-invoked skill may call out to model-invoked skills; a model-invoked skill should not depend on a user-invoked one, since nothing but a human can reach it.

**Skill internals.** A skill can be a single `SKILL.md`, or `SKILL.md` plus sibling reference files in the same folder for material that's only needed on some runs (progressive disclosure - keep `SKILL.md` itself lean, push detail into a linked file loaded on demand). Reference the existing `superpowers:writing-skills` and `skill-creator:skill-creator` skills (already available in this environment) when authoring or refining a skill - this repo doesn't duplicate that guidance.

**Naming and commands.** Every skill is named `vc-<name>` (folder and `name:` match). Each model-invoked skill is paired with two thin shims (a user-invoked one gets none, since a shim can't reach it - it's run as `/vc-<name>`), `commands/vc/<name>.md` and `commands/vampirecoder/<name>.md` (no `vc-` in the file name), that just tell Claude to invoke the matching `vc-<name>` skill with `$ARGUMENTS`. That is what makes `/vc:<name>` and `/vampirecoder:<name>` resolve; the skill's own `/vc-<name>` form works without them. `scripts/link-skills.sh` and the setup scripts' files install place both shim folders in a project's `.claude/commands/`; the plugin ships `commands/vc/` only (a plugin has one namespace, its name), so plugin installs get `/vc:<name>` but not `/vampirecoder:<name>`. The `npx skills` installer copies skills only, not `commands/`, so installs from it get `/vc-<name>` only.

**Agents.** A subagent a skill spawns (a pinned cheaper model, real parallelism, or output that should stay out of the calling skill's context) lives at the repo root as `agents/vc-<name>.md`, never inside a skill folder. Give it a narrow `description` so nothing outside its calling skill reaches for it, and pin `model:` deliberately. Installed through the plugin an agent is namespaced (`vc:vc-scout`); installed as files it is plain `vc-scout`. A skill that spawns one names both, e.g. "spawn the `vc-scout` subagent (`vc:vc-scout` when installed through the plugin)". The plugin picks up `agents/` by default; `scripts/link-skills.sh` and the setup scripts' files install copy or link it into `.claude/agents/`; the `npx skills` installer does not copy `agents/`, so skills that spawn one (the `delivery/` set) need it installed separately.

**Packaging.** The version lives in both `package.json` and `.claude-plugin/plugin.json` - bump both together, manually; no changesets or release automation yet. Because `plugin.json` sets `version`, installed plugin copies only update when it changes - a push to `main` without a bump doesn't reach anyone who already has it. Install paths:
- **Claude Code plugin.** `.claude-plugin/plugin.json` makes the repo root a plugin named `vc`; `.claude-plugin/marketplace.json` makes the same repo a single-plugin marketplace named `vampirecoder-skills` (`"source": "./"`), so the plugin id is `vc@vampirecoder-skills`. Plugin skill discovery only scans one level under a skills folder, so `plugin.json`'s `skills` array lists every bucket folder (`./skills/<bucket>/`) - **add a new bucket there** or its skills won't load from the plugin (`deprecated/` stays out). `"commands": "./commands/vc/"` replaces the default `commands/` scan so shims resolve as `/vc:<name>` rather than `/vc:vc:<name>`; `agents/` uses the default scan. Run `claude plugin validate .` after touching either manifest (the warning that the root `CLAUDE.md` isn't loaded as plugin context is expected - it's repo guidance, not plugin content).
- **Setup scripts.** `scripts/setup.sh` / `scripts/setup.ps1` install or update either the plugin or plain files (never both), at project scope (default) or user scope; see `README.md` for the flags. They're fetched from `main` over raw.githubusercontent.com, so keep the plugin id, marketplace name, namespaces and `vc-` prefix in them in step with the repo. `VC_REPO_URL` / `VC_MARKETPLACE` point them at a fork or a local checkout for testing.
- **`npx skills@latest add im-vampirecoder/skills`** walks the repo for `SKILL.md` files and copies skills only; it doesn't read `package.json` or the plugin manifests.
