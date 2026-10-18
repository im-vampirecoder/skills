#!/usr/bin/env python3
"""
After publishing a sprint release note, keep the parent "Sprint Releases" page
tidy, newest sprint first:

  1. Rewrite the parent page as a table: sprint name | link to its child page.
  2. Rewrite the folder's .order file so the wiki sidebar lists children
     descending (Sprint 30, 29, ... 1). Azure DevOps wikis order pages by .order,
     not alphabetically, and publish_wiki_page.py does not touch it.

Dry run by default -- prints the table, the new .order and the commit message.
Re-run with --push once the user has confirmed the commit message (global rule:
never commit without showing the message first).

Nothing project-specific is hardcoded. Defaults come from the repo's
.vc/config.toml and the skill's saved config (see config.py):
  --org          https://dev.azure.com/<[ado].organization>
  --project      [ado].project
  --wiki         <project>.wiki
  --parent-path  the saved wiki_path_template minus its last segment, e.g.
                 "/<root>/Product/Sprint Releases/Release Note - {sprint_name}"
                 -> "/<root>/Product/Sprint Releases"
Any of them can be overridden on the command line.

Usage (PowerShell on Windows, not Git Bash -- leading "/" gets mangled):
  python update_wiki_index.py [--org ...] [--project ...] [--wiki ...] [--parent-path "/<root>/Product/Sprint Releases"] [--push]

The wiki repo is cloned bare, because a normal checkout fails on Windows (the
wiki contains file names Windows can't create). The .order commit is built with
git plumbing against a temporary index; no working tree is involved.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as saved_config  # noqa: E402

MESSAGE = "Order sprint release notes newest first"  # single line, no co-author line


def run(cmd, cwd=None, env=None, input=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, env=env, input=input, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit(f"{' '.join(cmd)}\n{r.stderr}")
    return r.stdout


def vc_ado_section():
    """[ado] table of the nearest .vc/config.toml at or above the cwd ({} if none)."""
    for d in [Path.cwd(), *Path.cwd().parents]:
        f = d / ".vc" / "config.toml"
        if f.exists():
            with open(f, "rb") as fh:
                return tomllib.load(fh).get("ado", {})
    return {}


def folder_of(parent_path):
    # wiki file names replace spaces with "-": "/A/Sprint Releases" -> "A/Sprint-Releases"
    return "/".join(seg.replace(" ", "-") for seg in parent_path.strip("/").split("/"))


def read_children(repo, branch, folder):
    names = run(["git", "ls-tree", "--name-only", f"origin/{branch}", folder + "/"], cwd=repo).splitlines()
    stems = []
    for n in names:
        leaf = n.rsplit("/", 1)[-1]
        m = re.search(r"(\d+)\.md$", leaf)
        if m:
            stems.append((int(m.group(1)), leaf[:-3]))
    stems.sort(reverse=True)
    return stems


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--org", help="default: https://dev.azure.com/<[ado].organization> from .vc/config.toml")
    p.add_argument("--project", help="default: [ado].project from .vc/config.toml")
    p.add_argument("--wiki", help="default: <project>.wiki")
    p.add_argument("--parent-path", help="default: saved wiki_path_template minus its last segment")
    p.add_argument("--push", action="store_true", help="apply the changes (default: dry run)")
    args = p.parse_args()

    ado = vc_ado_section()
    if not args.org and ado.get("organization"):
        args.org = "https://dev.azure.com/" + ado["organization"]
    args.project = args.project or ado.get("project")
    if not (args.org and args.project):
        sys.exit("No org/project: pass --org/--project, or run /vc:setup to create .vc/config.toml")
    args.wiki = args.wiki or f"{args.project}.wiki"
    if not args.parent_path:
        saved = saved_config.load().get(saved_config.key(args.org, args.project), {})
        template = saved.get("wiki_path_template")
        if not template:
            sys.exit("No saved wiki_path_template for this project; pass --parent-path or run the skill's Step 5 first")
        args.parent_path = template.rsplit("/", 1)[0]

    org_name = args.org.rstrip("/").rsplit("/", 1)[-1]
    url = f"https://{org_name}@dev.azure.com/{org_name}/{args.project}/_git/{args.wiki}"
    folder = folder_of(args.parent_path)
    tmp = tempfile.mkdtemp(prefix="wikiidx-")
    repo = os.path.join(tmp, "wiki.git")
    try:
        run(["git", "clone", "--bare", "--single-branch", url, repo])
        branch = run(["git", "symbolic-ref", "--short", "HEAD"], cwd=repo).strip()  # the wiki's default branch
        run(["git", "config", "remote.origin.fetch", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"], cwd=repo)
        run(["git", "fetch", "origin"], cwd=repo)

        children = read_children(repo, branch, folder)
        if not children:
            sys.exit(f"No child pages found under {folder}")

        rows = ["| Sprint | Release note |", "|---|---|"]
        for num, stem in children:
            title = stem.replace("%2D", "~").replace("-", " ").replace("~", "-")
            rows.append(f"| Sprint {num} | [{title}](/{folder}/{stem}) |")
        table = "\n".join(rows) + "\n"
        order = "\n".join(stem for _, stem in children) + "\n"

        parent_md = folder + ".md"
        existing = run(["git", "show", f"origin/{branch}:{parent_md}"], cwd=repo, check=False).strip()
        if existing and not existing.startswith("| Sprint |"):
            sys.exit(f"{parent_md} has content that isn't our table; refusing to overwrite. Reconcile by hand.")

        print(f"Wiki: {args.org} / {args.project} / {args.wiki} (branch {branch}); parent page: {args.parent_path}\n")
        print("=== Parent page table ===\n" + table)
        print("=== .order ===\n" + order)
        print(f"=== Commit message ===\n{MESSAGE}")
        if not args.push:
            print("\n(dry run -- re-run with --push after the user confirms the message)")
            return

        # 1. table page (az creates its own wiki commit)
        tf = os.path.join(tmp, "index.md")
        Path(tf).write_text(table, encoding="utf-8", newline="\n")
        run([sys.executable, str(HERE / "publish_wiki_page.py"), "--org", args.org, "--project", args.project,
             "--wiki", args.wiki, "--path", args.parent_path, "--file-path", tf])

        # 2. .order commit via plumbing on top of the latest wiki branch
        run(["git", "fetch", "origin"], cwd=repo)
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "idx"))
        run(["git", "read-tree", f"origin/{branch}"], cwd=repo, env=env)
        blob = run(["git", "hash-object", "-w", "--stdin", "--no-filters"], cwd=repo, input=order).strip()
        run(["git", "update-index", "--cacheinfo", f"100644,{blob},{folder}/.order"], cwd=repo, env=env)
        tree = run(["git", "write-tree"], cwd=repo, env=env).strip()
        commit = run(["git", "commit-tree", tree, "-p", f"origin/{branch}", "-m", MESSAGE], cwd=repo, env=env).strip()
        print(run(["git", "push", "origin", f"{commit}:refs/heads/{branch}"], cwd=repo))
        print("Done.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
