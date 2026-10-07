"""Public run API shared by CLI and ordinary Python automation.

Execution adapters own the real platform handles. Queries read saved records;
neither a query nor the Console creates another observation loop.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

from .arc_bench import run_layout
from .records import write_json
from .control import process_identity, process_state

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {"completed", "failed", "stopped"}


def run_root():
    path = Path(os.environ.get("LAB_RUN_ROOT", ROOT / "runs/lab")).expanduser().resolve()
    run_layout.storage_path(path)
    return path


def resolve(run):
    candidate = Path(run).expanduser()
    if not (candidate / "manifest.json").is_file():
        if candidate.name != str(run) or str(run) in {".", ".."}:
            raise FileNotFoundError(f"run manifest not found: {candidate / 'manifest.json'}")
        candidate = run_root() / "runs" / str(run)
    candidate = candidate.resolve(strict=True)
    run_layout.storage_path(candidate)
    manifest = run_layout.manifest(candidate)
    if manifest.get("record_type") != "arc.run":
        raise ValueError(f"not a current ARC run: {candidate}; historical records use lab.exp/history")
    return candidate


def status(run=None, *, include_all=False):
    """Read saved execution facts and the variant's saved activity judgment."""
    if run is None:
        directory = run_root() / "runs"
        rows = [status(path) for path in directory.iterdir()
                if path.is_dir() and (path / "manifest.json").is_file()] if directory.is_dir() else []
        return sorted((row for row in rows if include_all or
                       (not row.get("archived") and row.get("lifecycle") != "completed")),
                      key=lambda row: row.get("created_at") or 0, reverse=True)
    path = resolve(run)
    manifest = run_layout.manifest(path)
    saved = path / "records/status.json"
    if saved.is_file():
        try:
            facts = json.loads(saved.read_text())
            if not isinstance(facts, dict):
                raise ValueError("saved status must be an object")
        except (OSError, ValueError) as exc:
            facts = {"lifecycle": "unknown", "activity": "unknown", "as_of": None,
                     "error": f"{saved}: {type(exc).__name__}: {exc}"}
    else:
        facts = {"lifecycle": "starting", "activity": "unknown", "brief": "尚无执行观察",
                 "as_of": manifest.get("created_at")}
    archive_path = path / "records/archive.json"
    archived = json.loads(archive_path.read_text()).get("archived", False) if archive_path.is_file() else False
    return {**manifest, **facts, "path": str(path), "archived": archived}


def _background(run, module, args, name):
    target = run_layout.manifest(run).get('target_config') or {}
    if name != 'relay' and target.get('kind') == 'local' and target.get('executor') != 'local':
        from .arc_bench.local_run import spawn
        receipt = spawn(run, module, args, name=name)
        write_json(run / 'records' / f'{name}.json', receipt)
        if name == 'supervisor':
            _background(run, 'lab.automation', ['relay', run], 'relay')
        return receipt.get('pid')
    records = run / "records"
    with (records / f"{name}.log").open("ab") as output:
        env = dict(os.environ, LAB_RUN=str(run), LAB_RUN_ROOT=str(run_root()))
        process = subprocess.Popen([sys.executable, "-m", module, *map(str, args)],
                                   cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    write_json(records / f"{name}.json", {**process_identity(process.pid),
                                          "module": module, "arguments": list(map(str, args)),
                                          "started_at": time.time()})
    return process.pid


def publish(path):
    """Publish saved facts; Console failure never changes execution status."""
    from .backend import publish_run, saved_record_summaries
    path = resolve(path)
    manifest = run_layout.manifest(path)
    config = manifest.get("observability") or {}
    if not config.get("service_url"):
        return
    try:
        token_file = config.get("registration_token_file")
        collector_file = config.get("collector_token_file")
        credentials = []
        for filename in (token_file, collector_file):
            if filename:
                source = Path(filename)
                if not source.is_absolute():
                    source = path / source
                credentials.append(source.read_text().strip())
            else:
                credentials.append(None)
        token, collector = credentials
        row = status(path)
        facts = {key: row[key] for key in (
            "lifecycle", "activity", "brief", "as_of", "last_activity_at", "evidence",
            "native", "spend", "resources", "error", "observation_failed_at"
        ) if key in row}
        records = saved_record_summaries(path)
        published = publish_run(config["service_url"], {**manifest, "archived": row["archived"]},
                                status=facts, records=records, token=token, collector_token=collector)
        write_json(path / "records/console-publish.json", {"as_of": time.time(), "published": True,
                   "run_id": published.get("run_id", path.name)})
    except Exception as exc:
        write_json(path / "records/console-publish.json", {"as_of": time.time(), "published": False,
                   "error": f"{type(exc).__name__}: {exc}"})


def start(variant, target, task, *, route=None, competition=False, script=None):
    """Assemble inputs, directly dispatch, then detach observation and automation."""
    from .arc_bench import execution
    if script:
        import shutil
        source = Path(script).resolve(strict=True)
    path = run_layout.create_run(run_root(), variant, target, str(task), route=route,
                                 competition=competition)
    try:
        if script:
            destination = path / "records/automation.py"
            shutil.copy2(source, destination)
        execution.assemble(path)
        execution.start(path)
    except Exception as exc:
        # The adapter may already have recorded an uncertain platform write.
        # An exception is not evidence that a dispatched execution failed.
        saved = path / "records/status.json"
        if not saved.is_file():
            write_json(saved, {"lifecycle": "failed", "activity": "unknown",
                       "as_of": time.time(), "error": f"{type(exc).__name__}: {exc}"})
        raise
    _background(path, "lab.automation", ["observe", path], "supervisor")
    if script:
        target_config = run_layout.manifest(path).get('target_config') or {}
        if target_config.get('kind') == 'local' and target_config.get('executor') != 'local':
            from .arc_bench.local_run import spawn
            receipt = spawn(path, '', [], script=destination, name='automation')
            write_json(path / 'records/automation.json', receipt)
        else:
            with (path / "records/automation.log").open("ab") as output:
                process = subprocess.Popen([sys.executable, str(destination)], cwd=ROOT,
                             env=dict(os.environ, LAB_RUN=str(path), LAB_RUN_ROOT=str(run_root())),
                             stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            write_json(path / "records/automation.json", {**process_identity(process.pid),
                        "source": str(destination), "started_at": time.time()})
    else:
        _background(path, "lab.automation", ["default", path], "automation")
    return status(path)


def _control(run, action):
    from .arc_bench import execution
    path = resolve(run)
    return execution.control(path, action)


def stop(run):
    """Stop only this run; its supervisor continues saving available results."""
    return _control(run, "stop")


def pause(run):
    return _control(run, "pause")


def resume(run):
    return _control(run, "resume")


def restart(run, *, target=None, task=None, route=None, snapshot=None):
    from .arc_bench.restart import restart as restart_run
    result = restart_run(resolve(run), target=target, task=task, route=route, snapshot=snapshot)
    path = resolve(result["path"] if isinstance(result, dict) else result)
    _background(path, "lab.automation", ["observe", path], "supervisor")
    _background(path, "lab.automation", ["default", path], "automation")
    return status(path)


def wait(run):
    """Wait for this run's saved terminal record, without platform polling."""
    path = resolve(run)
    while True:
        row = status(path)
        if row.get("lifecycle") in TERMINAL:
            return row
        supervisor = path / "records/supervisor.json"
        if supervisor.is_file() and process_state(json.loads(supervisor.read_text())) == "lost":
            raise RuntimeError(f"observer exited before a confirmed terminal record: {supervisor}; "
                               "actual execution may still be running; see saved logs")
        time.sleep(2)


def archive(run, *, undo=False):
    path = resolve(run)
    write_json(path / "records/archive.json", {"archived": not undo, "as_of": time.time()})
    publish(path)
    return status(path)


def logs(run, *, follow=False):
    path = resolve(run)
    cursors = {}
    while True:
        for log in sorted((path / "records").glob("*.log")):
            with log.open("rb") as stream:
                stream.seek(cursors.get(log, 0))
                first_chunk = True
                while chunk := stream.read(65536):
                    if first_chunk:
                        metadata = log.with_name(log.name + ".meta.json")
                        boundary = json.loads(metadata.read_text()) if metadata.is_file() else {}
                        suffix = "; 包含迁移历史，当前 run 边界未知" if boundary.get("retained_history") else ""
                        sys.stdout.write(f"\n--- {log.name}{suffix} ---\n")
                        first_chunk = False
                    sys.stdout.write(chunk.decode(errors="replace"))
                cursors[log] = stream.tell()
        sys.stdout.flush()
        if not follow or status(path).get("lifecycle") in TERMINAL:
            return
        time.sleep(1)


def evaluate(run, *, kind, snapshot=None, configuration=None):
    from .arc_bench.evaluate import evaluate_run
    return evaluate_run(resolve(run), kind=kind, snapshot=snapshot, configuration=configuration)
