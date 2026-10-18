---
description: Sync a feature's epic, stories, and tasks to Azure DevOps
argument-hint: <feature | feature-id> | tasks <feature | story>
---
Check if `ado` or `azure-devops` configured. If not, tell user we need to configure `Azure DevOps` prior to continue, then invoke `vc-setup` skill.

After the setup is done, or the configuration is found, invoke the `vc-sync-to-tracker` skill, with `$ARGUMENTS` as the feature identifier and `--target azure-devops` fixed, regardless of whatever `tracker` is set in `.vc/config.toml`.
