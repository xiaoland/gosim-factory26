"""Run independent local experiments and preserve their raw evidence."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import sys
from threading import Event, Lock
import time

from otlp_store import SIGNALS, initialize, list_batches, read_batch, receiver


NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def save_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def snapshot(source, destination):
    source = Path(source).expanduser().resolve(strict=True)
    if any(item.is_symlink() for item in (source, *source.rglob("*"))):
        raise ValueError(f"input contains a symbolic link: {source}")
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    elif source.is_dir():
        shutil.copytree(source, destination)
    else:
        raise ValueError(f"input must be a file or directory: {source}")
    digest = hashlib.sha256()
    paths = [destination] if destination.is_file() else sorted(
        (item for item in destination.rglob("*") if item.is_file()), key=lambda item: str(item.relative_to(destination)))
    for item in paths:
        relative = item.name if destination.is_file() else str(item.relative_to(destination))
        digest.update(relative.encode())
        digest.update(b"\0")
        with item.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return {"source": str(source), "sha256": digest.hexdigest(), "kind": "file" if destination.is_file() else "directory"}


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError(f"path must stay within this run: {value}")
    return path


def job_name(job):
    label = "-".join(str(job[key]) for key in ("variant", "competition", "task"))
    return re.sub(r"[^a-z0-9-]+", "-", label.lower()).strip("-")[:70] or "run"


def prepare(job, root, server):
    if not isinstance(job.get("inputs"), dict) or not job["inputs"]:
        raise ValueError("each job requires named, frozen inputs")
    if not isinstance(job.get("command"), list) or not job["command"] or not all(
            isinstance(arg, str) for arg in job["command"]):
        raise ValueError("each job requires an argv command")
    for key in ("variant", "competition", "task"):
        if not isinstance(job.get(key), str) or not job[key]:
            raise ValueError(f"each job requires {key}")
    run_id = job_name(job) + "-" + secrets.token_hex(5)
    run = root / run_id
    run.mkdir(parents=True)
    (run / "inputs").mkdir()
    (run / "workspace").mkdir()
    (run / "artifacts").mkdir()
    mapping = {"run_dir": str(run), "workspace": str(run / "workspace"),
               "artifacts": str(run / "artifacts")}
    frozen = {}
    for name, source in job["inputs"].items():
        if not NAME.fullmatch(name) or name in mapping:
            raise ValueError(f"invalid input name: {name}")
        source = Path(source).expanduser().resolve(strict=True)
        destination = run / "inputs" / name / source.name if source.is_file() else run / "inputs" / name
        frozen[name] = snapshot(source, destination)
        mapping[name] = str(destination)
    def expand(argument):
        def substitute(match):
            if match[1] not in mapping:
                raise ValueError(f"unknown command placeholder: {match[1]}")
            return mapping[match[1]]
        return PLACEHOLDER.sub(substitute, argument)
    command = [expand(argument) for argument in job["command"]]
    result_path = safe_relative(job.get("result_path", "workspace/experiment-result.json"))
    artifacts = [safe_relative(item) for item in job.get("artifact_paths", [])]
    database = run / "telemetry.sqlite"
    initialize(database)
    token = secrets.token_urlsafe(24)
    server.register(token, database)
    state = {"schema_version": 1, "run_id": run_id, "phase": "queued",
             "variant": job["variant"], "competition": job["competition"], "task": job["task"],
             "venue": job.get("venue", "local"), "inputs": frozen, "command": command,
             "result_path": str(result_path), "artifact_paths": [str(item) for item in artifacts],
             "created_at": time.time()}
    save_json(run / "run.json", state)
    return run, state, command, result_path, artifacts, token


def collect_artifacts(run, paths):
    collected = []
    workspace = (run / "workspace").resolve()
    for relative in paths:
        source = run / relative
        target = run / "artifacts" / relative
        record = {"path": str(relative)}
        try:
            resolved = source.resolve(strict=True)
            if not resolved.is_relative_to(workspace):
                raise ValueError("artifact must be inside the run workspace")
            if source.is_symlink() or resolved.is_dir() and any(item.is_symlink() for item in resolved.rglob("*")):
                raise ValueError("artifact contains a symbolic link")
            if resolved.is_dir():
                shutil.copytree(resolved, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(resolved, target)
            record["status"] = "collected"
            record["archive"] = str(target.relative_to(run))
        except FileNotFoundError:
            record["status"] = "missing"
        except (OSError, ValueError) as exc:
            record.update(status="failed", error=str(exc))
        collected.append(record)
    return collected


class Processes:
    def __init__(self):
        self.active = set()
        self.lock = Lock()
        self.interrupted = Event()

    def add(self, process):
        with self.lock:
            self.active.add(process)
            if self.interrupted.is_set():
                self._terminate(process)

    def remove(self, process):
        with self.lock:
            self.active.discard(process)

    @staticmethod
    def _terminate(process):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def stop(self):
        self.interrupted.set()
        with self.lock:
            running = list(self.active)
            for process in running:
                self._terminate(process)
        deadline = time.monotonic() + 5
        for process in running:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


def execute(prepared, server, processes):
    """运行已准备的 argv，保存退出码，并采用适配器结果中的完成状态。

    completed 表示适配器报告完成，不表示应用满分。
    产物采集及 telemetry 记录各自的结果，收到批次不证明诊断内容完整。
    """
    run, state, command, result_path, artifacts, token = prepared
    state.update(phase="running", started_at=time.time())
    save_json(run / "run.json", state)
    env = dict(os.environ)
    endpoint = f"http://127.0.0.1:{server.server_port}"
    env.update(OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,
               OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf",
               OTEL_EXPORTER_OTLP_HEADERS=f"x-experiment-token={token}",
               OTEL_EXPORTER_OTLP_COMPRESSION="none",
               EXPERIMENT_RUN_DIR=str(run), EXPERIMENT_ARTIFACT_DIR=str(run / "artifacts"))
    process = None
    try:
        with (run / "stdout.log").open("wb") as stdout, (run / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, cwd=run / "workspace", env=env,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            processes.add(process)
            state["runner_exit_code"] = process.wait()
        result_file = run / result_path
        if result_file.is_file():
            result = json.loads(result_file.read_text())
            if not isinstance(result, dict) or result.get("schema_version") != 1:
                raise ValueError("runner result must be a schema_version=1 object")
            state["result"] = result
            state["phase"] = "completed" if result.get("status") == "completed" else "failed"
        else:
            state["phase"] = "failed"
            state["error"] = "runner produced no result; inspect stdout.log and stderr.log"
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        state.update(phase="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        if process is not None:
            processes.remove(process)
        if processes.interrupted.is_set():
            state["phase"] = "interrupted"
        state["artifacts"] = collect_artifacts(run, artifacts)
        batches = list_batches(run / "telemetry.sqlite")
        state["telemetry"] = {"status": "received" if batches else "absent",
                              "batches": len(batches),
                              "signals": {name: sum(batch["signal"] == name for batch in batches)
                                          for name in SIGNALS.values()}}
        state["finished_at"] = time.time()
        save_json(run / "run.json", state)
    return state


def run_manifest(manifest_path, runs_root, max_parallel=None, listen_host="127.0.0.1"):
    manifest_path = Path(manifest_path).resolve(strict=True)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("jobs"), list) or not manifest["jobs"]:
        raise ValueError("manifest needs schema_version=1 and a nonempty jobs list")
    workers = max_parallel if max_parallel is not None else manifest.get("max_parallel", 1)
    if not isinstance(workers, int) or not 1 <= workers <= 64:
        raise ValueError("max_parallel must be in 1..64")
    root = Path(runs_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    processes = Processes()
    with receiver(listen_host) as server:
        jobs = []
        for job in manifest["jobs"]:
            resolved = dict(job)
            resolved["inputs"] = {name: str((manifest_path.parent / source).resolve())
                                  for name, source in job["inputs"].items()}
            jobs.append(resolved)
        prepared = [prepare(job, root, server) for job in jobs]
        for item in prepared:
            print(json.dumps({"run_id": item[1]["run_id"], "phase": "queued",
                              "evidence": str(item[0])}, ensure_ascii=False), flush=True)
        pool = ThreadPoolExecutor(max_workers=workers)
        try:
            futures = [pool.submit(execute, item, server, processes) for item in prepared]
            for future in as_completed(futures):
                state = future.result()
                line = {"run_id": state["run_id"], "phase": state["phase"],
                        "evidence": str(root / state["run_id"])}
                if isinstance(state.get("result"), dict) and "summary" in state["result"]:
                    line["summary"] = state["result"]["summary"]
                print(json.dumps(line, ensure_ascii=False), flush=True)
        except KeyboardInterrupt:
            processes.stop()
            raise
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
    return [json.loads((item[0] / "run.json").read_text()) for item in prepared]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run", help="run every manifest job with bounded parallelism")
    run.add_argument("manifest", type=Path)
    run.add_argument("--runs-root", type=Path, required=True)
    run.add_argument("--max-parallel", type=int)
    run.add_argument("--listen-host", default="127.0.0.1")
    status = commands.add_parser("status", help="read saved run state")
    status.add_argument("run", type=Path)
    telemetry = commands.add_parser("telemetry", help="list or export raw OTLP batches")
    telemetry.add_argument("run", type=Path)
    telemetry.add_argument("--signal", choices=tuple(SIGNALS.values()))
    telemetry.add_argument("--since", type=float, help="inclusive Unix timestamp")
    telemetry.add_argument("--until", type=float, help="exclusive Unix timestamp")
    telemetry.add_argument("--export", type=Path)
    args = parser.parse_args()
    if args.action == "run":
        states = run_manifest(args.manifest, args.runs_root, args.max_parallel, args.listen_host)
        return 0 if all(item["phase"] == "completed" for item in states) else 1
    if args.action == "status":
        from inspect_runs import show_run
        print(json.dumps(show_run(args.run), ensure_ascii=False, indent=2))
        return 0
    database = args.run / "telemetry.sqlite"
    rows = list_batches(database, args.signal, args.since, args.until)
    if args.export:
        args.export.mkdir(parents=True, exist_ok=True)
        for row in rows:
            _, payload = read_batch(database, row["id"])
            (args.export / f'{row["id"]:06d}-{row["signal"]}.pb').write_bytes(payload)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
