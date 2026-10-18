"""
Readiness signals read from files other skills write beside a local
story: the vc-tasks-breakdown output (task progress, open questions)
and the vc-prd-clarify questionnaire (Blocking items).
"""
import glob
import os
import re


def section(body, heading):
    """Text under '## <heading>' up to the next '## ' heading."""
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return match.group(1) if match else ""


def breakdown(story_path, number, root):
    """Task progress and open questions from vc-tasks-breakdown output in
    the feature's tasks/ folder. None when the story has no breakdown."""
    tasks_dir = os.path.join(os.path.dirname(story_path), "tasks")
    spec = os.path.join(tasks_dir, f"story-{number}-spec.md")
    if number is None or not os.path.isfile(spec):
        return None
    statuses = []
    for task in glob.glob(os.path.join(tasks_dir, f"story-{number}-task-*.md")):
        with open(task, encoding="utf-8") as handle:
            found = re.search(r"^\s*-?\s*Status:\s*(\w+)", handle.read(), re.M)
        statuses.append(found.group(1).lower() if found else "unknown")
    with open(spec, encoding="utf-8") as handle:
        questions = section(handle.read(), "Open Questions")
    open_questions = [q for q in re.findall(r"^\s*-\s+(.+)$", questions, re.M)
                      if q.strip().lower() not in ("none", "n/a", "...")]
    active = [st for st in statuses if st != "skipped"]
    return {
        "spec": os.path.relpath(spec, root),
        "tasks": len(active),
        "tasks_done": sum(1 for st in active if st == "done"),
        "open_questions": len(open_questions),
    }


def blocking_clarifications(story_path):
    """Lines marked Blocking in the feature's saved PRD/BA questionnaire.
    A rough count (the file may repeat the legend); the model reads the file."""
    path = os.path.join(os.path.dirname(story_path), "clarification-questions.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    return sum(1 for line in lines if "\U0001F534" in line and "|" not in line)
