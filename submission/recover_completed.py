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
import re
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


I14_VARIANTS = frozenset({"pi-braid-i14", "pi-braid-i14-cleaner",
                          "pi-braid-i14-reviewer", "pi-braid-i14-e2e"})
from agent_support import model_bindings, bind_retained_native_models


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
                alias.symlink_to(os.path.relpath(target, alias.parent), target_is_directory=True)
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


def refresh_native_materials(run, request, runtime, variant):
    """Refresh owned materials in templates and retained homes, preserving native memory."""
    work = run / "work"
    old_profiles = {profile["id"]: profile for profile in request["profiles"]}
    old_bindings = request["bindings"]
    backup = run / f"recovery-native-materials-{time.time_ns()}"
    backup.mkdir()
    for name in ("skills", "capabilities"):
        (work / name).rename(backup / name)
    shutil.copytree(ROOT / "skills", work / "skills")
    # Material generation must keep original role/profile identities. Its temporary
    # transport is discarded below; the explicit per-model override is applied last.
    declared_routes = os.environ.get("FACTORY26_MODEL_BINDINGS")
    if declared_routes and not any('-route-' in profile.get('provider', '') for profile in old_profiles.values()):
        routes, _ = model_bindings(require_key=False)
        material_routes = {}
        for selector, route in routes.items():
            material_routes.setdefault(selector.split('/', 1)[0],
                                       {key: value for key, value in route.items() if key != 'model_id'})
        os.environ["FACTORY26_MODEL_BINDINGS"] = json.dumps(material_routes)
    try:
        profiles, bindings = variant.native_files(
            work, runtime, work / "skills", os.environ.get("OPENAI_BASE_URL") or os.environ.get("FACTORY26_BASE_URL"),
            os.environ.get("VISUAL_BASE_URL"))
    finally:
        if declared_routes is not None:
            os.environ["FACTORY26_MODEL_BINDINGS"] = declared_routes
    current = {profile["id"]: profile for profile in profiles}
    if set(current) - set(old_profiles):
        raise ValueError("native material refresh cannot introduce assigned profiles")
    profiles, changes = [], []
    for profile_id, original in old_profiles.items():
        # 已迁移的成员保留历史 ID；base 中同名的新 DeepSeek profile
        # 不代表它仍使用 DeepSeek 材料，不能仅依据 ID 是否存在来选择。
        retained_glm_identity = (profile_id == "pi-deepseek-fast"
                                 and original.get("model") == "glm-5.3-flash"
                                 and "root-only" in original.get("tags", [])
                                 and request["root_profile_id"] != profile_id)
        material_id = "pi-glm-fast" if retained_glm_identity else profile_id
        if material_id not in current:
            raise ValueError(f"no authorized native materials for retained profile {profile_id}")
        replacement = current[material_id]
        for key in ("adapter_type", "adapter_version", "provider", "model", "reasoning",
                    "context_soft_ratio", "context_hard_bytes", "context_window_tokens"):
            if original.get(key) != replacement.get(key):
                raise ValueError(f"native material refresh changes {profile_id}.{key}")
        profiles.append(dict(original, user_instructions=replacement["user_instructions"]))
        if material_id != profile_id:
            source_folder = work / "capabilities" / material_id
            folder = work / "capabilities" / profile_id
            # 原 capabilities 已归档；这里只替换 native_files 本次新建的
            # 同名材料，不触碰保留的 native home 或模型配置。
            if folder.exists():
                shutil.rmtree(folder)
            shutil.copytree(source_folder, folder)
            launcher = folder / "pi"
            launcher.write_text(launcher.read_text().replace(str(source_folder), str(folder)))
            bindings[profile_id] = dict(bindings[material_id], executable=str(launcher),
                                        native_template=str(folder / "native-template"))
        template = Path(bindings[profile_id]["native_template"])
        old_template = backup / "capabilities" / Path(
            old_bindings[profile_id]["native_template"]).relative_to(work / "capabilities")
        # Keep every provider/model/transport setting from this run's own recipe.
        shutil.copy2(old_template / "models.json", template / "models.json")
        native_root = Path(old_bindings[profile_id]["native_home"]["root"])
        if not native_root.resolve().is_relative_to(work.resolve()):
            raise ValueError(f"native home root escapes the retained work directory: {native_root}")
        bindings[profile_id]["native_home"] = old_bindings[profile_id]["native_home"]
        for home in sorted(native_root.glob(profile_id + "-*")):
            if not home.is_dir() or not home.resolve().is_relative_to(native_root.resolve()):
                raise ValueError(f"invalid retained native home: {home}")
            before = hashes(home / "sessions")
            model_sha256 = hashlib.sha256((home / "models.json").read_bytes()).hexdigest()
            archived = backup / "native-homes" / home.name
            archived.mkdir(parents=True)
            material_changes = {}
            for name in ("agents", "settings.json", "pi-fff.json"):
                target, source_path = home / name, template / name
                if not source_path.exists():
                    continue
                if target.exists():
                    target.rename(archived / name)
                if source_path.is_dir():
                    shutil.copytree(source_path, target)
                    material_changes[name] = hashes(target)
                else:
                    shutil.copy2(source_path, target)
                    material_changes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
            if before != hashes(home / "sessions") or model_sha256 != hashlib.sha256(
                    (home / "models.json").read_bytes()).hexdigest():
                raise ValueError(f"native memory or model recipe changed during material refresh: {home}")
            changes.append({"profile_id": profile_id, "materials_profile": material_id,
                            "home": str(home), "backup": str(archived),
                            "session_files_unchanged": before, "models_sha256": model_sha256,
                            "materials": material_changes})
    (run / "recovery-native-materials.json").write_text(json.dumps({
        "source": "frozen package", "backup": str(backup), "homes": changes,
        "preserved": "Profile/model recipe, native sessions, authentication and application worktrees",
    }, ensure_ascii=False, indent=2) + "\n")
    return profiles, bindings


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
    routes, _ = model_bindings(require_key=False)
    configurations = set()
    native_roots = set()
    for profile_id, binding in request["bindings"].items():
        template = Path(binding["native_template"]).resolve(strict=True)
        native_root = Path(binding["native_home"]["root"]).resolve(strict=True)
        if not template.is_relative_to(run) or not native_root.is_relative_to(run):
            raise ValueError(f"native transport path escapes Braid run: {profile_id}")
        configurations.add(template / "models.json")
        homes = [home for home in native_root.glob(profile_id + "-*") if home.is_dir()]
        configurations.update(home / "models.json" for home in homes)
        native_roots.update([template, *homes])
    if request.get("pi", {}).get("home"):
        # Hosted ZIP exports omit empty global homes; session homes above remain mandatory.
        global_home = Path(request["pi"]["home"]).resolve()
        if not global_home.is_relative_to(run):
            raise ValueError("global native home escapes Braid run")
        if global_home.exists():
            if not global_home.is_dir():
                raise ValueError("global native home is not a directory")
            native_roots.add(global_home)
    changes = {}
    rebound_providers = set()
    for path in sorted(configurations):
        if not path.resolve(strict=True).is_relative_to(run):
            raise ValueError(f"native models path escapes Braid run: {path}")
        value = json.loads(path.read_text())
        bind_retained_native_models(value, routes)
        rebound_providers.update(value['providers'])
        changes[path] = value
    # Stored provider credentials take precedence over the selected environment.
    # Preserve all auth entries except those explicitly rebound by this recipe.
    for folder in sorted(native_roots):
        auth = folder / "auth.json"
        if auth.is_file():
            value = json.loads(auth.read_text())
            changes[auth] = {name: credential for name, credential in value.items() if name not in rebound_providers}
    originals = run / f"recovery-native-transport-{time.time_ns()}" / "originals"
    originals.mkdir(parents=True, exist_ok=False)
    previous_receipt = run / "recovery-native-transport.json"
    if previous_receipt.exists():
        shutil.copy2(previous_receipt, originals.parent / "previous-receipt.json")
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
        "providers": sorted({name for value in changes.values() if isinstance(value, dict)
                             for name in value.get('providers', {})}),
        "bindings": routes,
        "model_transports": sorted({(name, model['id'], model['samplingParams']['model'],
                                     model['baseUrl'])
                                    for path, value in changes.items() if path.name == 'models.json'
                                    for name, provider in value['providers'].items()
                                    for model in provider['models']}),
        "preserved": ["provider identities", "profiles", "roles", "recipe", "history"],
    }, indent=2) + "\n")


def material_notice_plan(run, source, manifest):
    """Freeze the explicit notice and verify live object routes without mutating Braid."""
    binding = source.get("material_notice_plan")
    if not binding:
        return None
    if (manifest.get("capabilities", {}).get("variant") not in I14_VARIANTS
            or not source.get("refresh_native_materials") or source["mode"] != "workspace-resume"):
        raise ValueError("material notice is only supported for explicitly refreshed I14 recovery")
    path = ROOT / binding["member"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise ValueError("frozen material notice plan SHA changed")
    plan = json.loads(path.read_text())
    if (plan["request_id"] != binding["request_id"] or plan["source_run_id"] != source["source_run_id"]
            or plan["braid_run_id"] != source["braid_run_id"]
            or Path(plan["retained_state"]) != run / "braid-state"
            or hashlib.sha256(plan["body"].encode()).hexdigest() != plan["body_sha256"]):
        raise ValueError("material notice source, state or body identity changed")
    for skill in plan["skills"]:
        expected = run / "work/skills" / skill["name"] / "SKILL.md"
        if Path(skill["path"]) != expected or hashlib.sha256(expected.read_bytes()).hexdigest() != skill["sha256"]:
            raise ValueError(f"prepared material notice skill path/SHA differs: {skill['name']}")
    target = plan["target"]
    if target["kind"] not in {"issue", "pr"} or target["node"] != f"{target['kind']}:{target['id']}":
        raise ValueError("material notice target node identity differs")
    members = {row["login"] for row in plan["recipients"]}
    mentions = set(re.findall(r"@([A-Za-z][A-Za-z0-9-]*)", plan["body"]))
    if mentions != set(plan["explicit_mentions"]) or len(members) != len(plan["recipients"]):
        raise ValueError("material notice mentions or recipients are ambiguous")
    with sqlite3.connect(f"file:{run / 'braid-state/braid.sqlite3'}?mode=ro", uri=True) as db:
        identity = db.execute("SELECT w.state,l.title,l.revision,l.body,l.desired_member_login FROM work_items w JOIN local_items l ON l.node_id=w.node_id WHERE w.node_id=?", (target["node"],)).fetchone()
        if not identity or (identity[0], identity[1], identity[2], hashlib.sha256(identity[3].encode()).hexdigest(), identity[4]) != (
                target["state"], target["title"], target["revision"], target["body_sha256"], target["owner"]):
            raise ValueError("material notice current target differs from frozen object identity")
        audience = {target["owner"], *mentions, *(row[0] for row in db.execute(
            "SELECT member_login FROM local_subscriptions WHERE work_item_node_id=? AND active=1 AND source='explicit'", (target["node"],)))}
        if audience != members:
            raise ValueError("normal comment would notify members outside the frozen recipient plan")
        for recipient in plan["recipients"]:
            route = db.execute("SELECT w.state,l.desired_member_login FROM work_items w JOIN local_items l ON l.node_id=w.node_id WHERE w.node_id=?", (recipient["node"],)).fetchone()
            active = db.execute("SELECT count(*) FROM assignments WHERE work_item_node_id=? AND member_login=? AND lifecycle='active'", (recipient["node"], recipient["login"])).fetchone()[0]
            if route != ("OPEN", recipient["login"]) or active != 1:
                raise ValueError(f"material notice recipient is no longer an active open-work owner: {recipient['login']}")
    frozen = run / "recovery-material-notice-plan.json"
    if frozen.exists() and frozen.read_bytes() != path.read_bytes():
        raise ValueError("retained recovery is already bound to a different material notice")
    if not frozen.exists():
        shutil.copy2(path, frozen)
    return plan


def send_material_notice(run, source, manifest, plan, braid, env, *, folder_name="recovery-material-notice", plan_sha256=None):
    """Use one normal comment; an ambiguous pending mutation is never resent."""
    import fcntl
    folder = run / folder_name
    folder.mkdir(exist_ok=True)
    identity = {name: source[name] for name in ("source_run_id", "braid_run_id", "workspace_sha256", "base_package_sha256", "braid_sha256")}
    identity.update(request_id=plan["request_id"], plan_sha256=plan_sha256 or source["material_notice_plan"]["sha256"],
                    recovery_source_sha256=manifest["files"]["recovery-source.json"]["sha256"],
                    main_sha256=manifest["files"]["main.py"]["sha256"])
    pending = folder / "pending.json"
    completed = folder / "receipt.json"
    def save(path, value):
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.chmod(0o600)
        temporary.replace(path)
    def matches():
        with sqlite3.connect(f"file:{run / 'braid-state/braid.sqlite3'}?mode=ro", uri=True) as db:
            return [row[0] for row in db.execute("SELECT comment_id,body FROM local_comments WHERE work_item_node_id=? AND writer_group IS NULL AND writer_turn IS NULL AND system_author IS NULL", (plan["target"]["node"],))
                    if row[1] is not None and hashlib.sha256(row[1].encode()).hexdigest() == plan["body_sha256"]]
    with (folder / 'notice.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prior = json.loads(pending.read_text()) if pending.exists() else None
        if prior and prior["identity"] != identity:
            raise ValueError("pending material notice belongs to different source/material/recovery inputs")
        existing = matches()
        if len(existing) > 1 or prior and not existing:
            raise ValueError("pending material notice has no unique unchanged comment; do not resend; inspect retained pending/CLI evidence")
        if completed.exists():
            receipt = json.loads(completed.read_text())
            if receipt["identity"] != identity or existing != [receipt["comment_id"]]:
                raise ValueError("completed material notice comment identity changed; do not resend")
            return receipt
        body = folder / "body.md"
        if not body.exists():
            body.write_text(plan["body"])
            body.chmod(0o600)
        if hashlib.sha256(body.read_bytes()).hexdigest() != plan["body_sha256"]:
            raise ValueError("material notice frozen body changed")
        command = [str(braid), "--state", str(run / "braid-state"), "--external", plan["target"]["kind"],
                   "comment", str(plan["target"]["id"]), "--body-file", str(body), "--json"]
        if not existing:
            record = {"identity": identity, "phase": "pending", "command": command, "body_sha256": plan["body_sha256"], "started_at": time.time()}
            save(pending, record)
            try:
                with (folder / "comment.stdout.json").open('xb') as stdout, (folder / "comment.stderr.log").open('xb') as stderr:
                    result = subprocess.run(command, env=env, stdout=stdout, stderr=stderr, timeout=60)
                record.update(exit_code=result.returncode, finished_at=time.time())
                save(pending, record)
                if result.returncode:
                    raise RuntimeError(f"material notice comment exited {result.returncode}; original stdout/stderr retained; do not resend")
                mutation = json.loads((folder / "comment.stdout.json").read_text())
                existing = matches()
                if existing != [mutation["id"]] or mutation.get("kind") != "comment" or mutation.get("action") != "created":
                    raise ValueError("material notice comment result differs from committed identity; do not resend")
            except BaseException as error:
                record.update(error={"type": type(error).__name__, "message": str(error)}, finished_at=time.time())
                save(pending, record)
                raise
        identifier = existing[0]
        readback = [str(braid), "--state", str(run / "braid-state"), "--external", "comment", "view", str(identifier),
                    "--include-hidden", "--json", "database_id,body,deliveries,lifecycle,thread_root"]
        token = uuid.uuid4().hex
        stdout_path, stderr_path = folder / f"readback-{token}.stdout.json", folder / f"readback-{token}.stderr.log"
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            result = subprocess.run(readback, env=env, stdout=stdout, stderr=stderr, timeout=60)
        if result.returncode:
            raise RuntimeError(f"material notice readback exited {result.returncode}; evidence retained; do not resend")
        rows = json.loads(stdout_path.read_text())
        recipients = {row["login"] for row in plan["recipients"]}
        if (len(rows) != 1 or str(rows[0]["database_id"]) != str(identifier)
                or rows[0]["body"] != plan["body"] or rows[0]["lifecycle"] == "deleted"
                or {row["recipient"] for row in rows[0]["deliveries"]} != recipients
                or any(row["status"] not in {"queued", "delivered"} for row in rows[0]["deliveries"])):
            raise ValueError("material notice comment/delivery differs from frozen plan; do not resend")
        receipt = {"identity": identity, "comment_id": identifier, "phase": "recorded",
                   "existing_comment_consumed": bool(prior or not (folder / 'comment.stdout.json').exists()),
                   "raw_readback": str(stdout_path), "raw_stderr": str(stderr_path), "readback_command": readback,
                   "deliveries": rows[0]["deliveries"], "recorded_at": time.time(),
                   "adoption": "not established; normal queued comment reference must be read by recipients"}
        save(completed, receipt)
        return receipt


def migrate_requirements(run, source, manifest, braid, env):
    migration = source.get("requirements_migration")
    if not migration:
        return
    payload = ROOT / migration["member"]
    if hashlib.sha256((payload / "requirements.yaml").read_bytes()).hexdigest() != migration["current_sha256"]:
        raise ValueError("frozen migrated requirements identity changed")
    retained = run / "input"
    if hashlib.sha256((retained / "requirements.yaml").read_bytes()).hexdigest() != migration["original_sha256"]:
        raise ValueError("retained requirements differ from authorized migration source")
    backup = run / "recovery-source-input-before-migration"
    shutil.copytree(retained, backup)
    database_backup = run / "recovery-source-database-before-requirements-migration"
    database_backup.mkdir()
    for name in ("braid.sqlite3", "braid.sqlite3-wal", "braid.sqlite3-shm"):
        path = run / "braid-state" / name
        if path.exists():
            shutil.copy2(path, database_backup / name)
    shutil.copytree(payload, retained, dirs_exist_ok=True)
    with sqlite3.connect(f"file:{run / 'braid-state/braid.sqlite3'}?mode=ro", uri=True) as db:
        owner = db.execute("SELECT desired_member_login FROM local_items WHERE node_id='issue:1'").fetchone()
        if not owner or not owner[0]:
            raise ValueError("requirements migration needs the existing root owner")
        recipients = {owner[0], *(row[0] for row in db.execute(
            "SELECT member_login FROM local_subscriptions WHERE work_item_node_id='issue:1' AND active=1 AND source='explicit'")),
            *(row[0] for row in db.execute("SELECT DISTINCT member_login FROM assignments WHERE lifecycle='active'"))}
    body = (" ".join("@" + login for login in sorted(recipients)) +
        "\n用户已明确选择：保留进度，迁移新版需求继续。现有应用、Git、Braid 工作项和原生会话历史均保留。" +
        f"需求来源仍为 {retained}，已替换为平台新版公开需求，SHA256={migration['current_sha256']}。" +
        f"旧需求 SHA256={migration['original_sha256']}，原件保存在 {backup}。" +
        "请立即读取新版 requirements.yaml，重新核对已实现与未实现需求，更新现有设计、工作项和交付计划；" +
        "沿用当前分工并协调必要修正，不重新从零生成。已有完成状态不自动证明满足新版需求。" +
        "本次结果单列为 I13 进度在新版需求下接续，不与旧版分数直接比较。此通知仅依据公开需求，不包含隐藏评测反馈。")
    plan = {"request_id": "requirements-migration-" + migration["current_sha256"][:16],
            "target": {"kind": "issue", "id": 1, "node": "issue:1"},
            "recipients": [{"login": login} for login in sorted(recipients)],
            "body": body, "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "requirements_migration": migration}
    plan_path = run / "recovery-requirements-migration.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    send_material_notice(run, source, manifest, plan, braid, env,
                         folder_name="recovery-requirements-notice", plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())


def load_packaged_model_environment(source, manifest):
    """Load only declared route credentials from the manifest-verified private file."""
    path = ROOT / '.private/model-env.json'
    if not path.exists():
        return
    if '.private/model-env.json' not in manifest['files']:
        raise ValueError('packaged model environment is not bound to the package manifest')
    if not source.get('override_native_transport'):
        raise ValueError('packaged model environment requires explicit native transport override')
    if (path.is_symlink() or path.parent.is_symlink()
            or not path.resolve(strict=True).is_relative_to(ROOT.resolve())):
        raise ValueError('packaged model environment must remain inside the package without links')
    # Platform ZIP extraction can discard stored modes. The caller has already
    # verified the manifest bytes, so restore privacy before reading credentials.
    path.parent.chmod(0o700)
    path.chmod(0o600)
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or set(payload) != {'environment'}:
        raise ValueError('packaged model environment requires exactly an environment mapping')
    values = payload['environment']
    if (not isinstance(values, dict) or not values.get('FACTORY26_MODEL_BINDINGS')
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in values.items())):
        raise ValueError('packaged model environment requires string names and values plus explicit bindings')
    previous = os.environ.get('FACTORY26_MODEL_BINDINGS')
    os.environ['FACTORY26_MODEL_BINDINGS'] = values['FACTORY26_MODEL_BINDINGS']
    try:
        routes, _ = model_bindings(require_key=False)
    finally:
        if previous is None:
            os.environ.pop('FACTORY26_MODEL_BINDINGS', None)
        else:
            os.environ['FACTORY26_MODEL_BINDINGS'] = previous
    credentials = {route['credential_env'] for route in routes.values()}
    if 'FACTORY26_MODEL_BINDINGS' in credentials or set(values) != {'FACTORY26_MODEL_BINDINGS', *credentials}:
        raise ValueError('packaged model environment must contain only bindings and their credential variables')
    if any(not values[name] for name in credentials):
        raise ValueError('packaged model environment lacks a declared credential')
    os.environ.update(values)


def recovery_execution_environment(source, variant_name, runtime, run, model_env, prepare_only, evidence_errors):
    work = run / "work"
    continuing = source["mode"] == "workspace-resume"
    resource_sources = {"helper": ROOT / "support/runtime_resources.py",
                        "native_module": runtime / "native-managed.mjs"}
    resource_capability = {name: path.is_file() for name, path in resource_sources.items()}
    managed_resource_enabled = continuing and (
        source.get("resource_admission") == "i13-2-v1" or all(resource_capability.values()))
    resource_environment = {}
    env = model_env
    if continuing:
        key = env.get("FACTORY26_API_KEY") or env.get("OPENAI_API_KEY")
        if not prepare_only and not key and not os.environ.get("FACTORY26_MODEL_BINDINGS"):
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
        if variant_name in {"pi-braid-i13", "pi-braid-i13-glm-root"} | I14_VARIANTS:
            import run as variant
            # These process settings are not retained in the native session files.
            env.update(variant.tool_environment(), PI_FFF_MODE="tools-only", PI_FFF_MULTIGREP="0",
                       PI_SUBAGENT_MAX_DEPTH="3")
        if managed_resource_enabled:
            from agent_support import runtime_resource_environment
            resource_environment = runtime_resource_environment(runtime, run)
            env.update(resource_environment)
        diagnostic_receipt(run / "recovery-resource-environment.json", {
            "source_resource_admission": source.get("resource_admission"),
            "capability": {name: {"path": str(resource_sources[name]), "present": present}
                           for name, present in resource_capability.items()},
            "enabled": managed_resource_enabled,
            "environment": resource_environment,
        }, evidence_errors)
    return env, managed_resource_enabled


def execute_recovery(run, source, manifest, request, env, braid, notice,
                     managed_resource_enabled, evidence_errors, output):
    work, runtime = run / "work", ROOT / "runtime"
    app, origin = work / "application", run / "braid-state/origin.git"
    continuing = source["mode"] == "workspace-resume"
    if notice:
        send_material_notice(run, source, manifest, notice, braid, env)
    # A source archive is historical; live readers must see the resumed sessions.
    old_native = run / "native"
    if old_native.exists() or old_native.is_symlink():
        old_native.rename(run / f"recovery-source-native-{time.time_ns()}")
    diagnostics = {}
    if evidence_errors:
        diagnostics["process_evidence_errors"] = evidence_errors
    collector = None
    shared_proxy = None
    execution_error = None
    cleanup_error = None
    try:
        try:
            collector, binding = start_local_telemetry(run)
            env.update(telemetry_environment(binding))
        except Exception as exc:
            if os.environ.get("FACTORY26_EXP_TELEMETRY_BINDING"):
                raise
            diagnostics["telemetry_diagnostic_error"] = f"{type(exc).__name__}: {exc}"
        if managed_resource_enabled:
            from agent_support import start_shared_proxy, stop_shared_proxy
            shared_proxy = start_shared_proxy(runtime, run, env)
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
        if shared_proxy is not None:
            try:
                stop_shared_proxy(shared_proxy, run)
            except Exception as exc:
                diagnostics['shared_proxy_cleanup_error'] = f'{type(exc).__name__}: {exc}'
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



def execute_verified_preparation(args, source, manifest):
    """Execute the already assembled public prepared payload without restoring it again."""
    output = args.output_dir.resolve(strict=True)
    run = output / ".factory26" / source["braid_run_id"]
    preparation = json.loads((run / "recovery-preparation.json").read_text())
    provenance = json.loads((run / "recovery-provenance.json").read_text())
    if preparation.get("mode") != "prepare-only" or preparation.get("models_started") is not False or provenance != source:
        raise ValueError("prepared recovery provenance differs from its frozen package")
    requirement = args.requirements_dir / "requirements.yaml"
    if hashlib.sha256(requirement.read_bytes()).hexdigest() != source["requirements_sha256"]:
        raise ValueError("current requirements differ from prepared recovery")
    request = json.loads((run / "braid-request.json").read_text())
    if request["run_id"] != source["braid_run_id"] or Path(request["state"]) != run / "braid-state":
        raise ValueError("prepared Braid request namespace or state path differs")
    braid = run / "work/bin/braid"
    if hashlib.sha256(braid.read_bytes()).hexdigest() != source["braid_sha256"]:
        raise ValueError("prepared Braid binary differs from its frozen package")
    # Lab's frozen recipe and current private deployment own execution routes and keys.
    # Packaged credentials belong to acquisition; they cannot replace this deployment.
    routes, model_env = model_bindings(require_key=True)
    transport = json.loads((run / "recovery-native-transport.json").read_text())
    if transport["bindings"] != routes:
        raise ValueError("current routes differ from prepared native transports; prepare again")
    evidence_errors = []
    env, managed = recovery_execution_environment(source, manifest.get("capabilities", {}).get("variant"),
                                                  ROOT / "runtime", run, model_env, False, evidence_errors)
    notice = material_notice_plan(run, source, manifest)
    execute_recovery(run, source, manifest, request, env, braid, notice, managed, evidence_errors, output)


def execute_prepared(args):
    """Consume runner assembly; never restore, rewrite history or refresh materials."""
    binding = json.loads(os.environ.get('FACTORY26_EXP_PREPARED_BINDING','{}'))
    assembly_path = Path(os.environ.get('FACTORY26_EXP_ASSEMBLY',''))
    if not binding or binding.get('attempt_id') != os.environ.get('FACTORY26_EXP_ATTEMPT_ID') or binding.get('assembly_status') != 'complete':
        raise ValueError('prepared执行缺少当前runner装配绑定')
    assembly = json.loads(assembly_path.read_text())
    if assembly.get('status') != 'assembled' or assembly.get('workspace') != binding['run_root']:
        raise ValueError('prepared执行装配原件与workspace不一致')
    manifest_path = Path(binding['manifest_path'])
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != binding['manifest_sha256']:
        raise ValueError('prepared manifest与装配绑定不一致')
    import exp_checkpoint
    manifest = json.loads(manifest_path.read_text())
    # Runner already resolved/retained v3 assets and verified the assembly. The standalone
    # delivered module must not import an implicit controller-side lab package.
    if manifest.get('schema_version') == 3:
        validation = {'status': manifest['status']}
        if not assembly.get('definitions'):
            raise ValueError('v3 prepared执行缺少runner定义装配回执')
    else:
        validation = exp_checkpoint.validate(manifest_path.parent)
    if manifest['kind'] != 'factory26.harness.prepared' or validation['status'] != 'complete':
        raise ValueError('prepared执行需要新版完整恢复合同')
    run = Path(binding['run_root'])
    if exp_checkpoint.inventory(run) != {name.removeprefix('run/'):value for name,value in manifest['files'].items() if name.startswith('run/')}:
        raise ValueError('可写恢复工作区在入口前与装配内容不一致')
    request = json.loads((run/'braid-request.json').read_text())
    if request['state'] != str(run/'braid-state'): raise ValueError('Braid state logical root不匹配')
    work = run/'work'
    definitions = {row['name']: Path(row['logical_root']) for row in manifest.get('definition_assets', [])}
    runtime = definitions.get('runtime', ROOT/'runtime')
    agent = definitions.get('agent', ROOT)
    braid = definitions.get('braid', work/'bin/braid')
    from agent_support import runtime_resource_environment, model_bindings
    _, env = model_bindings(require_key=True)
    env.update(runtime_resource_environment(runtime,run),
               XDG_CONFIG_HOME=str(work/'home/.config'),
               npm_config_cache=str(work/'cache/npm'), npm_config_store_dir=str(work/'cache/pnpm'),
               PI_SUBAGENTS_TEMP_ROOT=str(work/'tmp'/f'pi-subagents-uid-{os.getuid()}'),
               MCPORTER_CONFIG=str(agent/'tools/mcporter.json'),
               PBB_PIL_BIN=str(runtime/'node_modules/pi-lane/bin/pil.js'),
               AGENT_BROWSER_EXECUTABLE_PATH=str(browser_executable(runtime)),
               BROWSER_EXECUTABLE_PATH=str(browser_executable(runtime)),
               BROWSER_CHECK_NODE_MODULES=str(runtime/'node_modules'),
               HOME=str(work/'home'), TMPDIR=str(work/'tmp'), PI_CODING_AGENT_DIR=str(work/'home/.pi/agent'),
               PI_OFFLINE='1', PI_TELEMETRY='0', PI_SUBAGENT_MAX_DEPTH='3',
               PATH=os.pathsep.join((str(work/'bin'),str(runtime/'bin'),str(runtime/'node_modules/.bin'),env.get('PATH',''))))
    collector,binding = start_local_telemetry(run)
    env.update(telemetry_environment(binding))
    from agent_support import start_shared_proxy, stop_shared_proxy
    shared_proxy = start_shared_proxy(runtime,run,env)
    try:
        with (run/'recovery-braid.log').open('w') as log:
            execute_braid([str(braid),'local',str(run/'braid-request.json'),'--resume'],
                          run=run,app=work/'application',env=env,log=log,evidence=[])
        delivery = load_delivery(run/'braid-state/origin.git',request)
        application = run/'recovered-application'
        export_delivery(run/'braid-state/origin.git',delivery['delivery_commit'],application)
        deliver(application,args.output_dir)
        from braid_runtime import publish_application
        publish_application(run/'braid-state/origin.git',delivery['delivery_commit'],run/'application-artifact',
                            args.requirements_dir, {'attempt_id':os.environ['FACTORY26_EXP_ATTEMPT_ID'],'braid_run_id':request['run_id']})
    finally:
        stop_shared_proxy(shared_proxy,run)
        if collector: stop_local_telemetry(collector)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("requirements_dir", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--type", default="web")
    parser.add_argument("--prepare-only", action="store_true",
                        help="Restore and verify the workspace without starting Braid or calling models")
    parser.add_argument("--execute-prepared", action="store_true",
                        help="Execute an already assembled verified preparation without restoring or migrating it")
    args = parser.parse_args()
    if args.execute_prepared:
        if args.prepare_only: parser.error("execute-prepared不能重新prepare")
        return execute_prepared(args)
    print("Recovery: verifying packaged runtime and workspace", flush=True)
    manifest = verify_package(ROOT)
    source = json.loads((ROOT / "recovery-source.json").read_text())
    load_packaged_model_environment(source, manifest)
    variant_name = manifest.get("capabilities", {}).get("variant")
    model_env = dict(os.environ)
    if source.get("override_native_transport"):
        _, model_env = model_bindings(require_key=not args.prepare_only)
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
        relative = target.relative_to(run).as_posix()
        reconstruction = source.get("git_reconstruction", {}).get(relative)
        if not reconstruction:
            raise ValueError(f"clone .git missing; explicit Git reconstruction evidence required: {relative}")
        commit, branch = reconstruction["commit"], reconstruction["branch"]
        if not reconstruction.get("evidence"):
            raise ValueError(f"Git reconstruction lacks evidence: {relative}")
        target.mkdir(parents=True, exist_ok=True)
        def git(*arguments):
            return subprocess.check_output(["git", "-C", str(target), *arguments], text=True).strip()
        git("init", "-q", "-b", branch)
        git("remote", "add", "origin", str(origin))
        git("fetch", "-q", "origin")
        resolved = git("rev-parse", "--verify", commit + "^{commit}")
        if resolved != commit:
            raise ValueError(f"Git reconstruction requires full confirmed commit: {relative}")
        git("update-ref", "refs/heads/" + branch, commit)
        git("symbolic-ref", "HEAD", "refs/heads/" + branch)
        # Rebuild the index without checkout: retain uncommitted snapshot files.
        git("read-tree", commit)
        git("config", "user.name", "Factory Agent")
        git("config", "user.email", "factory26@localhost")
        git("config", "commit.gpgsign", "false")
        (target / ".git/info/exclude").write_text(".braid/\nnode_modules/\n")
        git_repairs.append({"path": str(target), "published_base": commit,
                            "branch": branch, "evidence": reconstruction["evidence"],
                            "retained_changes": git("status", "--porcelain")})
    (run / "recovery-git.json").write_text(json.dumps({
        "limitation": "Clone .git omitted; reconstructed HEAD/index from explicit evidence. Original staging, reflog and unpublished history are not restored",
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
        if source.get("resource_admission") == "i13-2-v1" or variant_name in I14_VARIANTS:
            profiles, bindings = refresh_native_materials(run, request, runtime, variant)
        else:
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
        # recipe identity. Keep the stored Profile revision for Braid to reconcile
        # updated instructions with the retained native session on resume.
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
    if continuing and source.get("override_native_transport"):
        override_native_transport(run, request)
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
    env, managed_resource_enabled = recovery_execution_environment(
        source, variant_name, runtime, run, model_env, args.prepare_only, evidence_errors)
    (run / "recovery-provenance.json").write_text(json.dumps(source, indent=2) + "\n")
    attempt.update(phase="prepared", prepared_at=time.time(), evidence_errors=evidence_errors,
                   source_process_evidence=str(prior_process_evidence) if prior_process_evidence.exists() else None)
    diagnostic_receipt(run / "recovery-attempt.json", attempt, evidence_errors)
    if source.get("with_official_signal_evidence"):
        diagnostic_receipt(run / "process-evidence/attempt.json", attempt, evidence_errors)
    migrate_requirements(run, source, manifest, braid, env)
    notice = material_notice_plan(run, source, manifest)
    if args.prepare_only:
        # This is a stopped daemon's transient socket namespace, not native
        # session history. Preserve its literal target before preparing anew.
        retired_links = []
        pulse = run / "work/home/.config/pulse"
        if pulse.is_dir() and not pulse.is_symlink():
            for link in pulse.iterdir():
                if re.fullmatch(r"[0-9a-f]{32}-runtime", link.name) and link.is_symlink():
                    target = os.readlink(link)
                    if re.fullmatch(r"/tmp/f26-[^/]+/pulse-[^/]+", target):
                        retired_links.append({"path": str(link), "target": target,
                                              "reason": "stopped PulseAudio transient runtime; original snapshot retained"})
                        link.unlink()
        diagnostic_receipt(run / "recovery-transient-links.json", {"retired_links": retired_links}, evidence_errors)
        build_links = []
        locations = [run / "work/application/backend/node_modules/.pnpm/better-sqlite3@11.10.0/node_modules/better-sqlite3/build/node_gyp_bins/python3"]
        locations.extend((run / "braid-state/worktrees").glob("*/*/backend/node_modules/.pnpm/better-sqlite3@11.10.0/node_modules/better-sqlite3/build/node_gyp_bins/python3"))
        for link in locations:
            if not link.is_symlink() or os.readlink(link) != "/usr/bin/python3":
                continue
            if not link.parent.resolve().is_relative_to(run.resolve()):
                raise ValueError("node-gyp build tool parent escapes the restored run")
            if not os.environ.get("FACTORY26_EXP_ATTEMPT_DIR"):
                raise ValueError("node-gyp tool materialization requires the explicitly frozen Lab target image")
            interpreter = Path("/usr/bin/python3").resolve(strict=True)
            if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
                raise ValueError("target image node-gyp Python is not an executable regular file")
            temporary = link.with_name(".python3." + uuid.uuid4().hex)
            try:
                shutil.copy2(interpreter, temporary)
                temporary.replace(link)
            finally:
                temporary.unlink(missing_ok=True)
            image_id = json.loads((Path(os.environ["FACTORY26_EXP_ATTEMPT_DIR"]) / "attempt.json").read_text())["job"]["backend"]["image_id"]
            build_links.append({"path": str(link), "raw_link": "/usr/bin/python3", "resolved_target": str(interpreter),
                                "sha256": hashlib.file_digest(interpreter.open("rb"), "sha256").hexdigest(),
                                "image_id": image_id, "reason": "rebuild stopped node-gyp tool under explicitly frozen target image"})
        diagnostic_receipt(run / "recovery-build-tools.json", {"materialized_links": build_links}, evidence_errors)
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
            "material_notice_plan": str(run / "recovery-material-notice-plan.json") if notice else None,
            "material_notice_sent": False,
        }, indent=2) + "\n")
        print(f"Recovery: prepared without starting Braid; run={run}", flush=True)
        return
    execute_recovery(run, source, manifest, request, env, braid, notice,
                     managed_resource_enabled, evidence_errors, output)


if __name__ == "__main__":
    main()
