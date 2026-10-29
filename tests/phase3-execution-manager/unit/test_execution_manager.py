from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.execution.config import ExecutionConfig
from backend.app.execution.contracts import ExecutionRequest, ExecutionStatus
from backend.app.execution.manager import ExecutionManager
from backend.app.execution.runtime_policy import RuntimePolicy, RuntimePolicyError
from backend.app.execution.workspace import WorkspaceError, WorkspaceManager


def test_workspace_manager_rejects_path_traversal(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    manager = WorkspaceManager(root)

    with pytest.raises(WorkspaceError):
        manager.register("escape", root / ".." / "outside")


def test_workspace_manager_registers_and_resolves_approved_workspace(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    workspace = root / "project"
    workspace.mkdir(parents=True)
    manager = WorkspaceManager(root)

    manager.register("project", workspace)

    assert manager.resolve("project") == workspace.resolve()


def test_workspace_manager_rejects_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable in this Windows environment")

    with pytest.raises(WorkspaceError):
        WorkspaceManager(root).register("link", link)


def test_runtime_policy_rejects_unapproved_image(tmp_path: Path) -> None:
    policy = RuntimePolicy(ExecutionConfig(workspace_root=tmp_path))
    request = ExecutionRequest(
        workspace_id="project",
        command=["python", "--version"],
        runtime="python",
        image="evil/image:latest",
    )

    with pytest.raises(RuntimePolicyError):
        policy.select_image(request)


def test_manager_returns_structured_workspace_failure(tmp_path: Path) -> None:
    adapter = SimpleNamespace()
    manager = ExecutionManager(
        ExecutionConfig(workspace_root=tmp_path),
        docker_adapter=adapter,
    )
    request = ExecutionRequest(
        workspace_id="missing",
        command=["python", "--version"],
        runtime="python",
    )

    result = manager.execute(request)

    assert result.status == ExecutionStatus.VALIDATION_FAILED
    assert result.error is not None
    assert result.error.category.value == "workspace"


def test_manager_maps_docker_connection_failure(tmp_path: Path) -> None:
    root = tmp_path / "workspaces"
    workspace = root / "project"
    workspace.mkdir(parents=True)
    adapter = SimpleNamespace(
        ping=lambda: (_ for _ in ()).throw(RuntimeError("Docker Engine is unavailable")),
        ensure_image=lambda image: None,
    )
    manager = ExecutionManager(
        ExecutionConfig(workspace_root=root),
        docker_adapter=adapter,
    )
    manager.register_workspace("project", workspace)

    result = manager.execute(
        ExecutionRequest(
            workspace_id="project",
            command=["python", "--version"],
            runtime="python",
        )
    )

    assert result.status == ExecutionStatus.RUNTIME_PREPARATION_FAILED
    assert result.error is not None
    assert result.error.category.value == "docker_connection"
