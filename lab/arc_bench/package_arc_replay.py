"""Package published applications or provisional Git snapshots for ARC replay."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

from .arc_artifacts import application_source, manifest as application_manifest, verify as verify_application


def _run_state(run):
    """Read either a current run manifest or a legacy experiment run.json."""
    path = Path(run)
    current = path / "manifest.json"
    legacy = path / "run.json"
    if current.is_file():
        value = json.loads(current.read_text(encoding="utf-8"))
        value.setdefault("run_id", path.name)
        value.setdefault("competition", bool(value.get("competition", False)))
        return value
    if legacy.is_file():
        return json.loads(legacy.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"run manifest not found: {current}")


def _new_application(run, state):
    """Resolve only stable producer paths from the current run layout."""
    declared = state.get("application_snapshot")
    candidates = []
    if declared:
        declared_path = Path(declared).expanduser()
        candidates.append(declared_path if declared_path.is_absolute() else Path(run) / declared_path)
    workspace = Path(run) / "data" / "workspace"
    # New runs store the application directly at data/workspace.  This is a
    # fixed producer path, not a latest-directory search.
    candidates.append(workspace)
    candidates.extend(workspace / relative for relative in (
        "official-generation/.lab-artifacts/application",
        "official/.lab-artifacts/application",
        "official-generation/template",
        "official/template",
        "application",
    ))
    for candidate in candidates:
        if candidate.is_dir():
            if (candidate / "application").is_dir() and (candidate / "receipt.json").is_file():
                candidate = candidate / "application"
            if (candidate / "frontend" / "package.json").is_file() and (candidate / "backend" / "package.json").is_file():
                return candidate.resolve()
    return None


def _task_registry():
    configured = os.environ.get("LAB_CONFIG")
    registry = Path(configured).expanduser() if configured else Path(__file__).with_name("targets.json")
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot read ARC task registry {registry}: {exc}") from exc
    tasks, aliases = payload.get("tasks", {}), payload.get("task_aliases", {})
    if not isinstance(tasks, dict) or not isinstance(aliases, dict):
        raise ValueError(f"invalid task registry in {registry}")
    return tasks, aliases, registry


def _registered_task(value):
    if not isinstance(value, str) or not value or Path(value).expanduser().is_absolute():
        return None
    tasks, aliases, registry = _task_registry()
    target = aliases.get(value, value)
    if isinstance(target, dict):
        return target
    if not isinstance(target, str):
        raise ValueError(f"task alias {value!r} has invalid target in {registry}")
    entry = tasks.get(target)
    return entry if isinstance(entry, dict) else None


def _requirements(run, state):
    # Evaluation runs carry an immutable input copy.  Prefer it over a
    # registry path so a later registry edit cannot change a replay package.
    candidates = [Path(run) / "inputs" / "requirements"]
    task = state.get("task")
    task_config = state.get("task_config") if isinstance(state.get("task_config"), dict) else {}
    task = task_config.get("requirements") or task_config.get("path") or task
    if task:
        candidate = Path(task).expanduser()
        if candidate.exists():
            candidates.append(candidate)
        else:
            entry = _registered_task(str(task))
            if entry:
                registered = entry.get("requirements") or entry.get("path")
                if registered:
                    candidates.append(Path(registered).expanduser())
    for candidate in candidates:
        if candidate.is_file() and candidate.name == "requirements.yaml":
            candidate = candidate.parent
        if candidate.is_dir() and (candidate / "requirements.yaml").is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"requirements.yaml not found for run {state.get('run_id', Path(run).name)}")


def _staging_root():
    root = Path(os.environ.get("FACTORY26_TEMP_ROOT", Path(__file__).resolve().parents[2] / ".tmp"))
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    if os.uname().sysname == "Darwin" and not root.is_relative_to(Path("/Volumes/WorkSSD")):
        raise ValueError(f"replay staging must be on WorkSSD: {root}")
    return root


def package(runs, output, *, git_repo=None, ref=None):
    if (git_repo is None) != (ref is None):
        raise ValueError("--git-repo and --ref must be supplied together")
    if git_repo is None:
        return _package(runs, output)
    if len(runs) != 1:
        raise ValueError("A Git snapshot requires exactly one source --run")
    repository = Path(git_repo).resolve(strict=True)
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        text=True).strip()
    with TemporaryDirectory(prefix="arc-replay-", dir=_staging_root()) as directory:
        archive_path = Path(directory) / "application.tar"
        application = Path(directory) / "application"
        subprocess.run(["git", "-C", str(repository), "archive", "--format=tar",
                        "--output", str(archive_path), commit], check=True)
        with tarfile.open(archive_path) as archive:
            archive.extractall(application, filter="data")
        source = {"provisional": True,
                  "git": {"repository": str(repository), "ref": ref, "commit": commit}}
        return _package(runs, output, application=application, snapshot_source=source)


def package_snapshot(source_run, application, output, *, requirements=None,
                     task=None, platform_task=None):
    """Package an explicit immutable application for one new evaluation run."""
    source_run = Path(source_run).expanduser().resolve(strict=True)
    application = Path(application).expanduser().resolve(strict=True)
    state = _run_state(source_run)
    if not (application / "frontend" / "package.json").is_file() or not (application / "backend" / "package.json").is_file():
        raise ValueError(f"application snapshot is incomplete: {application}")
    return _package([source_run], Path(output).expanduser().resolve(), application=application,
                    requirements=Path(requirements).expanduser().resolve() if requirements else None,
                    task=task, platform_task=platform_task,
                    snapshot_source={"application_snapshot": str(application),
                                     "source_run": state.get("run_id", source_run.name)})


def _package(runs, output, *, application=None, snapshot_source=None,
             requirements=None, task=None, platform_task=None):
    cases, files = [], {}
    for run in runs:
        run = Path(run).expanduser().resolve(strict=True)
        state = _run_state(run)
        published = None if snapshot_source else next((path for path in (run / "workspace/official-generation/.lab-artifacts/application",
                                            run / "workspace/official/.lab-artifacts/application",
                                            run / "data/workspace/official-generation/.lab-artifacts/application",
                                            run / "data/workspace/official/.lab-artifacts/application")
                          if path.is_dir() and (path.parent / "receipt.json").is_file()), None)
        selected = (application if snapshot_source else published or _new_application(run, state) or next((path for path in (run / "workspace/official-generation/template",
                                                             run / "workspace/official/template",
                                                             run / "data/workspace/official-generation/template",
                                                             run / "data/workspace/official/template") if path.is_dir()),
                                         run / "workspace/official-generation/template")).resolve(strict=True)
        for part in ("frontend", "backend"):
            if not (selected / part / "package.json").is_file():
                identity = f" at Git commit {snapshot_source['git']['commit']}" if snapshot_source else ""
                raise ValueError(f"Missing {part}/package.json{identity}: {selected}")
        requirement_dir = requirements if snapshot_source and requirements is not None else _requirements(run, state)
        requirement = requirement_dir / "requirements.yaml"
        requirement_hash = hashlib.sha256(requirement.read_bytes()).hexdigest()
        if any(case["requirements_sha256"] == requirement_hash for case in cases):
            raise ValueError("A replay package must contain only one application per requirement")
        receipt = published.parent / "receipt.json" if published else None
        app_manifest = verify_application(selected, receipt) if receipt and receipt.is_file() else application_manifest(selected)
        hashes = {}
        for item in app_manifest["entries"]:
            if item["type"] != "file":
                raise ValueError(f"replay ZIP cannot transport application symlink: {item['path']}")
            path = selected / item["path"]
            hashes[item["path"]] = item["sha256"]
            files[f"applications/{state['run_id']}/{item['path']}"] = path
        provenance = ("git-archive-provisional" if snapshot_source else
                      "published" if published and selected == published.resolve() else "imported-at-packaging")
        cases.append({"run_id": state["run_id"], "variant": state.get("variant"),
                      "competition": state["competition"], "task": task or state["task"],
                      "platform_task": platform_task,
                      "requirements_sha256": requirement_hash, "files": hashes,
                      "application_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                      "application_manifest": app_manifest,
                      "source_application": {**application_source(state, run, app_manifest, provenance),
                                             **(snapshot_source or {})},
                      "provenance": provenance})
    manifest = {"mode": "artifact-replay", "delay_seconds": 3, "cases": cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(Path(__file__).with_name("arc_replay.py"), "main.py")
                archive.write(Path(__file__).with_name("arc_artifacts.py"), "arc_artifacts.py")
                archive.writestr("requirements.txt", "")
                archive.writestr("replay-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                for name, path in files.items():
                    archive.write(path, name)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--git-repo", type=Path, help="从指定 Git 仓库冻结阶段应用；必须配合 --ref，且只接受一个 --run")
    parser.add_argument("--ref", help="解析一次为 commit 后以 git archive 导出；不读取未提交工作树")
    args = parser.parse_args()
    manifest = package(args.run, args.output, git_repo=args.git_repo, ref=args.ref)
    print(json.dumps({"package": str(args.output), "runs": [case["run_id"] for case in manifest["cases"]]}))


if __name__ == "__main__":
    main()
