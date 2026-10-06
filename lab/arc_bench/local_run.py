"""Small Docker executor for current ARC runs.

The host assembles with the official SDK, then the target host owns the
container.  Container identity is persisted before start; later operations
use that exact CID and never signal the SSH process.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, is_dataclass
from decimal import Decimal
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from zipfile import ZIP_DEFLATED, ZipFile
from types import SimpleNamespace
from typing import Any, Mapping

try:
    from .run_layout import manifest, paths, write_json
except ImportError:  # The same file is copied as the standalone remote worker.
    def write_json(path: str | os.PathLike[str], value: Mapping[str, Any]) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _target(run: Path) -> dict[str, Any]:
    value = manifest(run).get("target_config") or {}
    if not isinstance(value, dict):
        raise ValueError("target_config must be an object")
    return value


def _remote(run: Path, target: Mapping[str, Any]) -> tuple[str, Path]:
    host = target.get("executor")
    root = target.get("remote_root")
    if not isinstance(host, str) or not host or not isinstance(root, str) or not root.startswith("/"):
        raise ValueError("remote Docker target needs executor and absolute remote_root")
    return host, Path(root) / "runs" / run.name


def _sdk(target: Mapping[str, Any]) -> Path:
    source = target.get("sdk_source")
    if not source:
        raise ValueError("ARC target needs sdk_source")
    source = Path(source).expanduser().resolve(strict=True)
    if not (source / "local_submit.py").is_file():
        raise ValueError(f"official SDK local_submit.py missing: {source}")
    return source


def _agent(run: Path, target: Mapping[str, Any]) -> Path:
    if manifest(run).get("run_kind") == "evaluation":
        destination = paths(run)["inputs"] / "arc-noop.zip"
        if not destination.is_file():
            source = Path(__file__).with_name("arc_bench_noop.py")
            artifacts = Path(__file__).with_name("arc_artifacts.py")
            with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
                archive.write(source, "main.py")
                archive.write(artifacts, "arc_artifacts.py")
                archive.writestr("requirements.txt", "")
        return destination
    value = target.get("agent_package") or manifest(run).get("agent_package")
    if value:
        return Path(value).expanduser().resolve(strict=True)
    program = paths(run)["program"]
    if not (program / "main.py").is_file() or not (program / "requirements.txt").is_file():
        raise ValueError("generation target needs agent_package or program main.py+requirements.txt")
    return program


def _requirements(run: Path) -> Path:
    value = paths(run)["inputs"] / "requirements"
    if not (value / "requirements.yaml").is_file():
        raise ValueError(f"requirements.yaml missing: {value}")
    return value


def _sdk_module(target: Mapping[str, Any]):
    sdk = _sdk(target)
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("factory26_official_local_submit", sdk / "local_submit.py")
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load official SDK: {sdk}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prepare_workspace(run: Path, target: Mapping[str, Any]) -> Path:
    sdk = _sdk(target)
    module = _sdk_module(target)
    output = paths(run)["inputs"] / "sdk-workspace"
    if output.exists() and any(output.iterdir()):
        return output
    state = manifest(run)
    task_config = state.get("task_config") if isinstance(state.get("task_config"), dict) else {}
    raw_task = str(task_config.get("platform_task") or state.get("task") or "")
    task = raw_task.rsplit("--", 1)[-1]
    competition = "public-practice" if task == "bookstack" else "hackathon"
    evaluation = state.get("run_kind") == "evaluation"
    args = SimpleNamespace(
        data_root=str(paths(run)["inputs"]), competition=competition, task=task,
        requirements_dir=str(_requirements(run)),
        tests_dir=str(paths(run)["inputs"] / "tests") if evaluation and (paths(run)["inputs"] / "tests").is_dir() else None,
        workspace=str(output), agent=str(_agent(run, target)),
        template=str(paths(run)["inputs"] / "application") if evaluation and (paths(run)["inputs"] / "application").is_dir() else None,
        image=str(target["image_id"]), run_as_root=True, memory=str(target.get("memory", "2g")),
        cpus=str(target.get("cpus", "1")), env_file=None,
        meter_base_url=None,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    module.assemble_workspace(args)
    write_json(paths(run)["records"] / "assembly.json", {
        "sdk_source": str(sdk), "sdk_local_submit": str(sdk / "local_submit.py"),
        "workspace": str(output), "prepared_at": time.time(), "mode": "official-sdk-prepare-only"})
    return output


def _meter(run: Path, target: Mapping[str, Any], phase: str, *, wait: bool = False,
           query_start: int | None = None) -> dict[str, Any]:
    """Capture shared access-key meter facts; never relabel them as per-run cost."""
    destination = paths(run)["records"] / f"meter-{phase}.json"
    source = target.get("environment_file") or target.get("private_env_file")
    result: dict[str, Any] = {"phase": phase, "scope": "account-key-window", "as_of": time.time()}
    if not source:
        result.update(status="unknown", reason="no_meter_environment_file")
        write_json(destination, result)
        return result
    values = {}
    for line in Path(source).expanduser().resolve(strict=True).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    key = values.get("OPENAI_API_KEY") or values.get("FACTORY26_API_KEY")
    if not key:
        result.update(status="unknown", reason="no_meter_key")
        write_json(destination, result)
        return result
    try:
        sdk = _sdk_module(target)
        if "SSL_CERT_FILE" not in os.environ:
            try:
                import certifi
                os.environ["SSL_CERT_FILE"] = certifi.where()
            except ImportError:
                pass
        base_url = target.get("meter_base_url") or values.get("ARCBENCH_METER_BASE_URL") or sdk.DEFAULT_METER_BASE_URL
        client = sdk.MeterUsageClient(str(base_url), key)
        snapshot = client.capture(wait_for_settlement=wait, query_start=query_start)
        raw = asdict(snapshot) if is_dataclass(snapshot) else vars(snapshot)
        raw["total_cost"] = str(raw.get("total_cost"))
        result.update(status="captured", raw=raw)
    except Exception as error:
        result.update(status="unknown", error=f"{type(error).__name__}: {error}")
    write_json(destination, result)
    return result


def _spend(run: Path, target: Mapping[str, Any], lifecycle: str) -> dict[str, Any]:
    baseline_path = paths(run)["records"] / "meter-baseline.json"
    terminal_path = paths(run)["records"] / "meter-terminal.json"
    current_path = paths(run)["records"] / "meter-current.json"
    baseline = json.loads(baseline_path.read_text()) if baseline_path.is_file() else None
    terminal = json.loads(terminal_path.read_text()) if terminal_path.is_file() else None
    current = json.loads(current_path.read_text()) if current_path.is_file() else None
    if lifecycle in {"running", "paused", "starting"} and (current is None or time.time() - current.get("as_of", 0) >= float(target.get("meter_interval_seconds", 300))):
        current = _meter(run, target, "current")
    if lifecycle in {"completed", "failed", "stopped"} and terminal is None:
        query_start = ((baseline or {}).get("raw") or {}).get("query_start")
        terminal = _meter(run, target, "terminal", wait=True, query_start=query_start)
    result = {"scope": "account-key-window", "status": "unknown", "baseline": baseline,
              "current": current, "terminal": terminal, "as_of": time.time()}
    end = terminal or current
    if baseline and end and baseline.get("status") == end.get("status") == "captured":
        try:
            sdk = _sdk_module(target)
            start_raw, end_raw = baseline["raw"], end["raw"]
            start = sdk.MeterUsageSnapshot(start_raw["access_key_id"], int(start_raw["total_tokens"]),
                                            Decimal(start_raw["total_cost"]), start_raw["currency"],
                                            int(start_raw["query_start"]))
            end = sdk.MeterUsageSnapshot(end_raw["access_key_id"], int(end_raw["total_tokens"]),
                                          Decimal(end_raw["total_cost"]), end_raw["currency"],
                                          int(end_raw["query_start"]))
            delta = sdk.MeterUsageClient.delta(start, end)
            raw_delta = asdict(delta)
            raw_delta["cost"] = str(raw_delta.get("cost"))
            result.update(status="captured", raw_delta=raw_delta,
                          value=raw_delta.get("cost"), currency=raw_delta.get("currency"),
                          kind="meter.usage.delta",
                          source={"baseline": "meter-baseline.json",
                                  "end": "meter-terminal.json" if terminal else "meter-current.json"},
                          note="shared access-key window delta; not exact per-run cost")
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"
    return result


def _public_inspect(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    state = value.get("State") if isinstance(value.get("State"), dict) else {}
    config = value.get("Config") if isinstance(value.get("Config"), dict) else {}
    return {"Id": value.get("Id"), "Name": value.get("Name"), "Image": value.get("Image"),
            "State": {key: state.get(key) for key in ("Status", "Running", "Paused", "ExitCode", "StartedAt", "FinishedAt")},
            "Labels": config.get("Labels") if isinstance(config.get("Labels"), dict) else {}}


def _stage_app(run: Path, sdk_workspace: Path) -> Path:
    """Make data/workspace the application/template tree, not SDK scaffolding."""
    app = paths(run)["workspace"]
    if manifest(run).get("run_kind") == "evaluation":
        app.mkdir(parents=True, exist_ok=True)
        return app
    template = sdk_workspace / "template"
    app.mkdir(parents=True, exist_ok=True)
    if not any(app.iterdir()):
        shutil.copytree(template, app, dirs_exist_ok=True)
    else:
        for name in ("requirements", ".arc"):
            source = template / name
            if source.exists():
                shutil.copytree(source, app / name, dirs_exist_ok=True)
    return app


def _remote_exec(host: str, command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    if host == "local":
        return subprocess.run(command, text=True, capture_output=True, check=check)
    return subprocess.run(["ssh", host, shlex.join(command)], text=True, capture_output=True, check=check)


def _verify_remote_sdk(host: str, target: Mapping[str, Any]) -> None:
    source = target.get("remote_sdk_source")
    if not source:
        return
    result = _remote_exec(host, ["test", "-f", f"{source}/local_submit.py"])
    if result.returncode:
        raise RuntimeError(f"remote official SDK missing: {source}: {result.stderr.strip()}")


def _sync(host: str, source: Path, destination: str) -> None:
    if host == "local":
        destination_path = Path(destination)
        if source.resolve() == destination_path.resolve():
            return
        destination_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination_path, dirs_exist_ok=True)
        return
    subprocess.run(["ssh", host, shlex.join(["mkdir", "-p", destination])], check=True)
    subprocess.run(["rsync", "-a", str(source) + "/", f"{host}:{destination}/"], check=True)


def _remote_file(host: str, path: Path, local: Path) -> bool:
    if host == "local":
        if not path.is_file():
            return False
        local.parent.mkdir(parents=True, exist_ok=True)
        if path.resolve() == local.resolve():
            return True
        shutil.copy2(path, local)
        return True
    local.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["rsync", "-a", f"{host}:{path}", str(local)], check=False,
                            text=True, capture_output=True)
    return result.returncode == 0 and local.is_file()


def _copy_file(host: str, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True) if host == "local" else None
    if host == "local":
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        return
    subprocess.run(["rsync", "-a", str(source), f"{host}:{destination}"], check=True)


def _stage_private_env(host: str, target: Mapping[str, Any], remote_run: Path) -> Path | None:
    source = target.get("environment_file") or target.get("private_env_file")
    if not source:
        return None
    source = Path(source).expanduser().resolve(strict=True)
    if host == "local":
        return source
    names = {line.split("=", 1)[0].strip() for line in source.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#") and "=" in line}
    if not names & {"FACTORY26_API_KEY", "OPENAI_API_KEY"}:
        raise ValueError(f"private environment has no supported API key variable: {source}")
    original = remote_run / ".private-source.env"
    mapped = remote_run / ".private.env"
    subprocess.run(["rsync", "-a", str(source), f"{host}:{original}"], check=True)
    command = ("awk -F= '$1==\"FACTORY26_API_KEY\" {print; print \"OPENAI_API_KEY=\" $2; next} {print}' "
               f"{shlex.quote(str(original))} > {shlex.quote(str(mapped))} && "
               f"chmod 600 {shlex.quote(str(mapped))}")
    result = _remote_exec(host, ["sh", "-c", command], check=True)
    return mapped


def _push_remote_manifest(run: Path, host: str, remote_run: Path, target: Mapping[str, Any]) -> None:
    """Publish a remote-safe manifest without leaking Mac material paths."""
    if host == "local":
        return
    value = json.loads(json.dumps(manifest(run)))
    observability = value.get("observability") if isinstance(value.get("observability"), dict) else {}
    for field in ("registration_token_file", "collector_token_file"):
        source_value = observability.get(field)
        if source_value:
            source = Path(source_value).expanduser()
            if source.is_file():
                destination = remote_run / ".private" / source.name
                _push_private_file(host, source.resolve(), destination)
                observability[field] = str(destination)
    if observability:
        value["observability"] = observability
    local_root = str(run)

    def relocate(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: relocate(child) for key, child in item.items()}
        if isinstance(item, list):
            return [relocate(child) for child in item]
        if isinstance(item, str):
            if item == local_root or item.startswith(local_root + "/"):
                return str(remote_run) + item[len(local_root):]
            if item.startswith("/Volumes/WorkSSD/"):
                return None
        return item

    value = relocate(value)
    remote_target = dict(value.get("target_config") or {})
    if target.get("remote_sdk_source"):
        remote_target["sdk_source"] = target["remote_sdk_source"]
    remote_target["executor"] = "local"
    remote_target["remote_root"] = str(remote_run.parent.parent)
    remote_target["environment_file"] = str(remote_run / ".private.env")
    for key in ("runtime", "skills"):
        candidate = remote_run / "data" / "sdk-workspace" / "submission" / key
        if _remote_exec(host, ["test", "-d", str(candidate)]).returncode == 0:
            remote_target[key] = str(candidate)
        else:
            remote_target.pop(key, None)
    remote_target.pop("agent_package", None)
    value["target_config"] = remote_target
    encoded = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()).decode()
    _remote_exec(host, ["sh", "-c", f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(str(remote_run / 'manifest.json'))}"], check=True)


def _push_private_file(host: str, source: Path, destination: Path) -> None:
    _remote_exec(host, ["mkdir", "-p", str(destination.parent)], check=True)
    if host == "local":
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
    else:
        subprocess.run(["rsync", "-a", str(source), f"{host}:{destination}"], check=True)
    _remote_exec(host, ["chmod", "600", str(destination)], check=True)


def _push_remote_registry(host: str, remote_run: Path, current_target: Mapping[str, Any]) -> None:
    source = Path(__file__).with_name("targets.json")
    value = json.loads(source.read_text())
    project = str(Path(__file__).resolve().parents[2])
    third_party_remote = str(remote_run / "source/third_party")
    task_inputs_remote = remote_run / "source/task-inputs"

    def relocate(item: Any, key: str | None = None) -> Any:
        if isinstance(item, dict):
            return {name: relocate(child, name) for name, child in item.items()}
        if isinstance(item, list):
            return [relocate(child, key) for child in item]
        if isinstance(item, str):
            if key in {"runtime", "skills"} and item.startswith("/Volumes/WorkSSD/"):
                return str(remote_run / "data/sdk-workspace/submission" / key)
            if item.startswith(project + "/third_party/"):
                return third_party_remote + item[len(project + "/third_party"):]
            if item.startswith("/Volumes/WorkSSD/"):
                if key == "sdk_source":
                    return "/home/yyh/factory26-lab-sdk"
                if key == "environment_file":
                    return str(remote_run / ".private.env")
                if key and ("token" in key.lower() or "observ" in key.lower()):
                    candidate = Path(item)
                    if candidate.is_file():
                        destination = remote_run / ".private" / candidate.name
                        _push_private_file(host, candidate, destination)
                        return str(destination)
                return None
        return item

    tasks = value.get("tasks") if isinstance(value.get("tasks"), dict) else {}
    for alias, entry in tasks.items():
        if not isinstance(entry, dict):
            continue
        for field in ("requirements", "tests"):
            source_value = entry.get(field)
            if not source_value:
                continue
            source_path = Path(source_value).expanduser().resolve(strict=True)
            destination = task_inputs_remote / alias / field
            _sync(host, source_path, str(destination))
            entry[field] = str(destination)

    current_executor = current_target.get("executor")
    for entry in (value.get("targets") or {}).values():
        if isinstance(entry, dict) and entry.get("executor") in {host, current_executor}:
            entry["executor"] = "local"
            entry["remote_root"] = str(remote_run.parent.parent)

    value = relocate(value)
    encoded = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()).decode()
    _remote_exec(host, ["sh", "-c", f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(str(remote_run / 'source/lab/arc_bench/targets.json'))}"], check=True)


def _deploy_helper(host: str, remote_run: Path) -> Path:
    helper = remote_run / "local_run_remote.py"
    # Keep the remote closure beside the run, so its exact bytes travel with the run.
    source = Path(__file__).resolve()
    _remote_exec(host, ["mkdir", "-p", str(remote_run)])
    if host == "local":
        shutil.copy2(source, helper)
        return helper
    subprocess.run(["rsync", "-a", str(source), f"{host}:{helper}"], check=True)
    return helper


def _helper(host: str, remote_run: Path, phase: str, config: Mapping[str, Any]) -> subprocess.CompletedProcess[str]:
    helper = _deploy_helper(host, remote_run)
    payload = json.dumps(dict(config), ensure_ascii=False, separators=(",", ":"))
    return _remote_exec(host, ["python3", str(helper), phase, payload])


def _container_name(run: Path) -> str:
    return "factory26-" + "".join(c if c.isalnum() or c in "-_" else "-" for c in run.name)[:50]


def _create_argv(run: Path, target: Mapping[str, Any], remote_run: Path, workspace: Path,
                 private_env: Path | None = None, native_scope: str | None = None,
                 image_id: str | None = None) -> list[str]:
    name = _container_name(run)
    argv = ["create", "--init", "--name", name,
            "--label", "io.factory26.managed=true", "--label", f"io.factory26.run={run.name}",
            "--mount", f"type=bind,source={remote_run / 'data/sdk-workspace'},target=/workspace",
            "--mount", f"type=bind,source={remote_run / 'data/workspace'},target=/workspace/template",
            "--memory", str(target.get("memory", "2g")), "--cpus", str(target.get("cpus", "1"))]
    if native_scope:
        argv += ["--mount", f"type=bind,source={remote_run / 'data/harness'},"
                 "target=/workspace/template/.factory26/data/harness"]
    env_file = private_env
    if env_file:
        argv += ["--env-file", str(env_file)]
    for key, value in (target.get("environment") or {}).items():
        if isinstance(key, str) and isinstance(value, str):
            argv += ["--env", f"{key}={value}"]
    argv.append(str(image_id or target["image_id"]))
    return argv


def _resolve_remote_image(host: str, target: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    requested = str(target["image_id"])
    checked = _remote_exec(host, ["docker", "image", "inspect", requested, "--format", "{{.Id}}"])
    if checked.returncode == 0 and checked.stdout.strip():
        return requested, {"requested": requested, "resolved": requested, "mode": "requested"}
    raise RuntimeError(f"target image unavailable with exact requested image ID {requested}: {checked.stderr.strip()}")


def assemble(run: str | os.PathLike[str]) -> dict[str, Any]:
    run = Path(run).expanduser().resolve()
    target = _target(run)
    simulation = manifest(run).get("run_kind") == "evaluation" and manifest(run).get("evaluation_kind") == "simulate"
    if simulation:
        host, remote_run = _remote(run, target)
        _remote_exec(host, ["mkdir", "-p", str(remote_run / "data/workspace"), str(remote_run / "inputs"), str(remote_run / "records")], check=True)
        _sync(host, paths(run)["workspace"], str(remote_run / "data/workspace"))
        _sync(host, paths(run)["inputs"], str(remote_run / "inputs"))
        return {"run": str(run), "app": str(paths(run)["workspace"]), "remote_run": str(remote_run),
                "executor": host, "image_id": None, "status": "prepared", "mode": "simulate"}
    workspace = _prepare_workspace(run, target)
    app = _stage_app(run, workspace)
    host, remote_run = _remote(run, target)
    _verify_remote_sdk(host, target)
    _sync(host, workspace, str(remote_run / "data/sdk-workspace"))
    _sync(host, app, str(remote_run / "data/workspace"))
    _remote_exec(host, ["mkdir", "-p", str(remote_run / "data/harness"), str(remote_run / "records")], check=True)
    harness = paths(run)["harness"]
    if harness.is_dir():
        _sync(host, harness, str(remote_run / "data/harness"))
    return {"run": str(run), "workspace": str(workspace), "app": str(app), "remote_run": str(remote_run),
            "executor": host, "image_id": target.get("image_id"), "status": "prepared"}


def start(run: str | os.PathLike[str]) -> dict[str, Any]:
    run = Path(run).expanduser().resolve()
    target = _target(run)
    identity = paths(run)["records"] / "docker.json"
    if identity.is_file():
        raise RuntimeError("Docker identity already exists; refusing a second container for this run")
    prepared = assemble(run)
    host, remote_run = _remote(run, target)
    if prepared.get("mode") == "simulate":
        config = manifest(run).get("evaluation", {})
        argv = config.get("argv") or config.get("command")
        if not isinstance(argv, list) or not argv:
            raise RuntimeError("simulate evaluation requires evaluation.argv")
        argv = [str(item).replace("{run}", str(remote_run)).replace("{workspace}", str(remote_run / "data/workspace"))
                for item in argv]
        payload = json.dumps({"remote_run": str(remote_run), "argv": argv}, separators=(",", ":"))
        helper = _deploy_helper(host, remote_run)
        command = "cd {root} && nohup python3 {helper} simulate {payload} > {log} 2>&1 &".format(
            root=shlex.quote(str(remote_run)), helper=shlex.quote(str(helper)), payload=shlex.quote(payload),
            log=shlex.quote(str(remote_run / "records/simulation-worker.log")))
        _remote_exec(host, ["sh", "-c", command], check=True)
        return {"lifecycle": "running", "executor": host, "remote_run": str(remote_run),
                "started_at": time.time(), "mode": "simulate"}
    private_env = _stage_private_env(host, target, remote_run)
    if not (paths(run)["records"] / "meter-baseline.json").is_file():
        _meter(run, target, "baseline")
    scope = manifest(run).get("native_scope_id")
    image_id, image_resolution = _resolve_remote_image(host, target)
    write_json(paths(run)["records"] / "image-resolution.json", image_resolution)
    config = {"remote_run": str(remote_run), "container_id": None,
              "container_name": _container_name(run), "run_id": run.name,
              "run_kind": manifest(run).get("run_kind", "generation"),
              "create_argv": _create_argv(run, target, remote_run, Path(prepared["workspace"]), private_env, scope, image_id)}
    created = _helper(host, remote_run, "create", config)
    try:
        value = json.loads(created.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        value = {"phase": "create", "exit_code": created.returncode,
                 "stdout": created.stdout, "stderr": created.stderr}
    write_json(paths(run)["records"] / "docker-create.json", value)
    cid = value.get("container_id")
    if not cid:
        return {"lifecycle": "unknown", "container_id": None, "exit_code": value.get("exit_code"),
                "daemon_id": value.get("daemon_id"), "as_of": time.time()}
    write_json(paths(run)["records"] / "docker.json", {
        "container_id": cid, "container_name": _container_name(run), "executor": host,
        "remote_run": str(remote_run), "image_id": image_id, "requested_image_id": target["image_id"],
        "daemon_id": value.get("daemon_id"), "created_at": time.time()})
    config["container_id"] = cid
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    helper = remote_run / "local_run_remote.py"
    command = "cd {root} && nohup python3 {helper} run {payload} > {log} 2>&1 &".format(
        root=json.dumps(str(remote_run)), helper=json.dumps(str(helper)),
        payload=shlex.quote(payload), log=json.dumps(str(remote_run / "records/docker-worker.log")))
    _remote_exec(host, ["sh", "-c", command], check=True)
    return {"lifecycle": "running", "container_id": cid, "container_name": _container_name(run),
            "executor": host, "remote_run": str(remote_run), "started_at": time.time()}


def spawn(run: str | os.PathLike[str], module: str, args: list[str] | tuple[str, ...],
          name: str, script: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Start a detached observer/automation process on the Docker host.

    The returned PID is only a remote-process receipt; lifecycle truth remains
    the Docker CID and records written by that process.  ``script`` may be a
    source path or source text; module execution is otherwise used directly.
    """
    run = Path(run).expanduser().resolve()
    target = _target(run)
    host, remote_run = _remote(run, target)
    safe = "".join(char if char.isalnum() or char in "-_" else "-" for char in name)
    if not safe:
        raise ValueError("spawn name must not be empty")
    remote_dir = remote_run / "automation"
    remote_script = remote_dir / f"{safe}.py"
    log = remote_dir / f"{safe}.log"
    _remote_exec(host, ["mkdir", "-p", str(remote_dir)], check=True)
    _remote_exec(host, ["mkdir", "-p", str(remote_run / "inputs")], check=True)
    _remote_exec(host, ["mkdir", "-p", str(remote_run / "records")], check=True)
    _push_remote_manifest(run, host, remote_run, target)
    baseline = paths(run)["records"] / "meter-baseline.json"
    if baseline.is_file():
        _copy_file(host, baseline, remote_run / "records/meter-baseline.json")
    _sync(host, paths(run)["inputs"], str(remote_run / "inputs"))
    _sync(host, paths(run)["program"], str(remote_run / "program"))
    repository = Path(__file__).resolve().parents[2]
    _sync(host, repository / "lab", str(remote_run / "source/lab"))
    _sync(host, repository / "scripts", str(remote_run / "source/scripts"))
    _sync(host, repository / "variants", str(remote_run / "source/variants"))
    _sync(host, repository / "harness", str(remote_run / "source/harness"))
    _sync(host, repository / "third_party/arc-bench", str(remote_run / "source/third_party/arc-bench"))
    _push_remote_registry(host, remote_run, target)
    if script is not None:
        source = Path(script).expanduser()
        try:
            source_file = source.is_file()
        except OSError:
            source_file = False
        if source_file:
            if host == "local":
                shutil.copy2(source, remote_script)
            else:
                subprocess.run(["rsync", "-a", str(source), f"{host}:{remote_script}"], check=True)
        else:
            encoded = base64.b64encode(str(script).encode()).decode()
            command = f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(str(remote_script))}"
            _remote_exec(host, ["sh", "-c", command], check=True)
        argv = ["python3", str(remote_script)]
    else:
        candidate = Path(module).expanduser() if module.endswith(".py") or "/" in module else None
        if candidate is not None and candidate.is_file():
            if host == "local":
                shutil.copy2(candidate, remote_script)
            else:
                subprocess.run(["rsync", "-a", str(candidate), f"{host}:{remote_script}"], check=True)
            argv = ["python3", str(remote_script)]
        else:
            argv = ["python3", "-m", module]
    remote_args = []
    local_root = str(run)
    for value in args:
        text = str(value)
        remote_args.append(str(remote_run) + text[len(local_root):] if text == local_root or text.startswith(local_root + "/") else text)
    argv.extend(remote_args)
    pythonpath = f"{remote_dir}:{remote_run / 'source'}:{remote_run / 'data/sdk-workspace/submission'}"
    command = "cd {root} && LAB_RUN={root} LAB_RUN_ROOT={run_root} PYTHONPATH={pythonpath} nohup {argv} > {log} 2>&1 < /dev/null & echo $!".format(
        root=shlex.quote(str(remote_run)), run_root=shlex.quote(str(remote_run.parent.parent)),
        pythonpath=shlex.quote(pythonpath),
        argv=" ".join(shlex.quote(value) for value in argv),
        log=shlex.quote(str(log)))
    result = _remote_exec(host, ["sh", "-c", command], check=True)
    pid = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else None
    receipt = {"name": safe, "module": module, "pid": pid, "executor": host,
               "remote_run": str(remote_run), "script": str(remote_script) if script is not None else None,
               "log": str(log), "started_at": time.time(), "stderr": result.stderr}
    write_json(paths(run)["records"] / f"spawn-{safe}.json", receipt)
    return receipt


def observe(run: str | os.PathLike[str]) -> dict[str, Any]:
    run = Path(run).expanduser().resolve()
    target = _target(run)
    host, remote_run = _remote(run, target)
    local_records = paths(run)["records"]
    simulation = local_records / "simulation-result.json"
    if host == "local" and simulation.is_file():
        value = json.loads(simulation.read_text())
        return {"lifecycle": "completed", "evaluation": value, "observed_at": time.time(),
                "spend": _spend(run, target, "completed")}
    if not simulation.is_file():
        _remote_file(host, remote_run / "records/simulation-result.json", simulation)
    if simulation.is_file():
        value = json.loads(simulation.read_text())
        return {"lifecycle": "completed", "evaluation": value, "observed_at": time.time(),
                "spend": _spend(run, target, "completed")}
    identity = local_records / "docker.json"
    if identity.is_file():
        handle = json.loads(identity.read_text())
        observed = _helper(host, remote_run, "observe", {"remote_run": str(remote_run),
                                                          "container_id": handle["container_id"]})
        if observed.returncode and observed.stderr:
            return {"lifecycle": "unknown", "container_id": handle.get("container_id"),
                    "observation_error": observed.stderr, "observed_at": time.time()}
    _remote_file(host, remote_run / "records/docker-observe.json", local_records / "docker-observe.json")
    _remote_file(host, remote_run / "records/docker-result.json", local_records / "docker-result.json")
    _remote_file(host, remote_run / "records/docker-start.json", local_records / "docker-start.json")
    for name in ("docker.stdout.log", "docker.stderr.log"):
        _remote_file(host, remote_run / "records" / name, local_records / name)
    result = local_records / "docker-result.json"
    if result.is_file():
        value = json.loads(result.read_text())
        live_value = json.loads((local_records / "docker-observe.json").read_text()) if (local_records / "docker-observe.json").is_file() else {}
        lifecycle = value.get("lifecycle", "unknown")
        return {"lifecycle": lifecycle, "container_id": value.get("container_id"),
                "exit_code": value.get("exit_code"), "resources": {"inspect": _public_inspect(value.get("inspect")),
                "live": live_value.get("resources")},
                "stderr": value.get("error"), "spend": _spend(run, target, lifecycle), "observed_at": time.time()}
    live = local_records / "docker-observe.json"
    if live.is_file():
        value = json.loads(live.read_text())
        value["inspect"] = _public_inspect(value.get("inspect"))
        value["spend"] = _spend(run, target, value.get("lifecycle", "unknown"))
        return {**value, "observed_at": time.time()}
    handle = json.loads(identity.read_text()) if identity.is_file() else {}
    if not handle and (local_records / "docker-create.json").is_file():
        return {"lifecycle": "unknown", "container_id": None, "executor": host,
                "observed_at": time.time(), "remote_run": str(remote_run),
                "error": "create response had no verified container identity",
                "spend": _spend(run, target, "unknown")}
    return {"lifecycle": "starting", "container_id": handle.get("container_id"),
            "executor": host, "observed_at": time.time(), "remote_run": str(remote_run),
            "spend": _spend(run, target, "starting")}


def control(run: str | os.PathLike[str], action: str) -> dict[str, Any]:
    if action not in {"pause", "resume", "stop"}:
        raise ValueError(f"unsupported Docker action: {action}")
    run = Path(run).expanduser().resolve()
    target = _target(run)
    host, remote_run = _remote(run, target)
    record = paths(run)["records"] / "docker.json"
    if not record.is_file():
        raise RuntimeError("Docker container identity is not recorded; refusing wrapper control")
    cid = json.loads(record.read_text())["container_id"]
    result = _helper(host, remote_run, "control", {"remote_run": str(remote_run),
                                                      "container_id": cid, "action": action,
                                                      "cause": f"requested:{action}"})
    if result.returncode:
        raise RuntimeError(f"Docker {action} failed for {cid}: {result.stderr.strip()}")
    _remote_file(host, remote_run / "records/docker-control.json", paths(run)["records"] / "docker-control.json")
    value = json.loads((paths(run)["records"] / "docker-control.json").read_text())
    return {"action": value.get("action"), "container_id": value.get("container_id"),
            "commands": [{"verb": row.get("verb"), "exit_code": row.get("exit_code")}
                         for row in value.get("commands", [])], "as_of": value.get("as_of")}


def save(run: str | os.PathLike[str]) -> dict[str, Any]:
    run = Path(run).expanduser().resolve()
    facts = observe(run)
    target = _target(run)
    host, remote_run = _remote(run, target)
    errors = []
    for member in ("data/sdk-workspace", "data/workspace", "data/harness", "records"):
        destination = (paths(run)["inputs"] / "sdk-workspace") if member == "data/sdk-workspace" else paths(run)["root"] / member
        if host == "local":
            if not destination.is_dir():
                errors.append({"member": member, "error": "local execution tree missing"})
            continue
        source = f"{host}:{remote_run / member}/"
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["rsync", "-a", source, str(destination) + "/"], check=False,
                                text=True, capture_output=True)
        if result.returncode:
            errors.append({"member": member, "exit_code": result.returncode,
                           "stderr": result.stderr})
    terminal = facts.get("lifecycle") in {"completed", "failed", "stopped"}
    value = {"saved": terminal and not errors,
             "lifecycle": facts.get("lifecycle"), "scope": ["data/workspace", "data/harness", "records"],
             "errors": errors, "as_of": time.time()}
    write_json(paths(run)["records"] / "save.json", value)
    return value


def sync_saved(run: str | os.PathLike[str]) -> dict[str, Any]:
    """Mirror only remote records already written by execution-side workers."""
    run = Path(run).expanduser().resolve()
    target = _target(run)
    host, remote_run = _remote(run, target)
    destination = paths(run)["records"]
    destination.mkdir(parents=True, exist_ok=True)
    if host == "local":
        synced = destination.is_dir() and any(destination.iterdir())
        value = {"synced": synced, "executor": host, "remote_run": str(remote_run),
                 "exit_code": 0 if synced else 1,
                 "stderr": "" if synced else "local records directory is missing", "as_of": time.time()}
        write_json(destination / "saved-sync.json", value)
        return value
    result = subprocess.run(["rsync", "-a", f"{host}:{remote_run / 'records'}/", str(destination) + "/"],
                            check=False, text=True, capture_output=True)
    value = {"synced": result.returncode == 0, "executor": host,
             "remote_run": str(remote_run), "exit_code": result.returncode,
             "stderr": result.stderr, "as_of": time.time()}
    write_json(destination / "saved-sync.json", value)
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("create", "run", "observe", "control", "simulate"))
    parser.add_argument("config")
    args = parser.parse_args(argv)
    config = json.loads(args.config)
    root = Path(config["remote_run"])
    records = root / "records"
    records.mkdir(parents=True, exist_ok=True)

    def docker(*command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["docker", *command], text=True, capture_output=True)

    def save(name: str, value: Mapping[str, Any]) -> None:
        write_json(records / name, value)

    if args.phase == "create":
        command = docker(*config["create_argv"])
        value = {"phase": "create", "exit_code": command.returncode,
                 "stdout": command.stdout, "stderr": command.stderr, "as_of": time.time()}
        if command.returncode == 0 and command.stdout.strip():
            value["container_id"] = command.stdout.strip().splitlines()[-1].strip()
        if not value.get("container_id"):
            lookup = docker("ps", "-aq", "--filter", f"name=^/{config['container_name']}$")
            value["lookup"] = {"exit_code": lookup.returncode, "stdout": lookup.stdout,
                               "stderr": lookup.stderr}
            if lookup.returncode == 0 and lookup.stdout.strip():
                value["container_id"] = lookup.stdout.strip().splitlines()[-1].strip()
        if value.get("container_id"):
            checked = docker("inspect", value["container_id"])
            value["identity_inspect"] = {"exit_code": checked.returncode,
                                          "stdout": checked.stdout, "stderr": checked.stderr}
            try:
                labels = json.loads(checked.stdout)[0].get("Config", {}).get("Labels", {})
                if labels.get("io.factory26.run") != config.get("run_id"):
                    value["container_id"] = None
                    value["identity_error"] = "container label does not match run"
            except (ValueError, IndexError):
                value["container_id"] = None
                value["identity_error"] = "container inspect could not be parsed"
        daemon = docker("info", "--format", "{{.ID}}")
        value["daemon_id"] = daemon.stdout.strip() if daemon.returncode == 0 else None
        save("docker-create.json", value)
        print(json.dumps(value, ensure_ascii=False), flush=True)
        return command.returncode
    cid = config.get("container_id")
    if args.phase == "observe":
        inspected = docker("inspect", cid)
        if inspected.returncode:
            value = {"lifecycle": "unknown", "container_id": cid,
                     "error": inspected.stderr, "inspect_exit_code": inspected.returncode,
                     "observed_at": time.time()}
        else:
            try:
                inspection = json.loads(inspected.stdout)[0]
                state = inspection.get("State", {})
                control_path = records / "docker-control.json"
                prior = json.loads(control_path.read_text()) if control_path.is_file() else {}
                if prior.get("action") == "stop" and not state.get("Running"):
                    lifecycle = "stopped"
                elif state.get("Paused"):
                    lifecycle = "paused"
                elif state.get("Running"):
                    lifecycle = "running"
                elif state.get("ExitCode") == 0:
                    lifecycle = "completed"
                else:
                    lifecycle = "failed"
                stats = docker("stats", "--no-stream", "--format", "{{json .}}", cid)
                value = {"lifecycle": lifecycle, "container_id": cid, "exit_code": state.get("ExitCode"),
                         "inspect": inspection, "resources": {"stats_stdout": stats.stdout,
                         "stats_stderr": stats.stderr, "stats_exit_code": stats.returncode},
                         "observed_at": time.time()}
            except (ValueError, IndexError) as error:
                value = {"lifecycle": "unknown", "container_id": cid,
                         "error": f"inspect parse failed: {error}", "stdout": inspected.stdout,
                         "stderr": inspected.stderr, "observed_at": time.time()}
        save("docker-observe.json", value)
        return 0
    if args.phase == "control":
        action = config["action"]
        inspected = docker("inspect", cid)
        try:
            state = json.loads(inspected.stdout)[0].get("State", {})
        except (ValueError, IndexError):
            state = {}
        verbs = ["unpause"] if action == "stop" and state.get("Paused") else []
        verbs.append({"pause": "pause", "resume": "unpause", "stop": "stop"}[action])
        rows = []
        for verb in verbs:
            changed = docker(verb, cid)
            rows.append({"verb": verb, "exit_code": changed.returncode,
                         "stdout": changed.stdout, "stderr": changed.stderr})
            if changed.returncode:
                save("docker-control.json", {"action": action, "cause": config.get("cause"),
                                               "container_id": cid, "commands": rows, "as_of": time.time()})
                return changed.returncode
        save("docker-control.json", {"action": action, "cause": config.get("cause"),
                                       "container_id": cid, "commands": rows, "as_of": time.time()})
        return 0
    if args.phase == "simulate":
        command = subprocess.run(config["argv"], cwd=str(root), text=True, capture_output=True)
        save("simulation-result.json", {"lifecycle": "completed", "argv": config["argv"],
                                         "exit_code": command.returncode, "stdout": command.stdout,
                                         "stderr": command.stderr, "finished_at": time.time()})
        return 0
    started = docker("start", cid)
    save("docker-start.json", {"container_id": cid, "exit_code": started.returncode,
                                "stdout": started.stdout, "stderr": started.stderr,
                                "as_of": time.time()})
    if started.returncode:
        save("docker-result.json", {"container_id": cid, "lifecycle": "failed",
                                     "exit_code": started.returncode, "error": started.stderr,
                                     "as_of": time.time()})
        return started.returncode
    waited = docker("wait", cid)
    try:
        exit_code = int(waited.stdout.strip())
    except ValueError:
        exit_code = None
    inspected = docker("inspect", cid)
    try:
        inspection = json.loads(inspected.stdout)[0]
    except (ValueError, IndexError):
        inspection = {"exit_code": inspected.returncode, "stdout": inspected.stdout,
                      "stderr": inspected.stderr}
    logs = docker("logs", cid)
    (records / "docker.stdout.log").write_text(logs.stdout)
    (records / "docker.stderr.log").write_text(logs.stderr)
    stopped = False
    control_path = records / "docker-control.json"
    if control_path.is_file():
        try:
            stopped = json.loads(control_path.read_text()).get("action") == "stop"
        except ValueError:
            stopped = False
    lifecycle = "stopped" if stopped else ("completed" if exit_code == 0 or config.get("run_kind") == "evaluation" else "failed")
    value = {"container_id": cid, "lifecycle": lifecycle,
             "exit_code": exit_code, "wait_stdout": waited.stdout, "wait_stderr": waited.stderr,
             "inspect": inspection, "finished_at": time.time()}
    save("docker-result.json", value)
    return 0 if exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
