---
description: Create or update a feature's epic, stories, and tasks in the configured tracker
argument-hint: <feature | feature-id> [--target <azure-devops|github|linear|local>] | tasks <feature | story>
---

Invoke the `vc-sync-to-tracker` skill now, passing `$ARGUMENTS` through
as-is (feature identifier plus any `--target` flag, or a leading `tasks`
token to sync only tasks).
