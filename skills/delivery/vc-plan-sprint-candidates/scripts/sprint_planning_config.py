"""
Tracking-repo config and sprint timing, shared by the fetch and settle
scripts: read .vc/config.toml, and split sprints into past / current /
future around a date.
"""
import os
import tomllib
from datetime import date


def read_config(root):
    path = os.path.join(root, ".vc", "config.toml")
    if not os.path.isfile(path):
        return {}
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def read_tracker(root, override):
    return override or read_config(root).get("tracker")


def classify_sprints(sprints, today):
    past, current, future = [], None, []
    for sprint in sprints:
        try:
            start = date.fromisoformat(sprint["start_date"])
            finish = date.fromisoformat(sprint["finish_date"])
        except ValueError:
            continue
        if finish < today:
            past.append(sprint)
        elif start > today:
            future.append(sprint)
        else:
            current = sprint
    past.sort(key=lambda s: s["finish_date"], reverse=True)
    future.sort(key=lambda s: s["start_date"])
    return past, current, future
