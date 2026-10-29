from __future__ import annotations

import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.execution.config import ExecutionConfig
from backend.app.execution.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from backend.app.execution.manager import ExecutionManager


FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "phase3-execution-manager" / "fixtures" / "execution"


def print_result(label: str, result: ExecutionResult) -> None:
    print(f"--- {label} RESULT ---")
    print(f"Status: {result.status.value}")
    print(f"Exit code: {result.exit_code}")
    print("Stdout:")
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    print("Stderr:")
    print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    print(f"Duration seconds: {result.duration_seconds:.3f}")
    print(f"Timed out: {result.timed_out}")
    print(f"Output truncated: {result.output_truncated}")
    print(f"Cleanup succeeded: {result.cleanup_succeeded}")


def execute_demo(manager: ExecutionManager, workspace: Path, runtime: str, source: Path, command: list[str]) -> ExecutionResult:
    target = workspace / source.name
    shutil.copy2(source, target)
    manager.register_workspace(runtime, workspace)
    return manager.execute(
        ExecutionRequest(workspace_id=runtime, command=command, runtime=runtime)
    )


def main() -> None:
    print("ARES PHASE 3 EXECUTION DEMO")
    with TemporaryDirectory(prefix="ares-phase3-demo-", dir=REPOSITORY_ROOT / "tests") as temporary:
        workspace_root = Path(temporary)
        workspace = workspace_root / "workspace"
        workspace.mkdir()
        manager = ExecutionManager(ExecutionConfig(workspace_root=workspace_root))

        python_result = execute_demo(
            manager,
            workspace,
            "python",
            FIXTURE_ROOT / "python" / "task_summary.py",
            ["python", "task_summary.py"],
        )
        print_result("PYTHON", python_result)

        node_result = execute_demo(
            manager,
            workspace,
            "node",
            FIXTURE_ROOT / "node" / "task-summary.js",
            ["node", "task-summary.js"],
        )
        print_result("NODE.JS", node_result)

        assert python_result.status == ExecutionStatus.SUCCEEDED
        assert python_result.exit_code == 0
        assert node_result.status == ExecutionStatus.SUCCEEDED
        assert node_result.exit_code == 0
        print("ARES DEMO PASSED")


if __name__ == "__main__":
    main()
