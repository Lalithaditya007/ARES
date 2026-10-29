from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from .contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, RuntimeFamily


class ProjectCommandError(ValueError):
    pass


class ProjectRunnerError(ValueError):
    pass


class ExecutionManagerProtocol(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        ...


class ProjectCommand:
    def __init__(
        self,
        original: str,
        runtime: RuntimeFamily,
        arguments: list[str],
    ) -> None:
        self.original = original
        self.runtime = runtime
        self.arguments = arguments


class ProjectRunResult:
    def __init__(
        self,
        commands: list[ProjectCommand],
        results: list[ExecutionResult],
    ) -> None:
        self.commands = commands
        self.results = results

    @property
    def overall_success(self) -> bool:
        return bool(self.results) and all(
            result.status == ExecutionStatus.SUCCEEDED
            and result.cleanup_succeeded
            for result in self.results
        )


_COMMANDS = {
    ("python", "main.py"): RuntimeFamily.PYTHON,
    ("node", "app.js"): RuntimeFamily.NODE,
}
_COMMAND_PATTERN = re.compile(r"^(python|node)[ \t]+([^\s]+)$")


def parse_project_command(line: str) -> ProjectCommand | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = _COMMAND_PATTERN.fullmatch(stripped)
    if match is None:
        raise ProjectCommandError(f"unsupported command: {line!r}")

    key = (match.group(1), match.group(2))
    runtime = _COMMANDS.get(key)
    if runtime is None:
        raise ProjectCommandError(f"unsupported command: {line!r}")
    return ProjectCommand(
        original=stripped,
        runtime=runtime,
        arguments=[key[0], key[1]],
    )


class ProjectRunner:
    def __init__(self, execution_manager: ExecutionManagerProtocol) -> None:
        self._execution_manager = execution_manager

    def read_commands(self, workspace_path: Path) -> list[ProjectCommand]:
        commands_path = workspace_path / "commands.txt"
        try:
            lines = commands_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ProjectRunnerError("unable to read workspace commands.txt") from exc

        commands = [
            command
            for line in lines
            if (command := parse_project_command(line)) is not None
        ]
        if not commands:
            raise ProjectRunnerError("commands.txt contains no executable commands")
        return commands

    def run(self, workspace_id: str, workspace_path: Path) -> ProjectRunResult:
        commands = self.read_commands(workspace_path)
        results: list[ExecutionResult] = []
        for command in commands:
            result = self._execution_manager.execute(
                ExecutionRequest(
                    workspace_id=workspace_id,
                    command=command.arguments,
                    runtime=command.runtime,
                )
            )
            results.append(result)
            if result.status not in {
                ExecutionStatus.SUCCEEDED,
                ExecutionStatus.COMMAND_FAILED,
            }:
                break
        return ProjectRunResult(commands, results)
