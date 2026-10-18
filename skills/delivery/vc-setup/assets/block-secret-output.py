#!/usr/bin/env python3
"""
Claude Code PreToolUse hook (matcher: Bash) installed by /vc:setup into
<tracking repo>/.claude/hooks/, for macOS and Linux. block-secret-output.ps1
is the Windows twin with the same rules (keep the two in sync). Blocks
shell commands that would print a secret into the conversation:

  - reading a secret file (.env and variants, private keys, credential
    files, anything under secrets/) with a command that prints content;
  - dumping the environment (env, printenv, set, Get-ChildItem env:) or
    echoing a variable whose name looks like a secret;
  - CLI commands whose job is to print a token or password.

Template env files (.env.example, .env.sample, .env.template) stay
readable. Reads the hook JSON on stdin; to block, prints a PreToolUse
`permissionDecision: deny` with the reason. Anything it cannot parse is let
through (the settings.json deny rules still apply).
"""
import json
import re
import sys

TEMPLATE_ENV = re.compile(r"\.env\.(example|sample|template|dist|defaults)\b", re.I)

SECRET_FILE = re.compile(
    r"""(?:^|[\s/\\'"=<:@])(?:
        \.env(?:\.[\w.-]+)?            # .env, .env.local, .env.production
      | [\w.-]*\.(?:pem|key|p12|pfx|jks|keystore)
      | id_(?:rsa|dsa|ecdsa|ed25519)
      | \.npmrc | \.pypirc | \.netrc | \.git-credentials
      | credentials(?:\.json)?
      | secrets?\.(?:json|ya?ml|toml|env)
      | secrets[/\\][^\s'"]*
      | \.aws[/\\]credentials | \.azure[/\\][^\s'"]* | \.ssh[/\\][^\s'"]*
    )(?=$|[\s'";|&)>])""",
    re.X | re.I,
)

PRINTERS = re.compile(
    r"""(?:^|[\s|;&(`$])(?:
        cat | tac | less | more | head | tail | bat | nl | od | xxd | hexdump | strings
      | grep | egrep | rg | ag | awk | sed | cut | sort | uniq | base64 | jq | yq
      | type | Get-Content | gc | Select-String | sls | source | \.
      | cp | scp | curl | wget                       # exfiltration of the file
    )(?=$|\s)""",
    re.X | re.I,
)

ENV_DUMP = re.compile(
    r"""(?:^|[;&|]\s*)(?:
        env | printenv | set | export\s+-p | declare\s+-x
      | (?:Get-ChildItem|gci|dir|ls)\s+env:
    )\s*(?:$|[|;&>])""",
    re.X | re.I,
)

SECRET_NAME = r"[\w]*(?:TOKEN|SECRET|PASSWORD|PASSWD|PWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|PAT|CREDENTIAL|CONN(?:ECTION)?_?STRING|CLIENT_?SECRET)[\w]*"
ECHO_SECRET = re.compile(
    rf"""(?:\b(?:echo|printf|print|Write-(?:Host|Output))\b[^;|&]*
          (?:\$\{{?{SECRET_NAME}\}}?|\$env:{SECRET_NAME}))
       | \bprintenv\s+{SECRET_NAME}\b""",
    re.X | re.I,
)

TOKEN_COMMANDS = [
    (r"\baz\s+account\s+get-access-token\b", "prints an Azure access token"),
    (r"\bgh\s+auth\s+token\b", "prints the GitHub token"),
    (r"\bgh\s+auth\s+status\b.*--show-token", "prints the GitHub token"),
    (r"\baws\s+configure\s+(get\s+\S*(secret|token)|export-credentials)", "prints AWS credentials"),
    (r"\bgit\s+config\b.*\b(token|password|extraheader)\b", "may print a git credential"),
    (r"\bgit\s+credential(-\w+)?\s+(fill|get)\b", "prints a git credential"),
    (r"\bsecurity\s+find-(generic|internet)-password\b.*\s-[wg]\b", "prints a keychain password"),
    (r"\bkubectl\s+get\s+secrets?\b.*-o\s*(yaml|json|jsonpath)", "prints Kubernetes secret data"),
    (r"\b(op\s+read|vault\s+(kv\s+get|read))\b", "prints a secret from a vault"),
    (r"\bdocker\s+(inspect|compose\s+config)\b", "may print secrets from container env"),
]


def check(command):
    """Return the reason to block, or None."""
    stripped = TEMPLATE_ENV.sub(" ", command)
    if SECRET_FILE.search(stripped) and PRINTERS.search(command):
        return "reads a secret file (.env, key, credentials, or secrets/) in a way that prints it"
    if ENV_DUMP.search(command):
        return "dumps environment variables, which can hold secrets"
    if ECHO_SECRET.search(command):
        return "prints a variable whose name looks like a secret"
    for pattern, reason in TOKEN_COMMANDS:
        if re.search(pattern, command, re.I):
            return reason
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = check(command)
    if reason:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked by the vc secret guard: this command {reason}. "
                "Do not print secrets into the conversation; ask the user to check "
                "the value themselves, or reference the variable without printing it."),
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
