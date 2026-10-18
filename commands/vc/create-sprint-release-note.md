---
description: Draft (and optionally publish) a non-technical, plain-language Sprint Release Note grouped by feature/epic, as a wiki page, an email-ready HTML file, or both
argument-hint: '[sprint number(s), e.g. 27 | 28-30 | last 2] (omit for the latest completed sprint)'
---

Invoke the `vc-create-sprint-release-note` skill now, passing
`$ARGUMENTS` through as-is as the sprint(s) to cover. Empty `$ARGUMENTS`
means the most recently completed sprint — the skill's own Step 1
resolves this.
