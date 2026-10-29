from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from docker.errors import APIError, DockerException, ImageNotFound
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout

from backend.app.execution.contracts import ExecutionRequest, ExecutionStatus
from backend.app.execution.docker_adapter import DockerAdapter, ImagePreparationError


def _request(**overrides: object) -> ExecutionRequest:
    values: dict[str, object] = {
        "workspace_id": "sample",
        "command": ["python", "--version"],
        "runtime": "python",
    }
    values.update(overrides)
    return ExecutionRequest.model_validate(values)


def test_adapter_maps_success_and_applies_sandbox_options(tmp_path: Path) -> None:
    container = Mock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.side_effect = [b"Python 3.10\n", b""]
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.exit_code == 0
    assert result.stdout == "Python 3.10\n"
    client.containers.create.assert_called_once()
    options = client.containers.create.call_args.kwargs
    assert options["network_disabled"] is True
    assert options["user"] == "1000:1000"
    assert options["cap_drop"] == ["ALL"]
    assert options["security_opt"] == ["no-new-privileges:true"]
    assert options["volumes"][str(tmp_path)]["bind"] == "/workspace"
    container.remove.assert_called_once_with(force=True)


def test_adapter_maps_missing_image_and_still_attempts_cleanup(tmp_path: Path) -> None:
    client = SimpleNamespace(
        containers=SimpleNamespace(create=Mock(side_effect=ImageNotFound("missing")))
    )

    result = DockerAdapter(client).run(_request(), tmp_path, "missing:image")

    assert result.status == ExecutionStatus.RUNTIME_PREPARATION_FAILED
    assert result.error is not None
    assert result.error.category.value == "image"


def test_adapter_truncates_large_output(tmp_path: Path) -> None:
    container = Mock()
    container.wait.return_value = {"StatusCode": 1}
    container.logs.side_effect = [b"0123456789", b"error"]
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(
        _request(output_limit_bytes=4), tmp_path, "python:3.10.19-slim-bookworm"
    )

    assert result.status == ExecutionStatus.COMMAND_FAILED
    assert result.output_truncated is True
    assert result.stdout == "0123"


def test_adapter_stops_and_maps_timeout(tmp_path: Path) -> None:
    container = Mock()
    container.wait.side_effect = ReadTimeout("timed out")
    container.logs.side_effect = [b"", b""]
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.TIMED_OUT
    assert result.timed_out is True
    container.stop.assert_called_once_with(timeout=5)


def test_adapter_reports_cleanup_failure(tmp_path: Path) -> None:
    container = Mock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.side_effect = [b"ok", b""]
    container.remove.side_effect = DockerException("cleanup failed")
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CLEANUP_FAILED
    assert result.cleanup_succeeded is False


def test_adapter_maps_log_retrieval_failure_without_leaking_exception(
    tmp_path: Path,
) -> None:
    container = Mock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.side_effect = RuntimeError("unexpected log failure")
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CONTAINER_FAILED
    assert result.error is not None
    assert result.error.category.value == "docker_connection"
    container.remove.assert_called_once_with(force=True)


def test_adapter_maps_non_timeout_transport_failure(tmp_path: Path) -> None:
    container = Mock()
    container.wait.side_effect = RequestsConnectionError("pipe disconnected")
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CONTAINER_FAILED
    assert result.timed_out is False


def test_adapter_maps_container_creation_failure(tmp_path: Path) -> None:
    client = SimpleNamespace(
        containers=SimpleNamespace(create=Mock(side_effect=APIError("create failed")))
    )

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CONTAINER_FAILED
    assert result.error is not None
    assert result.error.category.value == "container"


def test_adapter_maps_container_start_failure(tmp_path: Path) -> None:
    container = Mock()
    container.start.side_effect = APIError("start failed")
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CONTAINER_FAILED
    container.remove.assert_called_once_with(force=True)


def test_adapter_maps_container_wait_failure(tmp_path: Path) -> None:
    container = Mock()
    container.wait.side_effect = APIError("wait failed")
    client = SimpleNamespace(containers=SimpleNamespace(create=Mock(return_value=container)))

    result = DockerAdapter(client).run(_request(), tmp_path, "python:3.10.19-slim-bookworm")

    assert result.status == ExecutionStatus.CONTAINER_FAILED
    container.remove.assert_called_once_with(force=True)


def test_image_preparation_reports_pull_failure() -> None:
    images = SimpleNamespace(
        get=Mock(side_effect=ImageNotFound("missing")),
        pull=Mock(side_effect=DockerException("pull failed")),
    )

    with pytest.raises(ImagePreparationError):
        DockerAdapter(SimpleNamespace(images=images)).ensure_image("missing:image")
