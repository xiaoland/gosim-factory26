"""Bounded, workspace-contained source snapshots for the double compiler."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from ..errors import SvcError
from .model import PathPart, Snapshot


MAX_LOCAL_FILE_BYTES = 4_194_304


class LocalSources:
    def __init__(self, module: Path) -> None:
        self.module = _resolve_module(module)
        self.module_dir = self.module.parent
        self.workspace = _workspace_for_module(self.module)
        self.snapshots: dict[str, Snapshot] = {}

    def snapshot_local(self, source: str, path: tuple[PathPart, ...]) -> Snapshot:
        if (
            not source
            or Path(source).is_absolute()
            or urlsplit(source).scheme
            or "\0" in source
        ):
            raise SvcError(
                "invalid-double-local-path",
                "Local sources must be relative paths.",
                {"module": str(self.module), "path": list(path), "source": source},
            )
        return self.snapshot_path(self.resolve(source, path, kind="file"))

    def snapshot_path(self, path: Path) -> Snapshot:
        logical = path.relative_to(self.workspace).as_posix()
        existing = self.snapshots.get(logical)
        if existing is not None:
            return existing
        raw = self.read_bounded(
            path, MAX_LOCAL_FILE_BYTES, "double-local-file-too-large"
        )
        snapshot = Snapshot(
            logical_path=logical,
            sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),
            content_base64=base64.b64encode(raw).decode("ascii"),
        )
        self.snapshots[logical] = snapshot
        return snapshot

    def resolve(
        self,
        source: str,
        path: tuple[PathPart, ...],
        *,
        kind: Literal["file", "directory"],
        allow_absolute: bool = False,
    ) -> Path:
        return self.resolve_from(
            source,
            self.module_dir,
            path,
            kind=kind,
            error_code="double-local-path-outside-workspace",
            allow_absolute=allow_absolute,
        )

    def resolve_from(
        self,
        source: str,
        base: Path,
        path: tuple[PathPart, ...],
        *,
        kind: Literal["file", "directory"],
        error_code: str,
        allow_absolute: bool = False,
    ) -> Path:
        candidate = Path(source)
        if (candidate.is_absolute() and not allow_absolute) or "\0" in source:
            raise SvcError(
                error_code,
                "Local path must be relative and remain within the selected workspace.",
                {"module": str(self.module), "path": list(path), "source": source},
            )
        try:
            resolved = (
                candidate.resolve(strict=True)
                if candidate.is_absolute()
                else (base / candidate).resolve(strict=True)
            )
            resolved.relative_to(self.workspace)
        except (OSError, RuntimeError, ValueError) as error:
            raise SvcError(
                error_code,
                "Local path does not exist within the selected workspace.",
                {"module": str(self.module), "path": list(path), "source": source},
            ) from error
        valid = resolved.is_file() if kind == "file" else resolved.is_dir()
        if not valid:
            raise SvcError(
                error_code,
                f"Local path must resolve to a {kind}.",
                {"module": str(self.module), "path": list(path), "source": source},
            )
        return resolved

    def read_bounded(self, path: Path, maximum: int, code: str) -> bytes:
        try:
            size = path.stat().st_size
            if size > maximum:
                raise _too_large(code, self.module, path, size, maximum)
            raw = path.read_bytes()
            if len(raw) > maximum:
                raise _too_large(code, self.module, path, len(raw), maximum)
            return raw
        except SvcError:
            raise
        except OSError as error:
            raise SvcError(
                "double-local-file-unavailable",
                "Local source could not be read.",
                {"module": str(self.module), "source": str(path)},
            ) from error


def _resolve_module(module: Path) -> Path:
    try:
        resolved = module.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise SvcError(
            "double-module-unavailable",
            "Double module does not exist.",
            {"module": str(module)},
        ) from error
    if not resolved.is_file():
        raise SvcError(
            "double-module-unavailable",
            "Double module must be a file.",
            {"module": str(module)},
        )
    return resolved


def _workspace_for_module(module: Path) -> Path:
    return next(
        (parent.resolve() for parent in module.parents if (parent / ".git").exists()),
        module.parent.resolve(),
    )


def _too_large(
    code: str, module: Path, source: Path, size: int, maximum: int
) -> SvcError:
    return SvcError(
        code,
        "Local source exceeds its byte bound.",
        {
            "module": str(module),
            "source": str(source),
            "bytes": size,
            "max_bytes": maximum,
        },
    )


__all__ = ["LocalSources"]
