---
name: vc-sync-to-ado
description: Sync a feature's epic, feature, stories, and (when available) tasks to Azure DevOps specifically. Thin alias over vc-sync-to-tracker with the target fixed to azure-devops.
---

# Sync to ADO

Invoke the `vc-sync-to-tracker` skill now, with `$ARGUMENTS` as the
feature identifier and `--target azure-devops` fixed, regardless of
whatever `tracker` is set in `.vc/config.toml`.

This skill holds no logic of its own — see `vc-sync-to-tracker` for the
actual create/update/tagging behavior.
