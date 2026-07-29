# Skills

Skills live in bucket folders under this directory, one folder per skill:
`skills/<bucket>/<skill-name>/SKILL.md`.

Buckets are created on demand - there's nothing here yet. When the first
skill lands, start with whichever bucket fits and add more buckets only when
a skill genuinely doesn't belong in an existing one:

- `engineering/` - daily code work (debugging, review, TDD, architecture)
- `productivity/` - daily non-code workflow tools
- `in-progress/` - drafts not yet reliable enough to use for real
- `misc/` - kept around but rarely used
- `deprecated/` - no longer used, kept for reference

Each bucket folder should have its own `README.md` listing the skills in it
with a one-line description, split into **User-invoked** and **Model-invoked**
(see `CLAUDE.md` at the repo root for what that split means and the
`SKILL.md` frontmatter contract).
