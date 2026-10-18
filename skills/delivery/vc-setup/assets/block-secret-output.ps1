<#
Claude Code PreToolUse hook (matcher: Bash) for Windows, installed by
/vc:setup into <tracking repo>\.claude\hooks\. Same rules as
block-secret-output.py (keep the two in sync); needs only Windows
PowerShell 5.1+ or PowerShell 7, no Python.

Blocks shell commands that would print a secret into the conversation:
reading a secret file (.env and variants, private keys, credential files,
anything under secrets/) with a command that prints content; dumping the
environment or echoing a secret-named variable; CLI commands whose job is
to print a token or password. Template env files (.env.example, .sample,
.template) stay readable. Reads the hook JSON on stdin; to block, prints a
PreToolUse `permissionDecision: deny`. Unparseable input is let through
(the settings.json deny rules still apply).
#>
$ErrorActionPreference = 'Stop'
$Opts = [System.Text.RegularExpressions.RegexOptions]::IgnoreCase

$TemplateEnv = '\.env\.(example|sample|template|dist|defaults)\b'

$SecretFile = '(?:^|[\s/\\''"=<:@])(?:' +
    '\.env(?:\.[\w.-]+)?' +
    '|[\w.-]*\.(?:pem|key|p12|pfx|jks|keystore)' +
    '|id_(?:rsa|dsa|ecdsa|ed25519)' +
    '|\.npmrc|\.pypirc|\.netrc|\.git-credentials' +
    '|credentials(?:\.json)?' +
    '|secrets?\.(?:json|ya?ml|toml|env)' +
    '|secrets[/\\][^\s''"]*' +
    '|\.aws[/\\]credentials|\.azure[/\\][^\s''"]*|\.ssh[/\\][^\s''"]*' +
    ')(?=$|[\s''";|&)>])'

$Printers = '(?:^|[\s|;&(`$])(?:' +
    'cat|tac|less|more|head|tail|bat|nl|od|xxd|hexdump|strings' +
    '|grep|egrep|rg|ag|awk|sed|cut|sort|uniq|base64|jq|yq' +
    '|type|Get-Content|gc|Select-String|sls|source|\.' +
    '|cp|scp|curl|wget' +
    ')(?=$|\s)'

$EnvDump = '(?:^|[;&|]\s*)(?:env|printenv|set|export\s+-p|declare\s+-x' +
    '|(?:Get-ChildItem|gci|dir|ls)\s+env:)\s*(?:$|[|;&>])'

$SecretName = '\w*(?:TOKEN|SECRET|PASSWORD|PASSWD|PWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|PAT|CREDENTIAL|CONN(?:ECTION)?_?STRING|CLIENT_?SECRET)\w*'
$EchoSecret = '(?:\b(?:echo|printf|print|Write-(?:Host|Output))\b[^;|&]*' +
    '(?:\$\{?' + $SecretName + '\}?|\$env:' + $SecretName + '))' +
    '|\bprintenv\s+' + $SecretName + '\b'

$TokenCommands = @(
    @('\baz\s+account\s+get-access-token\b', 'prints an Azure access token'),
    @('\bgh\s+auth\s+token\b', 'prints the GitHub token'),
    @('\bgh\s+auth\s+status\b.*--show-token', 'prints the GitHub token'),
    @('\baws\s+configure\s+(get\s+\S*(secret|token)|export-credentials)', 'prints AWS credentials'),
    @('\bgit\s+config\b.*\b(token|password|extraheader)\b', 'may print a git credential'),
    @('\bgit\s+credential(-\w+)?\s+(fill|get)\b', 'prints a git credential'),
    @('\bsecurity\s+find-(generic|internet)-password\b.*\s-[wg]\b', 'prints a keychain password'),
    @('\bkubectl\s+get\s+secrets?\b.*-o\s*(yaml|json|jsonpath)', 'prints Kubernetes secret data'),
    @('\b(op\s+read|vault\s+(kv\s+get|read))\b', 'prints a secret from a vault'),
    @('\bdocker\s+(inspect|compose\s+config)\b', 'may print secrets from container env')
)

function Test-Command([string]$Command) {
    $stripped = [regex]::Replace($Command, $TemplateEnv, ' ', $Opts)
    if ([regex]::IsMatch($stripped, $SecretFile, $Opts) -and [regex]::IsMatch($Command, $Printers, $Opts)) {
        return 'reads a secret file (.env, key, credentials, or secrets/) in a way that prints it'
    }
    if ([regex]::IsMatch($Command, $EnvDump, $Opts)) { return 'dumps environment variables, which can hold secrets' }
    if ([regex]::IsMatch($Command, $EchoSecret, $Opts)) { return 'prints a variable whose name looks like a secret' }
    foreach ($entry in $TokenCommands) {
        if ([regex]::IsMatch($Command, $entry[0], $Opts)) { return $entry[1] }
    }
    return $null
}

# Dot-sourced (for tests): define Test-Command only.
if ($MyInvocation.InvocationName -eq '.') { return }

try {
    $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
} catch {
    exit 0
}
if ($payload.tool_name -ne 'Bash') { exit 0 }
$command = [string]$payload.tool_input.command
$reason = Test-Command $command
if ($reason) {
    $out = @{ hookSpecificOutput = @{
        hookEventName = 'PreToolUse'
        permissionDecision = 'deny'
        permissionDecisionReason = "Blocked by the vc secret guard: this command $reason. Do not print secrets into the conversation; ask the user to check the value themselves, or reference the variable without printing it."
    } }
    [Console]::Out.Write(($out | ConvertTo-Json -Compress -Depth 4))
}
exit 0
