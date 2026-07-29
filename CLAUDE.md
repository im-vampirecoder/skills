# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill into ~/.claude/skills for local testing
```

There is no build, lint, or test step - skills are Markdown files with YAML frontmatter, not code that compiles or runs standalone.

## Architecture

This is a Claude Code [Agent Skills](https://code.claude.com/docs/en/skills) repository: a flat collection of `skills/<bucket>/<skill-name>/SKILL.md` files, each one an independent, self-contained unit Claude Code can discover, invoke, or auto-trigger.

**Bucket layout.** Skills are grouped under `skills/` by bucket (`engineering/`, `productivity/`, `in-progress/`, `misc/`, `deprecated/` - see `skills/README.md`). Buckets exist for human navigation only; nothing in tooling treats one bucket differently from another yet. Each bucket folder should carry its own `README.md` listing its skills, one line each, split into User-invoked / Model-invoked.

**`SKILL.md` frontmatter contract:**

```yaml
---
name: skill-name
description: What it does and, for model-invoked skills, when to reach for it.
disable-model-invocation: true   # omit unless the skill must be user-invoked only
---
```

- **Model-invoked** (default - omit `disable-model-invocation`): Claude can trigger it automatically when the task fits, and other skills can invoke it. The `description` needs rich trigger phrasing ("Use when the user wants..., mentions...") since that's what drives auto-invocation.
- **User-invoked** (`disable-model-invocation: true`): reachable only when a human explicitly types the skill name. The `description` is a plain human-facing one-liner - no trigger phrasing needed, nothing else fires it automatically.

A user-invoked skill may call out to model-invoked skills; a model-invoked skill should not depend on a user-invoked one, since nothing but a human can reach it.

**Skill internals.** A skill can be a single `SKILL.md`, or `SKILL.md` plus sibling reference files in the same folder for material that's only needed on some runs (progressive disclosure - keep `SKILL.md` itself lean, push detail into a linked file loaded on demand). Reference the existing `superpowers:writing-skills` and `skill-creator:skill-creator` skills (already available in this environment) when authoring or refining a skill - this repo doesn't duplicate that guidance.

**Packaging.** `package.json` carries the repo version (starts at `0.0.0-alpha`), bumped manually for now - no changesets or release automation yet. Publishing model is `npx skills@latest add im-vampirecoder/skills` only - no Claude Code plugin channel, so there's no `.claude-plugin/plugin.json` or `marketplace.json`. That installer just walks the repo for `SKILL.md` files and doesn't read `package.json` at all, so it's already installable the moment a `SKILL.md` exists.
