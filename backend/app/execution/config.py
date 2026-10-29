from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .contracts import RuntimeFamily


class ExecutionConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    workspace_root: Path
    runtime_images: dict[RuntimeFamily, str] = Field(
        default_factory=lambda: {
            RuntimeFamily.PYTHON: "python:3.10.19-slim-bookworm",
            RuntimeFamily.NODE: "node:22.14.0-bookworm-slim",
        }
    )
    memory_limit: str = "512m"
    cpu_limit: float = Field(default=1.0, gt=0, le=4)
    process_limit: int = Field(default=256, gt=0, le=4096)
