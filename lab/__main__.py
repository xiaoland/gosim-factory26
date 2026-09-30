"""Local experiment CLI. Human and JSON views read the same saved facts."""

import argparse
import codecs
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from .assets import frozen_host_runtime
from .control import owner_state, process_start, send, wait_for_change
from .otlp import SIGNALS, database_for_run, export_batches, list_batches, list_receive_errors, new_session, receiver
from .plan import create
from .records import read_json, write_json
from .run import _expand, controller, start
from .status import experiment_summary, read_status, show


def _experiment_for_run(run):
    run = Path(run).expanduser().resolve(strict=True)
    row = read_status(run)
    candidate = run.parent.parent
    if (candidate / "manifest.json").is_file() and read_json(candidate / "manifest.json").get(
            "experiment_id") == row.get("experiment_id"):
        return candidate
    candidate = run.parent / ".experiments" / row["experiment_id"]
    if (candidate / "manifest.json").is_file():
        return candidate
    raise ValueError(f"cannot locate frozen experiment for run: {run}")


def _events(experiment, after=None):
    experiment = Path(experiment)
    controllers = sorted((experiment / "controllers").glob("*/controller.json"),
                         key=lambda p: read_json(p).get("started_at", 0))
    rows = []
    skip = bool(after)
    for owner_path in controllers:
        log = owner_path.parent / "notifications.jsonl"
        if not log.is_file():
            continue
        for line in log.read_text().splitlines():
            row = json.loads(line)
            cursor = f"{row['controller_id']}:{row['seq']}"
            if skip:
                if cursor == after:
                    skip = False
                continue
            rows.append({**row, "cursor": cursor})
    if skip:
        raise ValueError(f"unknown event cursor: {after}")
    return rows


def _render(value, *, all_jobs=False):
    if value["kind"] == "run":
        lines = [f"{value['run_id']} | {value['phase']} | {value['path']}"]
        if value.get("labels"):
            lines.append("标签: " + json.dumps(value["labels"], ensure_ascii=False))
        if value.get("error"):
            lines.append(f"错误: {value['error']}")
        if value.get("result_error"):
            lines.append(f"结果文件错误: {value['result_error']}")
        if value.get("telemetry_error"):
            lines.append(f"过程采集错误: {value['telemetry_error']}")
        result = value.get("result") if isinstance(value.get("result"), dict) else {}
        if result.get("error"):
            lines.append(f"结果错误: {result['error']}")
        if result.get("summary"):
            lines.append("结果: " + json.dumps(result["summary"], ensure_ascii=False))
        if value.get("telemetry"):
            telemetry = value["telemetry"]
            lines.append(f"OTLP: {telemetry.get('status', 'unknown')}，{telemetry.get('batches', 0)} 批，"
                         f"截止 ID {telemetry.get('until_batch_id')}")
        for name, path in value["evidence"].items():
            lines.append(f"{name}: {path}")
        return "\n".join(lines)
    lines = [f"实验: {value['path']}",
             f"计划任务 {value['planned_jobs']} · 尝试 {value['attempts']} · 实际启动 {value['started_attempts']}"]
    lines.append("尝试状态: " + ", ".join(f"{name} {count}" for name, count in
                                       sorted(value.get("attempt_phases", {}).items())))
    if value.get("comparison"):
        lines.append("比较意图: " + json.dumps(value["comparison"], ensure_ascii=False))
    phases = {}
    for job in value["jobs"]:
        phases[job["latest_phase"]] = phases.get(job["latest_phase"], 0) + 1
    lines.append("任务状态: " + ", ".join(f"{name} {count}" for name, count in sorted(phases.items())))
    selected = value["jobs"] if all_jobs else [job for job in value["jobs"] if job["latest_phase"] not in
                                           ("completed", "finished") or job.get("latest_result_status") not in
                                           (None, "completed") or job.get("latest_result_contract") in
                                           ("invalid", "preflight-failed") or job.get("latest_exit_code") not in
                                           (None, 0)]
    if not selected and not all_jobs:
        selected = value["jobs"][:5]
    for job in selected:
        labels = job.get("latest_labels") or job.get("labels") or {}
        label = " / ".join(str(labels.get(name) or "?") for name in ("variant", "task"))
        if labels.get("case"):
            label = labels["case"] + " | " + label
        lines.append(f"{job['job_id']} {label}: {job['latest_phase']}"
                     f" | 退出 {job.get('latest_exit_code')} | 结果 {job.get('latest_result_status') or '-'}"
                     f" | 最新 {job['latest'] or '-'} | 最近有效结果 {job['latest_valid_result'] or '-'}")
        for attempt in job["attempts"]:
            if all_jobs or attempt["run_id"] == job.get("latest"):
                name = (attempt.get("labels") or {}).get("run_name")
                if name:
                    lines.append(f"  {name} | {attempt['run_id']} | {attempt['phase']}")
    if len(selected) < len(value["jobs"]):
        lines.append(f"另有 {len(value['jobs']) - len(selected)} 个任务；使用 --all 或 --json 查看全部。")
    return "\n".join(lines)


def _session_evidence(run, session_id):
    manifest = Path(run) / "native" / "manifest.json"
    entries = read_json(manifest)["sessions"]
    matches = [entry for entry in entries if session_id in
               (entry.get("native_id"), entry.get("native_session_id"))]
    if len(matches) != 1 or not matches[0].get("native"):
        raise ValueError(f"native session not uniquely archived: {session_id}")
    return matches[0]["native"]


def _read_evidence(run, relative, offset, size):
    root = Path(run).expanduser().resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("evidence reference is not a file inside this run")
    with path.open("rb") as stream:
        line = 1
        remaining = offset
        while remaining:
            chunk = stream.read(min(65536, remaining))
            if not chunk:
                raise ValueError(f"evidence offset exceeds file size: {offset}")
            line += chunk.count(b"\n")
            remaining -= len(chunk)
        stream.seek(offset)
        content = stream.read(size)
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        decoded = decoder.decode(content, final=False)
        pending = decoder.getstate()[0]
        while pending:
            extra = stream.read(1)
            if not extra:
                decoded += decoder.decode(b"", final=True)
                break
            content += extra
            decoded += decoder.decode(extra, final=False)
            pending = decoder.getstate()[0]
        next_offset = offset + len(content)
        more = bool(stream.read(1))
    return {"path": str(path), "offset": offset, "line": line,
            "next_offset": next_offset, "next_line": line + content.count(b"\n"),
            "truncated": more, "text": decoded}


def _serve_old(run, host):
    run = Path(run).expanduser().resolve(strict=True)
    database = database_for_run(run)
    if not database.is_file():
        raise FileNotFoundError(database)
    session = new_session(database, "backfill")
    import secrets
    token = secrets.token_urlsafe(24)
    with receiver(host) as server:
        server.register(token, database, session)
        print(json.dumps({"run": str(run), "session": session,
                          "endpoint": f"http://{host}:{server.server_port}",
                          "headers": f"x-experiment-token={token}",
                          "protocol": "http/protobuf"}, ensure_ascii=False), flush=True)
        try:
            signal.pause()
        except KeyboardInterrupt:
            pass


def _resource_action(run, action):
    state = read_status(run)
    try:
        experiment = _experiment_for_run(run)
        manifest = read_json(experiment / "manifest.json")
        job = next(item for item in manifest["jobs"] if item["id"] == state["job_id"])
        commands = job.get("resource_handlers", {}).get(action)
    except (OSError, ValueError, KeyError, StopIteration):
        commands = None
    if not commands:
        return {"status": "unavailable", "reason": f"no frozen {action} handler"}
    if manifest.get("schema_version") == 3:
        try:
            frozen_host_runtime(manifest.get("controller_runtime"))
        except (OSError, ValueError) as exc:
            return {"status": "unconfirmed",
                    "reason": f"host runtime verification failed: {type(exc).__name__}: {exc}"}
    if isinstance(commands[0], str):
        commands = [commands]
    mapping = {"run_id": Path(run).name, "run_dir": str(run),
               "workspace": str(Path(run) / "workspace"), "artifacts": str(Path(run) / "artifacts")}
    for name, item in job["inputs"].items():
        source = Path(experiment) / "inputs" / item["id"] / item["content"]
        mapping[name] = str(Path(run) / "inputs" / name /
                            source.name) if source.is_file() else str(Path(run) / "inputs" / name)
    results = []
    for argv in commands:
        try:
            observed = subprocess.run(_expand(argv, mapping), cwd=Path(run) / "workspace", capture_output=True,
                                      text=True, timeout=45)
            try:
                details = json.loads(observed.stdout)
            except json.JSONDecodeError:
                details = None
            results.append({"exit_code": observed.returncode, "details": details,
                            "stdout": observed.stdout if details is None else None,
                            "stderr": observed.stderr})
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"error": f"{type(exc).__name__}: {exc}"})
    return {"status": "completed" if all(item.get("exit_code") == 0 for item in results) else "unconfirmed",
            "handlers": results}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:2] == ["telemetry", "serve"]:
        argv = ["telemetry-serve", *argv[2:]]
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    plan = commands.add_parser("plan", help="freeze one experiment without executing jobs")
    plan.add_argument("manifest", type=Path)
    plan.add_argument("--experiment-root", type=Path)
    plan.add_argument("--runs-root", type=Path)
    plan.add_argument("--max-parallel", type=int)
    run = commands.add_parser("run", help="run a source manifest or continue never-attempted jobs")
    run.add_argument("reference", type=Path)
    run.add_argument("--experiment-root", type=Path)
    run.add_argument("--runs-root", type=Path)
    run.add_argument("--max-parallel", type=int)
    run.add_argument("--listen-host", default="127.0.0.1")
    run.add_argument("--background", action="store_true")
    run.add_argument("--run-labels", type=Path, help="JSON mapping job IDs to labels for this execution")
    internal = commands.add_parser("_controller")
    internal.add_argument("experiment", type=Path)
    internal.add_argument("--retry-of", type=Path)
    internal.add_argument("--listen-host", default="127.0.0.1")
    internal.add_argument("--run-labels-json", type=json.loads)
    retry = commands.add_parser("retry", help="allocate a new attempt of an existing job")
    retry.add_argument("run", type=Path)
    retry.add_argument("--background", action="store_true")
    retry.add_argument("--run-labels", type=Path, help="new execution labels; previous attempt labels are not inherited")
    show_cmd = commands.add_parser("show")
    show_cmd.add_argument("reference", type=Path)
    show_cmd.add_argument("--json", action="store_true")
    show_cmd.add_argument("--all", action="store_true", help="show every job in the text view")
    status = commands.add_parser("status", help="read one raw run record")
    status.add_argument("run", type=Path)
    for action in ("stop", "parallel"):
        command = commands.add_parser(action)
        command.add_argument("experiment", type=Path)
        if action == "parallel":
            command.add_argument("slots", type=int)
    operation = commands.add_parser("operation", help="read a saved control operation by ID")
    operation.add_argument("experiment", type=Path)
    operation.add_argument("id")
    events = commands.add_parser("events")
    events.add_argument("experiment", type=Path)
    events.add_argument("--after")
    wait = commands.add_parser("wait")
    wait.add_argument("experiment", type=Path)
    wait.add_argument("--after")
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("reference", type=Path)
    cleanup = commands.add_parser("cleanup", help="explicitly clean frozen owned resources of one run")
    cleanup.add_argument("run", type=Path)
    gc_plan_cmd = commands.add_parser("gc-plan", help="build a read-only, receipt-bound reclamation plan")
    gc_plan_cmd.add_argument("--root", action="append", type=Path, required=True)
    gc_plan_cmd.add_argument("--asset-root", action="append", type=Path, default=[])
    gc_plan_cmd.add_argument("--protect", action="append", type=Path, default=[])
    evidence = commands.add_parser("evidence")
    evidence.add_argument("run", type=Path)
    evidence.add_argument("path", nargs="?")
    evidence.add_argument("--session", help="archived native session ID from native/manifest.json")
    evidence.add_argument("--offset", type=int, default=0)
    evidence.add_argument("--bytes", type=int, default=4096)
    trace = commands.add_parser("trace", help="cross-link saved work-item/session evidence without inference")
    trace.add_argument("run", type=Path)
    trace.add_argument("--work-item", help="exact kind:number, for example issue:6")
    trace.add_argument("--session", help="exact native session ID")
    trace.add_argument("--pid", type=int, help="exact recorded callback PID")
    trace.add_argument("--commit", help="exact recorded commit/digest")
    trace.add_argument("--tree", help="exact recorded base/head ref")
    trace.add_argument("--text", help="bounded text candidate search inside an exact scope")
    trace.add_argument("--record", help="exact native record ID; enables bounded raw read")
    trace.add_argument("--tool-call", help="exact tool call ID; returns call/result record locations")
    trace.add_argument("--offset", type=int, default=0, help="byte offset within the exact record")
    trace.add_argument("--bytes", type=int, default=4096)
    telemetry = commands.add_parser("telemetry")
    telemetry.add_argument("run", type=Path)
    telemetry.add_argument("--signal", choices=tuple(SIGNALS.values()))
    telemetry.add_argument("--since", type=float)
    telemetry.add_argument("--until", type=float)
    telemetry.add_argument("--after-id", type=int)
    telemetry.add_argument("--until-id", type=int)
    telemetry.add_argument("--limit", type=int)
    telemetry.add_argument("--errors-after-id", type=int, default=0)
    telemetry.add_argument("--errors-limit", type=int, default=100)
    telemetry.add_argument("--export", type=Path)
    backfill = commands.add_parser("telemetry-serve", help="open an explicit backfill session")
    backfill.add_argument("run", type=Path)
    backfill.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    if args.action == "plan":
        target = args.experiment_root or (None if args.runs_root else
            args.manifest.parent / f"{args.manifest.stem}.experiment-{time.time_ns()}")
        experiment = create(args.manifest, experiment_root=target, runs_root=args.runs_root,
                            max_parallel=args.max_parallel)
        print(json.dumps({"experiment": str(experiment), "summary": experiment_summary(experiment)},
                         ensure_ascii=False))
        return 0
    if args.action == "run":
        reference = args.reference.resolve(strict=True)
        if reference.is_file():
            target = args.experiment_root or (None if args.runs_root else
                reference.parent / f"{reference.stem}.experiment-{time.time_ns()}")
            experiment = create(reference, experiment_root=target, runs_root=args.runs_root,
                                max_parallel=args.max_parallel)
        else:
            experiment = reference
            if args.max_parallel is not None:
                parser.error("parallel adjustment on an existing experiment uses the parallel command")
        print(json.dumps({"experiment": str(experiment)}, ensure_ascii=False), flush=True)
        outcome = start(experiment, listen_host=args.listen_host, background=args.background,
                        run_labels=read_json(args.run_labels) if args.run_labels else None)
        return 0 if isinstance(outcome, dict) else outcome
    if args.action == "_controller":
        records = controller(args.experiment, retry_of=args.retry_of, listen_host=args.listen_host,
                             run_labels=args.run_labels_json)
        own = [row for row in records if row.get("controller") == read_json(args.experiment / "active.json")["controller_id"]]
        prepared = read_json(args.experiment / "manifest.json")["jobs"]
        return 0 if all(job["preparation"]["status"] == "ready" for job in prepared) and all(
            row.get("phase") == "finished" and (
            row.get("result", {}).get("status") == "completed" if row.get("result_path") else
            row.get("runner_exit_code") == 0) for row in own) else 1
    if args.action == "retry":
        experiment = _experiment_for_run(args.run)
        outcome = start(experiment, retry_of=args.run, background=args.background,
                        run_labels=read_json(args.run_labels) if args.run_labels else None)
        return 0 if isinstance(outcome, dict) else outcome
    if args.action == "show":
        value = show(args.reference)
        print(json.dumps(value, ensure_ascii=False, indent=2) if args.json else _render(value, all_jobs=args.all))
        return 0
    if args.action == "status":
        print(json.dumps(read_status(args.run), ensure_ascii=False, indent=2))
        return 0
    if args.action in ("stop", "parallel"):
        value = send(args.experiment, args.action, **({"slots": args.slots} if args.action == "parallel" else {}))
        print(json.dumps(value, ensure_ascii=False))
        return 0
    if args.action == "operation":
        if not re.fullmatch(r"[0-9a-f]{24}", args.id):
            parser.error("operation ID must be 24 lowercase hex characters")
        controller_paths = list((args.experiment / "controllers").glob(f"*/operations/{args.id}.request.json"))
        if len(controller_paths) != 1:
            raise ValueError(f"operation request not uniquely found: {args.id}")
        result = controller_paths[0].with_name(f"{args.id}.result.json")
        print(json.dumps({"request": read_json(controller_paths[0]),
                          "result": read_json(result) if result.is_file() else None}, ensure_ascii=False, indent=2))
        return 0
    if args.action == "events":
        print(json.dumps(_events(args.experiment, args.after), ensure_ascii=False, indent=2))
        return 0
    if args.action == "wait":
        while True:
            rows = _events(args.experiment, args.after)
            if rows:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
                return 0
            active_path = args.experiment / "active.json"
            active = read_json(active_path) if active_path.is_file() else None
            if owner_state(active) != "alive" or active.get("phase") != "running":
                print(json.dumps({"status": "controller-unavailable", "owner": owner_state(active),
                                  "experiment": str(args.experiment)}, ensure_ascii=False))
                return 2
            after = int(args.after.split(":", 1)[1]) if args.after and args.after.startswith(
                active["controller_id"] + ":") else 0
            wait_for_change(args.experiment, after)
    if args.action == "reconcile":
        reference = args.reference.resolve(strict=True)
        experiment = _experiment_for_run(reference) if (reference / "run.json").is_file() else reference
        active_path = experiment / "active.json"
        active = read_json(active_path) if active_path.is_file() else None
        observation = {"observed_at": time.time(), "owner_state": owner_state(active),
                       "owner": active, "reference": str(reference)}
        if (reference / "run.json").is_file():
            row = read_status(reference)
            observation.update(saved_phase=row.get("phase"), saved_pid=row.get("pid"),
                               process_state="alive" if row.get("pid") and
                               row.get("process_start") == process_start(row["pid"]) else "unconfirmed",
                               resources=_resource_action(reference, "inspect"))
        output = experiment / "controllers" / (active["controller_id"] if active else "orphan") / "observations"
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / f"{time.time_ns()}.json", observation)
        print(json.dumps(observation, ensure_ascii=False, indent=2))
        return 0
    if args.action == "cleanup":
        run = args.run.expanduser().resolve(strict=True)
        experiment = _experiment_for_run(run)
        state = read_status(run)
        owner = read_json(experiment / "active.json")
        if state.get("phase") == "running" and owner_state(owner) == "alive":
            raise ValueError("active run must be stopped through its controller before cleanup")
        if state.get("pid") and state.get("process_start") == process_start(state["pid"]):
            raise ValueError("the recorded process still exists; stop it before resource cleanup")
        result = _resource_action(run, "cleanup")
        output = experiment / "controllers" / owner["controller_id"] / "observations"
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / f"cleanup-{time.time_ns()}.json", {"run": str(run), **result})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "completed" else 2
    if args.action == "gc-plan":
        from .gc import plan as gc_plan
        value = gc_plan(args.root, args.asset_root, args.protect)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0 if value["complete"] else 2
    if args.action == "evidence":
        if args.path and args.session:
            parser.error("path and --session are mutually exclusive")
        path = _session_evidence(args.run, args.session) if args.session else args.path
        if path:
            if args.offset < 0 or args.bytes < 1:
                parser.error("offset must be nonnegative and bytes positive")
            value = _read_evidence(args.run, path, args.offset, args.bytes)
        else:
            value = show(args.run)["evidence"]
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    if args.action == "trace":
        # Background controller snapshots intentionally omit optional analysis modules.
        from .analysis.trace import trace as trace_run
        if args.offset < 0 or args.bytes < 1:
            parser.error("offset must be nonnegative and bytes positive")
        value = trace_run(args.run, work_item=args.work_item, session=args.session, pid=args.pid,
                          commit=args.commit, tree=args.tree, text=args.text, record=args.record,
                          tool_call=args.tool_call, offset=args.offset, size=args.bytes)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    if args.action == "telemetry":
        database = database_for_run(args.run)
        limit = args.limit if args.limit is not None else (None if args.export else 100)
        if args.export:
            value = export_batches(database, args.export, signal=args.signal, after_id=args.after_id,
                                   until_id=args.until_id, limit=limit)
        else:
            value = list_batches(database, args.signal, args.since, args.until,
                                 after_id=args.after_id, until_id=args.until_id, limit=limit)
        errors = list_receive_errors(database, after_id=args.errors_after_id, limit=args.errors_limit)
        print(json.dumps({"database": str(database), "batches": value, "next_batch_id": value[-1]["id"] if value else args.after_id,
                          "errors": errors, "next_error_id": errors[-1]["id"] if errors else args.errors_after_id},
                         ensure_ascii=False, indent=2))
        return 0
    if args.action == "telemetry-serve":
        _serve_old(args.run, args.host)
        return 0
    raise AssertionError(args.action)


if __name__ == "__main__":
    sys.exit(main())
