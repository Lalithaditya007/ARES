from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app.execution.contracts import ExecutionResult, ExecutionStatus
from backend.app.execution.project_runner import (
    ProjectCommandError,
    ProjectRunner,
    ProjectRunnerError,
    parse_project_command,
)


@pytest.mark.parametrize(
    ("line", "runtime", "arguments"),
    [
        ("python main.py", "python", ["python", "main.py"]),
        ("  node\tapp.js  ", "node", ["node", "app.js"]),
    ],
)
def test_parse_project_command_allowlist(line, runtime, arguments) -> None:
    command = parse_project_command(line)

    assert command is not None
    assert command.runtime.value == runtime
    assert command.arguments == arguments


def test_parse_project_command_ignores_blank_lines_and_comments() -> None:
    assert parse_project_command("") is None
    assert parse_project_command("  # comment") is None


@pytest.mark.parametrize(
    "line",
    [
        "python ../../outside.py",
        "node app.js; whoami",
        "python main.py && node app.js",
        'python -c "print(1)"',
        "cmd.exe /c dir",
        "sh -c something",
        "python main.py > output.txt",
        "python main.py extra",
    ],
)
def test_parse_project_command_rejects_unsafe_commands(line: str) -> None:
    with pytest.raises(ProjectCommandError):
        parse_project_command(line)


def test_project_runner_executes_sequentially_and_collects_results(tmp_path) -> None:
    manager = Mock()
    manager.execute.side_effect = [
        ExecutionResult(status=ExecutionStatus.SUCCEEDED, exit_code=0),
        ExecutionResult(status=ExecutionStatus.SUCCEEDED, exit_code=0),
    ]
    (tmp_path / "commands.txt").write_text(
        "# comment\npython main.py\n\nnode app.js\n", encoding="utf-8"
    )

    result = ProjectRunner(manager).run("demo", tmp_path)

    assert result.overall_success is True
    assert [command.original for command in result.commands] == [
        "python main.py",
        "node app.js",
    ]
    assert [call.args[0].command for call in manager.execute.call_args_list] == [
        ["python", "main.py"],
        ["node", "app.js"],
    ]


def test_project_runner_continues_after_program_failure(tmp_path) -> None:
    manager = Mock()
    manager.execute.side_effect = [
        ExecutionResult(status=ExecutionStatus.COMMAND_FAILED, exit_code=3),
        ExecutionResult(status=ExecutionStatus.SUCCEEDED, exit_code=0),
    ]
    (tmp_path / "commands.txt").write_text("python main.py\nnode app.js\n", encoding="utf-8")

    result = ProjectRunner(manager).run("demo", tmp_path)

    assert result.overall_success is False
    assert len(result.results) == 2


def test_project_runner_stops_after_infrastructure_failure(tmp_path) -> None:
    manager = Mock()
    manager.execute.side_effect = [
        ExecutionResult(status=ExecutionStatus.TIMED_OUT, timed_out=True),
        ExecutionResult(status=ExecutionStatus.SUCCEEDED, exit_code=0),
    ]
    (tmp_path / "commands.txt").write_text("python main.py\nnode app.js\n", encoding="utf-8")

    result = ProjectRunner(manager).run("demo", tmp_path)

    assert result.overall_success is False
    assert len(result.results) == 1


def test_project_runner_rejects_missing_or_empty_commands_file(tmp_path) -> None:
    runner = ProjectRunner(SimpleNamespace())

    with pytest.raises(ProjectRunnerError):
        runner.run("demo", tmp_path)
    (tmp_path / "commands.txt").write_text("# only comments\n", encoding="utf-8")
    with pytest.raises(ProjectRunnerError):
        runner.run("demo", tmp_path)
