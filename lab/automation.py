"""Ordinary Python automation; no experiment controller or future-job queue."""
import argparse
import json
from pathlib import Path
import time

from . import run
from .records import write_json
from .control import process_state


def observe(path):
    """Own observation and recovery of exactly one dispatched run."""
    from .arc_bench import execution
    path = run.resolve(path)
    while True:
        try:
            facts = execution.observe(path)
        except Exception as exc:
            prior = run.status(path)
            facts = {"lifecycle": prior.get("lifecycle", "unknown"), "activity": "unknown",
                     "as_of": prior.get("as_of"), "observation_failed_at": time.time(),
                     "error": f"{type(exc).__name__}: {exc}"}
            write_json(path / "records/observation-error.json", facts)
        write_json(path / "records/status.json", facts)
        run.publish(path)
        if facts.get("lifecycle") in run.TERMINAL:
            try:
                saved = execution.save(path)
                write_json(path / "records/result-save.json", saved)
                run.publish(path)
                if saved.get("saved") is True:
                    return
            except Exception as exc:
                write_json(path / "records/result-save.json", {"saved": False,
                           "error": f"{type(exc).__name__}: {exc}", "as_of": time.time()})
        manifest = run.run_layout.manifest(path)
        interval = manifest.get("observation_interval", 10)
        if manifest.get("target_kind") == "hosted":
            age = time.time() - manifest.get("created_at", time.time())
            interval = 180 if age < 600 else 480
        time.sleep(interval)


def default(path):
    """The sole automatic evaluation initiator for a normal single-task run."""
    path = run.resolve(path)
    terminal = run.wait(path)
    if terminal["lifecycle"] != "completed":
        return
    task = run.run_layout.manifest(path).get("task_config", {})
    entries = task.get("evaluations", [])
    if not entries:
        return
    while True:
        save = path / "records/result-save.json"
        if save.is_file() and json.loads(save.read_text()).get("saved") is True:
            break
        supervisor = path / "records/supervisor.json"
        if supervisor.is_file() and process_state(json.loads(supervisor.read_text())) == "lost":
            raise RuntimeError(f"run terminal but result recovery has not completed: {save}")
        time.sleep(2)
    from .arc_bench.evaluate import freeze_application, evaluate_run
    snapshot = freeze_application(path)
    launched = []
    for entry in entries:
        try:
            result = evaluate_run(path, kind=entry["kind"], snapshot=snapshot, configuration=entry)
            launched.append({"configuration": entry, "run": result})
        except Exception as exc:
            launched.append({"configuration": entry, "error": f"{type(exc).__name__}: {exc}"})
        write_json(path / "records/automatic-evaluations.json", {"snapshot": str(snapshot),
                   "items": launched, "as_of": time.time()})


def relay(path):
    """Recover saved remote records; never run a second execution observer."""
    from .arc_bench.local_run import sync_saved, save
    path = run.resolve(path)
    while True:
        synced = sync_saved(path)
        if synced.get('synced'):
            row = run.status(path)
            run.publish(path)
            receipt = path / 'records/result-save.json'
            if row.get('lifecycle') in run.TERMINAL and receipt.is_file():
                if json.loads(receipt.read_text()).get('saved') is True:
                    recovered = save(path)
                    write_json(receipt, recovered)
                    if recovered.get('saved') is True:
                        state = run.run_layout.manifest(path)
                        state['lifecycle'] = row['lifecycle']
                        run.run_layout.write_manifest(path, state)
                        run.publish(path)
                        return
        time.sleep(10)


def stages(initial_run, tasks):
    """Continue only normal completion, preserving same-variant data per stage."""
    current = run.resolve(initial_run)
    results = []
    for task in tasks:
        terminal = run.wait(current)
        results.append(terminal)
        if terminal["lifecycle"] != "completed":
            return results
        next_run = run.restart(current, task=task)
        current = Path(next_run["path"])
    results.append(run.wait(current))
    return results


def facts(path):
    """Saved observations include spend/native/resources with source and as_of."""
    return run.status(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "default", "relay"))
    parser.add_argument("run")
    args = parser.parse_args(argv)
    {'observe': observe, 'default': default, 'relay': relay}[args.mode](args.run)


if __name__ == "__main__":
    main()
