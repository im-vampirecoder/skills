"""Parse a vc user-flow map (`<feature folder>/ux/user-flow.md`).

Shared by check_user_flow.py and user_flow_requirements.py. Python 3 stdlib only.
The format is defined in references/user-flow-template.md and
references/flow-diagram-conventions.md.
"""

import hashlib
import re
from pathlib import Path

SECTION_RE = re.compile(r"^##\s+(\d)\.\s+(.*)$")
NODE_ID = r"[A-Za-z][A-Za-z0-9_]*"
# Node shapes: ["..."] screen, {"..."} decision, (["..."]) / (("...")) / ("...") start or end markers.
SHAPE_RE = r'(\[\(.*?\)\]|\(\[.*?\]\)|\(\(.*?\)\)|\[.*?\]|\{.*?\}|\(.*?\))'
NODE_RE = re.compile(rf"^({NODE_ID})\s*{SHAPE_RE}\s*(?::::\s*({NODE_ID}))?\s*;?$")
EDGE_RE = re.compile(rf"^({NODE_ID})\s*(-->|-\.->|==>)\s*(?:\|(.*?)\|)?\s*({NODE_ID})\s*;?$")
CLASS_RE = re.compile(rf"^class\s+([A-Za-z0-9_,\s]+?)\s+({NODE_ID})\s*;?$")
SKIP_RE = re.compile(r"^(flowchart\b|graph\b|classDef\b|linkStyle\b|style\b|subgraph\b|end$|direction\b|%%)")
SCREEN_NUM_RE = re.compile(r"^\[(\d+)\]")
ID_TOKEN_RE = re.compile(r"\b(?:FR|NFR|BR|ERR)-[A-Za-z0-9.-]+[A-Za-z0-9]")
NODE_REF_RE = re.compile(rf"^\s*`?({NODE_ID})`?")


def read_frontmatter(text):
    """Flat `key: value` frontmatter; `[a, b]` values become lists."""
    if not text.startswith("---"):
        return {}
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
    return meta


def split_sections(text):
    """{section number: (heading, body lines with their 1-based line numbers)}."""
    sections, current = {}, None
    for number, line in enumerate(text.splitlines(), 1):
        match = SECTION_RE.match(line)
        if match:
            current = int(match.group(1))
            sections[current] = (match.group(2).strip(), [])
        elif current is not None:
            sections[current][1].append((number, line))
    return sections


def flow_hash(text):
    """sha256 over sections 1-4, ignoring trailing spaces and blank-line runs."""
    sections = split_sections(text)
    parts = []
    for n in (1, 2, 3, 4):
        heading, lines = sections.get(n, ("", []))
        body = [l.rstrip() for _, l in lines]
        parts.append(f"## {n}. {heading}\n" + "\n".join(l for l in body if l))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def mermaid_lines(lines):
    """Lines inside the first ```mermaid block of a section, with line numbers."""
    out, inside = [], False
    for number, line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if inside:
                break
            inside = stripped[3:].strip().lower() == "mermaid"
            continue
        if inside and stripped:
            out.append((number, stripped))
    return out


def unquote(label):
    label = label.strip()
    return label[1:-1] if len(label) >= 2 and label[0] == label[-1] == '"' else label


def parse_diagram(lines):
    """Nodes, edges, per-node classes and lines the parser didn't understand."""
    nodes, edges, unparsed = {}, [], []
    classes = {}
    for number, line in mermaid_lines(lines):
        if SKIP_RE.match(line):
            continue
        node, edge, cls = NODE_RE.match(line), EDGE_RE.match(line), CLASS_RE.match(line)
        if edge:
            src, _, label, dst = edge.groups()
            edges.append({"from": src, "to": dst, "label": label, "line": number})
        elif node:
            node_id, shape, klass = node.groups()
            inner = shape[1:-1]
            if shape[:2] in ("([", "((", "[("):
                inner = shape[2:-2]
            nodes[node_id] = {"id": node_id, "raw": inner, "label": unquote(inner),
                              "decision": shape.startswith("{"), "line": number}
            if klass:
                classes.setdefault(node_id, set()).add(klass)
        elif cls:
            for node_id in re.split(r"[,\s]+", cls.group(1).strip()):
                classes.setdefault(node_id, set()).add(cls.group(2))
        else:
            unparsed.append((number, line))
    for node_id, node in nodes.items():
        node["classes"] = classes.get(node_id, set())
        match = SCREEN_NUM_RE.match(node["label"])
        node["screen"] = int(match.group(1)) if match and not node["decision"] else None
    return nodes, edges, unparsed


def parse_table(lines):
    """First markdown table in a section: list of {header: cell} plus line number."""
    rows, headers = [], None
    for number, line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if headers:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if headers is None:
            headers = [h.lower() for h in cells]
        elif not all(set(c) <= set("-: ") for c in cells):
            row = dict(zip(headers, cells))
            row["_line"] = number
            rows.append(row)
    return rows


def cell(row, *names):
    """A row's value under the first header that starts with one of `names`."""
    for name in names:
        for key, value in row.items():
            if key.startswith(name):
                return value
    return ""


def ids_in(text):
    return ID_TOKEN_RE.findall(text or "")


def node_ref(text):
    match = NODE_REF_RE.match(text or "")
    return match.group(1) if match else None


def load_map(path):
    text = Path(path).read_text(encoding="utf-8")
    sections = split_sections(text)
    get = lambda n: sections.get(n, ("", []))[1]
    nodes, edges, unparsed = parse_diagram(get(1))
    return {
        "path": str(path),
        "text": text,
        "meta": read_frontmatter(text),
        "sections": sections,
        "nodes": nodes,
        "edges": edges,
        "unparsed": unparsed,
        "screens": parse_table(get(2)),
        "flows": parse_table(get(3)),
        "transitions": parse_table(get(4)),
        "hash": flow_hash(text),
    }
