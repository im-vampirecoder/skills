"""
The counting behind a candidate plan, kept deterministic so every run
gives the same numbers: backlog order, readiness flags, throughput scaled
by capacity (stories Done per sprint, never story points), and the
per-feature roll-up.
"""
import statistics

from sprint_planning_capacity import load_capacity

PRIORITY_RANK = {"must-have": 0, "should-have": 1, "nice-to-have": 2}
# Bugs interleave with stories: a critical bug sits with must-haves, and so on.
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
MIN_HISTORY = 3
CORE_SHARE = 0.8


def backlog_order(item):
    # Azure DevOps has a real backlog order (StackRank / BacklogPriority): use it.
    if item.get("backlog_rank") is not None:
        return (0, item["backlog_rank"], item["id"])
    rank = SEVERITY_RANK.get(item.get("severity"), 3) if item["kind"] == "bug" \
        else PRIORITY_RANK.get(item.get("priority"), 3)
    return (1, rank, item["kind"] != "bug", item["epic"] or "",
            item["feature_id"] or "", item["number"] or 0, item["id"])


def readiness_flags(story, stories_by_id, features):
    flags = []
    if story["kind"] == "bug":
        if not story["has_repro_steps"]:
            flags.append("no steps to reproduce")
        if not story["has_expected_actual"]:
            flags.append("expected/actual result missing")
        if not story["severity"]:
            flags.append("no severity")
        if not story["status_known"]:
            flags.append(f"unknown status '{story['status']}'")
        return flags
    if story["acceptance_criteria"] == 0:
        flags.append("no acceptance criteria")
    if not story["feature_id"]:
        flags.append("no parent feature")
    elif story["feature_id"] not in features:
        flags.append(f"parent feature {story['feature_id']} has no prd.md")
    for dep in story["dependencies"]:
        other = stories_by_id.get(dep)
        if other is None:
            flags.append(f"dependency {dep} not found")
        elif other["status"] != "done":
            flags.append(f"depends on {dep} ({other['status']}, not done)")
    breakdown = story["breakdown"]
    if breakdown and breakdown["open_questions"]:
        flags.append(f"{breakdown['open_questions']} open question(s) in {breakdown['spec']}")
    if story["blocking_clarifications"]:
        flags.append(f"feature questionnaire has ~{story['blocking_clarifications']} "
                     "Blocking item(s) - check clarification-questions.md")
    if not story["status_known"]:
        flags.append(f"unknown status '{story['status']}'")
    return flags


def full_time_hours(capacity):
    """Current members at full time, no time off: the contract's stand-in
    for a past sprint that has no capacity.md."""
    return round(sum((m.get("hours_per_day") or 0) * capacity["working_days"]
                     for m in capacity.get("members", []) if isinstance(m, dict)), 2)


def throughput(past, stories, capacity, history):
    rows = []
    target_hours = capacity["recomputed_hours"]
    for sprint in past[:history]:
        past_capacity = load_capacity(sprint["capacity_path"]) or {}
        hours = past_capacity.get("recomputed_hours")
        rows.append({
            "sprint": sprint["name"], "slug": sprint["slug"],
            "done": sum(1 for s in stories
                        if s["status"] == "done" and s["iteration_slug"] == sprint["slug"]),
            "available_hours": hours if hours is not None else full_time_hours(capacity),
            "hours_assumed": hours is None,
        })
    result = {"sprints": rows, "available": len(rows) >= MIN_HISTORY}
    if not result["available"]:
        result["reason"] = (f"only {len(rows)} past sprint(s); "
                            f"{MIN_HISTORY} needed - the team judges fit without a number")
        return result
    done = [row["done"] for row in rows]
    if statistics.median(done) == 0:
        result.update(available=False, reason="median of 0 stories Done per sprint - no basis "
                      "for a number; the team judges fit")
        return result
    hours = [row["available_hours"] for row in rows if row["available_hours"]]
    usual = statistics.median(hours) if hours else None
    scale = (target_hours / usual) if usual and target_hours else 1.0
    scaled = statistics.median(done) * scale
    result.update({
        "median_done": statistics.median(done), "min_done": min(done), "max_done": max(done),
        "usual_hours": usual, "scale": round(scale, 2), "scaled_throughput": round(scaled, 1),
        # Rounded, not floored: small teams (1-3 stories a sprint) would otherwise get 0.
        "core_limit": min(round(scaled), round(scaled * CORE_SHARE)), "full_limit": round(scaled),
    })
    return result


def feature_rollup(stories, features):
    rollup = {}
    for story in stories:
        if story["kind"] == "bug":
            continue  # bugs link to a feature at most; they do not finish one
        entry = rollup.setdefault(story["feature_id"], {
            "feature_id": story["feature_id"],
            "title": features.get(story["feature_id"], {}).get("title"),
            "epic": story["epic"], "states": {},
        })
        entry["states"][story["status"]] = entry["states"].get(story["status"], 0) + 1
    for feature_id, feature in features.items():
        # A feature with no stories yet is a gap: it needs story writing first.
        rollup.setdefault(feature_id, {"feature_id": feature_id, "title": feature["title"],
                                       "epic": feature["epic"], "states": {}})
    return list(rollup.values())
