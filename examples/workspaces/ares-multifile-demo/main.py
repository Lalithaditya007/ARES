from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tasks() -> list[dict[str, Any]]:
    data = json.loads((Path(__file__).parent / "tasks.json").read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("tasks.json must contain a list")
    return data


def summarize_tasks(records: list[dict[str, Any]]) -> tuple[int, int, int, float]:
    if not records:
        raise ValueError("tasks.json must contain at least one task")
    completed = 0
    for record in records:
        if not {"id", "title", "status"} <= record.keys():
            raise ValueError("each task requires id, title, and status")
        if record["status"] not in {"completed", "pending"}:
            raise ValueError("status must be completed or pending")
        completed += record["status"] == "completed"
    total = len(records)
    pending = total - completed
    return total, completed, pending, completed / total * 100


def main() -> None:
    print("ARES MULTI-FILE PYTHON START")
    try:
        total, completed, pending, percentage = summarize_tasks(load_tasks())
        invalid_handled = False
        try:
            summarize_tasks([{"id": "invalid"}])
        except ValueError:
            invalid_handled = True
        if not invalid_handled:
            raise AssertionError("invalid task data was not rejected")
        print(f"Total tasks: {total}")
        print(f"Completed tasks: {completed}")
        print(f"Pending tasks: {pending}")
        print(f"Completion: {percentage:.2f}%")
        print(f"Invalid record handled: {invalid_handled}")
        print("ARES MULTI-FILE PYTHON COMPLETE")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Execution error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
