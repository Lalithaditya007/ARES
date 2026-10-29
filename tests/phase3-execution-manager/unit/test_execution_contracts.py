import pytest
from pydantic import ValidationError

from backend.app.execution.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    RuntimeFamily,
    truncate_output,
)


def test_execution_request_accepts_a_bounded_argument_list() -> None:
    request = ExecutionRequest(
        workspace_id="sample-project",
        command=["python", "-m", "pytest", "-q"],
        runtime=RuntimeFamily.PYTHON,
    )

    assert request.command == ["python", "-m", "pytest", "-q"]
    assert request.timeout_seconds == 120


@pytest.mark.parametrize(
    "payload",
    [
        {"workspace_id": "../outside", "command": ["python"], "runtime": "python"},
        {"workspace_id": "project", "command": [], "runtime": "python"},
        {"workspace_id": "project", "command": ["python"], "runtime": "ruby"},
        {"workspace_id": "project", "command": ["python"], "runtime": "python", "timeout_seconds": 0},
        {"workspace_id": "project", "command": ["python"], "runtime": "python", "environment": {"TOKEN": "secret"}},
    ],
)
def test_execution_request_rejects_unsafe_or_invalid_values(payload: dict) -> None:
    with pytest.raises(ValidationError):
        ExecutionRequest.model_validate(payload)


def test_truncate_output_preserves_utf8_boundaries() -> None:
    value, truncated = truncate_output("hello \N{SNOWMAN}", 7)

    assert value == "hello "
    assert truncated is True


def test_result_status_distinguishes_command_failure_from_timeout() -> None:
    command_failure = ExecutionStatus.COMMAND_FAILED
    timeout = ExecutionStatus.TIMED_OUT

    assert command_failure != timeout
