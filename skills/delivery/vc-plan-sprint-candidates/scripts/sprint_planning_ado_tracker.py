"""
Read sprint planning data from Azure DevOps (`tracker = "azure-devops"`),
returning the same tracker-neutral shapes as sprint_planning_local_tracker.

  - Sprints: the team's iterations (`az boards iteration team list`). The
    capacity file stays local: artifacts/sprints/<slug>/capacity.md.
  - Items: the story type and the bug type under `[ado].area_path`, found
    by WIQL, fields fetched in batches of 200 (`workitemsbatch`).
  - Status: each work item State is mapped through its type's state
    category: Proposed -> new (ready when it equals `ready_state` /
    `bug_ready_state`), InProgress/Resolved -> in-progress,
    Completed -> done, Removed -> removed.
  - An item whose iteration is not one of the team's sprints is in the
    backlog (iteration None).
  - When a local story/bug file carries the item's `ado_id`, its
    dependencies, breakdown, and clarification signals are merged in, and
    with an empty ready state its local `status: ready` decides readiness.

Uses `az boards` / `az devops invoke` only, never `az rest`.
"""
import html
import json
import os
import platform
import re
import subprocess
import tempfile

import sprint_planning_local_tracker as local_tracker
from sprint_planning_frontmatter import sprint_slug

IS_WINDOWS = platform.system() == "Windows"
CATEGORY_STATUS = {"Proposed": "new", "InProgress": "in-progress", "Resolved": "in-progress",
                   "Completed": "done", "Removed": "removed"}


def az(args):
    proc = subprocess.run(["az"] + args + ["-o", "json"], capture_output=True, text=True,
                          shell=IS_WINDOWS)
    if proc.returncode != 0:
        raise RuntimeError(f"az {' '.join(args[:3])} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def _org(cfg):
    return f"https://dev.azure.com/{cfg['organization']}"


def node_to_iteration_path(path):
    r"""'\Proj\Iteration\Sprint 1' (classification node) -> 'Proj\Sprint 1'."""
    parts = [p for p in (path or "").strip("\\").split("\\") if p]
    if len(parts) >= 2 and parts[1] == "Iteration":
        del parts[1]
    return "\\".join(parts)


def strip_html(raw):
    text = re.sub(r"<br\s*/?>|</(p|div|li|h\d)>", "\n", raw or "")
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def list_sprints(cfg, root):
    team = cfg.get("team") or f"{cfg['project']} Team"
    rows = az(["boards", "iteration", "team", "list", "--team", team,
               "--project", cfg["project"], "--org", _org(cfg)]) or []
    sprints = []
    for row in rows:
        attrs = row.get("attributes") or {}
        slug = sprint_slug(row["name"])
        sprints.append({
            "slug": slug, "name": row["name"],
            "iteration_path": node_to_iteration_path(row.get("path") or row["name"]),
            "start_date": (attrs.get("startDate") or "")[:10],
            "finish_date": (attrs.get("finishDate") or "")[:10],
            "capacity_path": os.path.join(root, "artifacts", "sprints", slug, "capacity.md"),
        })
    return sprints


def backlog_iteration(cfg):
    """The team's backlog iteration, as a work item IterationPath."""
    team = cfg.get("team") or f"{cfg['project']} Team"
    settings = az(["devops", "invoke", "--area", "work", "--resource", "teamsettings",
                   "--route-parameters", f"project={cfg['project']}", f"team={team}",
                   "--org", _org(cfg), "--api-version", "7.1", "--http-method", "GET"]) or {}
    node = settings.get("backlogIteration") or {}
    return node_to_iteration_path(node.get("path")) or node.get("name") or cfg["project"]


def type_states(cfg, work_item_type):
    result = az(["devops", "invoke", "--area", "wit", "--resource", "workItemTypeStates",
                 "--route-parameters", f"project={cfg['project']}", f"type={work_item_type}",
                 "--org", _org(cfg), "--api-version", "7.1", "--http-method", "GET"]) or {}
    return {s["name"]: s.get("category") for s in result.get("value", [])}


def _wiql_list(values):
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def query_ids(cfg, types, closed_states, sprint_paths):
    open_clause = f"[System.State] NOT IN ({_wiql_list(closed_states)})" if closed_states else "1 = 1"
    in_sprints = f" OR [System.IterationPath] IN ({_wiql_list(sprint_paths)})" if sprint_paths else ""
    wiql = ("SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project "
            f"AND [System.WorkItemType] IN ({_wiql_list(types)}) "
            f"AND [System.AreaPath] UNDER '{cfg['area_path'].replace(chr(39), chr(39) * 2)}' "
            f"AND ({open_clause}{in_sprints})")
    rows = az(["boards", "query", "--wiql", wiql, "--project", cfg["project"], "--org", _org(cfg)]) or []
    return [int(r.get("id") or r["fields"]["System.Id"]) for r in rows]


def fetch_batch(cfg, ids):
    """All fields for the ids, 200 per call (the batch API limit)."""
    items = []
    for start in range(0, len(ids), 200):
        body = {"ids": ids[start:start + 200], "errorPolicy": "omit"}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(body, handle)
            body_path = handle.name
        try:
            result = az(["devops", "invoke", "--area", "wit", "--resource", "workitemsbatch",
                         "--route-parameters", f"project={cfg['project']}",
                         "--org", _org(cfg), "--api-version", "7.1", "--http-method", "POST",
                         "--in-file", body_path]) or {}
        finally:
            os.unlink(body_path)
        items += [w for w in result.get("value", []) if w]
    return items


def _local_by_ado_id(root):
    found = {}
    for item in local_tracker.read_stories(root) + local_tracker.read_bugs(root):
        if item.get("ado_id"):
            found[int(item["ado_id"])] = item
    return found


def read_items(cfg, root, sprints, history_paths):
    """Open items plus everything in the listed (past) sprint paths."""
    story_type = cfg.get("story_work_item_type") or "User Story"
    bug_type = cfg.get("bug_work_item_type", "Bug")
    types = [t for t in (story_type, bug_type) if t]
    states = {t: type_states(cfg, t) for t in types}
    ready = {story_type: cfg.get("ready_state") or "", bug_type: cfg.get("bug_ready_state") or ""}
    closed = sorted({name for cats in states.values() for name, cat in cats.items()
                     if cat in ("Completed", "Removed")})
    sprint_by_path = {s["iteration_path"]: s["slug"] for s in sprints}
    local = _local_by_ado_id(root)

    items = []
    for work_item in fetch_batch(cfg, query_ids(cfg, types, closed, history_paths)):
        fields = work_item.get("fields", {})
        number = int(work_item.get("id") or fields.get("System.Id"))
        kind = "bug" if fields.get("System.WorkItemType") == bug_type else "story"
        wtype = bug_type if kind == "bug" else story_type
        state = fields.get("System.State") or ""
        status = CATEGORY_STATUS.get(states[wtype].get(state), "new")
        mapped = local.get(number, {})
        if status == "new" and (state == ready[wtype] and ready[wtype]):
            status = "ready"
        elif status == "new" and not ready[wtype] and mapped.get("status") == "ready":
            status = "ready"  # no ready state on the board: the local file decides
        iteration = fields.get("System.IterationPath")
        slug = sprint_by_path.get(iteration)
        criteria = fields.get("Microsoft.VSTS.Common.AcceptanceCriteria") or ""
        repro = strip_html(fields.get("Microsoft.VSTS.TCM.ReproSteps"))
        severity = re.sub(r"^\d+\s*-\s*", "", fields.get("Microsoft.VSTS.Common.Severity") or "")
        rank = fields.get("Microsoft.VSTS.Common.StackRank", fields.get("Microsoft.VSTS.Common.BacklogPriority"))
        items.append({
            "id": mapped.get("id") or f"ADO-{number}",
            "ado_id": number, "title": fields.get("System.Title") or "",
            "path": mapped.get("path"), "number": None,
            "feature_id": f"ADO-{fields['System.Parent']}" if fields.get("System.Parent") else None,
            "epic": None, "kind": kind, "state": state,
            "status": status, "status_known": state in states[wtype],
            "iteration": iteration if slug else None, "iteration_slug": slug,
            "backlog_rank": rank,
            "acceptance_criteria": len(re.findall(r"<li", criteria)) or
                                   len([l for l in strip_html(criteria).splitlines() if l.strip()]),
            "priority": None, "severity": severity.lower() or None,
            "has_repro_steps": bool(repro), "has_expected_actual":
                "expected" in repro.lower() and "actual" in repro.lower(),
            "type": mapped.get("type") or kind,
            "dependencies": mapped.get("dependencies", []),
            "breakdown": mapped.get("breakdown"),
            "blocking_clarifications": mapped.get("blocking_clarifications"),
        })
    return items


def read_features(cfg, root, items):
    """Parent work items (Features) of the items, keyed ADO-<id>, with
    local feature ids swapped in where a prd.md carries the ado_id."""
    local, _ = local_tracker.read_features(root)
    local_by_ado = {int(f["ado_id"]): f for f in local.values() if f.get("ado_id")}
    parent_ids = sorted({int(i["feature_id"][4:]) for i in items if i["feature_id"]})
    features = {}
    for work_item in fetch_batch(cfg, parent_ids) if parent_ids else []:
        number = int(work_item["id"])
        fields = work_item.get("fields", {})
        features[f"ADO-{number}"] = {
            "id": f"ADO-{number}", "slug": None, "title": fields.get("System.Title"),
            "epic": None, "ado_id": number,
            "path": local_by_ado.get(number, {}).get("path"),
        }
    return features
