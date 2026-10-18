"""Parse a vc as-built pack (`<feature folder>/as-built/`, or its `.draft/`).

Shared by check_as_built.py and its level modules. Python 3 stdlib only.
The file formats are defined in references/templates/.
"""

import re
from pathlib import Path

LABELS = {"✅": "asserted", "🔵": "corroborated", "🟡": "inferred"}
PACK_FILES = ("spec.md", "evidence.md", "flows.md", "states.md", "erd.md", "use-cases/index.md")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
SID_RE = re.compile(r"\bS(\d+)(?::(\d+)(?:-(\d+))?)?\b")
PATH_RE = re.compile(r"(?<![\w/.@+-])((?:[\w@.+-]+/)+[\w@.+-]+\.\w+)(?::(\d+)(?:-(\d+))?)?")
BACKTICK_RE = re.compile(r"`([^`]+)`")
OMITTED_RE = re.compile(r"^_(Omitted|None|No cross-repo hops)\b", re.I)


def read_frontmatter(text):
    """Flat `key: value` frontmatter; `[a, b]` values become lists."""
    if not text.startswith("---"):
        return {}, 0
    end = text.find("\n---", 3)
    meta = {}
    for line in text[3:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        meta[key.strip()] = value
    return meta, text[:end].count("\n") + 2


def split_sections(text, heading_re=H2_RE):
    """{heading: [(line number, line), ...]} in file order; repeated headings get ` #2` suffixes."""
    sections, current = {}, None
    for number, line in enumerate(text.splitlines(), 1):
        match = heading_re.match(line)
        if match and not (heading_re is H2_RE and line.startswith("###")):
            current = match.group(1)
            while current in sections:
                current += " #2"
            sections[current] = []
        elif current is not None:
            sections[current].append((number, line))
    return sections


def parse_tables(lines):
    """Every markdown table in `lines`: list of rows ({lowercase header: cell, "_line": n})."""
    tables, rows, headers = [], [], None
    for number, line in lines + [(None, "")]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if headers:
                tables.append(rows)
            rows, headers = [], None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if headers is None:
            headers = [h.lower() for h in cells]
        elif not all(set(c) <= set("-: ") for c in cells):
            row = dict(zip(headers, cells))
            row["_line"] = number
            rows.append(row)
    return tables


def first_table(lines):
    tables = parse_tables(lines)
    return tables[0] if tables else []


def is_omitted(lines):
    return any(OMITTED_RE.match(line.strip()) for _, line in lines)


def cell(row, *names):
    """A row's value under the first header that starts with one of `names`."""
    for name in names:
        for key, value in row.items():
            if key != "_line" and key.startswith(name):
                return value
    return ""


def label_of(row):
    value = cell(row, "label").strip()
    return value if value in LABELS else None


def mermaid_blocks(text):
    """[(kind, first line number, [(n, line)], h2, h3)] for every ```mermaid block."""
    blocks, inside, h2, h3 = [], None, None, None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if inside is None:
            if H2_RE.match(line) and not line.startswith("###"):
                h2, h3 = H2_RE.match(line).group(1), None
            elif H3_RE.match(line):
                h3 = H3_RE.match(line).group(1)
            elif stripped.startswith("```") and stripped[3:].strip().lower() == "mermaid":
                inside = []
            continue
        if stripped.startswith("```"):
            body = [(n, l) for n, l in inside if l.strip() and not l.strip().startswith("%%")]
            kind = body[0][1].split()[0] if body else ""
            blocks.append((kind, body[0][0] if body else number, body[1:], h2, h3))
            inside = None
        else:
            inside.append((number, line))
    return blocks


def path_citations(text):
    """[(path, start, end)] for every repo-path citation in `text`."""
    out = []
    for match in PATH_RE.finditer(text or ""):
        path, start, end = match.groups()
        out.append((path, int(start) if start else None, int(end) if end else None))
    return out


def sid_citations(text):
    return [(int(n), int(a) if a else None, int(b) if b else None) for n, a, b in SID_RE.findall(text or "")]


def submodule_root(root):
    config = Path(root) / ".vc" / "config.toml"
    if config.is_file():
        match = re.search(r'^submodule_root\s*=\s*"([^"]+)"', config.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1).strip("/")
    return "src"


def find_root(pack_dir):
    """The tracking repo root: the parent of the nearest `artifacts/` above the pack."""
    for parent in Path(pack_dir).resolve().parents:
        if parent.name == "artifacts":
            return parent.parent
    return None


def load_pack(pack_dir):
    pack_dir = Path(pack_dir)
    files = {}
    for name in [*PACK_FILES, *sorted(p.relative_to(pack_dir).as_posix()
                                      for p in (pack_dir / "use-cases").glob("uc-*.md"))]:
        path = pack_dir / name
        if path.is_file():
            files[name] = path.read_text(encoding="utf-8")
    spec_text = files.get("spec.md", "")
    meta, _ = read_frontmatter(spec_text)
    spec = split_sections(spec_text)
    sources = {}
    for row in first_table(spec.get("Sources", [])):
        match = re.fullmatch(r"S(\d+)", cell(row, "id").strip())
        if match:
            sources[int(match.group(1))] = {"path": cell(row, "path").strip("` "), "line": row["_line"]}
    return {"dir": pack_dir, "files": files, "meta": meta, "spec": spec, "sources": sources}
