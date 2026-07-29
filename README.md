# Vampire Coder Skills

Personal [Claude Code Agent Skills](https://code.claude.com/docs/en/skills) - the workflows and disciplines I actually use, packaged so they're reusable across projects instead of copy-pasted between them.

Skills get added one at a time, each one earned by a real, repeated need - not ported wholesale from someone else's set.

## Skills

- **[dotnet](./skills/dotnet/README.md)** - .NET/C# tooling

## Structure

See [`skills/README.md`](./skills/README.md) for how skills are organized into buckets, and [`CLAUDE.md`](./CLAUDE.md) for the `SKILL.md` authoring contract.

## Local development

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill into ~/.claude/skills for local testing
```

Re-run `link-skills.sh` after adding, removing, or renaming a skill.
