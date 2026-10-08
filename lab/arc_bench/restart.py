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
            variant: str | None = None, keep_data: bool = False) -> dict[str, Any]:
    """Stop/save a source, then assemble a fresh or data-retained run.

    By default the destination starts from the selected task's normal inputs,
    with a new workspace and native scope. ``keep_data`` explicitly retains
    the historical workspace/native migration contract; records, manifest,
    PIDs and platform identities are always new.
    """
    from . import execution
    source = Path(source_run).expanduser().resolve()
    source_state = manifest(source)
    if snapshot and not keep_data:
        raise ValueError("snapshot requires --keep-data")
    if variant is not None and variant != source_state.get("variant"):
        raise ValueError("restart cannot change variant")
    same_task = (task is None or task == source_state.get("task")) and (
        task_version is None or task_version == source_state.get("task_version"))
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
            route=route if route is not None else source_state.get('route_override') or (
                source_state.get('route') if source_state.get('model_recipe') == 'explicit' else None),
            competition=competition if competition is not None else bool(source_state.get("competition")),
            source={"run_id": source_state.get("run_id", source.name), "kind": "restart",
                    "keep_data": bool(keep_data)},
            run_id=destination.name if destination else None,
        )
    destination_paths = paths(destination)
    for key in ("program", "inputs", "workspace", "harness", "records", "snapshots", "evaluations"):
        destination_paths[key].mkdir(parents=True, exist_ok=True)
    if keep_data:
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
    if same_task:
        _copy_tree(paths(source)["inputs"] / "requirements", destination_paths["inputs"] / "requirements")
        for name in ('initial-application',):
            original = paths(source)['inputs']/name
            if original.is_dir():
                _copy_tree(original, destination_paths['inputs']/name)
        original_tests = paths(source)['inputs'] / 'tests'
        if original_tests.is_dir():
            _copy_tree(original_tests, destination_paths['inputs'] / 'tests')
        for name in ('task-context.md', 'gateway-routes.json', 'model-gateway.json'):
            original = paths(source)['inputs']/name
            if original.is_file():
                shutil.copy2(original, destination_paths['inputs']/name)
    fresh = manifest(destination)
    # A restart rebuilds the program and its runtime from the maintained target.
    # The source's frozen target remains authoritative only for its stop/save.
    if same_task:
        fresh['task_config'] = dict(source_state.get('task_config') or {})
        fresh['task_config']['requirements'] = str(destination_paths['inputs'] / 'requirements')
        for field, name in (('initial_application', 'initial-application'), ('task_context', 'task-context.md')):
            if (destination_paths['inputs']/name).exists():
                fresh['task_config'][field] = str(destination_paths['inputs']/name)
        for entry in fresh['task_config'].get('evaluations') or []:
            if not isinstance(entry, dict) or not entry.get('tests'):
                continue
            tests = Path(str(entry['tests'])).expanduser()
            if tests == paths(source)['inputs'] / 'tests':
                entry['tests'] = str(destination_paths['inputs'] / 'tests')
        fresh['model_recipe'] = source_state.get('model_recipe')
        fresh['model_routes'] = source_state.get('model_routes')
        if route is None and (source_state.get('model_recipe') == 'explicit' or
                              source_state.get('route_override')):
            route_input = destination_paths['inputs'] / 'gateway-routes.json'
            if route_input.is_file():
                fresh['route'] = str(route_input)
                fresh['route_override'] = str(route_input)
    fresh.update({
        "source_run": source_state.get("run_id", source.name),
        "restart_snapshot": snapshot,
        "task_version": task_version if task_version is not None else source_state.get("task_version") if same_task else None,
        "requirements_version": source_state.get("requirements_version") if same_task else None,
        "native_scope_id": source_state.get("native_scope_id") if keep_data and same_task else destination.name,
        "native_resume": keep_data and same_task and source_state.get("native_scope_id") is not None,
        "lifecycle": "starting",
    })
    if fresh['native_resume']:
        write_json(destination_paths['inputs']/'native-resume.json', {
            'kind': 'lab.native-resume', 'source_run': source.name,
            'native_scope_id': fresh['native_scope_id'],
            'requirements_version': fresh['requirements_version'],
            'source_lifecycle': execution.observe(source).get('lifecycle'),
            'saved': saved, 'created_at': time.time()})
    write_manifest(destination, fresh)
    execution.assemble(destination)
    started = execution.start(destination)
    write_json(destination_paths["records"] / "restart.json", {
        "source_run": str(source), "destination_run": str(destination),
        "saved": saved, "started": started, "created_at": time.time(),
        "keep_data": bool(keep_data),
    })
    return {**started, "path": str(destination), "source_run": source.name}
