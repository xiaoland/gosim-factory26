"""Freeze a reusable experiment plan before any command is dispatched."""

import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import time

from .records import inventory, merge_labels, read_json, write_json


def normalize(manifest, base):
    version = manifest.get("schema_version")
    if version not in (1, 2) or not isinstance(manifest.get("jobs"), list) or not manifest["jobs"]:
        raise ValueError("manifest must contain schema_version 1 or 2 and a nonempty jobs list")
    jobs = []
    used = set()
    for index, value in enumerate(manifest["jobs"], 1):
        if not isinstance(value, dict):
            raise ValueError(f"job {index} must be an object")
        inputs = value.get("inputs", {})
        command = value.get("command")
        if not isinstance(inputs, dict) or not isinstance(command, list) or not command or not all(
                isinstance(arg, str) for arg in command):
            raise ValueError(f"job {index} needs named inputs and argv")
        if any(not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name) or
               name in ("run_id", "run_dir", "workspace", "artifacts") for name in inputs):
            raise ValueError(f"job {index} has an invalid or reserved input name")
        if version == 1 and (not inputs or any(not value.get(name) for name in ("variant", "competition", "task"))):
            raise ValueError(f"v1 job {index} requires inputs, variant, competition and task")
        labels = merge_labels(
            {key: value[key] for key in ("competition", "variant", "task", "venue") if key in value},
            value.get("labels", {}))
        job_id = value.get("id") or f"job-{index:04d}"
        if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", job_id) or job_id in used:
            raise ValueError(f"duplicate or invalid job ID: {job_id}")
        used.add(job_id)
        handlers = value.get("resource_handlers", {})
        if not isinstance(handlers, dict) or any(name not in ("inspect", "cleanup") or
            not isinstance(argv, list) or not argv or not all(
                isinstance(arg, str) for arg in argv) and not all(
                    isinstance(command, list) and command and all(isinstance(arg, str) for arg in command)
                    for command in argv) for name, argv in handlers.items()):
            raise ValueError(f"invalid resource handlers for {job_id}")
        if ("result_path" in value and not isinstance(value["result_path"], str)) or not isinstance(
                value.get("artifact_paths", []), list) or not all(
                    isinstance(path, str) for path in value.get("artifact_paths", [])):
            raise ValueError(f"invalid result or artifact paths for {job_id}")
        if value.get("source_application") and not isinstance(value["source_application"], dict):
            raise ValueError(f"invalid application provenance for {job_id}")
        result = {"id": job_id, "labels": labels, "inputs": {}, "command": command,
                  "artifact_paths": value.get("artifact_paths", []),
                  "adapter_kind": value.get("adapter_kind") or ("arc-bench" if version == 1 else None)}
        if "result_path" in value or version == 1:
            result["result_path"] = value.get("result_path", "workspace/experiment-result.json")
        if handlers:
            result["resource_handlers"] = handlers
        if value.get("source_application"):
            result["source_application"] = value["source_application"]
        for name, source in inputs.items():
            if not isinstance(source, str) or not source:
                raise ValueError(f"invalid {job_id} input {name}")
            result["inputs"][name] = str((base / source).expanduser().resolve())
        jobs.append(result)
    slots = manifest.get("max_parallel", 1)
    if type(slots) is not int or slots < 1:
        raise ValueError("max_parallel must be a positive integer")
    return jobs, slots


def freeze_input(source, directory):
    staging = directory.with_name(directory.name + ".partial")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    origin = Path(source).resolve(strict=True)
    if origin.is_file():
        shutil.copy2(origin, staging / origin.name)
        content = origin.name
    elif origin.is_dir():
        shutil.copytree(origin, staging / "content", symlinks=True)
        content = "content"
    else:
        raise ValueError(f"input must be file or directory: {origin}")
    identity = inventory(staging / content)
    identity.update(source=str(origin), content=content)
    write_json(staging / "input.json", identity)
    staging.replace(directory)
    return identity


def freeze_controller(experiment):
    source = Path(__file__).resolve().parent
    target = experiment / "controller-source"
    staging = experiment / "controller-source.partial"
    package = staging / "lab"
    package.mkdir(parents=True)
    for path in source.glob("*.py"):
        shutil.copy2(path, package / path.name)
    (package / "__init__.py").touch(exist_ok=True)
    staging.replace(target)
    return inventory(target)


def create(manifest_path, *, experiment_root=None, runs_root=None, max_parallel=None):
    manifest_path = Path(manifest_path).expanduser().resolve(strict=True)
    raw = read_json(manifest_path)
    jobs, slots = normalize(raw, manifest_path.parent)
    if max_parallel is not None:
        if type(max_parallel) is not int or max_parallel < 1:
            raise ValueError("max_parallel must be a positive integer")
        slots = max_parallel
    if (experiment_root is None) == (runs_root is None):
        raise ValueError("choose exactly one of experiment_root and runs_root")
    if runs_root is not None:
        runs = Path(runs_root).expanduser().resolve()
        runs.mkdir(parents=True, exist_ok=True)
        parent = runs / ".experiments"
    else:
        parent = Path(experiment_root).expanduser().resolve().parent
    experiment_id = f"exp-{time.strftime('%Y%m%d-%H%M%S')}-{os.urandom(3).hex()}"
    experiment = parent / experiment_id if runs_root is not None else Path(experiment_root).expanduser().resolve()
    experiment.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest_path, experiment / "recipe.json")
    preparation_log = experiment / "preparation.jsonl"
    def record(kind, **details):
        with preparation_log.open("a") as stream:
            stream.write(json.dumps({"time": time.time(), "kind": kind, **details}, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    record("plan-created", recipe=str(experiment / "recipe.json"), jobs=len(jobs))
    if runs_root is None:
        runs = experiment / "runs"
        runs.mkdir()
    (experiment / "inputs").mkdir()
    (experiment / "controllers").mkdir()
    (experiment / "analysis").mkdir()
    source_controller = freeze_controller(experiment)
    record("controller-frozen", sha256=source_controller["sha256"])
    by_source = {}
    for job in jobs:
        frozen = {}
        errors = []
        for name, source in job["inputs"].items():
            if source not in by_source:
                input_id = f"input-{len(by_source) + 1:04d}"
                try:
                    identity = freeze_input(source, experiment / "inputs" / input_id)
                    by_source[source] = {"id": input_id, **identity}
                    record("input-frozen", input_id=input_id, source=source, sha256=identity["sha256"])
                except (OSError, ValueError) as exc:
                    by_source[source] = {"error": f"{type(exc).__name__}: {exc}", "source": source}
                    record("input-failed", input_id=input_id, source=source, error=str(exc))
            frozen_source = by_source[source]
            if "error" in frozen_source:
                errors.append({"input": name, **frozen_source})
            else:
                frozen[name] = {"id": frozen_source["id"], "content": frozen_source["content"],
                                "sha256": frozen_source["sha256"], "algorithm": frozen_source["algorithm"]}
        job["inputs"] = frozen
        job["preparation"] = {"status": "failed" if errors else "ready", "errors": errors}
    final = {"schema_version": 2, "record_type": "lab.experiment", "experiment_id": experiment_id,
             "source_manifest": str(manifest_path), "created_at": time.time(), "host": socket.gethostname(),
             "python": sys.version, "working_directory": os.getcwd(),
             "runs_root": os.path.relpath(runs, experiment), "max_parallel": slots,
             "controller_source": source_controller, "jobs": jobs,
             "comparison": raw.get("comparison")}
    write_json(experiment / "manifest.json", final)
    record("plan-published", ready=sum(job["preparation"]["status"] == "ready" for job in jobs),
           failed=sum(job["preparation"]["status"] == "failed" for job in jobs))
    return experiment
