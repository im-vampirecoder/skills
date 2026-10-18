"""Deterministic structural lint for a vc architecture spine (architecture.md).

Checks only what can be checked without judgment: frontmatter fields per
scope, leftover template placeholders, AD-n id numbering, required AD
fields, supersession links, Stack versions, and Criteria Coverage gaps.
Judgment calls (is this decision real, is the evidence right) belong to the
reviewer subagents, not here.

Usage: python scripts/lint_spine.py <path/to/architecture.md>
Exit code: 0 when no ERROR lines, 1 otherwise, 2 on bad usage.
Stdlib only, so it runs anywhere Python 3.8+ does.
"""

import re
import sys

SCOPES = {"product", "epic", "feature"}
AD_HEADING = re.compile(r"^###\s+AD-(\d+)\b")
SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")
# Template tokens like <decision> or {AD-id}; not HTML-ish tags such as <br>.
PLACEHOLDER = re.compile(r"<[a-z][^<>\n]{2,}>|\{[A-Za-z][^{}\n]*\}|\bTBD\b|\bTODO\b")


def parse_frontmatter(lines):
    """Return (fields dict, index of first body line)."""
    if not lines or lines[0].strip() != "---":
        return None, 0
    fields = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, i + 1
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.split("#", 1)[0].strip()
    return None, 0


def split_sections(body):
    """Map '## Heading' -> list of (line number, text) under it."""
    sections, current = {}, None
    for number, line in body:
        match = SECTION_HEADING.match(line)
        if match and not line.startswith("###"):
            current = match.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append((number, line))
    return sections


def table_rows(section_lines):
    """Data rows of the first Markdown table in a section, as cell lists."""
    rows = [line for _, line in section_lines if line.strip().startswith("|")]
    return [
        [cell.strip() for cell in row.strip().strip("|").split("|")]
        for row in rows[2:]  # skip header and separator
    ]


def lint(path):
    errors, warnings = [], []
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    fields, body_start = parse_frontmatter(lines)
    if fields is None:
        return ["missing or unterminated YAML frontmatter"], []
    scope = fields.get("scope", "")
    if scope not in SCOPES:
        errors.append(f"frontmatter scope '{scope}' is not one of {sorted(SCOPES)}")
    for key in ("status", "updated"):
        if not fields.get(key):
            errors.append(f"frontmatter '{key}' is missing or empty")
    if scope == "epic" and not fields.get("epic_id", "").startswith("EPIC-"):
        errors.append("epic scope needs epic_id: EPIC-<slug>")
    if scope == "feature" and not fields.get("feature_id", "").startswith("FEATURE-"):
        errors.append("feature scope needs feature_id: FEATURE-<slug>")

    body = list(enumerate(lines[body_start:], start=body_start + 1))
    in_fence = False
    for number, line in body:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for token in PLACEHOLDER.findall(INLINE_CODE.sub("", line)):
            errors.append(f"line {number}: leftover placeholder {token!r}")

    sections = split_sections(body)
    if scope == "product" and "Inherited Invariants" in sections:
        errors.append("product scope has no parent, so no Inherited Invariants section")

    # AD blocks: contiguous ids from 1, required fields, supersession links.
    blocks, order = {}, []
    for heading_name, section in sections.items():
        if heading_name != "Decisions":
            continue
        current = None
        for number, line in section:
            match = AD_HEADING.match(line)
            if match:
                current = int(match.group(1))
                if current in blocks:
                    errors.append(f"line {number}: duplicate AD-{current}")
                blocks[current] = {"line": number, "text": []}
                order.append(current)
            elif current is not None:
                blocks[current]["text"].append(line)
    if order and order != list(range(1, len(order) + 1)):
        errors.append(f"AD ids must run AD-1..AD-{len(order)} in order with no gaps, found {order}")
    superseded_by = {}
    for ad, block in blocks.items():
        text = "\n".join(block["text"])
        for field in ("Binds", "Prevents", "Rule"):
            if f"**{field}:**" not in text:
                errors.append(f"AD-{ad} (line {block['line']}) is missing **{field}:**")
        for old in re.findall(r"\*\*Supersedes:\*\*\s*AD-(\d+)", text):
            old = int(old)
            if old not in blocks or old >= ad:
                errors.append(f"AD-{ad} supersedes AD-{old}, which must be an earlier AD in this spine")
            superseded_by[old] = ad
        status = re.search(r"\*\*Status:\*\*\s*Superseded by AD-(\d+)", text)
        if status and superseded_by.get(ad) not in (None, int(status.group(1))):
            errors.append(f"AD-{ad} Status names AD-{status.group(1)}, but AD-{superseded_by[ad]} supersedes it")
    for old, new in superseded_by.items():
        if old in blocks and "Superseded by AD-" not in "\n".join(blocks[old]["text"]):
            errors.append(f"AD-{old} is superseded by AD-{new} but has no **Status:** Superseded line")

    for row in table_rows(sections.get("Stack", [])):
        if len(row) >= 4 and row[2] and not row[3]:
            errors.append(f"Stack row '{row[0]}' has a choice but no pinned version")

    if scope == "product" and "Proposed Parent Spine Changes" in sections:
        errors.append("product scope has no parent, so no Proposed Parent Spine Changes section")
    for row in table_rows(sections.get("Proposed Parent Spine Changes", [])):
        if len(row) < 6 or not row[5]:
            errors.append(f"Proposed Parent Spine Changes row '{row[0]}' has no status")
    for row in table_rows(sections.get("Technical Debt", [])):
        if len(row) < 4 or not row[3]:
            errors.append(f"Technical Debt row '{row[0]}' has no payoff trigger")

    if scope == "feature":
        coverage = table_rows(sections.get("Criteria Coverage", []))
        if not coverage:
            errors.append("feature scope needs a non-empty Criteria Coverage table")
        for row in coverage:
            if any(cell.upper() == "GAP" for cell in row) or (len(row) > 1 and not row[1]):
                warnings.append(f"Criteria Coverage gap: {row[0][:70]}")

    return errors, warnings


def main(argv):
    if len(argv) != 2:
        print("Usage: python scripts/lint_spine.py <path/to/architecture.md>")
        return 2
    errors, warnings = lint(argv[1])
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    if not errors and not warnings:
        print("OK: no structural issues")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
