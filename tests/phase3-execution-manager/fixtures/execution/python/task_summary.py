from __future__ import annotations

from typing import TypedDict


class TaskRecord(TypedDict):
    task_id: str
    title: str
    status: str


def summarize_tasks(records: list[TaskRecord]) -> tuple[int, int, float]:
    if not records:
        raise ValueError("at least one task is required")

    completed = 0
    for record in records:
        if not {"task_id", "title", "status"} <= record.keys():
            raise ValueError("task records require task_id, title, and status")
        if record["status"] not in {"completed", "pending"}:
            raise ValueError("task status must be completed or pending")
        completed += record["status"] == "completed"

    total = len(records)
    return completed, total - completed, completed / total * 100


def main() -> None:
    records: list[TaskRecord] = [
        {"task_id": "T-101", "title": "Plan sandbox", "status": "completed"},
        {"task_id": "T-102", "title": "Run tests", "status": "completed"},
        {"task_id": "T-103", "title": "Write report", "status": "pending"},
    ]

    print("ARES PYTHON EXAMPLE START")
    completed, pending, percentage = summarize_tasks(records)
    invalid_data_handled = False
    try:
        summarize_tasks([{"task_id": "T-104", "title": "Invalid"}])  # type: ignore
    except ValueError:
        invalid_data_handled = True

    if (completed, pending, round(percentage, 2)) != (2, 1, 66.67):
        raise AssertionError("unexpected task summary")
    print(f"Completed tasks: {completed}")
    print(f"Pending tasks: {pending}")
    print(f"Completion: {percentage:.2f}%")
    print(f"Invalid record handled: {invalid_data_handled}")
    print("ARES PYTHON EXAMPLE COMPLETE")


if __name__ == "__main__":
    main()
