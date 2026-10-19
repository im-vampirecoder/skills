#!/usr/bin/env bash
set -euo pipefail

# Symlinks every skill, command shim, and agent in this repo into a project's .claude/ folder so
# Claude Code loads them there while you develop: the git repo you run it from by default, or the
# directory given. Re-run after adding, removing, or renaming a skill, command, or agent; links into
# this repo that no longer resolve are pruned. A git pull keeps linked skills current automatically.
#
# Usage:
#   scripts/link-skills.sh [target-dir]            # link into <target-dir>/.claude
#   scripts/link-skills.sh --unlink [target-dir]   # remove every link into this repo from there

REPO="$(cd "$(dirname "$0")/.." && pwd)"

UNLINK=0
if [ "${1:-}" = "--unlink" ]; then UNLINK=1; shift; fi
if [ $# -gt 0 ]; then
  TARGET="$(cd "$1" && pwd)"
else
  TARGET="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
CLAUDE_DIR="$TARGET/.claude"

for sub in skills agents commands; do
  if [ -L "$CLAUDE_DIR/$sub" ]; then
    echo "error: $CLAUDE_DIR/$sub is itself a symlink ($(readlink "$CLAUDE_DIR/$sub"))." >&2
    echo "Remove it (rm \"$CLAUDE_DIR/$sub\") and re-run; the script will recreate it as a real dir." >&2
    exit 1
  fi
done

# Removes links under the target that point into this repo: all of them with --unlink, otherwise
# only the broken ones (a skill, command, or agent renamed or deleted since the last run).
prune() {
  [ -d "$CLAUDE_DIR" ] || return 0
  # find exits non-zero for a folder that doesn't exist yet; that's not an error here.
  { find "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands" -maxdepth 2 -type l 2>/dev/null || true; } |
    while IFS= read -r link; do
      case "$(readlink "$link")" in
        "$REPO"/*)
          if [ "$UNLINK" -eq 1 ] || [ ! -e "$link" ]; then
            rm "$link"
            echo "unlinked ${link#"$CLAUDE_DIR"/}"
          fi
          ;;
      esac
    done
}

prune
if [ "$UNLINK" -eq 1 ]; then
  echo "removed links into $REPO from $CLAUDE_DIR"
  exit 0
fi

echo "linking into $CLAUDE_DIR"
mkdir -p "$CLAUDE_DIR/skills"

found=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$CLAUDE_DIR/skills/$name"

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

# Slash-command shims: commands/<ns>/<cmd>.md -> .claude/commands/<ns>/<cmd>.md
for ns_dir in "$REPO"/commands/*/; do
  ns="$(basename "$ns_dir")"
  mkdir -p "$CLAUDE_DIR/commands/$ns"
  for cmd in "$ns_dir"*.md; do
    ln -sfn "$cmd" "$CLAUDE_DIR/commands/$ns/$(basename "$cmd")"
    echo "linked /$ns:$(basename "$cmd" .md)"
  done
done

# Subagents some skills spawn: agents/<name>.md -> .claude/agents/<name>.md
if [ -d "$REPO/agents" ]; then
  mkdir -p "$CLAUDE_DIR/agents"
  for agent in "$REPO"/agents/*.md; do
    ln -sfn "$agent" "$CLAUDE_DIR/agents/$(basename "$agent")"
    echo "linked agent $(basename "$agent" .md)"
  done
fi
