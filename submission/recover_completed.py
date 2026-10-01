"""Restore retained Braid state; optionally continue generation, then deliver main."""

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import time
import tempfile
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "support"))
from agent_support import (browser_executable, cleanup_workspace, deliver,
                           start_local_telemetry, stop_local_telemetry,
                           telemetry_environment, verify_package, hashes)
from braid_runtime import archive_state, export_delivery, load_delivery
from core import archive_sessions


def restore_launch_paths(run, request):
    """Restore declared launchers and the source package paths used by native sessions."""
    source_root = Path(json.loads((run / "materials.json").read_text())["runtime"]).parent
    aliases = []
    if source_root != ROOT:
        # The local ARC adapter wraps a submitted package in submission/agent.
        if ROOT.name != "agent" or ROOT.parent != source_root:
            raise ValueError(f"unsupported recovery package relocation: {source_root} -> {ROOT}")
        for name in ("runtime", "support", "extensions", "tools", "agents", "skills"):
            target = ROOT / name
            if not target.is_dir():
                continue
            alias = source_root / name
            if alias.exists() or alias.is_symlink():
                if alias.resolve() != target.resolve():
                    raise ValueError(f"recovery package path is already occupied: {alias}")
            else:
                alias.symlink_to(target, target_is_directory=True)
            aliases.append({"path": str(alias), "target": str(target)})
    paths = {Path(request["pi"]["executable"]), run / "work/bin/pbb"}
    paths.update(Path(binding["executable"]) for binding in request["bindings"].values())
    repaired = []
    for path in sorted(paths):
        if not path.resolve(strict=True).is_relative_to(run):
            raise ValueError(f"retained launcher is outside Braid run: {path}")
        before = stat.S_IMODE(path.stat().st_mode)
        # Hosted workspace exports can reduce every file to 0600, including launchers.
        path.chmod(0o755)
        repaired.append({"path": str(path), "previous_mode": oct(before), "mode": "0o755"})
    (run / "recovery-launch-paths.json").write_text(json.dumps({
        "package_aliases": aliases, "launchers": repaired,
    }, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("requirements_dir", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--type", default="web")
    parser.add_argument("--prepare-only", action="store_true",
                        help="Restore and verify the workspace without starting Braid or calling models")
    args = parser.parse_args()
    print("Recovery: verifying packaged runtime and workspace", flush=True)
    manifest = verify_package(ROOT)
    source = json.loads((ROOT / "recovery-source.json").read_text())
    workspace = ROOT / "recovery-workspace.zip"
    if manifest["files"]["recovery-workspace.zip"]["sha256"] != source["workspace_sha256"]:
        raise ValueError("recovery workspace hash changed")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run = output / ".factory26" / source["braid_run_id"]
    if run.exists():
        raise ValueError("recovery Braid run already exists")
    requirement = args.requirements_dir / "requirements.yaml"
    if hashlib.sha256(requirement.read_bytes()).hexdigest() != source["requirements_sha256"]:
        raise ValueError("current requirements differ from retained workspace")
    print("Recovery: restoring retained workspace", flush=True)
    prior_logs = run / f"recovery-source-logs-{time.time_ns()}"
    directories = []
    with ZipFile(workspace) as archive:
        for entry in archive.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "template":
                raise ValueError(f"unexpected workspace path: {entry.filename}")
            if len(path.parts) > 1 and path.parts[1] == "requirements":
                continue
            # Runner event files belong to this new execution, not the restored source.
            target = (run.joinpath("recovery-source-arc", *path.parts[2:])
                      if len(path.parts) > 1 and path.parts[1] == ".arc"
                      else output.joinpath(*path.parts[1:]))
            if path.parts[1:3] == (".factory26", source["braid_run_id"]) and path.name in {
                "recovery-braid.log", "recovery-diagnostics.json", "telemetry-collector.log"
            } and len(path.parts) == 4:
                target = prior_logs / path.name
            if target != output and not target.parent.resolve().is_relative_to(output):
                raise ValueError(f"workspace link escapes output: {entry.filename}")
            if target.is_symlink():
                raise ValueError(f"duplicate workspace link: {entry.filename}")
            mode = entry.external_attr >> 16
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                directories.append((target, mode))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if stat.S_ISLNK(mode):
                    os.symlink(archive.read(entry).decode(), target)
                else:
                    with archive.open(entry) as incoming, target.open("wb") as outgoing:
                        shutil.copyfileobj(incoming, outgoing)
                    if mode & 0o7777:
                        target.chmod(mode & 0o7777)
    for target, mode in reversed(directories):
        if mode & 0o7777:
            target.chmod(mode & 0o7777)
    request = json.loads((run / "braid-request.json").read_text())
    if request["run_id"] != source["braid_run_id"] or Path(request["state"]) != run / "braid-state":
        raise ValueError("Braid request does not match retained workspace")
    if not all((run / "braid-state" / name).is_file() for name in ("request.json", "braid.sqlite3")):
        raise ValueError("retained Braid state is incomplete")
    continuing = source["mode"] == "workspace-resume"
    with sqlite3.connect(f"file:{run / 'braid-state/braid.sqlite3'}?mode=ro", uri=True) as db:
        open_items = db.execute("SELECT node_id,state FROM work_items WHERE state NOT IN ('CLOSED','MERGED')").fetchall()
        worktrees = db.execute("SELECT path,head_ref,local_branch FROM worktrees").fetchall()
    if open_items and not continuing:
        raise ValueError(f"workspace has unfinished items; explicit generation recovery required: {open_items}")
    origin = run / "braid-state/origin.git"
    app = run / "work/application"
    seed = json.loads((run / "braid-state/request.json").read_text())["seed_commit"]
    git_repairs = []
    repositories = [(app, seed, "recovery-seed")]
    if continuing:
        repositories += [(Path(directory), head_ref, branch) for directory, head_ref, branch in worktrees]
    for target, head_ref, branch in repositories:
        if not target.is_relative_to(run):
            raise ValueError(f"retained clone is outside Braid run: {target}")
        if (target / ".git").exists():
            continue
        target.mkdir(parents=True, exist_ok=True)
        def git(*arguments):
            return subprocess.check_output(["git", "-C", str(target), *arguments], text=True).strip()
        git("init", "-q", "-b", branch)
        git("remote", "add", "origin", str(origin))
        git("fetch", "-q", "origin")
        ref = seed if target == app else "refs/remotes/origin/" + branch
        if target != app and subprocess.run(
                ["git", "-C", str(target), "rev-parse", "--verify", ref],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            ref = "refs/remotes/origin/" + head_ref.removeprefix("refs/heads/")
        commit = git("rev-parse", "--verify", ref)
        git("update-ref", "refs/heads/" + branch, commit)
        # Rebuild the index without checkout: retain uncommitted snapshot files.
        git("read-tree", commit)
        git("config", "user.name", "Factory Agent")
        git("config", "user.email", "factory26@localhost")
        git("config", "commit.gpgsign", "false")
        (target / ".git/info/exclude").write_text(".braid/\nnode_modules/\n")
        git_repairs.append({"path": str(target), "published_base": commit,
                            "retained_changes": git("status", "--porcelain")})
    (run / "recovery-git.json").write_text(json.dumps({
        "limitation": "Clone .git omitted by platform; unpublished commit history cannot be restored",
        "repaired": git_repairs}, indent=2) + "\n")
    prior_result = run / "braid-state/result.json"
    if prior_result.exists():
        shutil.copy2(prior_result, run / "recovery-source-result.json")
    work, runtime = run / "work", ROOT / "runtime"
    if continuing:
        restore_launch_paths(run, request)
    if source.get("refresh_native_materials"):
        print("Recovery: refreshing native instructions and skills", flush=True)
        # Rebuild harness-owned materials, not application files or the object store.
        # Retain the prior files so this hotfix has an inspectable before/after.
        import run as variant
        old_profiles = {profile["id"]: profile for profile in request["profiles"]}
        for name in ("skills", "capabilities"):
            (work / name).rename(run / f"recovery-source-{name}-{time.time_ns()}")
        shutil.copytree(ROOT / "skills", work / "skills")
        profiles, bindings = variant.native_files(
            work, runtime, work / "skills", os.environ["OPENAI_BASE_URL"],
            os.environ.get("VISUAL_BASE_URL"))
        if {profile["id"] for profile in profiles} != set(old_profiles):
            raise ValueError("native material hotfix cannot change assigned profiles")
        refreshable = {"user_instructions", "context_window_tokens"}
        for profile in profiles:
            original = old_profiles[profile["id"]]
            if ({key: value for key, value in profile.items() if key not in refreshable}
                    != {key: value for key, value in original.items() if key not in refreshable}):
                raise ValueError("native material hotfix cannot change Profile identity or model recipe")
        shutil.copy2(run / "braid-request.json", run / "recovery-source-braid-request.json")
        # Braid permits instruction/binding refresh but treats the token window as
        # recipe identity. Migrate only this metadata in the retained request;
        # the stored Profile revision remains old so native sessions are rebuilt.
        retained_path = run / "braid-state/request.json"
        retained = json.loads(retained_path.read_text())
        current_profiles = {profile["id"]: profile for profile in profiles}
        shutil.copy2(retained_path, run / "recovery-source-state-request.json")
        for profile in retained["profiles"]:
            current = current_profiles[profile["id"]]
            if "context_window_tokens" in current:
                profile["context_window_tokens"] = current["context_window_tokens"]
        retained_path.write_text(json.dumps(retained, indent=2) + "\n")
        request["profiles"] = profiles
        request["bindings"] = bindings
        request["root_check_messages"] = variant.ROOT_CHECK_MESSAGES
        request["pi"]["executable"] = str(variant.budgeted_pi(runtime, run))
        # Use current package routes/compatibility and rebuild the helper launcher;
        # retained native models and launcher paths belong to the old package.
        pbb = work / "bin/pbb"
        pbb.write_text("#!/bin/sh\nexec " + shlex.join((str(runtime / "bin/node"),
                       str(runtime / "node_modules/pi-background-bash/bin/pbb.js"))) + ' "$@"\n')
        pbb.chmod(0o755)
        (run / "braid-request.json").write_text(json.dumps(request, indent=2) + "\n")
        material_record = run / "materials.json"
        if material_record.exists():
            material_record.rename(run / f"recovery-source-materials-{time.time_ns()}.json")
        material_record.write_text(json.dumps({
            "agents": hashes(ROOT / "agents"), "skills": hashes(work / "skills"),
            "runtime": str(runtime), "recovery_base_package": source["base_package_sha256"],
        }, indent=2) + "\n")
        implementation_record = run / "implementation-hashes.json"
        if implementation_record.exists():
            implementation_record.rename(run / f"recovery-source-implementation-hashes-{time.time_ns()}.json")
        code_files = [*ROOT.glob("*.py"), *(ROOT / "agents").rglob("*"),
                      *(ROOT / "extensions").rglob("*"), *(ROOT / "tools").rglob("*")]
        implementation_record.write_text(json.dumps({
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in code_files if path.is_file()
        }, indent=2) + "\n")
    braid = work / "bin/braid"
    shutil.copy2(runtime / "bin/braid", braid)
    braid.chmod(0o755)
    env = dict(os.environ)
    if continuing:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("FACTORY26_API_KEY")
        if not key and not args.prepare_only:
            raise ValueError("generation recovery requires the current run API key")
        # Workspace ZIP extraction above preserves stored modes; packaged tools
        # get executable bits from verify_package, and new launchers set theirs.
        browser = str(browser_executable(runtime))
        # Keep old async records discoverable while giving browser sockets a short path.
        env.update(PORTLESS_PORT="1355", PORTLESS_HTTPS="0", PORTLESS_SYNC_HOSTS="0",
                   PORTLESS_STATE_DIR=str(work / "tmp/portless"),
                   npm_config_cache=str(work / "cache/npm"),
                   npm_config_store_dir=str(work / "cache/pnpm"),
                   HOME=str(work / "home"), TMPDIR=tempfile.mkdtemp(prefix="f26-", dir="/tmp"),
                   PI_SUBAGENTS_TEMP_ROOT=str(work / "tmp" / f"pi-subagents-uid-{os.getuid()}"),
                   XDG_CONFIG_HOME=str(work / "home/.config"),
                   PI_CODING_AGENT_DIR=str(work / "home/.pi/agent"),
                   PI_TELEMETRY="0", PI_OFFLINE="1", FACTORY26_API_KEY=key or "",
                   PBB_PIL_BIN=str(runtime / "node_modules/pi-lane/bin/pil.js"),
                   AGENT_BROWSER_EXECUTABLE_PATH=browser, BROWSER_EXECUTABLE_PATH=browser,
                   BROWSER_CHECK_NODE_MODULES=str(runtime / "node_modules"),
                   AGENT_BROWSER_SOCKET_DIR=str(work / "b"),
                   MCPORTER_CONFIG=str(ROOT / "tools/mcporter.json"),
                   FACTORY26_PI_TIMING_EXTENSION=str(ROOT / "extensions/factory-pi-timing.ts"),
                   FACTORY26_PI_TIMING_FILE=str(run / "pi-timing.jsonl"),
                   PATH=os.pathsep.join((str(work / "bin"), str(runtime / "bin"),
                                         str(runtime / "node_modules/.bin"), env.get("PATH", ""))))
        if os.environ.get("VISUAL_API_KEY"):
            env["FACTORY26_VISUAL_API_KEY"] = os.environ["VISUAL_API_KEY"]
        if manifest.get("capabilities", {}).get("variant") in {"pi-braid-i13", "pi-braid-i13-glm-root"}:
            import run as variant
            # These process settings are not retained in the native session files.
            env.update(variant.tool_environment(), PI_FFF_MODE="tools-only", PI_FFF_MULTIGREP="0",
                       PI_SUBAGENT_MAX_DEPTH="3")
    (run / "recovery-provenance.json").write_text(json.dumps(source, indent=2) + "\n")
    if args.prepare_only:
        save_environment = {name: env[name] for name in (
            "HOME", "TMPDIR", "PATH", "PI_CODING_AGENT_DIR", "PI_OFFLINE",
            "PI_SUBAGENT_MAX_DEPTH", "PI_FFF_MODE", "PI_FFF_MULTIGREP",
        ) if name in env}
        (run / "recovery-preparation.json").write_text(json.dumps({
            "mode": "prepare-only", "models_started": False, "braid": str(braid),
            "launcher_environment": save_environment,
            "pi_executable": request.get("pi", {}).get("executable"),
            "binding_executables": {name: binding["executable"]
                                    for name, binding in request.get("bindings", {}).items()},
        }, indent=2) + "\n")
        print(f"Recovery: prepared without starting Braid; run={run}", flush=True)
        return
    # A source archive is historical; live readers must see the resumed sessions.
    old_native = run / "native"
    if old_native.exists() or old_native.is_symlink():
        old_native.rename(run / f"recovery-source-native-{time.time_ns()}")
    diagnostics = {}
    collector = None
    execution_error = None
    cleanup_error = None
    try:
        try:
            collector, binding = start_local_telemetry(run)
            env.update(telemetry_environment(binding))
        except Exception as exc:
            diagnostics["telemetry_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        with (run / "recovery-braid.log").open("w") as log:
            command = [str(braid), "local", str(run / "braid-request.json")]
            if continuing:
                command.append("--offline-resume")
            print(f"Recovery: resuming Braid; log={run / 'recovery-braid.log'}", flush=True)
            subprocess.run(command, cwd=app,
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    except BaseException as exc:
        execution_error = exc
    finally:
        if continuing:
            try:
                cleanup_workspace(run)
            except Exception as exc:
                cleanup_error = exc
                diagnostics["cleanup_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        try:
            entries = archive_state(run / "braid-state", run)
            archive_sessions(run, work / "home/.pi/agent", work, entries, telemetry_env=env)
        except Exception as exc:
            diagnostics["native_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        if collector is not None:
            try:
                stop_local_telemetry(collector)
            except Exception as exc:
                diagnostics["telemetry_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        (run / "recovery-diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    if execution_error is not None:
        raise execution_error
    if cleanup_error is not None:
        raise cleanup_error
    result = json.loads((run / "braid-state/result.json").read_text())
    if result.get("status") != "quiescent" or result.get("root_issue", {}).get("state") != "CLOSED":
        raise RuntimeError(f"retained Braid did not finish: {result}")
    delivery = load_delivery(origin, request)
    application = run / "recovered-application"
    export_delivery(origin, delivery["delivery_commit"], application)
    deliver(application, output)
    (run / "recovery-provenance.json").write_text(json.dumps({**source, **delivery}, indent=2) + "\n")
    print(f"Recovered {source['source_run_id']} at {delivery['delivery_commit']}", flush=True)


if __name__ == "__main__":
    main()
