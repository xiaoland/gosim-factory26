"""Ordinary Python automation; no experiment controller or future-job queue."""
import argparse
import json
import os
from pathlib import Path
import time

from . import run
from .records import write_json
from .control import process_state


def _portable_after_save(path, saved, *, controller=False):
    """Create the portable package on the controller that owns the copy."""
    target = run.run_layout.manifest(path).get("target_config") or {}
    remote_source = target.get("kind") == "local" and target.get("executor") not in {None, "local"}
    if remote_source and not controller:
        # The execution host's save is only the source transport.  The Mac
        # relay owns the local copy and creates the portable package below.
        return saved
    try:
        from .portable_save import create
        package = create(path)
        return {**saved, "portable_package": package["package"],
                "portable_consistent": package["consistent"]}
    except Exception as exc:
        return {**saved, "portable_package_error": f"{type(exc).__name__}: {exc}"}


def observe(path):
    """Own observation and recovery of exactly one dispatched run."""
    from .arc_bench import execution
    path = run.resolve(path)
    while True:
        try:
            facts = execution.observe(path)
        except Exception as exc:
            # Keep the last good observation when a refresh fails.  Calling
            # run.status() here would merge the manifest into the saved status
            # and the small fallback object would erase spend/native/resource
            # facts that policies still need to reason about.
            prior = {}
            status_path = path / "records/status.json"
            try:
                value = json.loads(status_path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    prior = value
            except (OSError, ValueError, TypeError):
                pass
            facts = dict(prior)
            manifest = run.run_layout.manifest(path)
            facts.setdefault("lifecycle", manifest.get("lifecycle", "unknown"))
            facts["activity"] = "unknown"
            facts.setdefault("as_of", prior.get("as_of") or manifest.get("created_at"))
            failed_at = time.time()
            error = f"{type(exc).__name__}: {exc}"
            facts["observation_failed_at"] = failed_at
            facts["error"] = error
            write_json(path / "records/observation-error.json", {
                "lifecycle": facts["lifecycle"], "activity": "unknown",
                "as_of": facts.get("as_of"), "observation_failed_at": failed_at,
                "error": error,
            })
        write_json(path / "records/status.json", facts)
        run.publish(path)
        if facts.get("lifecycle") in run.TERMINAL:
            try:
                saved = execution.save(path)
                saved = _portable_after_save(path, saved)
                write_json(path / "records/result-save.json", saved)
                run.publish(path)
                if saved.get("saved") is True:
                    return
            except Exception as exc:
                write_json(path / "records/result-save.json", {"saved": False,
                           "error": f"{type(exc).__name__}: {exc}", "as_of": time.time()})
        manifest = run.run_layout.manifest(path)
        interval = manifest.get("observation_interval") or manifest.get("target_config", {}).get("observation_interval")
        if interval is None:
            age = time.time() - manifest.get("created_at", time.time())
            interval = (180 if age < 600 else 480) if manifest.get("target_kind") == "hosted" else 10
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
    from .arc_bench.evaluate import EVALUATION_KINDS, freeze_application, evaluate_run
    try:
        snapshot = freeze_application(path)
    except Exception as exc:
        write_json(path / "records/automatic-evaluations.json", {
            "items": [{"configuration": entry, "error": f"{type(exc).__name__}: {exc}"}
                      for entry in entries], "dispatch_complete": True, "as_of": time.time()})
        return
    launched = []
    source_target = run.run_layout.manifest(path).get("target_config") or {}
    remote_source = source_target.get("kind") == "local" and (
        source_target.get("executor") not in {None, "local"} or
        source_target.get("execution_role") == "remote"
    )
    for index, entry in enumerate(entries):
        try:
            # The controller owns the SSH topology and Helium profile.  A
            # remote execution host must not try to dispatch a child toward
            # another host (for example sfp7 -> wsl).  Keep only run-relative
            # inputs in the request; the Mac relay resolves them from its
            # saved source run.
            if remote_source and entry.get("kind") in EVALUATION_KINDS:
                deferred = dict(entry)
                for field in ("requirements", "tests"):
                    if deferred.get(field):
                        deferred[field] = f"inputs/{field}"
                launched.append({"configuration": deferred, "deferred": True,
                                 "request_id": f"{path.name}:evaluation:{entry['kind']}:{index}",
                                 "reason": "controller-evaluation-target"})
            else:
                result = evaluate_run(path, kind=entry["kind"], snapshot=snapshot, configuration=entry)
                launched.append({"configuration": entry, "run": result})
        except Exception as exc:
            launched.append({"configuration": entry, "error": f"{type(exc).__name__}: {exc}"})
        write_json(path / "records/automatic-evaluations.json", {"snapshot": str(snapshot),
                   "items": launched, "dispatch_complete": len(launched) == len(entries),
                   "as_of": time.time()})


def relay(path):
    """Recover saved remote records; never run a second execution observer."""
    from .arc_bench.local_run import sync_saved, save, mirror_saved_evaluations
    path = run.resolve(path)
    while True:
        synced = sync_saved(path)
        if synced.get('synced'):
            row = run.status(path)
            run.publish(path)
            remote_receipt = path / 'records/remote-result-save.json'
            if row.get('lifecycle') in run.TERMINAL and remote_receipt.is_file():
                if json.loads(remote_receipt.read_text()).get('saved') is True:
                    # Complete the controller copy before publishing save success
                    # or dispatching evaluations that consume that copy.
                    receipt = path / 'records/result-save.json'
                    recovered = json.loads(receipt.read_text()) if receipt.is_file() else {}
                    if not (recovered.get('saved') is True and recovered.get('storage_root') == str(path)):
                        recovered = save(path)
                    if recovered.get('saved') is True and not recovered.get('portable_package'):
                        recovered = _portable_after_save(path, recovered, controller=True)
                    write_json(receipt, recovered)
                    if recovered.get('saved') is not True:
                        time.sleep(10)
                        continue
                    entries = run.run_layout.manifest(path).get('task_config', {}).get('evaluations', [])
                    if row.get('lifecycle') == 'completed' and entries:
                        dispatched = path / 'records/automatic-evaluations.json'
                        if not dispatched.is_file():
                            time.sleep(10)
                            continue
                        evaluations = json.loads(dispatched.read_text())
                        if not (evaluations.get('dispatch_complete') or
                                len(evaluations.get('items', [])) >= len(entries)):
                            time.sleep(10)
                            continue
                        write_json(path / 'records/evaluation-relay.json', mirror_saved_evaluations(path))
                    if recovered.get('saved') is True:
                        state = run.run_layout.manifest(path)
                        state['lifecycle'] = row['lifecycle']
                        run.run_layout.write_manifest(path, state)
                        run.publish(path)
                        return
        time.sleep(10)


def stages(initial_run, tasks=None):
    """Continue only normal completion, preserving same-variant data per stage."""
    current = run.resolve(initial_run)
    origin = current
    plan = run.run_layout.manifest(origin).get('stage_plan', {})
    if tasks is None:
        tasks = plan['tasks'][1:]
    progress = {'task': plan.get('task'), 'runs': [str(current)],
                'current_run': str(current), 'phase': 'waiting'}
    record = origin / 'records/stages-progress.json'
    def save():
        write_json(record, {**progress, 'as_of': time.time()})
    results = []
    save()
    try:
        for task in tasks:
            terminal = run.wait(current)
            results.append(terminal)
            if terminal['lifecycle'] != 'completed':
                progress.update(phase='halted', source_lifecycle=terminal['lifecycle'])
                save()
                return results
            progress.update(phase='restarting', next_task=task)
            save()
            next_run = run.restart(current, task=task, keep_data=True)
            current = Path(next_run['path'])
            progress['runs'].append(str(current))
            progress.update(current_run=str(current), phase='waiting')
            progress.pop('next_task', None)
            save()
        terminal = run.wait(current)
        results.append(terminal)
        progress.update(phase='finished' if terminal['lifecycle'] == 'completed' else 'halted',
                        source_lifecycle=terminal['lifecycle'])
        save()
        return results
    except Exception as exc:
        progress.update(phase='error', error=f'{type(exc).__name__}: {exc}')
        if getattr(exc, 'lab_run_path', None):
            progress['failed_start_run'] = exc.lab_run_path
        save()
        raise


def facts(path):
    """Saved observations include spend/native/resources with source and as_of."""
    return run.status(path)


def watch(path=None, *, interval=10, follow=False):
    """Yield saved run facts until terminal; never create a second collector.

    A --script program can omit path and use LAB_RUN. Repeated snapshots are
    intentional: a Python policy may act on elapsed time without new activity.
    The source as_of remains unchanged, so stale observations stay distinguishable.
    """
    if interval <= 0:
        raise ValueError('watch interval must be positive')
    path = run.resolve(path or os.environ['LAB_RUN'])
    while True:
        observation = facts(path)
        if observation.get('lifecycle') in run.TERMINAL:
            if not follow:
                yield observation
                return
            children = run.successors(path)
            if len(children) > 1:
                continuation = observation.setdefault("continuation", {})
                continuation.update({"state": "ambiguous", "successors": children,
                                     "label": f"{path.name}→({len(children)} successors; explicit run required)"})
                yield observation
                return
            if len(children) == 1:
                child = children[0]
                continuation = observation.setdefault("continuation", {})
                mode = child.get("restart_mode")
                label = f"{path.name}→{child['run_id']}"
                if mode:
                    label += f"[{mode}]"
                continuation.update({"state": "handoff", "source_run": path.name,
                                     "successor": child, "restart_mode": mode, "label": label})
                yield observation
                path = run.resolve(child["path"])
                continue
            continuation = observation.setdefault("continuation", {})
            continuation.update({"state": "waiting", "source_run": path.name,
                                 "successors": [], "label": f"{path.name}→(waiting for explicit restart)"})
            yield observation
            time.sleep(interval)
            continue
        yield observation
        time.sleep(interval)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "default", "relay", "stages"))
    parser.add_argument("run")
    args = parser.parse_args(argv)
    {'observe': observe, 'default': default, 'relay': relay, 'stages': stages}[args.mode](args.run)


if __name__ == "__main__":
    main()
