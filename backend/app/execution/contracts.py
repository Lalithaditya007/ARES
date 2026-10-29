from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RuntimeFamily(str, Enum):
    PYTHON = "python"
    NODE = "node"


class ExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    COMMAND_FAILED = "command_failed"
    TIMED_OUT = "timed_out"
    VALIDATION_FAILED = "validation_failed"
    RUNTIME_PREPARATION_FAILED = "runtime_preparation_failed"
    CONTAINER_FAILED = "container_failed"
    CLEANUP_FAILED = "cleanup_failed"


class ExecutionErrorCategory(str, Enum):
    VALIDATION = "validation"
    WORKSPACE = "workspace"
    DOCKER_CONNECTION = "docker_connection"
    IMAGE = "image"
    CONTAINER = "container"
    TIMEOUT = "timeout"
    DEPENDENCY_INSTALLATION = "dependency_installation"
    CLEANUP = "cleanup"


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]
    command: list[Annotated[str, Field(min_length=1, max_length=256)]]
    runtime: RuntimeFamily
    image: str | None = Field(default=None, min_length=1, max_length=128)
    timeout_seconds: float = Field(default=120.0, gt=0, le=900)
    output_limit_bytes: int = Field(default=262_144, gt=0, le=10_485_760)

    @field_validator("command")
    @classmethod
    def validate_command(cls, command: list[str]) -> list[str]:
        if not command:
            raise ValueError("command must contain at least one argument")
        return command

    @field_validator("image")
    @classmethod
    def validate_image(cls, image: str | None) -> str | None:
        if image is not None and any(character.isspace() for character in image):
            raise ValueError("image must not contain whitespace")
        return image


class ExecutionError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: ExecutionErrorCategory
    message: str = Field(min_length=1, max_length=1024)


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ExecutionStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = Field(default=0.0, ge=0)
    error: ExecutionError | None = None
    timed_out: bool = False
    output_truncated: bool = False
    cleanup_succeeded: bool = True


def truncate_output(value: str, limit_bytes: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= limit_bytes:
        return value, False

    truncated = encoded[:limit_bytes].decode("utf-8", errors="ignore")
    return truncated, True
