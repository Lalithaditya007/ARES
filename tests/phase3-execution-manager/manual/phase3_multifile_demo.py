from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.app.execution.config import ExecutionConfig
from backend.app.execution.contracts import ExecutionStatus
from backend.app.execution.manager import ExecutionManager
from backend.app.execution.project_runner import ProjectRunner


SOURCE = ROOT / "examples" / "workspaces" / "ares-multifile-demo"
WORKSPACE_ROOT = ROOT / "examples" / "workspaces"
WORKSPACE = WORKSPACE_ROOT / "ares-multifile-demo"


def print_result(index: int, command, result) -> None:
    print(f"--- COMMAND {index} ---")
    print(f"Command: {command.original}")
    print(f"Runtime: {command.runtime.value}")
    print(f"Status: {result.status.value}")
    print(f"Exit code: {result.exit_code}")
    print("Stdout:")
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    print("Stderr:")
    print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    print(f"Duration seconds: {result.duration_seconds:.3f}")
    print(f"Output truncated: {result.output_truncated}")
    print(f"Cleanup succeeded: {result.cleanup_succeeded}")


def main() -> None:
    print("ARES MULTI-FILE PROJECT EXECUTION DEMO")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    for source in SOURCE.iterdir():
        target = WORKSPACE / source.name
        if source.is_file() and source.resolve() != target.resolve():
            shutil.copy2(source, target)

    manager = ExecutionManager(ExecutionConfig(workspace_root=WORKSPACE_ROOT))
    manager.register_workspace("ares-multifile-demo", WORKSPACE)
    run = ProjectRunner(manager).run("ares-multifile-demo", WORKSPACE)
    print(f"Workspace: {WORKSPACE.resolve()}")
    print("Docker mount: /workspace")

    for index, (command, result) in enumerate(zip(run.commands, run.results), start=1):
        print_result(index, command, result)

    print("--- OVERALL RESULT ---")
    print(f"Python result: {'PASS' if run.results[0].status == ExecutionStatus.SUCCEEDED else 'FAIL'}")
    print(f"Node result: {'PASS' if run.results[1].status == ExecutionStatus.SUCCEEDED else 'FAIL'}")
    print(f"Overall success: {run.overall_success}")
    if not run.overall_success:
        raise SystemExit(1)
    print("ARES MULTI-FILE DEMO PASSED")


if __name__ == "__main__":
    main()
