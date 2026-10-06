"""The small, boring filesystem contract shared by ARC runs.

The supervisor owns lifecycle and status.  This module only creates paths,
writes the manifest, and performs atomic record writes; it never starts a
process or talks to a platform.
"""

from __future__ import annotations

import json
import os
import tempfile
import sys
import time
from pathlib import Path
from typing import Any, Mapping


DIRECTORIES = (
    "program",
    "inputs",
    "data/workspace",
    "data/harness",
    "records",
    "snapshots",
    "evaluations",
)


def storage_path(path: Path) -> None:
    """Mac artifacts must physically remain on WorkSSD, including symlinks."""
    if sys.platform != "darwin":
        return
    path = Path(path).resolve()
    mount = Path("/Volumes/WorkSSD").resolve(strict=True)
    ancestor = path
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not path.is_relative_to(mount) or ancestor.stat().st_dev != mount.stat().st_dev:
        raise ValueError(f"Mac run storage must physically use WorkSSD: {path}")


def root(run_root: str | os.PathLike[str], run_id: str) -> Path:
    """Return a run path without creating it."""
    if not run_id or run_id in {".", ".."} or Path(run_id).name != run_id:
        raise ValueError("run_id must be one path component")
    path = Path(run_root).expanduser().resolve() / "runs" / run_id
    storage_path(path)
    return path


def create(run_root: str | os.PathLike[str], run_id: str) -> Path:
    """Create the fixed run tree and return its root."""
    run = root(run_root, run_id)
    run.mkdir(parents=True, exist_ok=False)
    for relative in DIRECTORIES:
        (run / relative).mkdir(parents=True, exist_ok=True)
    return run


def create_run(
    run_root: str | os.PathLike[str],
    variant: str,
    target: str,
    task: str,
    *,
    route: str | None = None,
    competition: bool = False,
    source: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> Path:
    """Create a run and its initial, explicit manifest."""
    if not variant or not target or not task:
        raise ValueError("variant, target and task are required")
    import uuid
    run = create(run_root, run_id or uuid.uuid4().hex)
    write_manifest(run, {
        "record_type": "arc.run",
        "run_id": run.name,
        "created_at": time.time(),
        "variant": variant,
        "target": target,
        "task": task,
        "route": route,
        "competition": bool(competition),
        "source": dict(source) if source else None,
    })
    return run


def paths(run: str | os.PathLike[str]) -> dict[str, Path]:
    run = Path(run).expanduser().resolve()
    return {
        "root": run,
        "program": run / "program",
        "inputs": run / "inputs",
        "workspace": run / "data" / "workspace",
        "harness": run / "data" / "harness",
        "records": run / "records",
        "snapshots": run / "snapshots",
        "evaluations": run / "evaluations",
        "manifest": run / "manifest.json",
        "status": run / "records" / "status.json",
    }


def write_json(path: str | os.PathLike[str], value: Mapping[str, Any]) -> None:
    """Atomically write one JSON record beside its final path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def manifest(run: str | os.PathLike[str]) -> dict[str, Any]:
    path = paths(run)["manifest"]
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be an object: {path}")
    return value


def write_manifest(run: str | os.PathLike[str], value: Mapping[str, Any]) -> None:
    write_json(paths(run)["manifest"], value)
