"""Restart one run without inheriting its process or platform identity."""

from __future__ import annotations

import json
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
            variant: str | None = None, keep_data: bool = False,
            allow_route_change: bool = False, route_change_reason: str | None = None,
            model_catalog: str | None = None) -> dict[str, Any]:
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
    i15_resume = keep_data and same_task and source_state.get('variant') == 'pi-braid-i15-reviewer-cleaner-e2e' and source_state.get('native_scope_id') is not None
    route_change = None
    catalog_override = None
    substitution = None
    if model_catalog is not None:
        target_config = source_state.get('target_config') or {}
        if not (i15_resume and allow_route_change and route is not None and
                target_config.get('kind') == 'local' and not source_state.get('competition')):
            raise ValueError('显式catalog仅支持本地自费I15授权原生模型替换')
        catalog_override = Path(model_catalog).expanduser().resolve(strict=True)
        supplied_catalog = json.loads(catalog_override.read_text())
        substitution = supplied_catalog.get('native_model_substitution')
        if not isinstance(substitution, dict) or substitution.get('text_alias') != 'glm-5.3-flash' or substitution.get('actual_text_model') != 'glm-5.3' or substitution.get('vision_alias') != 'i15-local-vision-flash':
            raise ValueError('catalog缺少明确的本轮Flash至GLM5.3/独立视觉替换声明')
        source_catalog = json.loads((paths(source)['inputs']/'model-gateway.json').read_text())
        allowed_connections = {(r['litellm_params']['api_base'],r['litellm_params']['api_key']) for r in source_catalog['model_list']}
        for row in supplied_catalog['model_list']:
            params = row['litellm_params']
            if (params['api_base'], params['api_key']) not in allowed_connections:
                raise ValueError('临时模型替换不能引入来源未配置的供应商连接')
    if allow_route_change and (not i15_resume or route is None or not route_change_reason or not route_change_reason.strip()):
        raise ValueError('授权路由变更需要I15同scope原生恢复、显式route及具体原因')
    if i15_resume and route is not None:
        frozen = json.loads((paths(source)['inputs']/'gateway-routes.json').read_text())
        supplied = json.loads(Path(route).expanduser().resolve(strict=True).read_text())
        for alias, chain in frozen.items():
            native_alias = 'deepseek-v4-flash-0731' if alias == 'deepseek-v4-flash' else alias
            if supplied.get(alias, supplied.get(native_alias)) != chain:
                if not allow_route_change:
                    raise ValueError('I15原生恢复默认保留冻结路由；变更需要--allow-route-change及原因')
        if supplied != frozen and allow_route_change:
            if set(supplied) != set(frozen) and catalog_override is None:
                raise ValueError('原生恢复路由变更不能改变模型alias集合')
            from tooling.scripts.hackathon_gateway import prepare_catalog
            prepare_catalog(catalog_override or paths(source)['inputs']/'model-gateway.json', supplied, aliases=list(supplied))
            route_change = {'authorized_by': 'user', 'reason': route_change_reason,
                            'old_routes': frozen, 'new_routes': supplied,
                            'changed_aliases': [alias for alias in sorted(set(frozen) | set(supplied)) if frozen.get(alias) != supplied.get(alias)],
                            'native_model_substitution': substitution}
    observed = execution.observe(source)
    if observed.get("lifecycle") not in {"completed", "failed", "stopped"}:
        execution.control(source, "stop")
        _wait_stopped(source)
    remote_data = None
    if i15_resume and not snapshot:
        from . import local_run
        destination_target = execution._target({"target": target or source_state["target"],
                                                "variant": source_state["variant"]})
        remote_data = local_run.saved_restart_source(source, destination_target)
    saved = remote_data["saved"] if remote_data else execution.save(source)
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
    if keep_data and not remote_data:
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
    if remote_data:
        fresh["remote_restart_data"] = remote_data
        # Route-change validation consumes this small native metadata locally;
        # the complete application/native state stays saved on the source host.
        from . import local_run
        scope = str(fresh["native_scope_id"])
        remote_routing = Path(remote_data["remote_run"]) / "data/harness" / scope / "routing-snapshot.json"
        exists = local_run._remote_exec(remote_data["executor"], ["test", "-f", str(remote_routing)])
        if exists.returncode == 0:
            if not local_run._remote_file(remote_data["executor"], remote_routing,
                                         destination_paths["harness"] / scope / "routing-snapshot.json"):
                raise RuntimeError("saved native routing snapshot could not be recovered")
        elif exists.returncode != 1:
            raise RuntimeError(f"saved native routing lookup failed: {exists.stderr}")
    if fresh['native_resume']:
        write_json(destination_paths['inputs']/'native-resume.json', {
            'kind': 'lab.native-resume', 'source_run': source.name,
            'native_scope_id': fresh['native_scope_id'],
            'requirements_version': fresh['requirements_version'],
            'source_lifecycle': execution.observe(source).get('lifecycle'),
            'saved': saved, 'created_at': time.time()})
    if catalog_override is not None:
        shutil.copy2(catalog_override, destination_paths['inputs']/'authorized-model-catalog.json')
    if route_change is not None:
        fresh['route_override'] = str(Path(route).expanduser().resolve(strict=True))
        fresh['native_route_change'] = route_change
    write_manifest(destination, fresh)
    execution.assemble(destination)
    started = execution.start(destination)
    write_json(destination_paths["records"] / "restart.json", {
        "source_run": str(source), "destination_run": str(destination),
        "saved": saved, "started": started, "created_at": time.time(),
        "keep_data": bool(keep_data),
    })
    return {**started, "path": str(destination), "source_run": source.name}
