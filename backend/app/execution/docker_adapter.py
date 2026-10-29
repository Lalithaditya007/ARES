from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, DockerException, ImageNotFound
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout, RequestException

from .contracts import (
    ExecutionError,
    ExecutionErrorCategory,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    truncate_output,
)


class ImagePreparationError(RuntimeError):
    pass


class DockerAdapter:
    def __init__(
        self,
        client: Any | None = None,
        *,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        process_limit: int = 256,
    ) -> None:
        self._client = client or docker.from_env()
        self._memory_limit = memory_limit
        self._cpu_limit = cpu_limit
        self._process_limit = process_limit

    def ping(self) -> None:
        try:
            self._client.ping()
        except DockerException as exc:
            raise RuntimeError("Docker Engine is unavailable") from exc

    def ensure_image(self, image: str) -> None:
        try:
            self._client.images.get(image)
        except ImageNotFound:
            try:
                self._client.images.pull(image)
            except DockerException as exc:
                raise ImagePreparationError(
                    f"Unable to prepare approved image: {image}"
                ) from exc
        except DockerException as exc:
            raise ImagePreparationError(
                f"Unable to inspect approved image: {image}"
            ) from exc

    def run(
        self,
        request: ExecutionRequest,
        workspace_path: Path,
        image: str,
    ) -> ExecutionResult:
        started_at = time.monotonic()
        container = None
        cleanup_succeeded = True
        result: ExecutionResult
        try:
            container = self._client.containers.create(
                image=image,
                command=request.command,
                working_dir="/workspace",
                volumes={
                    str(workspace_path): {
                        "bind": "/workspace",
                        "mode": "rw",
                    }
                },
                detach=True,
                user="1000:1000",
                network_disabled=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                mem_limit=self._memory_limit,
                nano_cpus=int(self._cpu_limit * 1_000_000_000),
                pids_limit=self._process_limit,
                labels={"ares.execution": "true"},
            )
            container.start()
            try:
                wait_result = container.wait(timeout=request.timeout_seconds)
                exit_code = int(wait_result["StatusCode"])
                status = (
                    ExecutionStatus.SUCCEEDED
                    if exit_code == 0
                    else ExecutionStatus.COMMAND_FAILED
                )
                timed_out = False
                error = None
            except (ReadTimeout, RequestsConnectionError) as exc:
                if not self._is_timeout(exc):
                    raise
                try:
                    container.stop(timeout=5)
                except (DockerException, RequestException):
                    pass
                exit_code = None
                status = ExecutionStatus.TIMED_OUT
                timed_out = True
                error = ExecutionError(
                    category=ExecutionErrorCategory.TIMEOUT,
                    message="Container execution exceeded the configured timeout",
                )

            stdout = self._read_logs(container, stdout=True)
            stderr = self._read_logs(container, stdout=False)
            stdout, stdout_truncated = truncate_output(
                stdout, request.output_limit_bytes
            )
            stderr, stderr_truncated = truncate_output(
                stderr, request.output_limit_bytes
            )
            result = ExecutionResult(
                status=status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=time.monotonic() - started_at,
                error=error,
                timed_out=timed_out,
                output_truncated=stdout_truncated or stderr_truncated,
            )
        except ImageNotFound as exc:
            result = self._failure(
                ExecutionStatus.RUNTIME_PREPARATION_FAILED,
                ExecutionErrorCategory.IMAGE,
                "The configured runtime image is unavailable",
                started_at,
                exc,
            )
        except APIError as exc:
            result = self._failure(
                ExecutionStatus.CONTAINER_FAILED,
                ExecutionErrorCategory.CONTAINER,
                "Docker could not create or start the execution container",
                started_at,
                exc,
            )
        except (
            DockerException,
            RequestException,
            KeyError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            result = self._failure(
                ExecutionStatus.CONTAINER_FAILED,
                ExecutionErrorCategory.DOCKER_CONNECTION,
                "Docker Engine could not execute the request",
                started_at,
                exc,
            )
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except (
                    DockerException,
                    OSError,
                    RuntimeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    cleanup_succeeded = False
        if not cleanup_succeeded:
            if result.error is None:
                result.status = ExecutionStatus.CLEANUP_FAILED
            result.cleanup_succeeded = False
            result.error = ExecutionError(
                category=ExecutionErrorCategory.CLEANUP,
                message="The execution container could not be removed",
            )
        return result

    @staticmethod
    def _is_timeout(error: Exception) -> bool:
        current: BaseException | None = error
        while current is not None:
            if isinstance(current, (ReadTimeout, TimeoutError)):
                return True
            current = current.__cause__ or current.__context__
        return "timed out" in str(error).lower()

    @staticmethod
    def _read_logs(container: Any, *, stdout: bool) -> str:
        logs = container.logs(stdout=stdout, stderr=not stdout)
        if isinstance(logs, bytes):
            return logs.decode("utf-8", errors="replace")
        return str(logs)

    @staticmethod
    def _failure(
        status: ExecutionStatus,
        category: ExecutionErrorCategory,
        message: str,
        started_at: float,
        cause: Exception,
    ) -> ExecutionResult:
        return ExecutionResult(
            status=status,
            duration_seconds=time.monotonic() - started_at,
            error=ExecutionError(category=category, message=message),
        )
