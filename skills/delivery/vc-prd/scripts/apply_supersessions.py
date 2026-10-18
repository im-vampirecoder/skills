"""Apply a delivered feature's supersessions to the PRDs it replaces.

    python3 apply_supersessions.py --root <tracking-repo> --feature <slug> [--date YYYY-MM-DD] [--dry-run]

Reads the feature PRD's frontmatter `supersedes: [...]` and its
`## Changes to delivered features` bullets (`- <old-id>: replaced by <new-id> ...`).
For each target requirement ID, adds `> Superseded by <new-id or FEATURE-slug> on <date>`
directly under the requirement in the old PRD, and adds the ID to that PRD's
frontmatter `superseded: [...]`. A `FEATURE-<slug>` target supersedes every live
ID in that PRD and gets one banner under its title. Idempotent: an existing
banner is never duplicated. Run only by `/vc:prd deliver` after the PO confirms.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ID = rf"(?:FR|NFR|BR|ERR)-{SLUG}\.{SLUG}"
DEF_RE = re.compile(rf"^\s*(?:-\s+\*\*({ID}):?\*\*|\|\s*({ID})\s*\|)")
CHANGE_RE = re.compile(rf"^\s*-\s+\*?\*?({ID}|FEATURE-{SLUG})\*?\*?:.*?replaced by\s+({ID})", re.I)


def find_prd(root, slug):
    artifacts = Path(root) / "artifacts"
    for path in [artifacts / slug / "prd.md", *artifacts.glob(f"epic-*/feature-{slug}/prd.md")]:
        if path.exists():
            return path
    raise SystemExit(f"no PRD for feature '{slug}'")


def frontmatter_list(text, key):
    match = re.search(rf"^{key}:\s*\[(.*?)\]\s*$", text, re.MULTILINE)
    return [v.strip().strip("'\"") for v in match.group(1).split(",") if v.strip()] if match else []


def set_frontmatter_list(text, key, values):
    line = f"{key}: [{', '.join(values)}]"
    if re.search(rf"^{key}:.*$", text, re.MULTILINE):
        return re.sub(rf"^{key}:.*$", line, text, count=1, flags=re.MULTILINE)
    end = text.find("\n---", 3)
    return text[:end] + "\n" + line + text[end:]


def apply_to_prd(path, targets, banner_date, dry_run):
    """targets: {old-id or FEATURE-slug: replacing id}. Returns the IDs marked."""
    lines = path.read_text(encoding="utf-8").splitlines()
    whole = next((v for k, v in targets.items() if k.startswith("FEATURE-")), None)
    out, marked, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if whole and line.startswith("# ") and not any("Superseded by" in l for l in lines[i + 1:i + 3]):
            out.append(f"> Superseded by {whole} on {banner_date}")
        match = DEF_RE.match(line)
        req_id = match and (match.group(1) or match.group(2))
        if req_id and (req_id in targets or whole):
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith(">"):
                out.append(lines[j])
                j += 1
            if not any("Superseded by" in l for l in lines[i + 1:j]):
                out.append(f"> Superseded by {targets.get(req_id, whole)} on {banner_date}")
            marked.append(req_id)
            i = j
            continue
        i += 1
    text = "\n".join(out) + "\n"
    text = set_frontmatter_list(text, "superseded", sorted(set(frontmatter_list(text, "superseded")) | set(marked)))
    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return marked


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--feature", required=True, help="the delivered, superseding feature's slug")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    prd = find_prd(args.root, args.feature)
    text = prd.read_text(encoding="utf-8")
    supersedes = frontmatter_list(text, "supersedes")
    if not supersedes:
        print("nothing to apply: no supersedes in frontmatter")
        return 0
    replaced = {m.group(1): m.group(2) for m in map(CHANGE_RE.match, text.splitlines()) if m}
    by_feature = {}
    for target in supersedes:
        owner = target[len("FEATURE-"):] if target.startswith("FEATURE-") else re.match(rf"\w+-({SLUG})\.", target).group(1)
        by_feature.setdefault(owner, {})[target] = replaced.get(target, f"FEATURE-{args.feature}")
    for owner, targets in sorted(by_feature.items()):
        marked = apply_to_prd(find_prd(args.root, owner), targets, args.date, args.dry_run)
        print(f"{'would mark' if args.dry_run else 'marked'} {owner}: {', '.join(marked) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
