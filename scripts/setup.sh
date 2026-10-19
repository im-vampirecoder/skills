#!/bin/sh
# Install or update the vc skills, using EITHER the Claude Code plugin OR plain files (never
# both), in the current project (default) or for your user. Safe to re-run: installs when
# missing, updates when present.
#
# Usage:
#   ./setup.sh [--plugin | --files] [--project | --user] [--yes]
#   curl -fsSL https://raw.githubusercontent.com/im-vampirecoder/skills/main/scripts/setup.sh | sh -s -- --plugin
#
# --files clones the repo to a temp folder, then copies every skill to <base>/.agents/skills/
# (linked into <base>/.claude/skills/), commands/<ns>/ to <base>/.claude/commands/<ns>/ and
# agents/ to <base>/.claude/agents/. <base> is the project's git root, or $HOME with --user.
# POSIX sh, so it also works when piped to `sh`.
set -eu

MARKETPLACE_SRC="${VC_MARKETPLACE:-im-vampirecoder/skills}"
MARKETPLACE_NAME="vampirecoder-skills"
PLUGIN="vc@vampirecoder-skills"
REPO_URL="${VC_REPO_URL:-https://github.com/im-vampirecoder/skills}"
# Command namespaces the files install owns under .claude/commands/.
NAMESPACES="vc vampirecoder"

METHOD="${VC_METHOD:-}"
SCOPE="${VC_SCOPE:-project}"
YES=0
for arg in "$@"; do
  case "$arg" in
    --plugin) METHOD=plugin ;;
    --files|--skills) METHOD=files ;;
    --project) SCOPE=project ;;
    --user) SCOPE=user ;;
    -y|--yes) YES=1 ;;
    -h|--help) sed -n '2,13p' "$0" 2>/dev/null || true; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done
[ "$METHOD" = skills ] && METHOD=files

die() { echo "ERROR: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
# True only if /dev/tty can really be opened (it can exist yet fail, e.g. in CI).
has_tty() { (: </dev/tty) 2>/dev/null; }

# Prompts read from the terminal, not stdin, so they work under `curl ... | sh`.
ask() {
  # ask "<question>" -> returns 0 for yes. Default is no.
  [ "$YES" = 1 ] && return 0
  has_tty || die "No terminal available to prompt. Re-run with --yes to confirm automatically."
  printf '%s [y/N] ' "$1" >/dev/tty
  read -r answer </dev/tty || answer=""
  case "$answer" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

case "$SCOPE" in project|user) ;; *) die "Invalid scope '$SCOPE' (use project or user)." ;; esac

# --- Install base: the project's git root, or $HOME for --user ----------------------------
have git || die "git not found."
root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ "$SCOPE" = project ]; then
  [ -n "$root" ] || die "Not inside a git repository. cd into your project first, or pass --user."
  base="$root"
else
  base="$HOME"
fi
# Run from the project (when there is one) so project-scope plugin installs resolve to it.
[ -n "$root" ] && cd "$root"
echo "Scope: $SCOPE ($base)"

# The other place an install could already live. Skills there would load twice next to ours.
other_base=""
if [ "$SCOPE" = project ]; then other_base="$HOME"; elif [ -n "$root" ]; then other_base="$root"; fi
[ "$other_base" = "$base" ] && other_base=""

# --- Pick a method ------------------------------------------------------------------------
if [ -z "$METHOD" ]; then
  has_tty || die "No terminal to prompt. Pass --plugin or --files."
  {
    echo
    echo "How do you want to install the vc skills? Pick ONE - do not use both."
    echo "  1) Claude Code plugin  (recommended for Claude Code users)"
    echo "  2) Files              (skills + /vc:* and /vampirecoder:* commands copied in)"
    printf 'Choice [1/2]: '
  } >/dev/tty
  read -r choice </dev/tty || choice=""
  case "$choice" in 1) METHOD=plugin ;; 2) METHOD=files ;; *) die "Invalid choice." ;; esac
fi
case "$METHOD" in plugin|files) ;; *) die "Invalid method '$METHOD' (use plugin or files)." ;; esac

# --- Helpers ------------------------------------------------------------------------------
# Scopes (user/project/local) the vc plugin is installed at for THIS project, one per line.
# A project-scope install belonging to another project (projectPath differs) is ignored.
plugin_scopes() {
  have claude || return 0
  here=$(pwd -W 2>/dev/null || pwd)
  claude plugin list --json 2>/dev/null | awk -v id="$PLUGIN" -v here="$here" '
    function norm(s) { gsub(/[\\]+/, "/", s); return tolower(s) }
    /^[[:space:]]*\{/ { eid = ""; scope = ""; path = "" }
    /"id":/ { eid = $0; sub(/.*"id": *"/, "", eid); sub(/".*/, "", eid) }
    /"scope":/ { scope = $0; sub(/.*"scope": *"/, "", scope); sub(/".*/, "", scope) }
    /"projectPath":/ { path = $0; sub(/.*"projectPath": *"/, "", path); sub(/".*/, "", path) }
    /^[[:space:]]*\}/ { if (eid == id && (scope != "project" || path == "" || norm(path) == norm(here))) print scope }
  '
}

# Paths of a files install under <base> (also catches skills linked by link-skills.sh), one per line.
files_installed() {
  for p in "$1"/.agents/skills/vc-* "$1"/.claude/skills/vc-* "$1"/.claude/agents/vc-*; do
    if [ -e "$p" ] || [ -L "$p" ]; then echo "$p"; fi
  done
  for ns in $NAMESPACES; do
    p="$1/.claude/commands/$ns"
    if [ -e "$p" ] || [ -L "$p" ]; then echo "$p"; fi
  done
}

# rm -rf on a link removes the link itself, never what it points at.
remove_files() {
  existing=$(files_installed "$1")
  [ -n "$existing" ] || return 0
  echo "Removing previously installed vc files:"
  echo "$existing"
  # .claude first so links go before their targets.
  for p in "$1"/.claude/skills/vc-* "$1"/.claude/agents/vc-* "$1"/.agents/skills/vc-*; do
    if [ -e "$p" ] || [ -L "$p" ]; then rm -rf "$p"; fi
  done
  for ns in $NAMESPACES; do rm -rf "${1:?}/.claude/commands/$ns"; done
}

# Offers to remove a files install found under <base>; aborts when declined.
clear_files_at() {
  existing=$(files_installed "$1")
  [ -n "$existing" ] || return 0
  echo
  echo "WARNING: vc files are already installed under $1:"
  echo "$existing"
  echo "Do NOT install vc twice: every skill and command would load twice."
  ask "Remove those files now?" || die "Aborted. Delete those paths first."
  remove_files "$1"
}

# --- Plugin -------------------------------------------------------------------------------
if [ "$METHOD" = plugin ]; then
  have claude || die "claude CLI not found. Install Claude Code first."

  clear_files_at "$base"
  [ -n "$other_base" ] && clear_files_at "$other_base"

  scopes=$(plugin_scopes)
  # One scope only: drop copies at the others.
  for scope in $scopes; do
    if [ "$scope" != "$SCOPE" ]; then
      echo
      echo "WARNING: the plugin is also installed at '$scope' scope."
      ask "Uninstall the $scope-scope copy?" || die "Aborted. Run: claude plugin uninstall $PLUGIN -s $scope"
      claude plugin uninstall "$PLUGIN" -s "$scope"
    fi
  done

  claude plugin marketplace add "$MARKETPLACE_SRC" --scope "$SCOPE" || echo "Marketplace already added, continuing."
  if printf '%s\n' "$scopes" | grep -qx "$SCOPE"; then
    echo "Plugin already installed at $SCOPE scope - updating."
    claude plugin marketplace update "$MARKETPLACE_NAME"
    claude plugin update "$PLUGIN" -s "$SCOPE"
  else
    claude plugin install "$PLUGIN" -s "$SCOPE"
  fi
  echo "Done. Restart Claude Code (or run /reload-plugins) to load the skills."
  [ "$SCOPE" = project ] && echo "Commit .claude/settings.json so teammates are prompted to install it."
  exit 0
fi

# --- Files --------------------------------------------------------------------------------
if [ -n "$(plugin_scopes)" ]; then
  echo
  echo "WARNING: the vc Claude Code plugin ($PLUGIN) is installed."
  echo "Do NOT use both the plugin and the files: every skill and command would load twice."
  ask "Remove the plugin now?" || die "Aborted. Remove it first with: claude plugin uninstall $PLUGIN"
  for scope in $(plugin_scopes); do
    claude plugin uninstall "$PLUGIN" -s "$scope"
  done
fi
[ -n "$other_base" ] && clear_files_at "$other_base"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
echo "Cloning $REPO_URL ..."
git clone --depth 1 -q "$REPO_URL" "$tmp/repo" || die "Could not clone $REPO_URL."
src="$tmp/repo"
[ -d "$src/skills" ] || die "The cloned repo has no skills/ folder."

# Remove first so skills deleted upstream disappear and new ones are picked up.
remove_files "$base"
mkdir -p "$base/.agents/skills" "$base/.claude/skills"

# Skills sit in bucket folders (skills/<bucket>/<name>/) upstream; installed flat.
count=0
for dir in "$src"/skills/*/*/; do
  dir=${dir%/}
  [ -f "$dir/SKILL.md" ] || continue
  bucket=${dir%/*}; bucket=${bucket##*/}
  [ "$bucket" = deprecated ] && continue
  name=${dir##*/}
  case "$name" in vc-*) ;; *) echo "Skipping '$name' (name must start with vc-)."; continue ;; esac
  cp -R "$dir" "$base/.agents/skills/$name"
  # Relative link so the folder stays portable. Where links are unavailable (e.g. Git Bash without
  # symlink support) `ln` makes a copy or fails: fall back to a plain copy.
  ln -s "../../.agents/skills/$name" "$base/.claude/skills/$name" 2>/dev/null || true
  if [ ! -L "$base/.claude/skills/$name" ]; then
    rm -rf "$base/.claude/skills/$name"
    cp -R "$dir" "$base/.claude/skills/$name"
  fi
  count=$((count + 1))
done
[ "$count" -gt 0 ] || die "No skills found in the cloned repo."

for ns in $NAMESPACES; do
  if [ -d "$src/commands/$ns" ]; then
    mkdir -p "$base/.claude/commands/$ns"
    cp "$src"/commands/"$ns"/*.md "$base/.claude/commands/$ns/"
  fi
done

if [ -d "$src/agents" ]; then
  mkdir -p "$base/.claude/agents"
  cp "$src"/agents/*.md "$base/.claude/agents/"
fi

echo "Installed $count skills into $base/.agents/skills (linked from .claude/skills), the /vc:* and /vampirecoder:* commands into .claude/commands and the subagents into .claude/agents."
echo "Done. Restart your agent session so they are picked up."
[ "$SCOPE" = project ] && echo "Commit .agents/ and .claude/ to share them with your team."
exit 0
