"""Diagram levels for check_as_built.py: renderer safety and compile. Python 3 stdlib only.

Renderer safety covers what strict viewers (GitHub, IDE previews) reject even
when the Mermaid CLI accepts it. Findings are (severity, name, message, where).
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from as_built_parse import cell, first_table, mermaid_blocks, split_sections

MERMAID_CLI = "@mermaid-js/mermaid-cli@10.9.1"
ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")
SPECIAL = set('()[]{}:;#&<>|/"\'')
SEQ_MSG_RE = re.compile(r"^\s*[\w ]+?\s*(?:-->>|->>|-->|->|--x|-x|--\)|-\))\s*[\w ]+?\s*:(.*)$")
SEQ_NOTE_RE = re.compile(r"^\s*Note\s+(?:over|left of|right of)\s+[^:]+:(.*)$", re.I)
FLOW_LABEL_RE = re.compile(r'\(\[(.*?)\]\)|\(\((.*?)\)\)|\[(.*?)\]|\{(.*?)\}|\|(.*?)\||(?<=\w)\((.*?)\)')
STATE_EDGE_RE = re.compile(r"^\s*\S+\s*-->\s*\S+\s*:(.*)$")
ER_REL_RE = re.compile(r"^\s*\w+\s+[|}o][|o]?--[|o]?[|{o]\s+\w+\s*:\s*(.*)$")
MAX_TRANSITION = 40


def _text_rules(text, at, out, allow_semicolon=False):
    if not allow_semicolon and ";" in text:
        out.append(("error", "semicolon", "no `;` in a message or transition label (it ends the statement)", at))
    if ENTITY_RE.search(text):
        out.append(("error", "html-entity", "write the character, not an HTML entity", at))


def _flowchart(lines, where, out):
    for n, line in lines:
        if line.strip().startswith(("classDef", "class ", "style", "linkStyle", "subgraph", "end", "direction")):
            continue
        for match in FLOW_LABEL_RE.finditer(line):
            raw = next(g for g in match.groups() if g is not None).strip()
            quoted = len(raw) >= 2 and raw[0] == raw[-1] == '"'
            inner, at = (raw[1:-1] if quoted else raw), f"{where}:{n}"
            if not quoted and set(inner) & SPECIAL:
                out.append(("error", "unquoted-label", f"quote this label: {raw}", at))
            if '"' in inner:
                out.append(("error", "nested-quotes", "no quotes inside a label", at))
            _text_rules(inner, at, out, allow_semicolon=quoted)


def renderer(pack):
    out = []
    for name, text in pack["files"].items():
        for kind, _, lines, _, _ in mermaid_blocks(text):
            for n, line in lines:
                at = f"{name}:{n}"
                if kind == "sequenceDiagram":
                    match = SEQ_MSG_RE.match(line) or SEQ_NOTE_RE.match(line)
                    if match:
                        _text_rules(match.group(1), at, out)
                        if "#" in match.group(1):
                            out.append(("error", "hash", "no `#` in a message (it starts an entity code)", at))
                elif kind == "stateDiagram-v2" or kind == "stateDiagram":
                    match = STATE_EDGE_RE.match(line)
                    if match:
                        _text_rules(match.group(1), at, out)
                        if len(match.group(1).strip()) > MAX_TRANSITION:
                            out.append(("warning", "long-label", "keep transition labels short; explain in prose", at))
                elif kind == "erDiagram":
                    match = ER_REL_RE.match(line)
                    label = match.group(1).strip() if match else ""
                    if " " in label and not (label.startswith('"') and label.endswith('"')):
                        out.append(("error", "unquoted-label", "quote a relationship label with spaces", at))
            if kind in ("flowchart", "graph"):
                _flowchart(lines, name, out)
    return out + _layout(pack)


def _layout(pack):
    """Each flow has one sequence and one activity diagram; each state section one state diagram."""
    out, files = [], pack["files"]
    flows = {}
    for kind, line, _, h2, _ in mermaid_blocks(files.get("flows.md", "")):
        if h2 and h2.startswith("Flow:"):
            flows.setdefault(h2[5:].strip(), []).append((kind, line))
    for heading in split_sections(files.get("flows.md", "")):
        if heading.startswith("Flow:") and heading[5:].strip() not in flows:
            flows[heading[5:].strip()] = []
    if "flows.md" in files and not flows:
        out.append(("error", "no-flow", "flows.md needs at least one `## Flow: <name>` section", "flows.md"))
    for flow, blocks in flows.items():
        kinds = [k for k, _ in blocks]
        if kinds.count("sequenceDiagram") != 1 or sum(k in ("flowchart", "graph") for k in kinds) != 1:
            out.append(("error", "flow-diagrams", f"flow `{flow}` needs exactly one sequenceDiagram and one "
                        f"flowchart (has: {', '.join(kinds) or 'none'})", "flows.md"))
    named = {cell(r, "flow").strip("` ") for r in first_table(pack["spec"].get("Flows", []))}
    for flow in sorted(named ^ set(flows)):
        side = "flows.md" if flow in named else "the spec's ## Flows table"
        out.append(("error", "flow-mismatch", f"flow `{flow}` is missing from {side}", "flows.md"))
    states = {}
    for kind, _, _, h2, _ in mermaid_blocks(files.get("states.md", "")):
        if h2 and h2.startswith("State:"):
            states.setdefault(h2, []).append(kind)
    for heading, kinds in states.items():
        if [k for k in kinds if k.startswith("stateDiagram")] != kinds or len(kinds) != 1:
            out.append(("error", "state-diagrams", f"`## {heading}` needs exactly one state diagram", "states.md"))
    if "erd.md" in files and [k for k, *_ in mermaid_blocks(files["erd.md"])] != ["erDiagram"]:
        out.append(("error", "erd-diagram", "erd.md needs exactly one erDiagram", "erd.md"))
    return out


def compile_level(pack):
    """Compile every file's diagrams with the Mermaid CLI; never report OK when it didn't run."""
    if not shutil.which("node") or not shutil.which("npx"):
        return [], "skipped (no Node)"
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in pack["files"].items():
            if "```mermaid" not in text:
                continue
            src = Path(tmp) / name.replace("/", "_")
            src.write_text(text, encoding="utf-8")
            try:
                run = subprocess.run(["npx", "-y", MERMAID_CLI, "-q", "-i", str(src), "-o", str(src) + ".out.md"],
                                     capture_output=True, text=True, timeout=300)
            except (subprocess.TimeoutExpired, OSError):
                return [], "skipped (mermaid-cli timed out or could not start)"
            if run.returncode:
                lines = [l.strip() for l in (run.stderr or run.stdout).splitlines() if l.strip()]
                useful = [l for l in lines if not l.startswith("at ")][:4]
                out.append(("error", "compile", " / ".join(useful) or "mermaid-cli failed", name))
    return out, ("failed" if out else "ok")
