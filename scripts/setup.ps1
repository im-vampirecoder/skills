# Install or update the vc skills, using EITHER the Claude Code plugin OR plain files (never
# both), in the current project (default) or for your user. Safe to re-run: installs when
# missing, updates when present.
#
# Usage:
#   .\setup.ps1 [-Method plugin|files] [-Scope project|user] [-Yes]
#   $env:VC_METHOD='plugin'; irm https://raw.githubusercontent.com/im-vampirecoder/skills/main/scripts/setup.ps1 | iex
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/im-vampirecoder/skills/main/scripts/setup.ps1))) -Method plugin -Scope user
#
# files: clones the repo to a temp folder, then copies every skill to <base>\.agents\skills\
# (linked into <base>\.claude\skills\), commands\<ns>\ to <base>\.claude\commands\<ns>\ and
# agents\ to <base>\.claude\agents\. <base> is the project's git root, or your home with -Scope user.
# Never calls `exit`, so it is safe under `iex`.
# No [ValidateSet] here: under `iex` the param block turns into variable attributes and an empty
# default would be rejected. The values are validated inside the function instead.
param(
    [string]$Method = $env:VC_METHOD,
    [string]$Scope = $env:VC_SCOPE,
    [switch]$Yes
)

function Invoke-VcSetup {
    param([string]$Method, [string]$Scope, [bool]$Yes)

    $MarketplaceSrc = if ($env:VC_MARKETPLACE) { $env:VC_MARKETPLACE } else { 'im-vampirecoder/skills' }
    $MarketplaceName = 'vampirecoder-skills'
    $Plugin = 'vc@vampirecoder-skills'
    $RepoUrl = if ($env:VC_REPO_URL) { $env:VC_REPO_URL } else { 'https://github.com/im-vampirecoder/skills' }
    # Command namespaces the files install owns under .claude\commands\.
    $Namespaces = 'vc', 'vampirecoder'

    function Test-Cmd($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

    function Confirm-Vc($question) {
        if ($Yes) { return $true }
        return ((Read-Host "$question [y/N]") -match '^(y|yes)$')
    }

    function Get-PluginScopes {
        if (-not (Test-Cmd claude)) { return @() }
        $json = claude plugin list --json 2>$null | Out-String
        if (-not $json.Trim()) { return @() }
        @($json | ConvertFrom-Json | Where-Object { $_.id -eq $Plugin } |
            Where-Object { $_.scope -ne 'project' -or -not $_.projectPath -or
                ((Resolve-Path $_.projectPath -ErrorAction SilentlyContinue).Path -eq (Get-Location).Path) } |
            ForEach-Object { $_.scope })
    }

    # Items of a files install under $base (also catches skills linked by link-skills.sh).
    function Get-InstalledFiles($base) {
        $patterns = @('.agents/skills/vc-*', '.claude/skills/vc-*', '.claude/agents/vc-*') +
            @($Namespaces | ForEach-Object { ".claude/commands/$_" })
        $items = @()
        foreach ($pattern in $patterns) {
            $items += @(Get-Item -Path (Join-Path $base $pattern) -Force -ErrorAction SilentlyContinue)
        }
        $items
    }

    # A junction/symlink is deleted as a link only - never recursed into its target.
    function Remove-Vc($item) {
        if ($item.LinkType) { [System.IO.Directory]::Delete($item.FullName, $false) }
        else { Remove-Item -LiteralPath $item.FullName -Recurse -Force }
    }

    function Remove-InstalledFiles($base) {
        $items = @(Get-InstalledFiles $base)
        if (-not $items) { return }
        Write-Host 'Removing previously installed vc files:'
        $items | ForEach-Object { Write-Host $_.FullName }
        # .claude first so links go before their targets.
        $items | Sort-Object { -not ($_.FullName -match '[\\/]\.claude[\\/]') } | ForEach-Object { Remove-Vc $_ }
    }

    # Offers to remove a files install found under $base; throws when declined.
    function Clear-FilesAt($base) {
        $existing = @(Get-InstalledFiles $base)
        if (-not $existing) { return }
        Write-Warning "vc files are already installed under ${base}:"
        $existing | ForEach-Object { Write-Host $_.FullName }
        Write-Warning 'Do NOT install vc twice: every skill and command would load twice.'
        if (-not (Confirm-Vc 'Remove those files now?')) { throw 'Aborted. Delete those paths first.' }
        Remove-InstalledFiles $base
    }

    if (-not $Scope) { $Scope = 'project' }
    if ($Scope -notin 'project', 'user') { throw "Invalid scope '$Scope' (use project or user)." }

    # --- Install base: the project's git root, or your home for -Scope user -----------------
    if (-not (Test-Cmd git)) { throw 'git not found.' }
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) { $root = $null }
    if ($Scope -eq 'project') {
        if (-not $root) { throw 'Not inside a git repository. cd into your project first, or pass -Scope user.' }
        $base = (Resolve-Path $root).Path
    } else {
        $base = $HOME
    }
    # Run from the project (when there is one) so project-scope plugin installs resolve to it.
    if ($root) { Set-Location $root }
    Write-Host "Scope: $Scope ($base)"

    # The other place an install could already live. Skills there would load twice next to ours.
    $otherBase = $null
    if ($Scope -eq 'project') { $otherBase = $HOME } elseif ($root) { $otherBase = (Resolve-Path $root).Path }
    if ($otherBase -eq $base) { $otherBase = $null }

    # --- Pick a method ----------------------------------------------------------------------
    if ($Method -eq 'skills') { $Method = 'files' }
    if (-not $Method) {
        Write-Host ''
        Write-Host 'How do you want to install the vc skills? Pick ONE - do not use both.'
        Write-Host '  1) Claude Code plugin  (recommended for Claude Code users)'
        Write-Host '  2) Files              (skills + /vc:* and /vampirecoder:* commands copied in)'
        switch (Read-Host 'Choice [1/2]') {
            '1' { $Method = 'plugin' }
            '2' { $Method = 'files' }
            default { throw 'Invalid choice.' }
        }
    }
    if ($Method -notin 'plugin', 'files') { throw "Invalid method '$Method' (use plugin or files)." }

    # --- Plugin -----------------------------------------------------------------------------
    if ($Method -eq 'plugin') {
        if (-not (Test-Cmd claude)) { throw 'claude CLI not found. Install Claude Code first.' }

        Clear-FilesAt $base
        if ($otherBase) { Clear-FilesAt $otherBase }

        $scopes = Get-PluginScopes
        # One scope only: drop copies at the others.
        foreach ($s in ($scopes | Where-Object { $_ -ne $Scope })) {
            Write-Warning "The plugin is also installed at '$s' scope."
            if (-not (Confirm-Vc "Uninstall the $s-scope copy?")) {
                throw "Aborted. Run: claude plugin uninstall $Plugin -s $s"
            }
            claude plugin uninstall $Plugin -s $s
            if ($LASTEXITCODE -ne 0) { throw "Uninstalling the $s-scope plugin failed." }
        }

        claude plugin marketplace add $MarketplaceSrc --scope $Scope
        if ($LASTEXITCODE -ne 0) { Write-Host 'Marketplace already added, continuing.' }
        if ($scopes -contains $Scope) {
            Write-Host "Plugin already installed at $Scope scope - updating."
            claude plugin marketplace update $MarketplaceName
            if ($LASTEXITCODE -ne 0) { throw 'Marketplace update failed.' }
            claude plugin update $Plugin -s $Scope
        } else {
            claude plugin install $Plugin -s $Scope
        }
        if ($LASTEXITCODE -ne 0) { throw 'Plugin install/update failed.' }
        Write-Host 'Done. Restart Claude Code (or run /reload-plugins) to load the skills.'
        if ($Scope -eq 'project') { Write-Host 'Commit .claude/settings.json so teammates are prompted to install it.' }
        return
    }

    # --- Files ------------------------------------------------------------------------------
    $pluginScopes = Get-PluginScopes
    if ($pluginScopes) {
        Write-Warning "The vc Claude Code plugin ($Plugin) is installed."
        Write-Warning 'Do NOT use both the plugin and the files: every skill and command would load twice.'
        if (-not (Confirm-Vc 'Remove the plugin now?')) {
            throw "Aborted. Remove it first with: claude plugin uninstall $Plugin"
        }
        foreach ($s in $pluginScopes) {
            claude plugin uninstall $Plugin -s $s
            if ($LASTEXITCODE -ne 0) { throw "Uninstalling the $s-scope plugin failed." }
        }
    }
    if ($otherBase) { Clear-FilesAt $otherBase }

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("vc-setup-" + [guid]::NewGuid().ToString('N'))
    try {
        Write-Host "Cloning $RepoUrl ..."
        git clone --depth 1 -q $RepoUrl (Join-Path $tmp 'repo')
        if ($LASTEXITCODE -ne 0) { throw "Could not clone $RepoUrl." }
        $src = Join-Path $tmp 'repo'
        if (-not (Test-Path -LiteralPath (Join-Path $src 'skills'))) { throw 'The cloned repo has no skills/ folder.' }

        # Remove first so skills deleted upstream disappear and new ones are picked up.
        Remove-InstalledFiles $base
        New-Item -ItemType Directory -Force -Path (Join-Path $base '.agents/skills'), (Join-Path $base '.claude/skills') | Out-Null

        # Skills sit in bucket folders (skills\<bucket>\<name>\) upstream; installed flat.
        $count = 0
        foreach ($bucket in Get-ChildItem -LiteralPath (Join-Path $src 'skills') -Directory) {
            if ($bucket.Name -eq 'deprecated') { continue }
            foreach ($dir in Get-ChildItem -LiteralPath $bucket.FullName -Directory) {
                if (-not (Test-Path -LiteralPath (Join-Path $dir.FullName 'SKILL.md'))) { continue }
                if ($dir.Name -notlike 'vc-*') { Write-Host "Skipping '$($dir.Name)' (name must start with vc-)."; continue }
                $real = Join-Path $base ".agents/skills/$($dir.Name)"
                $link = Join-Path $base ".claude/skills/$($dir.Name)"
                Copy-Item -LiteralPath $dir.FullName -Destination $real -Recurse -Force
                # A junction needs no admin rights on Windows (a symlink would). If linking fails for
                # any reason, fall back to a plain copy.
                try {
                    if ($IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop') {
                        New-Item -ItemType Junction -Path $link -Target $real -ErrorAction Stop | Out-Null
                    } else {
                        New-Item -ItemType SymbolicLink -Path $link -Target "../../.agents/skills/$($dir.Name)" -ErrorAction Stop | Out-Null
                    }
                } catch {
                    if (Test-Path -LiteralPath $link) { Remove-Vc (Get-Item -LiteralPath $link -Force) }
                    Copy-Item -LiteralPath $dir.FullName -Destination $link -Recurse -Force
                }
                $count++
            }
        }
        if ($count -eq 0) { throw 'No skills found in the cloned repo.' }

        foreach ($ns in $Namespaces) {
            $commands = Join-Path $src "commands/$ns"
            if (Test-Path -LiteralPath $commands) {
                $dest = Join-Path $base ".claude/commands/$ns"
                New-Item -ItemType Directory -Force -Path $dest | Out-Null
                Copy-Item -Path (Join-Path $commands '*.md') -Destination $dest -Force
            }
        }

        $agents = Join-Path $src 'agents'
        if (Test-Path -LiteralPath $agents) {
            $dest = Join-Path $base '.claude/agents'
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
            Copy-Item -Path (Join-Path $agents '*.md') -Destination $dest -Force
        }
    } finally {
        if (Test-Path -LiteralPath $tmp) {
            # git marks pack files read-only, so -Force is needed.
            Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host "Installed $count skills into $base\.agents\skills (linked from .claude\skills), the /vc:* and /vampirecoder:* commands into .claude\commands and the subagents into .claude\agents."
    Write-Host 'Done. Restart your agent session so they are picked up.'
    if ($Scope -eq 'project') { Write-Host 'Commit .agents/ and .claude/ to share them with your team.' }
}

Invoke-VcSetup -Method $Method -Scope $Scope -Yes $Yes.IsPresent
