"""Check named requirement IDs across a vc tracking repo.

    python3 check_requirement_ids.py --root <tracking-repo> [--json]

Errors: duplicate, malformed, wrong-feature, dangling, retired-but-cited (open
story), frozen-edited, bad supersedes target. Warnings: retired ID still cited
by a test case or mockup, BR not linked to any FR, glossary wording.
Exit code 1 when any error is found. Never writes a file.
"""

import argparse
import json
import re
import sys

from parse_requirement_ids import MAX_NAME, load_project, scan_malformed
from requirement_state import citations_by_id, index_definitions, read_baseline, read_glossary


GLOSSARY_CANDIDATE_MIN = 3
COMMON_WORDS = {"a", "an", "the", "with", "without", "for", "to", "of", "in", "on", "by", "and", "or",
                "per", "max", "min", "no", "not", "new", "old", "show", "create", "update", "delete",
                "send", "get", "set", "time", "limit", "after", "before", "when", "if"}


def _f(level, check, item_id, message, where=None):
    return {"level": level, "check": check, "id": item_id, "message": message, "where": where}


def _where(item):
    return f"{item['file']}:{item['line']}"


def glossary_words(root):
    """Term words, and alias -> term for aliases the glossary says to avoid."""
    terms = read_glossary(root)
    words = {w for term in terms for w in term.split("-")}
    return words, {alias: term for term, aliases in terms.items() for alias in aliases}


def check_definitions(project):
    findings, seen = [], {}
    for feature in project["features"]:
        for d in feature["definitions"]:
            if d["id"] in seen:
                findings.append(_f("error", "duplicate", d["id"], f"also defined at {seen[d['id']]}", _where(d)))
            seen.setdefault(d["id"], _where(d))
            if d["feature"] != feature["slug"]:
                findings.append(_f("error", "wrong-feature", d["id"],
                                   f"defined in feature '{feature['slug']}'; only its own PRD may define it", _where(d)))
            if len(d["name"]) > MAX_NAME:
                findings.append(_f("error", "malformed", d["id"], f"name longer than {MAX_NAME} chars", _where(d)))
            if d["type"] == "ERR" and not re.search(r"\bFR-", d["text"]):
                findings.append(_f("warning", "err-without-fr", d["id"], "error case names no FR in its For column", _where(d)))
    return findings


def check_citations(project, defs):
    findings, cited = [], citations_by_id(project)
    stories = {s["file"]: s for f in project["features"] for s in f["stories"]}
    for req_id, cites in cited.items():
        if req_id not in defs:
            for c in cites:
                findings.append(_f("error", "dangling", req_id, "cited but defined in no feature PRD", _where(c)))
            continue
        _, d = defs[req_id]
        if not d["retired"]:
            continue
        for c in cites:
            if c["kind"] == "story" and stories.get(c["file"], {}).get("status") not in ("done", "removed"):
                findings.append(_f("error", "retired-but-cited", req_id,
                                   f"retired ({d['replaced_by'] or 'no replacement'}) but an open story implements it", _where(c)))
            elif c["kind"] in ("test-case", "mockup"):
                findings.append(_f("warning", "retired-but-cited", req_id,
                                   f"retired; revise this {c['kind']} (replaced by {d['replaced_by'] or 'nothing'})", _where(c)))
    for feature in project["features"]:
        slugs = {f"FEATURE-{f['slug']}" for f in project["features"]}
        for target in feature["supersedes"]:
            if target not in defs and target not in slugs:
                findings.append(_f("error", "bad-supersedes", target, "supersedes target does not exist", feature["file"]))
    return findings


def check_links_and_frozen(project, defs, root):
    findings, cited, baseline = [], citations_by_id(project), read_baseline(root)
    for feature in project["features"]:
        for d in feature["definitions"]:
            if baseline.get(d["id"]) and baseline[d["id"]] != d["hash"]:
                findings.append(_f("error", "frozen-edited", d["id"],
                                   "text changed after the ID froze; restore it and add a new ID instead", _where(d)))
            if d["type"] == "BR" and not d["retired"]:
                cites_fr = re.search(r"\bFR-", d["text"])
                cited_by_fr = any(defs.get(c["id"]) for c in cited.get(d["id"], []) if c["kind"] == "prd")
                if not cites_fr and not cited_by_fr:
                    findings.append(_f("warning", "br-unlinked", d["id"], "business rule is linked to no FR", _where(d)))
    return findings


def check_glossary(project, root):
    findings, (terms, avoid) = [], glossary_words(root)
    if not terms:
        return findings
    for feature in project["features"]:
        for d in feature["definitions"]:
            for alias, term in avoid.items():
                if re.search(rf"(^|-){re.escape(alias)}(-|$)", d["name"]):
                    findings.append(_f("warning", "glossary-alias", d["id"], f"uses '{alias}'; glossary term is '{term}'", _where(d)))
    # Domain words reused across several IDs but never defined: glossary candidates.
    counts = {}
    for feature in project["features"]:
        for d in feature["definitions"]:
            for word in set(d["name"].split("-")) - terms - COMMON_WORDS:
                counts.setdefault(word, set()).add(d["id"])
    candidates = sorted(w for w, ids in counts.items() if len(ids) >= GLOSSARY_CANDIDATE_MIN)
    if candidates:
        findings.append(_f("warning", "glossary-missing", ", ".join(candidates),
                           f"used in {GLOSSARY_CANDIDATE_MIN}+ IDs but not in docs/glossary.md", "docs/glossary.md"))
    return findings


def run(root):
    project = load_project(root)
    defs = index_definitions(project)
    findings = check_definitions(project) + check_citations(project, defs)
    findings += check_links_and_frozen(project, defs, root) + check_glossary(project, root)
    findings += [_f("error", "malformed", m["token"], "not <FR|NFR|BR|ERR>-<feature-slug>.<name>", _where(m))
                 for m in scan_malformed(root)]
    markers = {f["slug"]: f["open_markers"] for f in project["features"] if f["open_markers"]}
    return findings, markers, sum(len(f["definitions"]) for f in project["features"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings, markers, total = run(args.root)
    errors = [f for f in findings if f["level"] == "error"]
    if args.json:
        print(json.dumps({"findings": findings, "open_markers": markers, "ids": total}, indent=2))
    else:
        for f in findings:
            print(f"{f['level'].upper():7} [{f['check']}] {f['id']} - {f['message']} ({f['where']})")
        for slug, count in markers.items():
            print(f"INFO    [needs-clarification] {slug} - {count} open marker(s)")
        print(f"{total} IDs checked: {len(errors)} error(s), {len(findings) - len(errors)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
