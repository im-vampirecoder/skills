"""
Small, dependency-free helpers shared by the sprint planning scripts:

  - split_frontmatter / parse_frontmatter: read the YAML subset vc
    artifacts use (scalars, inline [a, b] lists, block "- item" lists, and
    block lists of one-level maps such as capacity.md's `members`). Not a
    general YAML parser - just enough for files vc skills write.
  - sprint_slug: the folder name rule from
    references/capacity-file-contract.md ("Sprint 42" -> "sprint-42").
"""
import re

_NULLS = {"", "null", "~", "none"}


def sprint_slug(name):
    """Last iteration-path segment, lowercased, non a-z0-9 runs -> '-'."""
    leaf = re.split(r"[\\/]", name.strip())[-1] if name else ""
    return re.sub(r"[^a-z0-9]+", "-", leaf.lower()).strip("-")


def split_frontmatter(text):
    """Return (frontmatter_text, body). No frontmatter -> ("", text)."""
    if not text.startswith("---"):
        return "", text
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not match:
        return "", text
    return match.group(1), match.group(2)


def _scalar(raw):
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.lower() in _NULLS:
        return None
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(part) for part in inner.split(",")] if inner else []
    return value


def _strip_comment(line):
    # Drop " # comment" tails, but keep '#' inside quotes or values like C#.
    return re.sub(r"\s+#\s.*$", "", line)


def parse_frontmatter(fm_text):
    """Parse the supported YAML subset into a dict."""
    data = {}
    current_key = None      # key whose block list we are filling
    current_item = None     # dict item inside that list, if any
    for raw_line in fm_text.splitlines():
        line = _strip_comment(raw_line.rstrip())
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if indent == 0:
            current_item = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            if value.strip():
                data[key] = _scalar(value)
                current_key = None
            else:
                data[key] = []
                current_key = key
            continue

        if current_key is None:
            continue
        if stripped.startswith("- "):
            entry = stripped[2:]
            if re.match(r"^[\w-]+\s*:", entry):
                key, _, value = entry.partition(":")
                current_item = {key.strip(): _scalar(value)}
                data[current_key].append(current_item)
            else:
                current_item = None
                data[current_key].append(_scalar(entry))
        elif current_item is not None and ":" in stripped:
            key, _, value = stripped.partition(":")
            current_item[key.strip()] = _scalar(value)
    return data


def read_markdown(path):
    """Return (frontmatter dict, body) for a markdown file."""
    with open(path, encoding="utf-8") as handle:
        fm_text, body = split_frontmatter(handle.read())
    return parse_frontmatter(fm_text), body
