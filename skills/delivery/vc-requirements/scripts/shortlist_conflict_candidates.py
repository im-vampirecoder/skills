"""Shortlist requirement pairs across features that might conflict.

    python3 shortlist_conflict_candidates.py --root <tracking-repo> [--feature <slug>] [--max-pairs 50]

Pairs live requirements from different features that share a signal: a
glossary term (aliases count as the term), the same state-transition entity,
the same Touchpoints entry, the same NFR category, or the same ID name.
Skips pairs already settled in a `## Decisions` entry naming both IDs.
Delivered-vs-delivered pairs go to `bug_candidates`, never judged. An
unscoped run over the threshold returns per-feature counts with
`needs_scope: true` instead of pairs. Prints JSON; never writes a file.
"""

import argparse
import json
import re
import sys
from itertools import combinations
from pathlib import Path

from parse_requirement_ids import ID_RE, load_project
from requirement_state import kebab, pending_supersessions, read_glossary, state_of

NFR_CATEGORIES = {
    "response-time": r"\b(\d+(\.\d+)?\s*(ms|s|sec|seconds?|minutes?)|within|wait|latency|response)\b",
    "availability": r"\b(uptime|available|availability|downtime|\d+(\.\d+)?\s*%)\b",
    "retention": r"\b(kept|keep|retain(ed)?|retention|delete[ds]? after|archive[ds]?|years?)\b",
    "access": r"\b(visible to|only .* can|access|permission|role)\b",
}
COMMON_TERM_SHARE = 0.5  # a term in more than half of all requirements is no signal
COMMON_TERM_MIN_REQS = 30


def section_lines(text, heading):
    inside, out = False, []
    for line in text.splitlines():
        if line.startswith("#"):
            inside = line.lstrip("#").strip().lower() == heading
            continue
        if inside and line.strip():
            out.append(line)
    return out


def feature_context(feature):
    text = Path(feature["file"]).read_text(encoding="utf-8")
    touch = {kebab(l.lstrip("- ").split("(")[0]) for l in section_lines(text, "touchpoints") if l.lstrip().startswith("-")}
    entities = set()
    for line in section_lines(text, "state transitions"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] and cells[0].lower() != "entity" and not set(cells[0]) <= set("-: "):
            entities.add(kebab(cells[0]))
    dismissed = [set(ID_RE.findall(l)) for l in section_lines(text, "decisions")]
    return touch, entities, [{f"{t}-{f}.{n}" for t, f, n in ids} for ids in dismissed if len(ids) >= 2]


def term_hits(d, glossary):
    words = " " + kebab(d["name"] + " " + d["text"]).replace("-", " ") + " "
    hits = set()
    for term, aliases in glossary.items():
        if any(f" {w.replace('-', ' ')} " in words for w in [term, *aliases]):
            hits.add(term)
    return hits


def signals_for(project, root):
    glossary, pending, out = read_glossary(root), pending_supersessions(project), []
    for feature in project["features"]:
        touch, entities, dismissed = feature_context(feature)
        for d in feature["definitions"]:
            if state_of(feature, d, pending).startswith(("retired", "superseded")):
                continue
            nfr = {c for c, rx in NFR_CATEGORIES.items() if d["type"] == "NFR" and re.search(rx, d["text"], re.I)}
            out.append({"def": d, "feature": feature, "terms": term_hits(d, glossary), "nfr": nfr,
                        "touch": touch, "entities": entities, "dismissed": dismissed})
    total = len(out)
    if total >= COMMON_TERM_MIN_REQS:
        counts = {}
        for r in out:
            for t in r["terms"]:
                counts[t] = counts.get(t, 0) + 1
        common = {t for t, n in counts.items() if n > total * COMMON_TERM_SHARE}
        for r in out:
            r["terms"] -= common
    return out


def shared(a, b):
    found = [f"term:{t}" for t in sorted(a["terms"] & b["terms"])]
    found += [f"nfr:{c}" for c in sorted(a["nfr"] & b["nfr"])]
    found += [f"touchpoint:{t}" for t in sorted(a["touch"] & b["touch"])]
    found += [f"entity:{e}" for e in sorted(a["entities"] & b["entities"])]
    if a["def"]["name"] == b["def"]["name"]:
        found.append("same-name")
    return found


def shortlist(root, feature=None, max_pairs=50):
    project = load_project(root, drafts=True)  # see an in-progress vc-prd draft
    reqs = signals_for(project, root)
    pairs, bugs = [], []
    for a, b in combinations(reqs, 2):
        fa, fb = a["feature"], b["feature"]
        if fa["slug"] == fb["slug"] or (feature and feature not in (fa["slug"], fb["slug"])):
            continue
        ids = {a["def"]["id"], b["def"]["id"]}
        if any(ids <= d for d in a["dismissed"] + b["dismissed"]):
            continue
        signal = shared(a, b)
        if not signal:
            continue
        pair = {"a": a["def"]["id"], "b": b["def"]["id"], "a_feature": fa["slug"], "b_feature": fb["slug"],
                "a_status": fa["status"], "b_status": fb["status"], "signals": signal,
                "a_text": a["def"]["text"], "b_text": b["def"]["text"]}
        (bugs if fa["status"] == fb["status"] == "delivered" else pairs).append(pair)
    pairs.sort(key=lambda p: (p["a_status"] == "delivered") + (p["b_status"] == "delivered"))
    result = {"scope": feature, "pairs": pairs, "bug_candidates": bugs, "needs_scope": False}
    if feature is None and len(pairs) > max_pairs:
        per = {}
        for p in pairs:
            for slug in (p["a_feature"], p["b_feature"]):
                per[slug] = per.get(slug, 0) + 1
        result.update(pairs=[], needs_scope=True, pair_count=len(pairs), per_feature=per)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--feature", help="pair this feature against all others")
    parser.add_argument("--max-pairs", type=int, default=50)
    args = parser.parse_args()
    print(json.dumps(shortlist(args.root, args.feature, args.max_pairs), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
