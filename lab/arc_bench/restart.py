"""Restart one run without inheriting its process or platform identity."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from .run_layout import create_run, manifest, paths, write_json, write_manifest


def _copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"missing restart data: {source}")
    shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)


def _wait_stopped(run: Path, timeout: float = 30.0) -> dict[str, Any]:
    from . import execution
    deadline = time.monotonic() + timeout
    latest: dict[str, Any] = {}
    while time.monotonic() < deadline:
        latest = execution.observe(run)
        if latest.get("lifecycle") in {"stopped", "completed", "failed"}:
            return latest
        time.sleep(0.5)
    raise RuntimeError(f"source run did not reach a stopped state: {latest}")


def restart(source_run: str | Path, destination_run: str | Path | None = None, *,
            task: str | None = None, target: str | None = None,
            route: str | None = None, competition: bool | None = None,
            task_version: str | None = None, snapshot: str | None = None,
            variant: str | None = None) -> dict[str, Any]:
    """Stop/save a source, then assemble a fresh same-variant run.

    Only ``data`` and explicit ``inputs`` are migrated. Records, manifest,
    PIDs, native handles and platform identities are intentionally new.
    """
    from . import execution
    source = Path(source_run).expanduser().resolve()
    source_state = manifest(source)
    if variant is not None and variant != source_state.get("variant"):
        raise ValueError("restart cannot change variant")
    observed = execution.observe(source)
    if observed.get("lifecycle") not in {"completed", "failed", "stopped"}:
        execution.control(source, "stop")
        _wait_stopped(source)
    saved = execution.save(source)
    if saved.get("saved") is not True:
        raise RuntimeError(f"source data was not saved: {saved}")
    root = source.parents[1]
    destination = Path(destination_run).expanduser().resolve() if destination_run else None
    if destination is not None and destination.exists():
        raise FileExistsError(destination)
    if destination is not None and destination.parent != source.parent:
        raise ValueError("restart destination must be in the same run registry")
    destination = create_run(
            root, str(source_state["variant"]), target or str(source_state["target"]),
            task or str(source_state["task"]),
            route=route if route is not None else source_state.get("route"),
            competition=competition if competition is not None else bool(source_state.get("competition")),
            source={"run_id": source_state.get("run_id", source.name), "kind": "restart"},
            run_id=destination.name if destination else None,
        )
    destination_paths = paths(destination)
    for key in ("program", "inputs", "workspace", "harness", "records", "snapshots", "evaluations"):
        destination_paths[key].mkdir(parents=True, exist_ok=True)
    data_source = paths(source)["workspace"].parent
    if snapshot:
        candidate = Path(snapshot).expanduser()
        if not candidate.is_absolute():
            candidate = paths(source)["snapshots"] / candidate
        candidate = candidate.resolve(strict=True)
        if not candidate.is_relative_to(paths(source)["snapshots"].resolve()):
            raise ValueError("snapshot must be inside source snapshots")
        data_source = candidate
    _copy_tree(data_source, destination_paths["workspace"].parent)
    same_task = (task is None or task == source_state.get("task")) and (
        task_version is None or task_version == source_state.get("task_version"))
    if same_task:
        _copy_tree(paths(source)["inputs"] / "requirements", destination_paths["inputs"] / "requirements")
    fresh = manifest(destination)
    if target is None or target == source_state.get('target'):
        fresh['target_config'] = source_state.get('target_config')
    if same_task:
        fresh['task_config'] = source_state.get('task_config')
    fresh.update({
        "source_run": source_state.get("run_id", source.name),
        "restart_snapshot": snapshot,
        "task_version": task_version if task_version is not None else source_state.get("task_version") if same_task else None,
        "requirements_version": source_state.get("requirements_version") if same_task else None,
        "native_scope_id": source_state.get("native_scope_id") if same_task else destination.name,
        "native_resume": same_task and source_state.get("native_scope_id") is not None,
        "lifecycle": "starting",
    })
    write_manifest(destination, fresh)
    execution.assemble(destination)
    started = execution.start(destination)
    write_json(destination_paths["records"] / "restart.json", {
        "source_run": str(source), "destination_run": str(destination),
        "saved": saved, "started": started, "created_at": time.time(),
    })
    return {**started, "path": str(destination), "source_run": source.name}
