import os
import shutil
import time
from pathlib import Path

import docker
import pytest

from backend.app.execution.contracts import ExecutionRequest, ExecutionStatus
from backend.app.execution.config import ExecutionConfig
from backend.app.execution.docker_adapter import DockerAdapter
from backend.app.execution.manager import ExecutionManager
from backend.app.execution.project_runner import ProjectRunner

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "execution"


def _manager_for_fixture(tmp_path: Path, runtime: str, fixture: Path) -> ExecutionManager:
    root = tmp_path / "workspaces"
    workspace = root / runtime
    workspace.mkdir(parents=True)
    shutil.copy2(fixture, workspace / fixture.name)
    manager = ExecutionManager(ExecutionConfig(workspace_root=root))
    manager.register_workspace(runtime, workspace)
    return manager


def _assert_success(result, expected_stdout: str) -> None:
    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.exit_code == 0
    assert result.stdout == expected_stdout
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.output_truncated is False
    assert result.cleanup_succeeded is True


def _assert_no_new_execution_containers(client: docker.DockerClient, before: set[str]) -> None:
    after = {
        container.id
        for container in client.containers.list(
            all=True, filters={"label": "ares.execution=true"}
        )
    }
    assert after <= before


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_python_runtime_command_with_real_docker(tmp_path: Path) -> None:
    manager = _manager_for_fixture(
        tmp_path, "python", FIXTURE_ROOT / "python" / "task_summary.py"
    )
    result = manager.execute(ExecutionRequest(
        workspace_id="python",
        command=["python", "task_summary.py"],
        runtime="python",
        timeout_seconds=60,
    ))
    _assert_success(
        result,
        "ARES PYTHON EXAMPLE START\n"
        "Completed tasks: 2\n"
        "Pending tasks: 1\n"
        "Completion: 66.67%\n"
        "Invalid record handled: True\n"
        "ARES PYTHON EXAMPLE COMPLETE\n",
    )


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_node_runtime_command_with_real_docker(tmp_path: Path) -> None:
    manager = _manager_for_fixture(
        tmp_path, "node", FIXTURE_ROOT / "node" / "task-summary.js"
    )
    result = manager.execute(ExecutionRequest(
        workspace_id="node",
        command=["node", "task-summary.js"],
        runtime="node",
        timeout_seconds=60,
    ))
    _assert_success(
        result,
        "ARES NODE EXAMPLE START\n"
        "Completed tasks: 2\n"
        "Pending tasks: 1\n"
        "Completion: 66.67%\n"
        "Invalid record handled: True\n"
        "ARES NODE EXAMPLE COMPLETE\n",
    )


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_execution_manager_runs_registered_workspace(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    workspace = root / "project"
    workspace.mkdir(parents=True)
    manager = ExecutionManager(ExecutionConfig(workspace_root=root))
    manager.register_workspace("project", workspace)

    result = manager.execute(
        ExecutionRequest(
            workspace_id="project",
            command=["python", "--version"],
            runtime="python",
            timeout_seconds=60,
        )
    )

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.cleanup_succeeded is True


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_nonzero_command_and_cleanup_with_real_docker(tmp_path: Path) -> None:
    client = docker.from_env()
    before = {
        container.id
        for container in client.containers.list(
            all=True, filters={"label": "ares.execution=true"}
        )
    }
    root = tmp_path / "workspaces"
    workspace = root / "integration"
    workspace.mkdir(parents=True)
    manager = ExecutionManager(ExecutionConfig(workspace_root=root))
    manager.register_workspace("integration", workspace)
    result = manager.execute(
        ExecutionRequest(
            workspace_id="integration",
            command=["python", "-c", "raise SystemExit(7)"],
            runtime="python",
        )
    )

    assert result.status == ExecutionStatus.COMMAND_FAILED
    assert result.exit_code == 7
    assert result.cleanup_succeeded is True
    _assert_no_new_execution_containers(client, before)


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_runtime_error_returns_stderr_through_manager(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    workspace = root / "runtime-error"
    workspace.mkdir(parents=True)
    manager = ExecutionManager(ExecutionConfig(workspace_root=root))
    manager.register_workspace("runtime-error", workspace)

    result = manager.execute(
        ExecutionRequest(
            workspace_id="runtime-error",
            command=["python", "-c", "raise RuntimeError('intentional fixture failure')"],
            runtime="python",
        )
    )

    assert result.status == ExecutionStatus.COMMAND_FAILED
    assert result.exit_code != 0
    assert "intentional fixture failure" in result.stderr
    assert result.cleanup_succeeded is True


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_multifile_command_runner_executes_both_programs(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    workspace = root / "project"
    workspace.mkdir(parents=True)
    demo_source = Path(__file__).parents[3] / "examples" / "workspaces" / "ares-multifile-demo"
    for filename in ("main.py", "app.js", "tasks.json", "commands.txt"):
        shutil.copy2(demo_source / filename, workspace / filename)

    manager = ExecutionManager(ExecutionConfig(workspace_root=root))
    manager.register_workspace("project", workspace)
    run = ProjectRunner(manager).run("project", workspace)

    assert run.overall_success is True
    assert [result.status for result in run.results] == [
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.SUCCEEDED,
    ]
    assert "Total tasks: 4" in run.results[0].stdout
    assert "Total tasks: 4" in run.results[1].stdout


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_timeout_stops_real_container_and_returns_promptly(tmp_path: Path) -> None:
    client = docker.from_env()
    before = {
        container.id
        for container in client.containers.list(
            all=True, filters={"label": "ares.execution=true"}
        )
    }
    adapter = DockerAdapter(client)
    adapter.ensure_image("python:3.10.19-slim-bookworm")
    started = time.monotonic()

    result = adapter.run(
        ExecutionRequest(
            workspace_id="integration",
            command=["python", "-c", "import time; time.sleep(10)"],
            runtime="python",
            timeout_seconds=1,
        ),
        tmp_path,
        "python:3.10.19-slim-bookworm",
    )

    assert time.monotonic() - started < 8
    assert result.status == ExecutionStatus.TIMED_OUT
    assert result.timed_out is True
    assert result.cleanup_succeeded is True
    _assert_no_new_execution_containers(client, before)


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_workspace_files_are_visible_and_persisted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_text("input")
    adapter = DockerAdapter()
    adapter.ensure_image("python:3.10.19-slim-bookworm")

    result = adapter.run(
        ExecutionRequest(
            workspace_id="integration",
            command=[
                "python",
                "-c",
                "from pathlib import Path; print(Path('/workspace/input.txt').read_text()); Path('/workspace/output.txt').write_text('created')",
            ],
            runtime="python",
        ),
        workspace,
        "python:3.10.19-slim-bookworm",
    )

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.stdout.strip() == "input"
    assert (workspace / "output.txt").read_text() == "created"


@pytest.mark.skipif(
    os.getenv("ARES_RUN_DOCKER_TESTS") != "1",
    reason="Set ARES_RUN_DOCKER_TESTS=1 to run real Docker integration tests",
)
def test_output_limit_is_reported_for_real_container(tmp_path: Path) -> None:
    adapter = DockerAdapter()
    adapter.ensure_image("python:3.10.19-slim-bookworm")

    result = adapter.run(
        ExecutionRequest(
            workspace_id="integration",
            command=["python", "-c", "print('x' * 10000)"],
            runtime="python",
            output_limit_bytes=64,
        ),
        tmp_path,
        "python:3.10.19-slim-bookworm",
    )

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.output_truncated is True
    assert len(result.stdout.encode("utf-8")) <= 64
