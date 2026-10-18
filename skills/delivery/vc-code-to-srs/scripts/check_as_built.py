"""Check a vc as-built pack (`<feature folder>/as-built/` or its `.draft/`).

    python3 check_as_built.py check <pack-dir> [--root <tracking repo>] [--no-compile] [--json]

Levels are reported separately, never as one PASS: structure, citations,
ids, renderer, self-containment, compile, business correctness. The tracking
repo root is found from the pack's path when --root is not given. Exit code 1
when any level has an error. Python 3 stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from as_built_parse import (BACKTICK_RE, LABELS, find_root, first_table, label_of, load_pack,  # noqa: E402
                            parse_tables, path_citations, sid_citations, submodule_root)
import as_built_content  # noqa: E402
import as_built_mermaid  # noqa: E402

CODE_EXT = r"(?:cs|cshtml|razor|resx|ts|tsx|js|jsx|mjs|vue|swift|kt|kts|dart|java|py|go|php|rb|json|xml|ya?ml|" \
           r"strings|xcstrings|arb|properties|sql|gradle|plist|toml)"
BARE_RE = re.compile(rf"(?<![\w/.@+-])[\w-]+\.{CODE_EXT}(?::\d+(?:-\d+)?)?(?![\w/])")
SKIP_RE = re.compile(r"Skip\s*=|\.skip\(|\bx(?:it|describe|test)\(|\.todo\(|@Disabled|@Ignore|\[Ignore|"
                     r"pytest\.mark\.skip|t\.Skip\(|XCTSkip|skip:\s*true|\bskip\(")
TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec|androidTest|test_\w+)/|[._-](test|spec)s?\.|Tests?\.\w+$", re.I)


class Lines:
    """Cached line counts and contents of cited files."""

    def __init__(self, root):
        self.root, self.cache = Path(root), {}

    def get(self, path):
        if path not in self.cache:
            target = self.root / path
            self.cache[path] = target.read_text(encoding="utf-8", errors="replace").splitlines() \
                if target.is_file() else None
        return self.cache[path]


def _check_cite(path, start, end, at, lines, smroot, out):
    if "..." in path or "…" in path:
        out.append(("error", "ellipsis", f"write the full path, not `{path}`", at))
        return None
    if not path.startswith(smroot + "/"):
        out.append(("error", "outside-root", f"`{path}` is not under `{smroot}/<repo>/`", at))
        return None
    content = lines.get(path)
    if content is None:
        out.append(("error", "missing-file", f"`{path}` does not exist", at))
        return None
    for number in (start, end):
        if number is not None and not 1 <= number <= len(content):
            out.append(("error", "line-range", f"`{path}` has {len(content)} lines, not line {number}", at))
            return None
    if start and end and end < start:
        out.append(("error", "line-range", f"`{path}:{start}-{end}` runs backwards", at))
    return content


def _skipped(content, start, end):
    first = max(0, (start or 1) - 3)
    return any(SKIP_RE.search(line) for line in content[first:(end or start or 1)])


def citations(pack, root):
    if root is None:
        return None
    out, lines, smroot, sources = [], Lines(root), submodule_root(root), pack["sources"]
    for n, src in sources.items():
        _check_cite(src["path"], None, None, f"spec.md:{src['line']}", lines, smroot, out)
    for name, text in pack["files"].items():
        labelled = {}
        for rows in parse_tables(list(enumerate(text.splitlines(), 1))):
            for row in rows:
                if "label" in row:
                    labelled[row["_line"]] = label_of(row)
        for number, line in enumerate(text.splitlines(), 1):
            at = f"{name}:{number}"
            spans = BACKTICK_RE.findall(line)
            if line.lstrip().startswith("|"):
                spans.append(BACKTICK_RE.sub("", line))
            for span in spans:
                for match in BARE_RE.finditer(span):
                    out.append(("error", "bare-basename", f"cite the repo path, not `{match.group(0)}`", at))
            cites = list(dict.fromkeys(c for span in spans for c in path_citations(span)))
            if name == "spec.md" or name.startswith("use-cases/"):
                for sid, start, end in sid_citations(BACKTICK_RE.sub("", line)):
                    if sid in sources:
                        cites.append((sources[sid]["path"], start, end))
            for path, start, end in cites:
                content = _check_cite(path, start, end, at, lines, smroot, out)
                if content and labelled.get(number) == "✅" and TEST_PATH_RE.search(path) and start \
                        and _skipped(content, start, end):
                    out.append(("error", "skipped-test", f"`{path}:{start}` is a skipped test; label it 🟡 and "
                                "add a gap", at))
    return out


def run(pack_dir, root=None, compile_diagram=True):
    pack = load_pack(pack_dir)
    root = Path(root) if root else find_root(pack_dir)
    levels = {
        "structure": as_built_content.structure(pack),
        "citations": citations(pack, root),
        "ids": as_built_content.ids(pack),
        "renderer": as_built_mermaid.renderer(pack),
        "self-containment": as_built_content.self_containment(pack),
    }
    compiled, status = as_built_mermaid.compile_level(pack) if compile_diagram else ([], "skipped (--no-compile)")
    levels["compile"] = compiled
    counts = {LABELS[k]: 0 for k in LABELS}
    for section in (*as_built_content.REQUIRED_CLAIMS, *as_built_content.OPTIONAL_CLAIMS):
        for row in first_table(pack["spec"].get(section, [])):
            if label_of(row):
                counts[LABELS[label_of(row)]] += 1
    return {"levels": levels, "compile_status": status, "labels": counts, "root": str(root) if root else None}


def report(result):
    lines = []
    for level, findings in result["levels"].items():
        if findings is None:
            lines.append(f"{level}: skipped (no tracking repo root found; pass --root)")
            continue
        errors = sum(1 for f in findings if f[0] == "error")
        status = result["compile_status"] if level == "compile" and not findings else \
            ("ok" if not errors else f"{errors} error(s)")
        lines.append(f"{level}: {status}")
        for severity, name, message, where in findings:
            lines.append(f"  {severity.upper()} [{name}] {where}: {message}")
    lines.append("business correctness: not machine-checked")
    c = result["labels"]
    lines.append(f"labels: ✅ {c['asserted']} · 🔵 {c['corroborated']} · 🟡 {c['inferred']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("pack")
    c.add_argument("--root")
    c.add_argument("--no-compile", action="store_true")
    c.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.pack, args.root, not args.no_compile)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else report(result))
    failed = any(f[0] == "error" for fs in result["levels"].values() if fs for f in fs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
