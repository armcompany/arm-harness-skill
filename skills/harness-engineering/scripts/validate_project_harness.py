#!/usr/bin/env python3
"""Validate the structural and cross-file invariants of a project harness."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED = [
    "AGENTS.md",
    ".harness/mission.md",
    ".harness/plan.md",
    ".harness/state.json",
    ".harness/journal.md",
    ".harness/errors.json",
    ".harness/decisions.md",
    ".harness/architecture.md",
    ".harness/context.md",
]
STATUSES = {"PENDING", "READY", "RUNNING", "BLOCKED", "DONE", "FAILED"}
TASK_HEADING = re.compile(r"^#{2,}\s+([A-Za-z][A-Za-z0-9]*-\d+[A-Za-z0-9-]*)\b", re.MULTILINE)
STATUS_LINE = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Status(?:\*\*)?\s*:\s*`?([A-Z]+)`?", re.MULTILINE | re.IGNORECASE)


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON in {path}: {exc}")
        return {}


def parse_plan(text: str, errors: list[str]) -> dict[str, str]:
    table_tasks: dict[str, str] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*-\d+[A-Za-z0-9-]*", cells[0]):
            continue
        status = cells[-1].upper()
        if cells[0] in table_tasks:
            errors.append(f"Duplicate task ID in plan: {cells[0]}")
        else:
            table_tasks[cells[0]] = status
            if status not in STATUSES:
                errors.append(f"Task {cells[0]} has invalid status: {status}")
    if table_tasks:
        return table_tasks

    matches = list(TASK_HEADING.finditer(text))
    tasks: dict[str, str] = {}
    for index, match in enumerate(matches):
        task_id = match.group(1)
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        status_match = STATUS_LINE.search(text, match.end(), block_end)
        if task_id in tasks:
            errors.append(f"Duplicate task ID in plan: {task_id}")
        elif not status_match:
            errors.append(f"Task {task_id} has no Status field")
        else:
            status = status_match.group(1).upper()
            tasks[task_id] = status
            if status not in STATUSES:
                errors.append(f"Task {task_id} has invalid status: {status}")
    if not tasks:
        errors.append("No task headings with IDs were found in .harness/plan.md")
    return tasks


def as_string_list(state: dict[str, Any], key: str, errors: list[str]) -> list[str]:
    value = state.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"state.json field {key} must be an array of task IDs")
        return []
    return value


def validate(root: Path, simulate: str | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for relative in REQUIRED:
        path = root / relative
        if not path.is_file():
            errors.append(f"Missing required file: {relative}")
    if errors:
        return errors

    state = load_json(root / ".harness/state.json", errors)
    error_log = load_json(root / ".harness/errors.json", errors)
    if not isinstance(state, dict):
        errors.append("state.json root must be an object")
        state = {}
    if simulate == "current-task-mismatch":
        state["currentTask"] = "SIM-999"

    tasks = parse_plan((root / ".harness/plan.md").read_text(encoding="utf-8"), errors)
    running = [task_id for task_id, status in tasks.items() if status == "RUNNING"]
    if len(running) > 1:
        errors.append(f"Plan has more than one RUNNING task: {', '.join(running)}")

    current = state.get("currentTask")
    if current is not None and not isinstance(current, str):
        errors.append("state.json currentTask must be a task ID or null")
    elif current and tasks.get(current) != "RUNNING":
        errors.append(f"currentTask {current} is not RUNNING in plan.md")
    elif running and current != running[0]:
        errors.append(f"Plan RUNNING task {running[0]} does not match currentTask {current!r}")

    completed = as_string_list(state, "completedTasks", errors)
    failed = as_string_list(state, "failedTasks", errors)
    for task_id in completed:
        if tasks.get(task_id) != "DONE":
            errors.append(f"completedTasks contains {task_id}, but plan status is {tasks.get(task_id)!r}")
    for task_id in failed:
        if tasks.get(task_id) != "FAILED":
            errors.append(f"failedTasks contains {task_id}, but plan status is {tasks.get(task_id)!r}")
    duplicates = set(completed) & set(failed)
    if duplicates:
        errors.append(f"Tasks appear as both completed and failed: {', '.join(sorted(duplicates))}")

    next_action = state.get("nextAction")
    if not isinstance(next_action, str) or not next_action.strip():
        errors.append("state.json nextAction must be a non-empty string")
    if not isinstance(state.get("blockers"), list):
        errors.append("state.json blockers must be an array")
    if not isinstance(state.get("validation"), dict):
        errors.append("state.json validation must be an object")

    checkpoint = state.get("lastCheckpoint")
    if checkpoint:
        if not isinstance(checkpoint, str):
            errors.append("state.json lastCheckpoint must be a path or null")
        elif not (root / checkpoint).is_file():
            errors.append(f"Referenced lastCheckpoint does not exist: {checkpoint}")

    entries = error_log.get("errors", []) if isinstance(error_log, dict) else error_log
    if not isinstance(entries, list):
        errors.append("errors.json must be an array or an object containing an errors array")
    else:
        seen: set[str] = set()
        required_error_fields = {"id", "timestamp", "task", "error", "probableCause", "attemptedFixes", "status", "resolution"}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"errors.json entry {index} must be an object")
                continue
            missing = required_error_fields - entry.keys()
            if missing:
                errors.append(f"errors.json entry {index} is missing: {', '.join(sorted(missing))}")
            error_id = entry.get("id")
            if isinstance(error_id, str):
                if error_id in seen:
                    errors.append(f"Duplicate error ID: {error_id}")
                seen.add(error_id)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root containing AGENTS.md and .harness/")
    parser.add_argument(
        "--simulate",
        choices=["current-task-mismatch"],
        help="Inject an in-memory inconsistency to verify that the sensor fails",
    )
    args = parser.parse_args()
    errors = validate(Path(args.root), args.simulate)
    if errors:
        print("Project harness validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Project harness validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
