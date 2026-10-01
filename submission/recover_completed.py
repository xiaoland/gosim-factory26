"""Restore retained Braid state; optionally continue generation, then deliver main."""

import argparse
import hashlib
import json
import os
import sqlite3
import signal
import stat
import time
import uuid
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


def diagnostic_receipt(path, value, errors):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    except OSError as exc:
        row = {"path": str(path), "error": {"type": type(exc).__name__, "message": str(exc),
                                           "errno": exc.errno, "filename": exc.filename}}
        errors.append(row)
        try:
            print(f"Recovery evidence unavailable: {json.dumps(row)}", file=sys.stderr, flush=True)
        except OSError:
            pass


def restore_launch_paths(run, request):
    """Restore declared launchers and the source package paths used by native sessions."""
    source_root = Path(json.loads((run / "materials.json").read_text())["runtime"]).parent
    aliases = []
    if source_root != ROOT:
        # The local ARC adapter wraps a submitted package in submission/agent;
        # retained local sessions need the same one-level alias when moved back.
        if ROOT.name == "agent" and ROOT.parent == source_root:
            pass
        elif source_root.name == "agent" and source_root.parent == ROOT:
            source_root.mkdir(exist_ok=True)
        else:
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


def replace_braid_deepseek_with_glm(run, variant):
    """Migrate this I13 execution recipe while retaining member and session identities."""
    if variant not in {"pi-braid-i13", "pi-braid-i13-glm-root"}:
        raise ValueError(f"unsupported DeepSeek Braid migration variant: {variant}")
    old_id, target_id = "pi-deepseek-fast", "pi-glm-fast"
    request_paths = [run / "braid-request.json", run / "braid-state/request.json"]
    requests = [json.loads(path.read_text()) for path in request_paths]
    if requests[0]["root_profile_id"] != requests[1]["root_profile_id"]:
        raise ValueError("launcher and retained requests disagree on root identity")
    migrations = []
    for request in requests:
        profiles = {profile["id"]: profile for profile in request["profiles"]}
        if len(profiles) != len(request["profiles"]):
            raise ValueError("duplicate profile identity in migration request")
        old, target = profiles[old_id], profiles[target_id]
        if (old.get("adapter_type"), old.get("provider"), old.get("model")) != (
                "pi", "factory26", "deepseek-v4-flash"):
            raise ValueError("migration requires pi-deepseek-fast factory26/deepseek-v4-flash")
        if (target.get("adapter_type"), target.get("provider"), target.get("model")) != (
                "pi", "factory26", "glm-5.3-flash"):
            raise ValueError("migration requires pi-glm-fast factory26/glm-5.3-flash")
        if request["root_profile_id"] == old_id:
            raise ValueError("migration cannot change the root model")
        updates = {name: target[name] for name in (
            "provider", "model", "reasoning", "context_soft_ratio", "context_hard_bytes", "context_window_tokens",
        )}
        updates.update(display_name=f"{old['display_name']} (GLM-5.3-Flash)",
                       tags=list(dict.fromkeys([*old.get("tags", []), "root-only"])))
        migrations.append({"profile_id": old_id, "before": {name: old.get(name) for name in updates},
                           "after": updates})
        old.update(updates)
    if migrations[0] != migrations[1]:
        raise ValueError("launcher and retained requests disagree on model migration")

    def retained_path(value):
        path = Path(value).resolve(strict=True)
        if not path.is_relative_to(run.resolve()):
            raise ValueError(f"model migration path escapes Braid run: {value}")
        return path

    target_binding = requests[0]["bindings"][target_id]
    target_models = json.loads(retained_path(
        retained_path(target_binding["native_template"]) / "models.json").read_text())
    provider = target_models["providers"]["factory26"]
    definitions = [model for model in provider["models"] if model["id"] == "glm-5.3-flash"]
    if len(definitions) != 1:
        raise ValueError("target native template does not contain exactly one GLM-5.3-Flash definition")
    definition = definitions[0]
    configurations = {retained_path(request["bindings"][old_id]["native_template"]) / "models.json"
                      for request in requests}
    native_roots = {retained_path(request["bindings"][old_id]["native_home"]["root"])
                    for request in requests}
    # I13's native factory names every home <profile-id>-<uuid>. Include sleeping
    # and replaced homes; resuming an existing home does not recopy its template.
    homes = {retained_path(path) for root in native_roots for path in root.glob(old_id + "-*")
             if path.is_dir()}
    configurations.update(home / "models.json" for home in homes)
    changes = {}
    for path in sorted(configurations):
        path = retained_path(path)
        value = json.loads(path.read_text())
        current = value["providers"]["factory26"]
        if any(current.get(name) != provider.get(name) for name in ("baseUrl", "api", "apiKey")):
            raise ValueError(f"native factory26 transport differs from GLM template: {path}")
        matching = [i for i, model in enumerate(current["models"]) if model["id"] == definition["id"]]
        if len(matching) > 1:
            raise ValueError(f"duplicate GLM model definition in {path}")
        if matching:
            current["models"][matching[0]] = definition
        else:
            current["models"].append(definition)
        changes[path] = value
    changes.update(zip(request_paths, requests))
    originals = run / "recovery-model-migration/originals"
    originals.mkdir(parents=True, exist_ok=False)
    history = [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
               for home in sorted(homes) for path in sorted((home / "sessions").rglob("*.jsonl"))]
    records = []
    for path, value in changes.items():
        backup = originals / path.relative_to(run)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
        records.append({"path": str(path), "original": str(backup), "before_sha256": before,
                        "after_sha256": hashlib.sha256(encoded).hexdigest()})
        # Each file is complete before replacement; a failure stops before Braid starts.
        temporary = path.with_name(path.name + ".model-migration.tmp")
        with temporary.open("xb") as stream:
            stream.write(encoded)
        temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        temporary.replace(path)
    receipt = {"operation": "replace-braid-deepseek-with-glm", "variant": variant,
               "applied_at": time.time(), "profile_change": migrations[0],
               "target_model_definition": definition, "files": records,
               "native_homes": [str(home) for home in sorted(homes)], "retained_history": history,
               "root_profile_id": requests[0]["root_profile_id"],
               "preserved": ["profile ID", "member identity", "assignments", "worktrees", "native history",
                             "root and other profiles", "subagent roles", "instructions", "skills"],
               "new_assignments": "old profile excluded by root-only tag"}
    (run / "recovery-model-migration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return requests[0]


def execute_braid(command, *, run, app, env, log, evidence):
    if not evidence:
        subprocess.run(command, cwd=app, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        return
    from agent_support import (process_evidence, process_identity, evidence_error,
                               _wait_process, _signal_process)
    operation = {"kind": "spawn", "role": "recovery-braid", "request_id": uuid.uuid4().hex,
                 "command": command, "phase": "request"}
    process_evidence(run, "operations.jsonl", operation)
    try:
        with subprocess.Popen(command, cwd=app, env=env, stdout=log, stderr=subprocess.STDOUT) as child:
            process_evidence(run, "operations.jsonl", {
                **operation, "kind": "process_started", "phase": "result",
                "process": process_identity(child.pid),
            })
            try:
                code = _wait_process(child, run, "recovery-braid")
            except BaseException:
                # Match subprocess.run: kill this child, then let Popen.__exit__
                # retain its normal wait or bounded KeyboardInterrupt policy.
                _signal_process(child, signal.SIGKILL, run, "recovery-braid-run-exception")
                raise
    except OSError as exc:
        process_evidence(run, "operations.jsonl", {
            **operation, "phase": "result", "result": "error", "error": evidence_error(exc),
        })
        raise
    if code:
        raise subprocess.CalledProcessError(code, command)


def override_native_transport(run, request):
    """Apply an explicitly selected run transport without changing native models."""
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        raise ValueError("native transport override requires OPENAI_BASE_URL")
    visual_url = os.environ.get("VISUAL_BASE_URL")
    configurations = set()
    for profile_id, binding in request["bindings"].items():
        template = Path(binding["native_template"]).resolve(strict=True)
        native_root = Path(binding["native_home"]["root"]).resolve(strict=True)
        if not template.is_relative_to(run) or not native_root.is_relative_to(run):
            raise ValueError(f"native transport path escapes Braid run: {profile_id}")
        configurations.add(template / "models.json")
        configurations.update(home / "models.json" for home in native_root.glob(profile_id + "-*")
                              if home.is_dir())
    changes = {}
    for path in sorted(configurations):
        if not path.resolve(strict=True).is_relative_to(run):
            raise ValueError(f"native models path escapes Braid run: {path}")
        value = json.loads(path.read_text())
        providers = value["providers"]
        providers["factory26"].update(baseUrl=base_url, apiKey="$FACTORY26_API_KEY")
        if "factory26-visual" in providers:
            providers["factory26-visual"].update(
                baseUrl=visual_url or base_url,
                apiKey="$FACTORY26_VISUAL_API_KEY" if visual_url else "$FACTORY26_API_KEY")
        changes[path] = value
    originals = run / "recovery-native-transport/originals"
    originals.mkdir(parents=True, exist_ok=False)
    records = []
    for path, value in changes.items():
        backup = originals / path.relative_to(run)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
        records.append({"path": str(path), "original": str(backup),
                        "before_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "after_sha256": hashlib.sha256(encoded).hexdigest()})
        temporary = path.with_name(path.name + ".transport-override.tmp")
        with temporary.open("xb") as stream:
            stream.write(encoded)
        temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        temporary.replace(path)
    (run / "recovery-native-transport.json").write_text(json.dumps({
        "operation": "override-native-transport", "applied_at": time.time(), "files": records,
        "providers": ["factory26", "factory26-visual"],
        "base_url_source": "OPENAI_BASE_URL", "visual_url_source": "VISUAL_BASE_URL or OPENAI_BASE_URL",
        "key_variables": ["FACTORY26_API_KEY", "FACTORY26_VISUAL_API_KEY when VISUAL_BASE_URL is set"],
        "preserved": ["provider IDs", "model definitions", "profiles", "roles", "recipe", "history"],
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
    evidence_errors = []
    declared_run_id = os.environ.get("ARC_BENCH_RUN_ID") or os.environ.get("ARC_RUN_ID")
    attempt = {"attempt_id": uuid.uuid4().hex, "started_at": time.time(), "phase": "restoring",
               "source_run_id": source["source_run_id"], "braid_run_id": source["braid_run_id"],
               "source_workspace_sha256": source["workspace_sha256"], "current_platform_run_id": declared_run_id,
               "current_platform_binding": "declared environment" if declared_run_id
                    else "not exposed; bind this attempt receipt to the new official journal/run artifact",
               "mode": "prepare-only" if args.prepare_only else "recovery-execution"}
    run.mkdir(parents=True)
    diagnostic_receipt(run / "recovery-attempt.json", attempt, evidence_errors)
    print("Recovery: restoring retained workspace", flush=True)
    prior_logs = run / f"recovery-source-logs-{time.time_ns()}"
    prior_process_evidence = run / f"recovery-source-process-evidence-{time.time_ns()}"
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
                "recovery-braid.log", "recovery-diagnostics.json", "telemetry-collector.log",
                "recovery-attempt.json", "recovery-braid-binary.json", "recovery-preparation.json",
                "recovery-launch-paths.json", "recovery-provenance.json", "recovery-git.json",
            } and len(path.parts) == 4:
                target = prior_logs / path.name
            if path.parts[1:4] == (".factory26", source["braid_run_id"], "process-evidence"):
                target = prior_process_evidence.joinpath(*path.parts[4:])
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
    if source.get("replace_braid_deepseek_with_glm"):
        if not continuing:
            raise ValueError("Braid model migration requires explicit generation recovery")
        request = replace_braid_deepseek_with_glm(run, manifest.get("capabilities", {}).get("variant"))
    if source.get("override_native_transport"):
        if not continuing:
            raise ValueError("native transport override requires explicit generation recovery")
        override_native_transport(run, request)
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
        prior_result.rename(run / "recovery-source-result.json")
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
    actual_braid_sha256 = hashlib.sha256(braid.read_bytes()).hexdigest()
    if actual_braid_sha256 != source["braid_sha256"]:
        raise ValueError("restored Braid binary differs from recovery source")
    diagnostic_receipt(run / "recovery-braid-binary.json", {
        "packaged": str(runtime / "bin/braid"), "restored": str(braid),
        "sha256": actual_braid_sha256,
        "source_sha256": source["braid_sha256"],
    }, evidence_errors)
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
    attempt.update(phase="prepared", prepared_at=time.time(), evidence_errors=evidence_errors,
                   source_process_evidence=str(prior_process_evidence) if prior_process_evidence.exists() else None)
    diagnostic_receipt(run / "recovery-attempt.json", attempt, evidence_errors)
    if source.get("with_official_signal_evidence"):
        diagnostic_receipt(run / "process-evidence/attempt.json", attempt, evidence_errors)
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
            "model_migration_receipt": str(run / "recovery-model-migration.json")
                                       if source.get("replace_braid_deepseek_with_glm") else None,
            "native_transport_receipt": str(run / "recovery-native-transport.json")
                                        if source.get("override_native_transport") else None,
        }, indent=2) + "\n")
        print(f"Recovery: prepared without starting Braid; run={run}", flush=True)
        return
    # A source archive is historical; live readers must see the resumed sessions.
    old_native = run / "native"
    if old_native.exists() or old_native.is_symlink():
        old_native.rename(run / f"recovery-source-native-{time.time_ns()}")
    diagnostics = {}
    if evidence_errors:
        diagnostics["process_evidence_errors"] = evidence_errors
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
            execute_braid(command, run=run, app=app, env=env, log=log,
                          evidence=source.get("with_official_signal_evidence", False))
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
