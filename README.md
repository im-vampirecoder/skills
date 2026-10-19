# Vampire Coder Skills

Personal [Claude Code Agent Skills](https://code.claude.com/docs/en/skills) - the workflows and disciplines I actually use, packaged so they're reusable across projects instead of copy-pasted between them.

Skills get added one at a time, each one earned by a real, repeated need - not ported wholesale from someone else's set.

## Skills

- **[delivery](./skills/delivery/README.md)** - PRD-to-shipped backlog and delivery pipeline: PRDs, user stories, tracker sync, task breakdown, implementation, review, test cases
- **[dotnet](./skills/dotnet/README.md)** - .NET/C# tooling
- **[ios](./skills/ios/README.md)** - iOS / App Store Connect release and app management

## Install

Pick ONE method, the Claude Code plugin or plain files. Never use both: every skill and command would load twice, and the setup script offers to remove the other one first. It installs into the current project by default (run it from inside the project's git repo), or for your user with `--user`. Re-run the same command later to update.

macOS / Linux / Git Bash:

```sh
curl -fsSL https://raw.githubusercontent.com/im-vampirecoder/skills/main/scripts/setup.sh | sh -s -- --plugin
```

Windows PowerShell:

```powershell
$env:VC_METHOD='plugin'; irm https://raw.githubusercontent.com/im-vampirecoder/skills/main/scripts/setup.ps1 | iex
```

Replace `plugin` with `files` to copy everything in instead. Without a method the script asks.

| Option | `setup.sh` | `setup.ps1` |
|---|---|---|
| Claude Code plugin | `--plugin` | `-Method plugin` or `VC_METHOD=plugin` |
| Plain files | `--files` (alias `--skills`) | `-Method files` or `VC_METHOD=files` |
| Current project (default) | `--project` | `-Scope project` or `VC_SCOPE=project` |
| Your user, every project | `--user` | `-Scope user` or `VC_SCOPE=user` |
| Auto-confirm removal prompts (CI) | `--yes` | `-Yes` |

With a downloaded copy, pass parameters the usual way, for example `& ([scriptblock]::Create((irm <url>))) -Method plugin -Scope user`.

**Plugin**: `claude plugin marketplace add im-vampirecoder/skills` + `claude plugin install vc@vampirecoder-skills` at the chosen scope (or `marketplace update` + `plugin update` when already installed). A copy at another scope is removed after a prompt. Commands resolve as `/vc:<name>`, skills as `/vc:vc-<name>`. At project scope, commit `.claude/settings.json` so teammates are prompted to install it. Doing it by hand: `/plugin install vc --marketplace im-vampirecoder/skills`.

**Files**: shallow-clones this repo to a temp folder (deleted afterwards), then, under the project root (or `~` with `--user`):

- copies each `skills/<bucket>/vc-*` to `.agents/skills/` and links it into `.claude/skills/` (relative symlink on macOS/Linux, junction on Windows, plain copy if linking is not possible),
- copies `commands/vc/` and `commands/vampirecoder/` to `.claude/commands/`, so both `/vc:*` and `/vampirecoder:*` work,
- copies `agents/*.md` to `.claude/agents/` (the subagents some skills spawn).

On update it first removes every `vc-*` skill and agent and both command folders, so skills deleted upstream disappear. Anything not named `vc-*` is left alone, and git is never touched.

`npx skills@latest add im-vampirecoder/skills` still works too, but copies skills only: no commands, no agents.

## Structure

See [`skills/README.md`](./skills/README.md) for how skills are organized into buckets, and [`CLAUDE.md`](./CLAUDE.md) for the `SKILL.md` authoring contract.

## Local development

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill, command shim, and agent into this git repo's .claude/ (or a given dir)
python3 -m unittest discover -s tests -p "test_*.py"   # run the skill script tests
```

Run `link-skills.sh` from the project you want to test the skills in (or pass its path), and re-run it after adding, removing, or renaming a skill; it prunes links that no longer resolve. `scripts/link-skills.sh --unlink [dir]` removes the links again. They count as a files install, so don't also install the plugin for that project (the setup script detects the links and offers to remove them).
