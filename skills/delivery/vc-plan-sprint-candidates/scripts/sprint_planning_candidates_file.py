"""
Read and update artifacts/sprints/<sprint-slug>/candidates.md for settle
(references/candidates-template.md is the format).

Only two columns are parsed: carryover `Decision` and candidates
`In sprint`, both keyed by the `Item` column (a STORY-..., BUG-..., or ADO-<n> id).
Everything else in the file is for people and is left untouched.
"""
import re

from sprint_planning_frontmatter import split_frontmatter, parse_frontmatter

ID_PATTERN = re.compile(r"\b(?:STORY|BUG|ADO)-[A-Za-z0-9-]+\b")


def _section(body, heading):
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return match.group(1) if match else ""


def _cells(line):
    return [cell.strip().strip("`").strip() for cell in line.strip().strip("|").split("|")]


def parse_table(section_text, wanted):
    """Rows of the first markdown table in a section, as {column: value} for
    the `Item` column plus the wanted one. Header names are matched
    case-insensitively; a missing column returns (None, problem)."""
    lines = [line for line in section_text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return [], None
    header = [name.lower() for name in _cells(lines[0])]
    for column in ("item", wanted.lower()):
        if column not in header:
            return None, f"table has no '{column}' column"
    item_at, wanted_at = header.index("item"), header.index(wanted.lower())
    rows = []
    for line in lines[2:]:
        cells = _cells(line)
        if len(cells) <= max(item_at, wanted_at):
            continue
        found = ID_PATTERN.search(cells[item_at])
        if not found:
            continue  # placeholder or "None." row
        rows.append({"id": found.group(0), "value": cells[wanted_at].lower()})
    return rows, None


def read_candidates(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    fm_text, body = split_frontmatter(text)
    meta = parse_frontmatter(fm_text)
    carryover, carry_problem = parse_table(_section(body, "Carryover"), "Decision")
    candidates, cand_problem = parse_table(_section(body, "Candidates"), "In sprint")
    problems = []
    if carry_problem:
        problems.append(f"Carryover {carry_problem}")
    if cand_problem:
        problems.append(f"Candidates {cand_problem}")
    return {"meta": meta, "carryover": carryover or [], "candidates": candidates or [],
            "problems": problems}


def mark_settled(path, record_lines):
    """Set frontmatter status: settled and append a dated block under
    '## Settle record' (created at the end of the file if missing)."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    fm_text, body = split_frontmatter(text)
    if re.search(r"^status:.*$", fm_text, re.M):
        fm_text = re.sub(r"^status:.*$", "status: settled", fm_text, count=1, flags=re.M)
    else:
        fm_text += "\nstatus: settled"
    block = "\n".join(record_lines) + "\n"
    heading = re.search(r"^##[ \t]+Settle record[ \t]*$", body, re.M)
    if heading:
        # Drop the template placeholder line, keep earlier records.
        tail = re.sub(r"^<filled by settle[^\n]*>\n?", "", body[heading.end():].lstrip("\n"), flags=re.M)
        body = body[:heading.end()] + "\n\n" + (tail.rstrip() + "\n\n" if tail.strip() else "") + block
    else:
        body = body.rstrip() + "\n\n## Settle record\n\n" + block
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"---\n{fm_text}\n---\n{body}")
