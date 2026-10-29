from __future__ import annotations

import os
from pathlib import Path


class WorkspaceError(ValueError):
    pass


class WorkspaceManager:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._registered: dict[str, Path] = {}

    def register(self, workspace_id: str, workspace_path: Path) -> None:
        if not workspace_id or any(
            character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
            for character in workspace_id
        ):
            raise WorkspaceError("workspace identifier contains unsupported characters")

        try:
            resolved_path = workspace_path.resolve(strict=True)
            root = self._root.resolve(strict=True)
        except FileNotFoundError as exc:
            raise WorkspaceError("workspace root and workspace must exist") from exc

        if not resolved_path.is_dir():
            raise WorkspaceError("workspace must be a directory")
        if os.path.commonpath([str(root), str(resolved_path)]) != str(root):
            raise WorkspaceError("workspace must be inside the approved workspace root")

        self._registered[workspace_id] = resolved_path

    def resolve(self, workspace_id: str) -> Path:
        try:
            workspace_path = self._registered[workspace_id]
        except KeyError as exc:
            raise WorkspaceError("workspace is not registered") from exc

        if workspace_path.resolve() != workspace_path:
            raise WorkspaceError("registered workspace path changed unexpectedly")
        return workspace_path
