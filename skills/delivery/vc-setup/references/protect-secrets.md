# Protect Secrets

Full procedure for `vc-setup`'s "Protect secrets" step (and `secure`
mode). Two layers, both in the tracking repo's shared
`.claude/settings.json` so every teammate gets them:

1. **Deny rules**: Claude Code refuses to read secret files at all.
2. **A PreToolUse hook** (`.claude/hooks/block-secret-output.py`): blocks
   shell commands that would print a secret into the conversation, which
   deny rules alone cannot catch (`env`, `echo $TOKEN`,
   `az account get-access-token`, `grep KEY .env`, ...).

Never read, print, or open a secret file while doing this step.

## 1. Deny rules

Add these to `permissions.deny`, keeping every rule already there:

```json
[
  "Read(./.env)",
  "Read(./.env.*)",
  "Read(./**/.env)",
  "Read(./**/.env.*)",
  "Read(./secrets/**)",
  "Read(./**/secrets/**)",
  "Read(./**/*.pem)",
  "Read(./**/*.key)",
  "Read(./**/id_rsa*)",
  "Read(./**/id_ed25519*)",
  "Bash(cat .env*)",
  "Bash(cat ./.env*)"
]
```

`Read(./.env.*)` also blocks template files such as `.env.example`. Tell
the user so; if they need the agent to read a template, they can add an
`allow` rule for that one file in `.claude/settings.local.json`.

## 2. The hook

Two scripts with the same rules ship in `{skill-dir}/assets/`:

| Script | Runs on | Needs |
|---|---|---|
| `block-secret-output.py` | macOS, Linux | Python 3 |
| `block-secret-output.ps1` | Windows | Windows PowerShell 5.1+ or PowerShell 7 (no Python) |

- Copy **both** to `.claude/hooks/` in the tracking repo (create the
  folder), so any teammate's machine has the one it needs. Overwrite an
  older copy only after showing the user it differs.
- Ask via `AskUserQuestion` which systems the team uses: "macOS/Linux
  only", "Windows only", or "Mixed".
- Work out this machine's hook command (Claude Code runs hook commands in
  bash, or in PowerShell on Windows without Git Bash):

  | This machine | Hook command | `shell` |
  |---|---|---|
  | macOS / Linux | `<python> "$CLAUDE_PROJECT_DIR/.claude/hooks/block-secret-output.py"`, `<python>` = `python3` if `command -v python3` finds it, else `python` | - |
  | Windows with Git Bash (`uname -s` starts with `MINGW`, `MSYS`, or `CYGWIN`) | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$CLAUDE_PROJECT_DIR/.claude/hooks/block-secret-output.ps1"` | - |
  | Windows, PowerShell only | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PROJECT_DIR\.claude\hooks\block-secret-output.ps1"` | `"powershell"` |

  macOS/Linux with no Python found → skip the hook, keep the deny rules,
  and say the hook needs Python 3 there.
- Where the hook entry goes:
  - **One system for the whole team** → shared `.claude/settings.json`,
    so everyone gets it from git.
  - **Mixed** → this machine's `.claude/settings.local.json` (personal,
    git-ignored; add it to `.gitignore` if it is not there), because no
    single command runs on both. Tell the user each teammate runs
    `/vc:setup secure` once on their own machine. The deny rules still
    go in the shared `settings.json`.
- The entry, added to `hooks.PreToolUse` unless one with the same command
  is already there (keep every other entry):
  ```json
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "<hook command from the table>",
        "timeout": 10,
        "statusMessage": "Checking for secret output"
      }
    ]
  }
  ```
  Add `"shell": "powershell"` to the inner hook object only for the
  PowerShell-only row.

## 3. Merge and write

- Read each file being changed (`.claude/settings.json`, and
  `.claude/settings.local.json` for a mixed team) first. Missing → start
  from `{}`. Not valid
  JSON → stop and tell the user: an invalid settings file silently
  disables all its settings, so it must be fixed by hand first.
- Merge as above (union of deny rules, hook entry added once), never
  replace the file.
- Show the user what will be added (new deny rules, the hook entry, the
  hook file) and ask via `AskUserQuestion` before writing: this file is
  shared with the whole team through git.
- Write it, then check it parses:
  `<python> -c "import json; json.load(open('.claude/settings.json'))"`
  (on Windows without Python:
  `powershell.exe -NoProfile -Command "Get-Content .claude/settings.json -Raw | ConvertFrom-Json | Out-Null"`).

## 4. Test the hook

Pipe two sample payloads through this machine's hook command; the first
must print a `deny` decision, the second nothing:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}' | <hook command>
echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | <hook command>
```

(In PowerShell: `'{"tool_name":...}' | <hook command>`.) A wrong result →
report it and leave the hook entry out rather than ship a hook that does
nothing.

## 5. Report

- Rules added (and those already present), the hook file path, and the
  test result.
- Remind the user to commit `.claude/settings.json` and both
  `.claude/hooks/block-secret-output.*` scripts so teammates get them
  (never `settings.local.json`).
- Hooks load at session start: the user opens `/hooks` once or restarts
  Claude Code for this session to pick it up.
- The two scripts hold the same rules; a change to one is made to the
  other too.
