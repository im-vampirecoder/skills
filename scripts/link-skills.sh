#!/usr/bin/env bash
set -euo pipefail

# Symlinks every skill, command shim, and agent in this repo into ~/.claude so Claude Code can
# discover and load them while you develop. Re-run after adding, removing, or
# renaming a skill, command, or agent. A git pull keeps linked skills current automatically.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude/skills"

if [ -L "$DEST" ]; then
  resolved="$(readlink -f "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run; the script will recreate it as a real dir." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

found=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    rm -rf "$target"
  fi

  ln -sfn "$src" "$target"
  echo "linked $name -> $src"
  found=$((found + 1))
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/deprecated/*' -print0 2>/dev/null)

if [ "$found" -eq 0 ]; then
  echo "no skills found under $REPO/skills yet"
fi

# Slash-command shims: commands/<ns>/<cmd>.md -> ~/.claude/commands/<ns>/<cmd>.md
for ns_dir in "$REPO"/commands/*/; do
  ns="$(basename "$ns_dir")"
  mkdir -p "$HOME/.claude/commands/$ns"
  for cmd in "$ns_dir"*.md; do
    ln -sfn "$cmd" "$HOME/.claude/commands/$ns/$(basename "$cmd")"
    echo "linked /$ns:$(basename "$cmd" .md)"
  done
done

# Subagents some skills spawn: agents/<name>.md -> ~/.claude/agents/<name>.md
if [ -d "$REPO/agents" ]; then
  mkdir -p "$HOME/.claude/agents"
  for agent in "$REPO"/agents/*.md; do
    ln -sfn "$agent" "$HOME/.claude/agents/$(basename "$agent")"
    echo "linked agent $(basename "$agent" .md)"
  done
fi
