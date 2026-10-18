"""Manage `artifacts/as-built-plan.json`, the resumable list of features to document from code.

    python3 as_built_plan.py init --from <candidates.json> [--root <repo>]   merge confirmed candidates, validate, write
    python3 as_built_plan.py validate [--root <repo>]
    python3 as_built_plan.py set-status <slug> <pending|deferred|partial|done> [--root <repo>]
    python3 as_built_plan.py next-batch [--size 3] [--root <repo>]           pending slugs, in plan order
    python3 as_built_plan.py status [--root <repo>]                          progress, drafts, stale packs
    python3 as_built_plan.py commits [--root <repo>]                         <repo>@<sha> for each cloned submodule
    python3 as_built_plan.py folder <slug> [--root <repo>]                   the feature folder for a slug

Run from the tracking repo root (or pass --root). Python 3 stdlib only.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from as_built_parse import read_frontmatter, submodule_root  # noqa: E402

PLAN = Path("artifacts") / "as-built-plan.json"
STATUSES = ("pending", "deferred", "partial", "done")
RESERVED = {"prd", "prd-history", "epics", "architecture", "decisions", "requirements-current", "bugs",
            "sprints", "reviews", "diagrams", "as-built-plan"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FLAGS = {"oauth", "payment", "webhook", "async", "multi-role", "state-machine", "throttle", "external-redirect"}


def feature_folder(root, slug):
    """Existing folder for the slug (unassigned or under an epic), else where a new one goes."""
    root = Path(root)
    for candidate in [root / "artifacts" / slug, *sorted((root / "artifacts").glob(f"epic-*/feature-{slug}"))]:
        if candidate.is_dir():
            return candidate
    return root / "artifacts" / slug


def load(root):
    path = Path(root) / PLAN
    if not path.is_file():
        return {"version": 1, "submodule_root": submodule_root(root), "shared_infrastructure": [], "features": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(root, plan):
    path = Path(root) / PLAN
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(root, plan):
    errors, smroot, seen = [], plan.get("submodule_root") or submodule_root(root), set()
    if plan.get("version") != 1:
        errors.append("version must be 1")

    def check_sources(where, sources):
        if not sources:
            errors.append(f"{where}: needs at least one source")
        for source in sources or []:
            if not source.startswith(smroot + "/") or not (Path(root) / source).exists():
                errors.append(f"{where}: source `{source}` is not an existing path under `{smroot}/`")

    for item in plan.get("shared_infrastructure", []):
        check_sources(f"shared infrastructure `{item.get('label', '?')}`", item.get("sources"))
    for feature in plan.get("features", []):
        slug = feature.get("slug", "")
        where = f"feature `{slug}`"
        if not SLUG_RE.match(slug) or len(slug) > 50:
            errors.append(f"{where}: slug must be kebab-case ASCII, at most 50 characters")
        if slug in RESERVED or slug.startswith(("epic-", "feature-")):
            errors.append(f"{where}: reserved slug")
        if slug in seen:
            errors.append(f"{where}: listed twice")
        seen.add(slug)
        if feature.get("feature_id") != f"FEATURE-{slug}":
            errors.append(f"{where}: feature_id must be FEATURE-{slug}")
        if feature.get("status") not in STATUSES:
            errors.append(f"{where}: status must be one of {', '.join(STATUSES)}")
        for flag in set(feature.get("complexity_flags", [])) - FLAGS:
            errors.append(f"{where}: unknown complexity flag `{flag}`")
        check_sources(where, feature.get("sources"))
        existing, folder = feature.get("existing_prd"), feature_folder(root, slug)
        if existing and not (Path(root) / existing).is_file():
            errors.append(f"{where}: existing_prd `{existing}` does not exist")
        if not existing and (folder / "prd.md").is_file():
            errors.append(f"{where}: `{folder.relative_to(root)}/prd.md` exists; set existing_prd or pick another slug")
    return errors


def commits(root):
    out, base = {}, Path(root) / submodule_root(root)
    for repo in sorted(p for p in base.glob("*") if (p / ".git").exists()):
        run = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True)
        out[repo.name] = run.stdout.strip() if run.returncode == 0 else "unknown"
    return out


def status(root, plan):
    rows, current = [], commits(root)
    for feature in plan.get("features", []):
        pack = feature_folder(root, feature["slug"]) / "as-built"
        meta, _ = read_frontmatter((pack / "spec.md").read_text(encoding="utf-8")) if (pack / "spec.md").is_file() \
            else ({}, 0)
        stale = []
        for entry in meta.get("sources", []) if isinstance(meta.get("sources"), list) else []:
            repo, _, sha = entry.partition("@")
            now = current.get(repo)
            if now and now != "unknown" and not (now.startswith(sha) or sha.startswith(now)):
                stale.append(f"{repo} {sha}->{now}")
        rows.append({"slug": feature["slug"], "status": feature["status"],
                     "pack": str(pack.relative_to(root)) if (pack / "spec.md").is_file() else None,
                     "draft": (pack / ".draft").is_dir(), "stale": stale})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").add_argument("--from", dest="source", required=True)
    sub.add_parser("validate")
    s = sub.add_parser("set-status")
    s.add_argument("slug")
    s.add_argument("status", choices=STATUSES)
    sub.add_parser("next-batch").add_argument("--size", type=int, default=3)
    sub.add_parser("status")
    sub.add_parser("commits")
    sub.add_parser("folder").add_argument("slug")
    args = parser.parse_args()
    root, plan = Path(args.root).resolve(), load(args.root)
    if args.cmd == "init":
        incoming = json.loads(Path(args.source).read_text(encoding="utf-8"))
        known = {f["slug"]: f for f in plan["features"]}
        for feature in incoming.get("features", []):
            kept = known.get(feature.get("slug"), {}).get("status")
            feature.setdefault("status", kept or "pending")
            known[feature.get("slug")] = {**known.get(feature.get("slug"), {}), **feature}
        plan["features"] = list(known.values())
        plan["shared_infrastructure"] = incoming.get("shared_infrastructure", plan["shared_infrastructure"])
    elif args.cmd == "set-status":
        matches = [f for f in plan["features"] if f["slug"] == args.slug]
        if not matches:
            print(f"no feature `{args.slug}` in {PLAN}")
            return 1
        matches[0]["status"] = args.status
    elif args.cmd == "next-batch":
        print(json.dumps([f["slug"] for f in plan["features"] if f["status"] == "pending"][:args.size]))
        return 0
    elif args.cmd == "status":
        print(json.dumps(status(root, plan), indent=2))
        return 0
    elif args.cmd == "commits":
        print(json.dumps([f"{repo}@{sha}" for repo, sha in commits(root).items()]))
        return 0
    elif args.cmd == "folder":
        print(feature_folder(root, args.slug).relative_to(root))
        return 0
    errors = validate(root, plan)
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        return 1
    if args.cmd in ("init", "set-status"):
        save(root, plan)
    print(f"{PLAN}: ok ({len(plan['features'])} features)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
