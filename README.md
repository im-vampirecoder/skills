# Vampire Coder Skills

Personal [Claude Code Agent Skills](https://code.claude.com/docs/en/skills) - the workflows and disciplines I actually use, packaged so they're reusable across projects instead of copy-pasted between them.

Skills get added one at a time, each one earned by a real, repeated need - not ported wholesale from someone else's set.

## Skills

- **[delivery](./skills/delivery/README.md)** - PRD-to-shipped backlog and delivery pipeline: PRDs, user stories, tracker sync, task breakdown, implementation, review, test cases
- **[dotnet](./skills/dotnet/README.md)** - .NET/C# tooling
- **[ios](./skills/ios/README.md)** - iOS / App Store Connect release and app management

## Structure

See [`skills/README.md`](./skills/README.md) for how skills are organized into buckets, and [`CLAUDE.md`](./CLAUDE.md) for the `SKILL.md` authoring contract.

## Local development

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill, command shim, and agent into ~/.claude for local testing
python3 -m unittest discover -s tests -p "test_*.py"   # run the skill script tests
```

Re-run `link-skills.sh` after adding, removing, or renaming a skill.
