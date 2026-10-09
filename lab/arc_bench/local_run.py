"""Small Docker executor for current ARC runs.

The host assembles with the official SDK, then the target host owns the
container.  Container identity is persisted before start; later operations
use that exact CID and never signal the SSH process.
"""

from __future__ import annotations

import argparse
import base64
from copy import deepcopy
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
import uuid
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


def _uses_prebuilt_runtime(run: Path, target: Mapping[str, Any]) -> bool:
    delivery = manifest(run).get("runtime_delivery")
    if delivery is not None:
        return delivery == "prebuilt"
    return bool(target.get("prebuilt_runtime"))


def _remote(run: Path, target: Mapping[str, Any]) -> tuple[str, Path]:
    host = target.get("executor")
    root = target.get("remote_root")
    if not isinstance(host, str) or not host or not isinstance(root, str) or not root.startswith("/"):
        raise ValueError("remote Docker target needs executor and absolute remote_root")
    return host, Path(root) / "runs" / run.name


def _remote_sdk_workspace(remote_run: Path, target: Mapping[str, Any]) -> Path:
    """Return the one SDK workspace path for this run.

    New runs are data-independent: their prepared SDK workspace lives under
    ``inputs``.  Only old P1 manifests without ``remote_runtime`` retain the
    historical ``data/sdk-workspace`` location for save/read compatibility.
    """
    if target.get("remote_runtime"):
        return remote_run / "inputs" / "sdk-workspace"
    return remote_run / "data" / "sdk-workspace"


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
        result = Path(value).expanduser().resolve(strict=True)
        if not result.is_dir():
            raise ValueError("local Docker generation requires a small agent program directory")
        runtime_entry = result / "runtime"
        if runtime_entry.exists() or runtime_entry.is_symlink():
            raise ValueError("agent program directory must not contain a runtime entry; use target.remote_runtime")
        return result
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
    competition = raw_task.rsplit("--", 1)[0] if "--" in raw_task else ("public-practice" if task == "bookstack" else "hackathon")
    evaluation = state.get("run_kind") == "evaluation"
    args = SimpleNamespace(
        data_root=str(paths(run)["inputs"]), competition=competition, task=task,
        requirements_dir=str(_requirements(run)),
        tests_dir=str(paths(run)["inputs"] / "tests") if evaluation and (paths(run)["inputs"] / "tests").is_dir() else None,
        workspace=str(output), agent=str(_agent(run, target)),
        template=(str(paths(run)["inputs"] / "application") if evaluation and (paths(run)["inputs"] / "application").is_dir()
                  else str(paths(run)["inputs"]/'initial-application') if task_config.get('initial_application') else None),
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


def _ensure_remote_runtime(run: Path, host: str, target: Mapping[str, Any]) -> dict[str, Any]:
    """Deploy one immutable host runtime and return execution-side facts."""
    source_value = target.get("runtime")
    destination_value = target.get("remote_runtime")
    if not source_value or not destination_value:
        raise ValueError("local Docker target needs runtime and remote_runtime")
    source = Path(str(source_value)).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError(f"runtime source is not a directory: {source}")
    destination = Path(str(destination_value))
    if not destination.is_absolute():
        raise ValueError("remote_runtime must be an absolute execution-host path")
    # runtime-source.json belongs to the runtime bundle itself.  The executor
    # must never overwrite it with deployment state.
    receipt = destination / ".lab-deployment.json"
    local_receipt = paths(run)["records"] / "runtime-deployment.json"
    exists = _remote_exec(host, ["test", "-d", str(destination)])
    receipt_exists = _remote_exec(host, ["test", "-f", str(receipt)])
    if exists.returncode == 0:
        if receipt_exists.returncode:
            raise RuntimeError(f"remote runtime exists without completion receipt: {destination}")
        if not _remote_file(host, receipt, local_receipt):
            raise RuntimeError(f"remote runtime receipt could not be read: {receipt}")
        value = json.loads(local_receipt.read_text())
        value.update({"path": str(destination), "reused": True, "observed_at": time.time()})
        write_json(local_receipt, value)
        return {"source": str(source), "path": str(destination), "receipt": str(receipt),
                "reused": True, "source_facts": value}
    if exists.returncode != 1:
        raise RuntimeError(f"cannot inspect remote runtime path {destination}: {exists.stderr.strip()}")
    # Never expose a partially cloned runtime.  The public path is published
    # only by the final rename after data and its own receipt are complete.
    staging = destination.with_name(destination.name + ".staging-" + uuid.uuid4().hex[:12])
    staging_receipt = staging / ".lab-deployment.json"
    source_metadata = None
    source_metadata_path = source / "runtime-source.json"
    if source_metadata_path.is_file():
        source_metadata = json.loads(source_metadata_path.read_text())
    base_value = target.get("remote_runtime_base")
    deployed_mode = "full-rsync"
    base_path = Path(str(base_value)) if base_value else None
    if base_path is not None and not base_path.is_absolute():
        raise ValueError("remote_runtime_base must be an absolute execution-host path")
    compatible = False
    base_metadata = None
    if base_path is not None and base_path != destination and source_metadata is not None:
        base_result = _remote_exec(host, ["cat", str(base_path / "runtime-source.json")])
        if base_result.returncode == 0:
            try:
                base_metadata = json.loads(base_result.stdout)
                comparable = ("backend", "platform", "npm_sha256", "native_patch_sha256", "native_modules_sha256",
                              "profile", "omitted_members", "slim_wrapper_sha256")
                compatible = all(base_metadata.get(key) == source_metadata.get(key) for key in comparable)
                source_package = (source_metadata.get("derivation") or {}).get("package_sha256")
                base_package = (base_metadata.get("derivation") or {}).get("package_sha256")
                # Slim runtimes derived from an already frozen native runtime
                # may not have a Python/package derivation hash.  Their
                # explicit profile, omission set and wrapper digests are the
                # base identity; a present package hash still must agree.
                compatible = compatible and (
                    (source_package and source_package == base_package) or
                    (not source_package and not base_package and source_metadata.get("profile") == "arc-core")
                )
            except json.JSONDecodeError:
                compatible = False
    if compatible and base_path is not None:
        # Clone a known-identical immutable base on the execution host. Reflink
        # is preferred, but the copy remains independent before the delta lands.
        _remote_exec(host, ["mkdir", "-p", str(destination.parent)], check=True)
        clone = _remote_exec(host, ["cp", "--reflink=auto", "-a", str(base_path) + "/.", str(staging)])
        if clone.returncode:
            compatible = False
        else:
            _remote_exec(host, ["rm", "-f", str(staging_receipt)], check=True)
            for member in ("bin/braid", "runtime-source.json"):
                _sync_file(host, source / member, str(staging / member))
            deployed_mode = "reflink-base-plus-braid"
    if not compatible:
        _sync(host, source, str(staging))
    source_metadata_result = _remote_exec(host, ["cat", str(staging / "runtime-source.json")])
    if source_metadata_result.returncode == 0:
        try:
            source_metadata = json.loads(source_metadata_result.stdout)
        except json.JSONDecodeError:
            source_metadata = {"raw": source_metadata_result.stdout}
    value = {"source": str(source), "path": str(destination),
             "runtime_source": source_metadata,
             "source_bytes": sum(item.stat().st_size for item in source.rglob("*") if item.is_file()),
             "source_mtime_ns": source.stat().st_mtime_ns, "deployed_at": time.time(),
             "reused": False, "mode": "fixed-readonly-runtime", "deployment_mode": deployed_mode,
             "base_runtime": str(base_path) if compatible and base_path is not None else None,
             "delta_members": ["bin/braid", "runtime-source.json"] if deployed_mode == "reflink-base-plus-braid" else ["**"]}
    encoded = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()).decode()
    _remote_exec(host, ["sh", "-c", f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(str(staging_receipt))}"], check=True)
    _remote_exec(host, ["mv", str(staging), str(destination)], check=True)
    write_json(local_receipt, value)
    return {"source": str(source), "path": str(destination), "receipt": str(receipt),
            "reused": False, "source_facts": value}


def _uses_proxy(target):
    # Historical frozen targets used the recipe name as this transport flag.
    return target.get('model_transport') == 'proxy' or target.get('model_recipe') == 'self-funded'


def _meter(run: Path, target: Mapping[str, Any], phase: str, *, wait: bool = False,
           query_start: int | None = None) -> dict[str, Any]:
    """Capture shared access-key meter facts; never relabel them as per-run cost."""
    destination = paths(run)["records"] / f"meter-{phase}.json"
    if _uses_proxy(target):
        result = {"phase": phase, "scope": "self-funded-provider", "status": "not_applicable",
                  "reason": "ARC shared-key meter is not used for self-funded recipes",
                  "as_of": time.time()}
        write_json(destination, result)
        return result
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
    if _uses_proxy(target):
        return {"scope": "self-funded-provider", "status": "not_collected",
                "reason": "No provider billing or verified per-request price is configured; native token usage is separate from monetary spend",
                "value": None, "currency": None, "kind": "unknown",
                "as_of": time.time()}
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
    state = manifest(run)
    task_config = state.get('task_config') or {}
    if not any(app.iterdir()) or (task_config.get('initial_application') and not state.get('source_run')):
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


_DEVELOPMENT_SOURCE_EXCLUDES = (
    ".git/",
    "node_modules/",
    "playwright-report/",
    "test-results/",
    "__pycache__/",
    ".pytest_cache/",
)


def _sync(host: str, source: Path, destination: str, *, excludes: tuple[str, ...] = ()) -> None:
    """Copy a source tree, optionally excluding local development debris."""
    patterns = tuple(dict.fromkeys(excludes))
    if host == "local":
        destination_path = Path(destination)
        if source.resolve() == destination_path.resolve():
            return
        destination_path.mkdir(parents=True, exist_ok=True)
        ignored = tuple(pattern.rstrip("/") for pattern in patterns)
        shutil.copytree(source, destination_path, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(*ignored) if ignored else None)
        return
    subprocess.run(["ssh", host, shlex.join(["mkdir", "-p", destination])], check=True)
    command = ["rsync", "-a"]
    for pattern in patterns:
        command.append(f"--exclude={pattern}")
    command += [str(source) + "/", f"{host}:{destination}/"]
    subprocess.run(command, check=True)


def _spawn_source_components(module: str, args: list[str] | tuple[str, ...], *, script=False) -> tuple[str, ...]:
    """Return source trees consumed by a remote observer/automation process."""
    components = ["lab", "tooling"]
    if script or (module == "lab.automation" and args and str(args[0]) == "stages"):
        components += ["variants", "materials", "third_party/arc-bench"]
    return tuple(components)


def _sync_file(host: str, source: Path, destination: str) -> None:
    """Copy one runtime delta without replacing the immutable base directory."""
    if host == "local":
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination_path)
        return
    subprocess.run(["rsync", "-a", str(source), f"{host}:{destination}"], check=True)


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


def _record_agent_log_baseline(run: Path, host: str, remote_run: Path) -> None:
    """Record the workspace log size immediately before this run starts.

    Restarted runs may intentionally carry the application workspace forward.
    The SDK does not emit a run delimiter, so this offset is the only cheap
    boundary that can distinguish newly appended output without rewriting the
    source log.  Missing baselines are handled as retained history by the
    observer rather than being presented as per-run output.
    """
    source = remote_run / "data/workspace/.arc/stdout.log"
    if host == "local":
        exists = source.is_file()
        size = source.stat().st_size if exists else 0
    else:
        result = _remote_exec(host, ["wc", "-c", str(source)])
        exists = result.returncode == 0
        try:
            size = int(result.stdout.split()[0]) if exists else 0
        except (ValueError, IndexError):
            exists, size = False, 0
    write_json(paths(run)["records"] / "agent-log-baseline.json", {
        "source": str(source), "source_exists": exists, "offset": size,
        "captured_at": time.time(), "boundary": "byte_offset_before_start"})


def _capture_agent_log(run: Path, host: str, remote_run: Path,
                       source_name: str, record_name: str) -> bool:
    """Copy only post-start agent output into records, retaining raw source."""
    records = paths(run)["records"]
    capture = records / f".{record_name}.capture"
    source = remote_run / "data/workspace/.arc" / source_name
    if not _remote_file(host, source, capture):
        return False
    baseline_path = records / "agent-log-baseline.json"
    baseline = None
    if baseline_path.is_file():
        try:
            candidate = json.loads(baseline_path.read_text())
            if isinstance(candidate, dict) and isinstance(candidate.get("offset"), int):
                baseline = candidate
        except (OSError, ValueError):
            baseline = None
    raw = capture.read_bytes()
    offset = int(baseline["offset"]) if baseline is not None else 0
    source_reset = baseline is not None and offset > len(raw)
    selected = raw[offset:] if baseline is not None and not source_reset else raw
    (records / record_name).write_bytes(selected)
    capture.unlink(missing_ok=True)
    write_json(records / f"{record_name}.meta.json", {
        "source": str(source), "source_bytes": len(raw), "offset": offset,
        "captured_bytes": len(selected),
        "retained_history": baseline is None or source_reset,
        "boundary": ("source_shorter_than_baseline" if source_reset else
                     ("byte_offset_before_start" if baseline is not None else "unknown")),
        "captured_at": time.time()})
    return True


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
    names = {line.split("=", 1)[0].strip() for line in source.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#") and "=" in line}
    if _uses_proxy(target):
        if not any(name.endswith(("_API_KEY", "_TOKEN")) for name in names):
            raise ValueError(f"self-funded environment has no provider credential variable: {source}")
    elif not names & {"FACTORY26_API_KEY", "OPENAI_API_KEY"}:
        raise ValueError(f"private environment has no supported API key variable: {source}")
    if host == "local":
        return source
    original = remote_run / ".private-source.env"
    mapped = remote_run / ".private.env"
    subprocess.run(["rsync", "-a", str(source), f"{host}:{original}"], check=True)
    if _uses_proxy(target):
        command = f"cp {shlex.quote(str(original))} {shlex.quote(str(mapped))} && chmod 600 {shlex.quote(str(mapped))}"
    else:
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
    remote_target["execution_role"] = "remote"
    remote_target["remote_root"] = str(remote_run.parent.parent)
    remote_target["environment_file"] = str(remote_run / ".private.env")
    if remote_target.get("kind") == "self-test" and host != "local":
        # Self-test auth originates from the already logged-in Mac Helium
        # profile.  Materialize only the target-domain Netscape cookies, then
        # hand that private file to the execution host with mode 0600.  The
        # value never enters the manifest, records, or command line.
        from . import self_test
        source = Path(self_test._cookie_file(target)).resolve(strict=True)
        destination = remote_run / ".private" / "self-test.cookies.txt"
        _push_private_file(host, source, destination)
        remote_target["cookie_file"] = str(destination)
        remote_target.pop("cookie_file_env", None)
        remote_target.pop("cookie_source", None)
    if target.get("remote_runtime"):
        remote_target["remote_runtime"] = str(target["remote_runtime"])
    if target.get("otlp_deps"):
        candidate = _remote_sdk_workspace(remote_run, target) / "submission" / "otlp-deps"
        if _remote_exec(host, ["test", "-d", str(candidate)]).returncode == 0:
            remote_target["otlp_deps"] = str(candidate)
    for key in ("runtime", "skills"):
        if key == "runtime" and target.get("remote_runtime"):
            remote_target["runtime"] = str(target["remote_runtime"])
            continue
        candidate = _remote_sdk_workspace(remote_run, target) / "submission" / key
        if _remote_exec(host, ["test", "-d", str(candidate)]).returncode == 0:
            remote_target[key] = str(candidate)
        else:
            remote_target.pop(key, None)
    remote_target.pop("agent_package", None)
    value["target_config"] = remote_target
    encoded = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()).decode()
    # Spawning automation can republish while the observer is reading. Never
    # truncate its manifest; publish a complete adjacent file with rename.
    temporary = remote_run / f".manifest.{uuid.uuid4().hex}.tmp"
    _remote_exec(host, ["sh", "-c",
        f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(str(temporary))} && "
        f"mv {shlex.quote(str(temporary))} {shlex.quote(str(remote_run / 'manifest.json'))}"], check=True)


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
            if key == "runtime" and item.startswith("/Volumes/WorkSSD/"):
                return str(current_target.get("remote_runtime") or (remote_run / "data/sdk-workspace/submission/runtime"))
            if key == "skills" and item.startswith("/Volumes/WorkSSD/"):
                return str(_remote_sdk_workspace(remote_run, current_target) / "submission/skills")
            if key == "otlp_deps" and item.startswith("/Volumes/WorkSSD/"):
                return str(_remote_sdk_workspace(remote_run, current_target) / "submission/otlp-deps")
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
                 image_id: str | None = None, runtime_path: str | None = None) -> list[str]:
    name = _container_name(run)
    argv = ["create", "--init", "--ulimit", "core=0:0", "--name", name,
            "--label", "io.factory26.managed=true", "--label", f"io.factory26.run={run.name}",
            "--mount", f"type=bind,source={_remote_sdk_workspace(remote_run, target)},target=/workspace",
            "--mount", f"type=bind,source={remote_run / 'data/workspace'},target=/workspace/template",
            "--memory", str(target.get("memory", "2g")), "--cpus", str(target.get("cpus", "1"))]
    if runtime_path:
        argv += ["--mount", f"type=bind,source={runtime_path},target=/workspace/submission/runtime,readonly"]
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


def saved_restart_source(source: Path, destination_target: Mapping[str, Any]) -> dict[str, Any] | None:
    """Retain terminal Local data on its execution host, without claiming a Mac save."""
    state = manifest(source)
    original = _target(source)
    if original.get("kind") != "local" or destination_target.get("kind") != "local":
        return None
    host, remote_run = _remote(source, original)
    if host == "local" or _remote(source, destination_target) != (host, remote_run):
        return None
    handle = json.loads((paths(source)["records"] / "docker.json").read_text())
    cid, daemon = handle.get("container_id"), handle.get("daemon_id")
    actual = _remote_exec(host, ["docker", "info", "--format", "{{.ID}}"], check=True).stdout.strip()
    if not cid or not daemon or actual != daemon:
        raise ValueError("same-host restart requires the source Docker daemon identity")
    checked = _remote_exec(host, ["docker", "inspect", str(cid)], check=True)
    inspection = json.loads(checked.stdout)[0]
    if inspection.get("Id") != cid or inspection.get("State", {}).get("Running"):
        raise ValueError("same-host restart requires the exact source container stopped")
    # Use the source's already installed, frozen executor save API. This is a
    # terminal save on the execution host, not a portable/controller recovery.
    code = ("import sys; from lab.arc_bench import execution; "
            "execution.save(sys.argv[1])")
    pythonpath = ":".join(str(remote_run / name) for name in
                         ("automation", "source", "inputs/sdk-workspace/submission"))
    _remote_exec(host, ["env", "PYTHONPATH=" + pythonpath, "python3", "-c", code,
                       str(remote_run)], check=True)
    receipt_path = paths(source)["records"] / "restart-remote-save.json"
    if not _remote_file(host, remote_run / "records/result-save.json", receipt_path):
        raise RuntimeError("same-host restart remote save receipt missing")
    saved = json.loads(receipt_path.read_text())
    if (saved.get("saved") is not True or saved.get("errors") != [] or
            saved.get("snapshot") is not False or saved.get("storage_root") != str(remote_run) or
            not {"data/workspace", "data/harness", "records"}.issubset(saved.get("scope") or []) or
            saved.get("lifecycle") not in {"completed", "failed", "stopped"}):
        raise ValueError(f"same-host restart requires a complete terminal remote save: {saved}")
    remote_manifest = paths(source)["records"] / "restart-remote-manifest.json"
    if not _remote_file(host, remote_run / "manifest.json", remote_manifest):
        raise RuntimeError("same-host restart source manifest missing")
    remote_state = json.loads(remote_manifest.read_text())
    for key in ("run_id", "task", "native_scope_id", "requirements_version"):
        if remote_state.get(key) != state.get(key):
            raise ValueError(f"same-host restart source {key} mismatch")
    return {"source_run": source.name, "executor": host, "remote_run": str(remote_run),
            "container_id": cid, "daemon_id": daemon, "native_scope_id": state.get("native_scope_id"),
            "task": state.get("task"), "saved": saved}


def _copy_saved_restart_data(run: Path, host: str, remote_run: Path,
                             source: Mapping[str, Any]) -> None:
    state = manifest(run)
    saved = source["saved"]
    origin = Path(str(source["remote_run"]))
    if (host != source["executor"] or origin != remote_run.parent / str(source["source_run"]) or
            state.get("source_run") != source["source_run"] or not state.get("native_resume") or
            state.get("native_scope_id") != source["native_scope_id"] or state.get("task") != source["task"] or
            saved.get("saved") is not True or saved.get("errors") != [] or
            saved.get("snapshot") is not False or saved.get("storage_root") != str(origin)):
        raise ValueError("same-host restart copy identity/save contract mismatch")
    daemon = _remote_exec(host, ["docker", "info", "--format", "{{.ID}}"], check=True).stdout.strip()
    inspected = json.loads(_remote_exec(host, ["docker", "inspect", source["container_id"]], check=True).stdout)[0]
    if daemon != source["daemon_id"] or inspected.get("Id") != source["container_id"] or inspected.get("State", {}).get("Running"):
        raise ValueError("same-host restart source container/daemon changed before copy")
    staging = remote_run / "data.restart-staging"
    # cp -a creates independent regular files; reflinks are copy-on-write, not
    # hardlinks. Never bind or mutate the source's saved data tree.
    command = " && ".join((
        "test -d " + shlex.quote(str(origin / "data/workspace")),
        "test -d " + shlex.quote(str(origin / "data/harness" / str(source["native_scope_id"]))),
        "test ! -e " + shlex.quote(str(staging)),
        "test ! -e " + shlex.quote(str(remote_run / "data")),
        "mkdir -p " + shlex.quote(str(remote_run)),
        "cp --reflink=auto -a " + shlex.quote(str(origin / "data")) + " " + shlex.quote(str(staging)),
        "mv " + shlex.quote(str(staging)) + " " + shlex.quote(str(remote_run / "data"))))
    _remote_exec(host, ["sh", "-c", command], check=True)
    write_json(paths(run)["records"] / "restart-data-copy.json", {
        "source": dict(source), "destination": str(remote_run / "data"),
        "method": "independent cp --reflink=auto -a", "controller_data_recovered": False,
        "as_of": time.time()})


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
    retained = manifest(run).get("remote_restart_data")
    app = paths(run)["workspace"] if retained else _stage_app(run, workspace)
    host, remote_run = _remote(run, target)
    _verify_remote_sdk(host, target)
    # Public packages install their small native/runtime inputs inside the
    # container before entry; do not deploy or mount the historical full
    # runtime for this path.  Legacy packages retain the explicit deployment
    # branch until their entry is migrated.
    public_program = workspace / "submission" / "runtime_install.py"
    if public_program.is_file() and not _uses_prebuilt_runtime(run, target):
        runtime_facts = {"mode": "container-installer", "path": None,
                         "source": "program/runtime_install.py"}
    else:
        runtime_facts = _ensure_remote_runtime(run, host, target)
    _sync(host, workspace, str(_remote_sdk_workspace(remote_run, target)))
    if retained:
        _copy_saved_restart_data(run, host, remote_run, retained)
        # Only SDK-owned execution inputs are refreshed. An empty controller
        # workspace must never upload the official baseline over saved work.
        for name in ("requirements", ".arc"):
            member = workspace / "template" / name
            if member.is_dir():
                _sync(host, member, str(remote_run / "data/workspace" / name))
    else:
        _sync(host, app, str(remote_run / "data/workspace"))
    # Establish the output boundary after workspace migration but before the
    # container starts; an inherited .arc log is therefore never relabeled as
    # this run's fresh process output.
    _record_agent_log_baseline(run, host, remote_run)
    _remote_exec(host, ["mkdir", "-p", str(remote_run / "data/harness"), str(remote_run / "records")], check=True)
    harness = paths(run)["harness"]
    if harness.is_dir() and not retained:
        _sync(host, harness, str(remote_run / "data/harness"))
    return {"run": str(run), "workspace": str(workspace), "app": str(app), "remote_run": str(remote_run),
            "executor": host, "image_id": target.get("image_id"), "runtime": runtime_facts,
            "status": "prepared"}


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
        command = "cd {root} && {{ nohup python3 {helper} simulate {payload} > {log} 2>&1 < /dev/null & }}".format(
            root=shlex.quote(str(remote_run)), helper=shlex.quote(str(helper)), payload=shlex.quote(payload),
            log=shlex.quote(str(remote_run / "records/simulation-worker.log")))
        write_json(paths(run)['records'] / 'dispatch.json', {
            'phase': 'simulate', 'executor': host, 'remote_run': str(remote_run), 'as_of': time.time()})
        _remote_exec(host, ["sh", "-c", command], check=True)
        return {"lifecycle": "starting", "executor": host, "remote_run": str(remote_run),
                "started_at": time.time(), "mode": "simulate"}
    # The official SDK runs this payload as root. Restored Git repositories
    # must have that execution owner; save returns them to the host afterward.
    _remote_exec(host, ["sudo", "-n", "chown", "-R", "-h", "0:0",
                        str(remote_run / "data")], check=True)
    private_env = _stage_private_env(host, target, remote_run)
    if not _uses_proxy(target) and not (paths(run)["records"] / "meter-baseline.json").is_file():
        _meter(run, target, "baseline")
    scope = manifest(run).get("native_scope_id")
    image_id, image_resolution = _resolve_remote_image(host, target)
    write_json(paths(run)["records"] / "image-resolution.json", image_resolution)
    config = {"remote_run": str(remote_run), "container_id": None,
              "container_name": _container_name(run), "run_id": run.name,
              "run_kind": manifest(run).get("run_kind", "generation"),
              "create_argv": _create_argv(run, target, remote_run, Path(prepared["workspace"]), private_env, scope, image_id,
                                           prepared["runtime"].get("path"))}
    helper = _deploy_helper(host, remote_run)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    write_json(paths(run)['records'] / 'dispatch.json', {
        'phase': 'create', 'executor': host, 'remote_run': str(remote_run),
        'container_name': config['container_name'], 'as_of': time.time()})
    created = _remote_exec(host, ["python3", str(helper), "create", payload])
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
    command = "cd {root} && {{ nohup python3 {helper} run {payload} > {log} 2>&1 < /dev/null & }}".format(
        root=json.dumps(str(remote_run)), helper=json.dumps(str(helper)),
        payload=shlex.quote(payload), log=json.dumps(str(remote_run / "records/docker-worker.log")))
    _remote_exec(host, ["sh", "-c", command], check=True)
    return {"lifecycle": "starting", "container_id": cid, "container_name": _container_name(run),
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
    # The observer consumes the same pre-start byte boundary used by the Mac
    # record.  Carry it with the identity/handle; without this, a remote
    # observer would conservatively label the whole inherited log as history.
    agent_baseline = paths(run)["records"] / "agent-log-baseline.json"
    if agent_baseline.is_file():
        _copy_file(host, agent_baseline, remote_run / "records/agent-log-baseline.json")
    # ``start`` records the verified CID on the Mac before dispatching the
    # execution-side observer.  Carry that exact handle into the remote
    # records domain; create.json alone is not an observation handle.
    identity = paths(run)["records"] / "docker.json"
    if identity.is_file():
        _copy_file(host, identity, remote_run / "records/docker.json")
    # The SDK workspace/runtime are already assembled and deployed. Only
    # inputs needed by this spawned process cross the host boundary.
    for relative in ("requirements", "tests", "application", "application-receipt.json",
                     "initial-application", "task-context.md", "gateway-routes.json",
                     "model-gateway.json", "native-resume.json"):
        source = paths(run)["inputs"] / relative
        destination = remote_run / "inputs" / relative
        if source.exists() and _remote_exec(host, ["test", "-e", str(destination)]).returncode:
            if source.is_dir():
                _sync(host, source, str(destination))
            else:
                _copy_file(host, source, destination)
    repository = Path(__file__).resolve().parents[2]
    _sync(host, paths(run)["program"], str(remote_run / "program"))
    # Python policies can call start/restart just like the existing stages program.
    for component in _spawn_source_components(module, args, script=script is not None):
        _sync(host, repository / component, str(remote_run / "source" / component),
              excludes=_DEVELOPMENT_SOURCE_EXCLUDES)
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
    pythonpath = f"{remote_dir}:{remote_run / 'source'}:{_remote_sdk_workspace(remote_run, target) / 'submission'}"
    command = "cd {root} && {{ LAB_RUN={root} LAB_RUN_ROOT={run_root} PYTHONPATH={pythonpath} nohup {argv} > {log} 2>&1 < /dev/null & echo $!; }}".format(
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
    observation_error = None
    if identity.is_file():
        handle = json.loads(identity.read_text())
        observed = _helper(host, remote_run, "observe", {"remote_run": str(remote_run),
                                                          "container_id": handle["container_id"]})
        if observed.returncode and observed.stderr:
            observation_error = observed.stderr
    _remote_file(host, remote_run / "records/docker-observe.json", local_records / "docker-observe.json")
    _remote_file(host, remote_run / "records/docker-result.json", local_records / "docker-result.json")
    _remote_file(host, remote_run / "records/docker-start.json", local_records / "docker-start.json")
    # The execution-side observer already writes a bounded status/native
    # summary.  Pull that fact record alongside Docker state; never copy raw
    # rollout/session logs as part of status observation.
    if host != "local":
        _remote_file(host, remote_run / "records/status.json", local_records / "remote-status.json")
    # The public entrypoint writes this after runtime installation and before
    # the variant starts.  Pull the small execution-side receipt with the
    # existing bounded records observation; no second observer is needed.
    _remote_file(host, remote_run / "data/workspace/.factory26/material-consumption.json",
                 local_records / "material-consumption.json")
    for name in ("docker.stdout.log", "docker.stderr.log"):
        _remote_file(host, remote_run / "records" / name, local_records / name)
    # The official SDK's agent runner redirects the normal process streams to
    # the mounted workspace, not to the container's stdout/stderr stream.
    # Keep those bounded process/error logs available to ``lab logs`` without
    # copying the large rollout/session event stream.
    _capture_agent_log(run, host, remote_run, "stdout.log", "agent.stdout.log")

    remote_status = {}
    remote_status_path = local_records / "remote-status.json"
    if host != "local" and remote_status_path.is_file():
        try:
            candidate = json.loads(remote_status_path.read_text())
            if isinstance(candidate, dict):
                remote_status = candidate
        except (OSError, ValueError):
            remote_status = {}

    def enrich(value: dict[str, Any]) -> dict[str, Any]:
        for key in ("activity", "brief", "last_activity_at", "evidence", "native", "spend", "resources"):
            if key in remote_status:
                value[key] = remote_status[key]
        if observation_error:
            value["observation_error"] = observation_error
        return value
    result = local_records / "docker-result.json"
    if result.is_file():
        value = json.loads(result.read_text())
        live_value = json.loads((local_records / "docker-observe.json").read_text()) if (local_records / "docker-observe.json").is_file() else {}
        lifecycle = value.get("lifecycle", "unknown")
        return enrich({"lifecycle": lifecycle, "container_id": value.get("container_id"),
                "exit_code": value.get("exit_code"), "resources": {"inspect": _public_inspect(value.get("inspect")),
                "live": live_value.get("resources")},
                "stderr": value.get("error"), "spend": _spend(run, target, lifecycle), "observed_at": time.time()})
    live = local_records / "docker-observe.json"
    if live.is_file():
        value = json.loads(live.read_text())
        value["inspect"] = _public_inspect(value.get("inspect"))
        value["spend"] = _spend(run, target, value.get("lifecycle", "unknown"))
        return enrich({**value, "observed_at": time.time()})
    handle = json.loads(identity.read_text()) if identity.is_file() else {}
    if not handle and (local_records / "docker-create.json").is_file():
        return enrich({"lifecycle": "unknown", "container_id": None, "executor": host,
                "observed_at": time.time(), "remote_run": str(remote_run),
                "error": "create response had no verified container identity",
                "spend": _spend(run, target, "unknown")})
    return enrich({"lifecycle": "starting", "container_id": handle.get("container_id"),
            "executor": host, "observed_at": time.time(), "remote_run": str(remote_run),
            "spend": _spend(run, target, "starting")})


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


def save(run: str | os.PathLike[str], *, live: bool = False,
         write_receipt: bool = True) -> dict[str, Any]:
    run = Path(run).expanduser().resolve()
    facts = observe(run)
    target = _target(run)
    host, remote_run = _remote(run, target)
    errors = []
    terminal = facts.get("lifecycle") in {"completed", "failed", "stopped"}
    if terminal:
        # Root-run SDK children create private native files. Return ownership
        # to this run's host owner without widening their permission modes.
        owner = _remote_exec(host, ["stat", "-c", "%u:%g", str(remote_run)])
        if owner.returncode == 0:
            ownership = _remote_exec(host, ["sudo", "-n", "chown", "-R", "-h",
                                          owner.stdout.strip(), str(remote_run / "data")])
            if ownership.returncode:
                errors.append({"member": "data", "exit_code": ownership.returncode,
                               "stderr": ownership.stderr})
        else:
            errors.append({"member": "data", "exit_code": owner.returncode,
                           "stderr": owner.stderr})
    sdk_member = "inputs/sdk-workspace" if target.get("remote_runtime") else "data/sdk-workspace"
    for member in (sdk_member, "data/workspace", "data/harness", "records"):
        destination = paths(run)["inputs"] / "sdk-workspace" if member == sdk_member else paths(run)["root"] / member
        if host == "local":
            if not destination.is_dir():
                errors.append({"member": member, "error": "local execution tree missing"})
            continue
        source = f"{host}:{remote_run / member}/"
        destination.mkdir(parents=True, exist_ok=True)
        # A run's harness contains live Unix sockets owned by native helpers.
        # They are runtime endpoints, not recoverable data; copying them makes
        # macOS rsync fail with mkstempsock instead of saving the run.
        # openrsync's delta receiver can abort when a previously mirrored
        # native status file changes size during recovery. Transfer complete
        # files so save never depends on that mutable local basis mapping.
        command = ["rsync", "-a", "--whole-file", "--no-devices", "--no-specials"]
        if member == "records":
            # Remote save success is not controller-side data recovery success.
            command += ["--exclude=/save.json", "--exclude=/result-save.json"]
        if member == sdk_member:
            # SDK submission is frozen program material; provider/model-proxy
            # state is private mutable service state and is not recovered into
            # the frozen local SDK copy.
            command += ["--exclude=/submission/.private/**", "--exclude=/submission/.private"]
        command += [source, str(destination) + "/"]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        if result.returncode:
            errors.append({"member": member, "exit_code": result.returncode,
                           "stderr": result.stderr})
    value = {"saved": (not errors) if live else terminal and not errors,
             "lifecycle": facts.get("lifecycle"), "scope": ["data/workspace", "data/harness", "records"],
             "storage_root": str(run),
             "snapshot": bool(live and not terminal),
             "excluded": ["inputs/sdk-workspace/submission/.private/**"] if target.get("remote_runtime") else [],
             "errors": errors, "as_of": time.time()}
    if write_receipt:
        write_json(paths(run)["records"] / "save.json", value)
        write_json(paths(run)["records"] / "result-save.json", value)
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
    status_probe = _remote_exec(host, ["test", "-f", str(remote_run / "records/status.json")])
    result = subprocess.run(["rsync", "-a", "--exclude=/save.json", "--exclude=/result-save.json",
                             f"{host}:{remote_run / 'records'}/", str(destination) + "/"],
                            check=False, text=True, capture_output=True)
    for name in ("save.json", "result-save.json"):
        _remote_file(host, remote_run / "records" / name, destination / f"remote-{name}")
    value = {"synced": result.returncode == 0 and status_probe.returncode == 0, "executor": host,
             "remote_run": str(remote_run), "exit_code": result.returncode,
             "status_record": status_probe.returncode == 0,
             "stderr": result.stderr, "as_of": time.time()}
    write_json(destination / "saved-sync.json", value)
    return value


def mirror_saved_evaluations(source_run: str | os.PathLike[str]) -> dict[str, Any]:
    """Dispatch deferred controller evaluations and relay saved child facts.

    This consumes only ``automatic-evaluations.json`` after the source
    observer has saved it. Deferred evaluations are created by the controller
    through ``evaluate_run``; already-dispatched remote children have their
    manifest copied from the execution host, then a local relay mirrors
    records from that existing remote identity.
    """
    source = Path(source_run).expanduser().resolve()
    from .evaluate import EVALUATION_KINDS
    state = manifest(source)
    target = state.get("target_config") or {}
    if (target.get("kind") != "local" or target.get("executor") in {None, "local"}):
        return {"mirrored": [], "skipped": [], "status": "unsupported_source_target"}
    receipt_path = paths(source)["records"] / "automatic-evaluations.json"
    if not receipt_path.is_file():
        return {"mirrored": [], "skipped": [], "status": "receipt_not_saved"}
    receipt = json.loads(receipt_path.read_text())
    items = receipt.get("items") if isinstance(receipt, dict) else None
    if not isinstance(items, list):
        return {"mirrored": [], "skipped": [{"reason": "invalid_evaluation_receipt"}],
                "status": "unsupported_receipt"}
    host, source_remote = _remote(source, target)
    if not target.get("remote_root"):
        return {"mirrored": [], "skipped": [{"reason": "source_remote_root_missing"}],
                "status": "unsupported_source_target"}
    run_root = paths(source)["root"].parent
    mirrored, skipped = [], []
    prior_relay = {}
    prior_path = paths(source)["records"] / "evaluation-relay.json"
    if prior_path.is_file():
        try:
            prior = json.loads(prior_path.read_text())
            prior_relay = {row.get("request_id"): row for row in prior.get("mirrored", [])
                           if isinstance(row, dict) and row.get("request_id")}
        except (OSError, ValueError, TypeError):
            prior_relay = {}
    for index, item in enumerate(items):
        configuration = item.get("configuration") if isinstance(item, dict) else None
        request_id = item.get("request_id") if isinstance(item, dict) else None
        if (isinstance(item, dict) and item.get("deferred") and
                isinstance(configuration, dict) and
                configuration.get("kind") in EVALUATION_KINDS):
            if request_id in prior_relay:
                mirrored.append(prior_relay[request_id])
                continue
            try:
                # The remote source has already saved its data domain, but
                # the Mac copy is fetched only here.  The child is born on
                # the controller so it can reach the selected evaluation
                # target (and, for self-test, use the approved Helium session).
                local_receipt = paths(source)["records"] / "save.json"
                local_saved = json.loads(local_receipt.read_text()) if local_receipt.is_file() else {}
                if not (local_saved.get("saved") is True and local_saved.get("storage_root") == str(source)):
                    local_saved = save(source)
                if local_saved.get("saved") is not True:
                    raise RuntimeError(f"source data save incomplete: {local_saved}")
                from .evaluate import evaluate_run, freeze_application
                source_state = manifest(source)
                source_state["lifecycle"] = local_saved["lifecycle"]
                write_json(paths(source)["manifest"], source_state)
                snapshot = freeze_application(source)
                kind = configuration["kind"]
                result = evaluate_run(source, kind=kind, snapshot=snapshot,
                                      configuration=configuration)
                mirrored.append({"request_id": request_id, "kind": kind,
                                 "run": result, "source_run": source.name,
                                 "dispatch": "mac-controller-evaluation"})
            except Exception as error:
                skipped.append({"index": index, "request_id": request_id,
                                "reason": f"evaluation_dispatch:{type(error).__name__}: {error}"})
            continue
        child = item.get("run") if isinstance(item, dict) else None
        if not isinstance(child, dict):
            skipped.append({"index": index, "reason": "missing_saved_child_receipt"})
            continue
        child_id = child.get("run_id")
        remote_value = child.get("path")
        if not isinstance(child_id, str) or not child_id or Path(child_id).name != child_id:
            skipped.append({"index": index, "reason": "invalid_child_run_id"})
            continue
        if not isinstance(remote_value, str) or not Path(remote_value).is_absolute():
            skipped.append({"index": index, "run_id": child_id, "reason": "missing_remote_child_path"})
            continue
        remote_child = Path(remote_value)
        if remote_child.name != child_id or remote_child.parent != source_remote.parent:
            skipped.append({"index": index, "run_id": child_id, "reason": "child_path_outside_remote_run_root"})
            continue
        local_child = run_root / child_id
        local_manifest = local_child / "manifest.json"
        if not local_manifest.exists():
            if local_child.exists():
                skipped.append({"index": index, "run_id": child_id, "reason": "local_child_path_conflict"})
                continue
            local_child.mkdir(parents=True, exist_ok=False)
            for relative in ("program", "inputs", "data/workspace", "data/harness", "records", "snapshots", "evaluations"):
                (local_child / relative).mkdir(parents=True, exist_ok=True)
            if not _remote_file(host, remote_child / "manifest.json", local_manifest):
                shutil.rmtree(local_child)
                skipped.append({"index": index, "run_id": child_id, "reason": "remote_child_manifest_unavailable"})
                continue
        try:
            child_manifest = manifest(local_child)
            if child_manifest.get("run_kind") != "evaluation" or child_manifest.get("evaluation_kind") != "task":
                skipped.append({"index": index, "run_id": child_id, "reason": "unsupported_child_kind"})
                continue
            child_target = deepcopy(child_manifest.get("target_config") or {})
            child_target["executor"] = target["executor"]
            child_target["remote_root"] = target["remote_root"]
            child_manifest["target_config"] = child_target
            child_manifest["target_kind"] = "local"
            child_manifest["remote_origin"] = {"host": host, "path": str(remote_child),
                                                 "source_run": source.name, "source_receipt": str(receipt_path)}
            write_json(local_manifest, child_manifest)
        except (OSError, ValueError, TypeError) as error:
            skipped.append({"index": index, "run_id": child_id,
                            "reason": f"invalid_child_manifest:{type(error).__name__}"})
            continue
        # A task-evaluation child may also have inherited an application log.
        # Mirror only its non-secret byte boundary so the relay's remote
        # observer can produce correctly scoped process logs; no credentials
        # or SDK workspace are needed for this handoff.
        _remote_file(host, remote_child / "records/agent-log-baseline.json",
                     local_child / "records/agent-log-baseline.json")
        relay_record = local_child / "records/relay.json"
        alive = False
        if relay_record.is_file():
            try:
                from .control import process_state
                alive = process_state(json.loads(relay_record.read_text())) == "alive"
            except (OSError, ValueError, TypeError):
                alive = False
        if not alive:
            from lab import run as public_run
            public_run._background(local_child, "lab.automation", ["relay", str(local_child)], "relay")
        mirrored.append({"run_id": child_id, "path": str(local_child), "relay_started": not alive,
                         "remote_path": str(remote_child), "source_run": source.name})
    return {"mirrored": mirrored, "skipped": skipped,
            "status": "completed" if not skipped else "partial"}


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
