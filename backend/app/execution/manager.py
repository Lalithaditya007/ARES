from __future__ import annotations

from pathlib import Path

from .config import ExecutionConfig
from .contracts import (
    ExecutionError,
    ExecutionErrorCategory,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from .docker_adapter import DockerAdapter, ImagePreparationError
from .runtime_policy import RuntimePolicy, RuntimePolicyError
from .workspace import WorkspaceError, WorkspaceManager


class ExecutionManager:
    def __init__(
        self,
        config: ExecutionConfig,
        *,
        workspace_manager: WorkspaceManager | None = None,
        docker_adapter: DockerAdapter | None = None,
    ) -> None:
        self._config = config
        self._workspaces = workspace_manager or WorkspaceManager(config.workspace_root)
        self._runtime_policy = RuntimePolicy(config)
        self._docker = docker_adapter or DockerAdapter(
            memory_limit=config.memory_limit,
            cpu_limit=config.cpu_limit,
            process_limit=config.process_limit,
        )

    def register_workspace(self, workspace_id: str, workspace_path: Path) -> None:
        self._workspaces.register(workspace_id, workspace_path)

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        try:
            workspace_path = self._workspaces.resolve(request.workspace_id)
        except WorkspaceError as exc:
            return self._failure(
                ExecutionStatus.VALIDATION_FAILED,
                ExecutionErrorCategory.WORKSPACE,
                str(exc),
            )

        try:
            image = self._runtime_policy.select_image(request)
        except RuntimePolicyError as exc:
            return self._failure(
                ExecutionStatus.RUNTIME_PREPARATION_FAILED,
                ExecutionErrorCategory.IMAGE,
                str(exc),
            )

        try:
            self._docker.ping()
            self._docker.ensure_image(image)
        except ImagePreparationError as exc:
            return self._failure(
                ExecutionStatus.RUNTIME_PREPARATION_FAILED,
                ExecutionErrorCategory.IMAGE,
                str(exc),
            )
        except RuntimeError as exc:
            return self._failure(
                ExecutionStatus.RUNTIME_PREPARATION_FAILED,
                ExecutionErrorCategory.DOCKER_CONNECTION,
                str(exc),
            )

        return self._docker.run(request, workspace_path, image)

    @staticmethod
    def _failure(
        status: ExecutionStatus,
        category: ExecutionErrorCategory,
        message: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            status=status,
            error=ExecutionError(category=category, message=message),
        )
