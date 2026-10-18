"""Check a vc user-flow map, or print its flow_hash.

    python3 check_user_flow.py check <ux/user-flow.md> [--prd <prd.md>] [--no-compile] [--json]
    python3 check_user_flow.py hash <ux/user-flow.md>

Levels are reported separately, never as one PASS: structure, renderer,
consistency, requirements (with --prd), compile, business correctness.
Exit code 1 when any level has an error. Python 3 stdlib only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_flow_parse import cell, load_map, mermaid_lines, node_ref  # noqa: E402
import user_flow_requirements  # noqa: E402

MERMAID_CLI = "@mermaid-js/mermaid-cli@10.9.1"
ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")
SPECIAL = set('()[]{}:;#&<>|/"\'')


def structure(flow):
    out = []
    nodes, edges = flow["nodes"], flow["edges"]
    for number, line in flow["unparsed"]:
        out.append(("error", "unparsed", f"not understood: `{line}` (one node or one edge per line)", number))
    if not nodes:
        return out + [("error", "no-diagram", "section 1 has no mermaid flowchart nodes", None)]
    exits = {n: [e for e in edges if e["from"] == n] for n in nodes}
    for node_id, node in nodes.items():
        outs = exits[node_id]
        if node["decision"]:
            if len(outs) < 2:
                out.append(("error", "decision-exits", f"decision {node_id} needs 2+ exits", node["line"]))
        if len(outs) >= 2 and any(not (e["label"] or "").strip('" ') for e in outs):
            out.append(("error", "unlabelled-branch", f"{node_id} branches with an unlabelled exit", node["line"]))
        terminal = "terminal" in node["classes"]
        if not outs and not terminal:
            out.append(("error", "dead-end", f"{node_id} has no way out and isn't marked terminal", node["line"]))
        if "temporary" in node["classes"] and not any(e["to"] != node_id for e in outs):
            out.append(("error", "temporary-trap", f"temporary state {node_id} has no way out", node["line"]))
        if node["screen"] is not None and not node["classes"] & {"happy", "error", "edge"}:
            out.append(("warning", "no-case-class", f"{node_id} has no happy/error/edge class", node["line"]))
    for e in edges:
        for end in (e["from"], e["to"]):
            if end not in nodes:
                out.append(("error", "undefined-node", f"edge uses {end}, which isn't defined on its own line", e["line"]))
    entries = [n for n, node in nodes.items() if "entry" in node["classes"]] or [next(iter(nodes))]
    seen, todo = set(entries), list(entries)
    while todo:
        for e in exits.get(todo.pop(), []):
            if e["to"] not in seen:
                seen.add(e["to"])
                todo.append(e["to"])
    for node_id in nodes:
        if node_id not in seen:
            out.append(("error", "unreachable", f"{node_id} can't be reached from an entry", nodes[node_id]["line"]))
    return out


def renderer(flow):
    out = []
    labelled = [(n["raw"], n["line"], n["id"]) for n in flow["nodes"].values()]
    labelled += [(e["label"], e["line"], f"{e['from']}->{e['to']}") for e in flow["edges"] if e["label"]]
    for raw, line, where in labelled:
        quoted = len(raw) >= 2 and raw[0] == raw[-1] == '"'
        inner = raw[1:-1] if quoted else raw
        if not quoted and set(inner) & SPECIAL:
            out.append(("error", "unquoted-label", f"{where}: quote this label", line))
        if '"' in inner:
            out.append(("error", "nested-quotes", f"{where}: no quotes inside a label", line))
        if ENTITY_RE.search(inner):
            out.append(("error", "html-entity", f"{where}: write the character, not an HTML entity", line))
        if "\\n" in inner:
            out.append(("error", "newline-escape", f"{where}: use <br/> for a line break, not \\n", line))
        if re.search(r"<br\s*>", inner):
            out.append(("warning", "br-tag", f"{where}: write <br/>", line))
    return out


def consistency(flow):
    out = []
    diagram = {n["screen"]: n for n in flow["nodes"].values() if n["screen"] is not None}
    table = {}
    for row in flow["screens"]:
        try:
            table[int(cell(row, "#").strip("[] "))] = row
        except ValueError:
            out.append(("error", "screen-number", f"Screens row needs a number in #: {row}", row["_line"]))
    for n in sorted(set(diagram) - set(table)):
        out.append(("error", "screen-missing-row", f"[{n}] is in the diagram but not the Screens table", diagram[n]["line"]))
    for n in sorted(set(table) - set(diagram)):
        out.append(("error", "screen-missing-node", f"[{n}] is in the Screens table but not the diagram", table[n]["_line"]))
    flows = {cell(r, "flow").strip("` ") for r in flow["flows"]}
    for n, row in sorted(table.items()):
        named = {f.strip("` ") for f in cell(row, "flow").split(",") if f.strip("`- —")}
        if not named:
            out.append(("error", "screen-no-flow", f"[{n}] belongs to no flow", row["_line"]))
        for f in sorted(named - flows):
            out.append(("error", "unknown-flow", f"[{n}] names flow `{f}`, which isn't in the Flows table", row["_line"]))
    edges = Counter((e["from"], e["to"]) for e in flow["edges"])
    rows = Counter((node_ref(cell(r, "from")), node_ref(cell(r, "to"))) for r in flow["transitions"])
    for (a, b), count in sorted((edges - rows).items()):
        out.append(("error", "edge-missing-row", f"edge {a} -> {b} has no Transitions row" + (f" (x{count})" if count > 1 else ""), None))
    for (a, b), count in sorted((rows - edges).items()):
        out.append(("error", "row-missing-edge", f"Transitions row {a} -> {b} has no diagram edge", None))
    return out


def compile_level(flow):
    if not shutil.which("node") or not shutil.which("npx"):
        return [], "skipped (no Node)"
    source = "\n".join(line for _, line in mermaid_lines(flow["sections"].get(1, ("", []))[1]))
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "flow.mmd", Path(tmp) / "flow.svg"
        src.write_text(source, encoding="utf-8")
        try:
            run = subprocess.run(["npx", "-y", MERMAID_CLI, "-q", "-i", str(src), "-o", str(dst)],
                                 capture_output=True, text=True, timeout=300)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return [], "skipped (mermaid-cli timed out or could not start)"
    if run.returncode:
        # Keep the parser's message (e.g. "Parse error on line 3: ... Expecting ..."), not the stack.
        lines = [l.strip() for l in (run.stderr or run.stdout).splitlines() if l.strip()]
        useful = [l for l in lines if not l.startswith("at ")][:4]
        return [("error", "compile", " / ".join(useful) or "mermaid-cli failed", None)], "failed"
    return [], "ok"


def run(path, prd=None, compile_diagram=True):
    flow = load_map(path)
    levels = {"structure": structure(flow), "renderer": renderer(flow), "consistency": consistency(flow)}
    levels["requirements"] = user_flow_requirements.check(flow, prd) if prd else None
    compiled, status = compile_level(flow) if compile_diagram else ([], "skipped (--no-compile)")
    levels["compile"] = compiled
    meta = flow["meta"]
    approval = meta.get("status", "draft")
    if approval == "approved" and meta.get("flow_hash") != flow["hash"]:
        approval = f"approved, but stale: flow_hash {meta.get('flow_hash')} != {flow['hash']}"
    return {"levels": levels, "compile_status": status, "hash": flow["hash"], "approval": approval}


def report(result):
    lines = []
    for level, findings in result["levels"].items():
        if findings is None:
            lines.append(f"{level}: skipped (no --prd)")
            continue
        errors = sum(1 for f in findings if f[0] == "error")
        status = result["compile_status"] if level == "compile" and not findings else ("ok" if not errors else f"{errors} error(s)")
        lines.append(f"{level}: {status}")
        for lvl, name, msg, line in findings:
            lines.append(f"  {lvl.upper()} [{name}]" + (f" line {line}" if line else "") + f": {msg}")
    lines.append("business correctness: not machine-checked")
    lines.append(f"flow_hash: {result['hash']} · status: {result['approval']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("path")
    c.add_argument("--prd")
    c.add_argument("--no-compile", action="store_true")
    c.add_argument("--json", action="store_true")
    sub.add_parser("hash").add_argument("path")
    args = parser.parse_args()
    if args.cmd == "hash":
        print(load_map(args.path)["hash"])
        return 0
    result = run(args.path, args.prd, not args.no_compile)
    print(json.dumps(result, indent=2) if args.json else report(result))
    failed = any(f[0] == "error" for fs in result["levels"].values() if fs for f in fs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
