"""
Load and check sprint capacity files against
references/capacity-file-contract.md.

  load_capacity(path, expected=None) -> dict with the parsed fields,
  `recomputed_hours`, and `problems` (stop) / `warnings` (continue) lists,
  or None when the file does not exist.
"""
import os
from datetime import date

from sprint_planning_frontmatter import read_markdown

REQUIRED = [
    "sprint", "iteration_path", "start_date", "finish_date", "working_days",
    "members", "available_hours", "published_by", "published_at",
]
MEMBER_REQUIRED = ["name", "hours_per_day", "time_off_hours"]


def _as_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def recompute_hours(working_days, members):
    """max(0, hours_per_day x working_days - time_off_hours), summed."""
    total = 0.0
    for member in members:
        per_day = _number(member.get("hours_per_day")) or 0
        off = _number(member.get("time_off_hours")) or 0
        total += max(0.0, per_day * working_days - off)
    return round(total, 2)


def load_capacity(path, expected=None):
    """expected: optional {"sprint": ..., "iteration_path": ...} to match."""
    if not os.path.isfile(path):
        return None
    data, notes = read_markdown(path)
    result = {"path": path, "notes": notes.strip(), "problems": [], "warnings": []}
    result.update(data)

    missing = [key for key in REQUIRED if data.get(key) in (None, "", [])]
    if missing:
        result["problems"].append(f"missing required field(s): {', '.join(missing)}")
        return result

    members = data["members"] if isinstance(data["members"], list) else []
    for index, member in enumerate(members):
        if not isinstance(member, dict):
            result["problems"].append(f"members[{index}] is not a name/hours entry")
            continue
        gaps = [key for key in MEMBER_REQUIRED if member.get(key) is None]
        if gaps:
            result["problems"].append(
                f"members[{index}] ({member.get('name', '?')}) missing: {', '.join(gaps)}")
        elif _number(member["hours_per_day"]) == 0:
            result["warnings"].append(
                f"{member['name']} has hours_per_day 0 - probably should be left out")

    start, finish = _as_date(data["start_date"]), _as_date(data["finish_date"])
    published = _as_date(data["published_at"])
    if not start or not finish:
        result["problems"].append("start_date/finish_date must be YYYY-MM-DD")
    working_days = _number(data["working_days"])
    if working_days is None:
        result["problems"].append("working_days must be a number")
    if result["problems"]:
        return result

    if expected:
        for key in ("sprint", "iteration_path"):
            if expected.get(key) and str(data[key]) != str(expected[key]):
                result["problems"].append(
                    f"{key} is '{data[key]}' but the sprint being planned is '{expected[key]}'")

    recomputed = recompute_hours(working_days, members)
    result["recomputed_hours"] = recomputed
    stated = _number(data["available_hours"])
    if stated is None or abs(stated - recomputed) > 0.01:
        result["warnings"].append(
            f"available_hours is {data['available_hours']} but the formula gives "
            f"{recomputed}; using {recomputed}")
    if published and published > start:
        result["warnings"].append(
            "capacity was published after the sprint started - likely negotiated in planning")
    result["start_date"], result["finish_date"] = start.isoformat(), finish.isoformat()
    return result
