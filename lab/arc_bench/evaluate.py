"""Build and dispatch an independent evaluation of a frozen application.

The old ``prepare`` entry point remains below for historical ``lab.exp``
recipes.  New runs use :func:`freeze_application` and :func:`evaluate_run`;
they never infer an application from another run's mutable ``latest`` path.
"""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
from zipfile import ZIP_DEFLATED, ZipFile

from lab.exp.core import record, require, read

from .arc_artifacts import copy_snapshot, manifest as application_manifest, verify as verify_application
from .run_layout import create_run, manifest as read_run_manifest, paths, write_json, write_manifest


EVALUATION_KINDS = {"simulate", "task", "official"}


def _run_root(run):
    """Resolve the new Lab run root without importing the public run module."""
    value = Path(run).expanduser().resolve()
    if (value / "manifest.json").is_file():
        return value
    raise FileNotFoundError(f"run manifest not found: {value / 'manifest.json'}")


def _work_temp_root():
    """Keep evaluation staging on the project volume, including on macOS."""
    configured = os.environ.get("FACTORY26_TEMP_ROOT")
    root = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[2] / ".tmp"
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    if os.uname().sysname == "Darwin" and not root.is_relative_to(Path("/Volumes/WorkSSD")):
        raise ValueError(f"evaluation staging must be on WorkSSD: {root}")
    return root


def _as_path(value, *, base=None, label="path"):
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute() and base is not None:
        path = Path(base) / path
    try:
        return path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{label} does not exist: {path}") from exc


def _application_root(value):
    """Accept an application directory, snapshot parent, or receipt reference."""
    path = _as_path(value, label="application snapshot")
    if path.is_file():
        if path.name in {"receipt.json", "application-snapshot.json"}:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key in ("application", "path", "snapshot"):
                if payload.get(key):
                    return _application_root(payload[key])
        raise ValueError(f"application snapshot must be a directory: {path}")
    if (path / "application").is_dir() and (path / "receipt.json").is_file():
        return path / "application"
    if (path / "frontend" / "package.json").is_file() and (path / "backend" / "package.json").is_file():
        return path
    raise ValueError(f"directory is not a complete ARC application snapshot: {path}")


def _application_candidates(run, state):
    workspace = paths(run)["workspace"]
    declared = state.get("application_snapshot")
    if declared:
        yield _as_path(declared, base=run, label="declared application snapshot")
    # Current runs save the application itself at data/workspace.  Keep this
    # explicit producer path ahead of the historical nested layouts; it is
    # not a search for the newest directory.
    if workspace.is_dir():
        yield workspace
    # These are fixed producer paths, not a latest/mtime search.
    for relative in (
        "official-generation/.lab-artifacts/application",
        "official/.lab-artifacts/application",
        "official-generation/template",
        "official/template",
        "application",
    ):
        candidate = workspace / relative
        if candidate.is_dir():
            yield candidate


def freeze_application(source_run, ref=None):
    """Create or return an immutable application snapshot for ``source_run``.

    ``ref`` is an explicit application directory/snapshot path.  Without it,
    only the fixed ARC producer output locations are considered.  The returned
    path is the copied ``application`` directory, suitable for an evaluation
    input.  A receipt and source relation are saved beside it.
    """
    source = _run_root(source_run)
    state = read_run_manifest(source)
    temporary = None
    if isinstance(ref, dict):
        repository = _as_path(ref.get("git_repo"), label="Git repository")
        commit = ref.get("commit")
        if not repository or not commit:
            raise ValueError("Git snapshot reference needs git_repo and commit")
        commit = subprocess.check_output(
            ["git", "-C", str(repository), "rev-parse", "--verify", "--end-of-options", f"{commit}^{{commit}}"],
            text=True).strip()
        temporary = tempfile.TemporaryDirectory(prefix="arc-application-", dir=_work_temp_root())
        archive = Path(temporary.name) / "application.tar"
        extracted = Path(temporary.name) / "application"
        subprocess.run(["git", "-C", str(repository), "archive", "--format=tar", "--output", str(archive), commit], check=True)
        with tarfile.open(archive) as stream:
            stream.extractall(extracted, filter="data")
        selected = _application_root(extracted)
    else:
        selected = _application_root(ref) if ref is not None else None
    if selected is None:
        if state.get("lifecycle") != "completed":
            raise RuntimeError("a running application needs an explicit path or Git commit snapshot")
        for candidate in _application_candidates(source, state):
            try:
                selected = _application_root(candidate)
                break
            except ValueError:
                continue
    if selected is None:
        raise FileNotFoundError(
            f"no frozen application found for run {state.get('run_id', source.name)}; "
            "pass an explicit application snapshot"
        )
    identity = application_manifest(selected)
    snapshot_parent = paths(source)["snapshots"] / f"application-{identity['sha256'][:24]}"
    application = snapshot_parent / "application"
    receipt = snapshot_parent / "receipt.json"
    if application.is_dir() or receipt.is_file():
        if not (application.is_dir() and receipt.is_file()):
            raise ValueError(f"incomplete application snapshot: {snapshot_parent}")
        verify_application(application, receipt)
    else:
        snapshot_parent.mkdir(parents=True, exist_ok=False)
        copy_snapshot(selected, snapshot_parent)
    relation = {
        "kind": "arc.application-snapshot",
        "source_run": state.get("run_id", source.name),
        "source_path": str(selected),
        "snapshot": str(application),
        "receipt": str(receipt),
        "algorithm": identity["algorithm"],
        "sha256": identity["sha256"],
        "created_at": time.time(),
    }
    write_json(snapshot_parent / "source.json", relation)
    write_json(paths(source)["records"] / "application-snapshot.json", relation)
    if temporary is not None:
        temporary.cleanup()
    return application


def _config_for_kind(state, kind, configuration):
    if configuration is not None:
        value = deepcopy(configuration)
    else:
        task_config = state.get("task_config", {})
        entries = task_config.get("evaluations", []) if isinstance(task_config, dict) else []
        matches = [entry for entry in entries if entry.get("kind") == kind]
        if len(matches) > 1:
            raise ValueError(f"task config has multiple {kind} evaluations; pass configuration explicitly")
        value = deepcopy(matches[0]) if matches else {"kind": kind}
    if value.get("kind", kind) != kind:
        raise ValueError(f"evaluation configuration kind is not {kind!r}")
    if kind == "official" and value.get("billing_mode") not in {"self_funded", "competition"}:
        raise ValueError("official evaluation requires billing_mode=self_funded or competition")
    if kind == "simulate":
        command = value.get("argv", value.get("command"))
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            raise ValueError("simulate evaluation requires a non-empty argv list")
        # ``argv`` is the new run contract; retain ``command`` as a readable
        # compatibility alias for older saved evaluation recipes.
        value["argv"] = list(command)
        value["command"] = list(command)
    return value


def _task_registry():
    """Read the maintained task alias registry without treating an alias as a path."""
    configured = os.environ.get("LAB_CONFIG")
    registry = Path(configured).expanduser() if configured else Path(__file__).with_name("targets.json")
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot read ARC task registry {registry}: {exc}") from exc
    tasks = payload.get("tasks", {})
    aliases = payload.get("task_aliases", {})
    if not isinstance(tasks, dict) or not isinstance(aliases, dict):
        raise ValueError(f"invalid task registry in {registry}")
    return tasks, aliases, registry


def _registered_task(value):
    """Return (alias, entry) for a registered task name, or ``(None, None)``."""
    if not isinstance(value, str) or not value or Path(value).expanduser().is_absolute():
        return None, None
    tasks, aliases, registry = _task_registry()
    alias = value
    target = aliases.get(value, value)
    if isinstance(target, dict):
        return alias, target
    if not isinstance(target, str):
        raise ValueError(f"task alias {value!r} has invalid target in {registry}")
    entry = tasks.get(target)
    if not isinstance(entry, dict):
        return None, None
    return alias, entry


def _task_reference(value, *, source, state):
    """Resolve a path or registry alias to a frozen requirements directory."""
    if value is not None:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = source / candidate
        if candidate.exists():
            return candidate.resolve(strict=True), None, None
        alias, entry = _registered_task(str(value))
        if entry is None:
            raise FileNotFoundError(f"task {value!r} is neither a path nor a registered alias")
        requirements = entry.get("requirements") or entry.get("path")
        if not requirements:
            raise ValueError(f"registered task {value!r} has no requirements path")
        return _as_path(requirements, base=source, label=f"requirements for task {value!r}"), alias, entry

    # A generation run already has an immutable requirements copy.  Prefer it
    # when no new task was requested; this preserves the exact task version.
    frozen = paths(source)["inputs"] / "requirements"
    if (frozen / "requirements.yaml").is_file():
        task_config = state.get("task_config") if isinstance(state.get("task_config"), dict) else {}
        return frozen.resolve(), task_config.get("alias") or state.get("task"), None
    task_config = state.get("task_config") if isinstance(state.get("task_config"), dict) else {}
    value = task_config.get("requirements") or task_config.get("path") or state.get("task")
    if value is None:
        raise FileNotFoundError("evaluation has no frozen requirements or task alias")
    return _task_reference(value, source=source, state=state)


def _task_paths(source, state, configuration):
    task = configuration.get("task") or configuration.get("requirements")
    requirements, alias, entry = _task_reference(task, source=source, state=state)
    if requirements and requirements.is_file():
        requirements = requirements.parent
    if not requirements or not (requirements / "requirements.yaml").is_file():
        raise FileNotFoundError("evaluation needs a requirements directory containing requirements.yaml")
    tests = configuration.get("tests")
    if tests is None and configuration.get("test_source"):
        tests = configuration["test_source"]
    if tests is None and isinstance(entry, dict):
        tests = entry.get("tests")
    if tests is None and requirements is not None and (requirements / "tests").is_dir():
        tests = requirements / "tests"
    if tests is None and isinstance(task, (str, os.PathLike)):
        candidate = Path(task).expanduser()
        if (candidate / "tests").is_dir():
            tests = candidate / "tests"
    tests = _as_path(tests, base=source, label="tests") if tests else None
    return requirements, tests, (alias or state.get("task")), entry


def _copy_input(source, destination, *, label):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    return destination


def _noop_package(destination):
    """Create the real ARC no-op package used by task evaluations.

    It is deliberately tiny: the application is already frozen and supplied
    as the SDK template.  The package only records that the evaluator, rather
    than an agent generation, consumed that template.
    """
    destination = Path(destination)
    if destination.is_file():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "x", ZIP_DEFLATED) as archive:
        archive.write(Path(__file__).with_name("arc_bench_noop.py"), "main.py")
        archive.write(Path(__file__).with_name("arc_artifacts.py"), "arc_artifacts.py")
        archive.writestr("requirements.txt", "")
    return destination


def evaluate_run(source_run, kind, snapshot=None, configuration=None):
    """Create and dispatch one independent evaluation run.

    The execution adapter owns Local/Hosted platform details.  This function
    owns only run identity, immutable input copies and evaluation provenance.
    """
    if kind not in EVALUATION_KINDS:
        raise ValueError(f"unsupported evaluation kind: {kind}")
    source = _run_root(source_run)
    source_state = read_run_manifest(source)
    config = _config_for_kind(source_state, kind, configuration)
    application = freeze_application(source, snapshot)
    application = _application_root(application)
    requirements, tests, task_alias, task_entry = _task_paths(source, source_state, config)
    target = config.get("target", source_state.get("target"))
    if not isinstance(target, str):
        target = source_state.get("target_name") or "local"
    task_config = source_state.get("task_config") if isinstance(source_state.get("task_config"), dict) else {}
    platform_task = (config.get("platform_task") or
                     (task_entry or {}).get("platform_task") or
                     task_config.get("platform_task") or task_alias or target)
    task = str(config.get("task") or task_alias or platform_task)
    run_root = source.parents[1]
    evaluation = create_run(run_root, source_state.get("variant", "unknown"), target, task,
                            route=config.get("route"),
                            competition=config.get("billing_mode") == "competition" or
                            bool(config.get("competition", False)),
                            source={"run_id": source_state.get("run_id", source.name), "kind": kind})
    layout = paths(evaluation)
    # Keep the evaluation's mutable input copy independent from the source.
    _copy_input(application, layout["inputs"] / "application")
    shutil.copy2(application.parent / "receipt.json", layout["inputs"] / "application-receipt.json")
    _copy_input(requirements, layout["inputs"] / "requirements")
    if tests is not None:
        _copy_input(tests, layout["inputs"] / "tests")
    # The current Local/Hosted SDK consumes the application as its template
    # root.  Keep this second copy separate from provenance inputs: the
    # evaluator is allowed to mutate it while the immutable input remains
    # available for replay and diagnosis.
    _copy_input(application, layout["workspace"])
    replay_package = None
    if kind == "official":
        if config.get("billing_mode") not in {"self_funded", "competition"}:
            raise ValueError("official evaluation requires an explicit billing_mode")
        from .package_arc_replay import package_snapshot
        replay_package = layout["inputs"] / "official-replay.zip"
        package_snapshot(source, application, replay_package,
                         requirements=requirements, task=task,
                         platform_task=platform_task)
    noop_package = _noop_package(layout["inputs"] / "arc-noop.zip") if kind == "task" else None
    manifest = read_run_manifest(evaluation)
    manifest.update({
        "record_type": "arc.run",
        "run_kind": "evaluation",
        "evaluation_kind": kind,
        "evaluator": f"arc-bench:{kind}",
        "source_run": source_state.get("run_id", source.name),
        "source_run_path": str(source),
        "application_snapshot": str(application),
        "application_sha256": application_manifest(application)["sha256"],
        "evaluation": config,
        # A target switch must assemble its own physical contract.  Never
        # carry source credentials/hosts/sdk paths into an independent run.
        "target_config": config.get("target_config"),
        "task_config": {"alias": task_alias,
                         "platform_task": platform_task,
                         # Keep the execution-facing paths absolute here;
                         # remote adapters relocate them when publishing the
                         # manifest.  Relative paths remain in
                         # evaluation_inputs for human/replay use.
                         "requirements": str(layout["inputs"] / "requirements"),
                         "tests": str(layout["inputs"] / "tests") if tests else None},
        "agent_package": (str(replay_package) if replay_package else
                          str(noop_package) if noop_package else config.get("agent_package")),
        "replay_package": str(replay_package) if replay_package else None,
        "evaluation_inputs": {"requirements": "inputs/requirements", "tests": "inputs/tests" if tests else None,
                               "application": "inputs/application",
                               "workspace_application": "data/workspace"},
        "lifecycle": "starting",
    })
    # Resolve a named target from the maintained registry without assembling
    # the generation variant.  This is the only target materialization needed
    # before the execution adapter starts an evaluation run.
    from .execution import _target as resolve_target, freeze_model_channel
    if not manifest.get("target_config"):
        manifest["target_config"] = resolve_target(manifest)
    target_config = dict(manifest["target_config"])
    if target_config.get("kind") == "hosted":
        # Hosted upload needs a frozen model channel even for a replay.  The
        # billing identity remains separate in ``billing_mode``.
        frozen_state, target_config, _ = freeze_model_channel(
            evaluation, manifest, target_config)
        manifest.update(frozen_state)
    else:
        # Local task/simulate evaluation is a no-model application check. Do
        # not read or transport a generation recipe, provider environment, or
        # route merely because the target registry has generation defaults.
        for field in ("model_recipe", "model_aliases", "model_alias_map",
                      "environment_file", "credential_file", "credential_env",
                      "model_config", "route"):
            target_config.pop(field, None)
    manifest["target_config"] = target_config
    manifest["target_kind"] = manifest["target_config"].get("kind")
    manifest["evaluation_assembly"] = {
        "mode": "replay" if replay_package else "noop" if noop_package else "argv",
        "application": "data/workspace",
        "requirements": "inputs/requirements",
        "tests": "inputs/tests" if tests else None,
    }
    write_manifest(evaluation, manifest)
    write_json(layout["records"] / "evaluation-inputs.json", {
        "source_run": source_state.get("run_id", source.name),
        "application": manifest["application_sha256"],
        "kind": kind,
        "configuration": config,
        "billing_mode": config.get("billing_mode"),
        "created_at": time.time(),
    })
    # Evaluation assembly is complete above.  Starting dispatches directly to
    # local_run/hosted_run; it must not invoke the generation variant builder.
    from . import execution
    started = execution.start(evaluation)
    # Evaluation is a normal run: exactly one run observer owns status/save.
    # Do not start the generation default automation here (it would recurse
    # into another evaluation after a terminal replay).
    from lab.run import _background
    observer_pid = _background(evaluation, "lab.automation", ["observe", str(evaluation)], "supervisor")
    child = {"run_id": manifest["run_id"], "path": str(evaluation),
             "source_run": manifest["source_run"], "kind": kind,
             "target": target, "observer_pid": observer_pid,
             "observer_record": "records/supervisor.json"}
    write_json(layout["records"] / "child-run.json", child)
    if isinstance(started, dict):
        return {**started, "run_id": manifest["run_id"], "path": str(evaluation),
                "source_run": manifest["source_run"], "evaluation_kind": kind,
                "child_run": child}
    return {"run_id": manifest["run_id"], "path": str(evaluation),
            "source_run": manifest["source_run"], "evaluation_kind": kind,
            "started": started, "child_run": child}


def prepare(application, output, *, host_runtime_receipt, runner_runtime_receipt,
            storage, budget, resource_limits, requirements, tests, runner, image, endpoint, admission_volume,
            competition, task, application_receipt, source_attempt, selection=None,
            experiment_key='arc-evaluation', slots=1, authorization=None, authority_handoff=None):
    """No source-run path inference or inherited model/fee permission is performed."""
    from lab.exp.controller import build
    adapter = Path(__file__).resolve().parent
    inputs = {'application': application,
              'application_receipt': application_receipt, 'requirements': requirements,
              'tests': tests, 'runner': runner, 'noop': {'source': str(adapter / 'arc_bench_noop.py')}}
    command = [require(read(runner_runtime_receipt), 'runtime')['launcher'], '-m', 'lab.arc_bench.arc_bench_adapter', '--runner', '{runner}',
               '--application', '{application}', '--application-receipt', '{application_receipt}',
               '--noop-script', '{noop}', '--requirements', '{requirements}', '--tests', '{tests}',
               '--workspace', '{workspace}', '--competition', competition, '--task', task,
               '--image', image, '--source-run-id', source_attempt,
               '--admission-volume', admission_volume, '--shared-docker-slots', str(slots)]
    if selection:
        inputs['selection'] = selection
        command += ['--selection', '{selection}']
    spec = record('experiment', experiment_id=experiment_key, max_parallel=1, storage=storage, budget=budget, authorization=authorization,
                  controller_runtime=str(Path(host_runtime_receipt).resolve()),
                  runner_runtime=str(Path(runner_runtime_receipt).resolve()),
                  jobs=[{'id': 'evaluation', 'purpose': 'evaluate', 'inputs': inputs, 'command': command,
                         'source_attempt': source_attempt,
                         'backend': {'kind': 'local', 'capabilities_required': ['arc-sdk-host-docker'],
                                     'external_docker': {'endpoint': endpoint, 'image_id': image, 'slots': slots,
                                                         'admission_volume': admission_volume, 'authority_handoff': authority_handoff}},
                         'outputs': [{'name': 'workspace', 'type': 'terminal-archive', 'path': '.'},
                                     {'name': 'score', 'type': 'evaluation-result', 'path': 'experiment-result.json'}],
                         'limits': {'wall_seconds': budget['wall_seconds_per_attempt'],
                                    'storage_bytes': storage['workspace_bytes_per_run'],
                                    'telemetry_bytes': storage['telemetry_bytes_per_run'], **resource_limits}}])
    recipe = Path(output).with_name(Path(output).name + '.recipe.json')
    recipe.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    build(recipe, output)
    return Path(output).resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True, help='new exp evaluation recipe with explicit artifact inputs')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args(argv)
    spec = require(json.loads(args.spec.read_text()), 'experiment')
    if any(job['purpose'] != 'evaluate' for job in spec['jobs']):
        raise ValueError('evaluation recipe may contain only evaluate jobs')
    from lab.exp.controller import build, start
    build(args.spec, args.output)
    root = args.output.resolve()
    print(root)
    if not args.build_only:
        print(json.dumps(start(root), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
