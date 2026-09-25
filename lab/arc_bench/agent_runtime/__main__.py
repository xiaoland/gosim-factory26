"""Standalone ARC-Bench SDK command for any Python Agent package."""

import argparse
from contextlib import contextmanager, ExitStack, nullcontext
import fcntl
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from arcbench_agent_runtime import AgentRuntime
from arcbench_agent_runtime.events import EventClient
from arcbench_agent_runtime.traceability import TABLE_NAMES, TraceabilityStore


API_VERSION = 1
VERSION = "arcbench-agent-runtime 0.1.0 (official starter 2026-09-25)"
GUIDE = """ARC-Bench reporting

Put this file in the Agent ZIP and pass its absolute path through your Harness.
Python >=3.10 is required. Runner ARCBENCH_* paths are used by default;
outside a Runner, pass --output-dir. All concurrent writers should use this
tool so its file locks can protect the shared SDK store and event stream.

Examples:
  python3 /absolute/path/arc-runtime.pyz methods --json
  printf '%s' '{"interface_id":"api.users","req_ids":["REQ-1"],"type":"api","content":"GET /users","file_path":"backend/users.py"}' | python3 /absolute/path/arc-runtime.pyz traceability upsert_interface --json-file - --json
  python3 /absolute/path/arc-runtime.pyz events mark_implementation_done --json-file state.json --json
  python3 /absolute/path/arc-runtime.pyz notify-history --json
  python3 /absolute/path/arc-runtime.pyz publish-history --source-repo /path/to/repo --ref refs/heads/delivery --json

Use notify-history for an existing Runner-root Git repository; publish-history
imports one selected commit into a managed Runner-root repository. --json emits
one v1 result with paths, status and operation details; exit 1 may mean partial.
Only report relationships and test outcomes supported by actual work.
A written refresh signal does not prove the hosted UI received it.
The official evaluation score is separate from Agent declarations.
"""

# This is the wrapper's public surface, independent of future SDK additions.
TRACEABILITY_METHODS = frozenset("""
export_snapshot store_requirement_tree get_requirement list_requirements
upsert_requirement update_requirement_fields delete_requirement get_scenario
list_scenarios upsert_scenario delete_scenario get_interface list_interfaces
upsert_interface update_interface_fields set_interface_implemented
delete_interface get_test list_tests upsert_test update_test_fields
set_test_pass_status set_test_pass_statuses
reset_test_pass_statuses_for_requirement delete_test insert_call_edge
list_call_edges delete_call_edge upsert_node_state set_requirement_state
get_node_state get_requirement_state list_node_states list_requirement_states
delete_node_state upsert_node_contract get_node_contract list_node_contracts
delete_node_contract clear_node_design_artifacts
""".split())
EVENT_METHODS = frozenset("""
mark_design_started mark_design_done mark_design_failed
mark_implementation_started mark_implementation_done mark_implementation_failed
mark_test_passed mark_test_failed mark_run_started mark_run_completed
mark_run_failed mark_run_paused mark_run_resumed notify_traceability_changed
""".split())
READ_ONLY_METHODS = frozenset(name for name in TRACEABILITY_METHODS
                              if name.startswith(("get_", "list_")) or name == "export_snapshot")


@contextmanager
def locked_store(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".arc-runtime.lock").open("a") as stream:
        # Advisory locks coordinate this tool's callers, not direct SDK writers.
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


@contextmanager
def locked_stores(*directories, first=None):
    with ExitStack() as stack:
        # History publication takes its repository lock before the event lock.
        for directory in sorted(set(directories), key=lambda path: (path != first, str(path))):
            stack.enter_context(locked_store(directory))
        yield


def check_tables(directory):
    # Upstream read_json treats a corrupt table as empty; preserve it instead.
    for name in TABLE_NAMES:
        path = directory / (name + ".json")
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"{path}: official table must be a JSON object")


class GitCommandError(RuntimeError):
    def __init__(self, command, result):
        self.command = command
        self.returncode = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr
        super().__init__(result.stderr.strip() or result.stdout.strip() or
                         f"git exited {result.returncode}")


def git(directory, *arguments, check=True):
    command = ["git", "-C", str(directory), *arguments]
    result = subprocess.run(command, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if check and result.returncode:
        raise GitCommandError(command, result)
    return result


def error_info(exc):
    error = {"type": type(exc).__name__, "message": str(exc)}
    if isinstance(exc, GitCommandError):
        error.update(command=exc.command, exit_code=exc.returncode,
                     stdout=exc.stdout, stderr=exc.stderr)
    return error


def paths_for(runtime):
    return {"project_dir": str(runtime.paths.project_dir),
            "traceability_dir": str(runtime.paths.traceability_dir),
            "runner_events_path": str(runtime.paths.runner_events_path),
            "operation_log": str(runtime.paths.project_dir /
                                 ".arc/runtime-reporting/operations.jsonl")}


def event_lock(runtime, held_directory):
    directory = runtime.paths.runner_events_path.parent
    # A custom events path may put both locks in the same directory.
    return nullcontext() if directory == held_directory else locked_store(directory)


def notify_history(runtime, result, *, preview=False):
    project = runtime.paths.project_dir
    result.update(mode="existing", phase="verify_repository")
    if not (project / ".git").exists():
        raise ValueError(f"Runner project is not a Git worktree root: {project}")
    top = git(project, "rev-parse", "--show-toplevel").stdout.strip()
    if Path(top).resolve() != project:
        raise ValueError(f"Runner project is not a Git worktree root: {project}")
    result.update(selected_commit=git(
        project, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip(),
        history_updated=False, history_changed=False)
    result["phase"] = "write_signal"
    with event_lock(runtime, project / ".arc/runtime-reporting"):
        runtime.events.notify_commit_history_changed("existing_history_changed",
                                                     preview=preview)
    result["signal_written"] = True
    result["phase"] = "completed"


def publish_history(runtime, source_repo, ref, result, *, preview=False):
    """Import one immutable ancestry, leaving application files and the index alone."""
    result.update(mode="imported", source_repo=str(source_repo), requested_ref=ref,
                  history_changed=False, history_updated=False,
                  signal_written=False, phase="resolve_source")
    source = source_repo.resolve(strict=True)
    result["source_repo"] = str(source)
    project = runtime.paths.project_dir
    if source == project:
        raise ValueError("source repository equals Runner project; use notify-history")
    oid = git(source, "rev-parse", "--verify", "--end-of-options",
              ref + "^{commit}").stdout.strip()
    result["selected_commit"] = oid
    result["phase"] = "prepare_target"
    git_dir = project / ".git"
    if not git_dir.exists():
        git(project, "init", "-q", "-b", "arc-delivery")
        result["repository_initialized"] = True
        git(project, "config", "arcbench.history-publisher", "1")
    else:
        marker = git(project, "config", "--get", "arcbench.history-publisher",
                     check=False)
        if marker.returncode or marker.stdout.strip() != "1":
            raise ValueError(f"Runner project already has an unmanaged Git repository: {project}")
    current = git(project, "rev-parse", "--verify", "HEAD", check=False)
    current_ref = git(project, "symbolic-ref", "--quiet", "HEAD", check=False)
    delivery_ref = git(project, "rev-parse", "--verify", "refs/heads/arc-delivery",
                       check=False)
    changed = (current.returncode or current.stdout.strip() != oid or
               current_ref.stdout.strip() != "refs/heads/arc-delivery" or
               delivery_ref.returncode or delivery_ref.stdout.strip() != oid)
    if changed:
        result["phase"] = "import_commit"
        if git(project, "cat-file", "-e", oid + "^{commit}", check=False).returncode:
            git(project, "fetch", "--no-tags", "--quiet", str(source), oid)
        result["phase"] = "update_ref"
        git(project, "update-ref", "refs/heads/arc-delivery", oid)
        result["history_updated"] = True
        git(project, "symbolic-ref", "HEAD", "refs/heads/arc-delivery")
        result["history_changed"] = True
    # A previous call may have updated the ref but failed to write its signal.
    result["phase"] = "write_signal"
    with event_lock(runtime, project / ".arc/runtime-reporting"):
        runtime.events.notify_commit_history_changed("delivery_history_published",
                                                     preview=preview)
    result["signal_written"] = True
    result["phase"] = "completed"


def record_operation(runtime, record):
    path = runtime.paths.project_dir / ".arc/runtime-reporting/operations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked_store(runtime.paths.runner_events_path.parent):
        with path.open("a", encoding="utf-8") as output:
            output.write(json.dumps({"time": time.time(), "sdk": VERSION,
                                     **record}, ensure_ascii=False) + "\n")


def result_record(operation, runtime=None):
    return {"api_version": API_VERSION, "operation": operation, "status": "failed",
            "paths": paths_for(runtime) if runtime else {}, "result": {}}


def emit(record, *, json_mode, legacy=None):
    if json_mode:
        print(json.dumps(record, ensure_ascii=False))
    elif record["status"] == "completed":
        print(json.dumps(legacy if legacy is not None else
                         {"status": "completed", "result": record["result"]},
                         ensure_ascii=False))
    else:
        error = record.get("error", {})
        print(f"ARC {record['operation']}: {error.get('type', 'Error')}: "
              f"{error.get('message', 'unknown error')}", file=sys.stderr)
    if record.get("diagnostic_error"):
        print(f"ARC diagnostic write failed: {record['diagnostic_error']}",
              file=sys.stderr)
    return 0 if record["status"] == "completed" else 1


def run_operation(args):
    operation = (f"{args.command}.{args.method}" if args.command in
                 ("traceability", "events") else args.command)
    record = result_record(operation)
    runtime = None
    invoked_sdk = False
    try:
        runtime = AgentRuntime.from_env(project_dir=str(args.output_dir)
                                        if args.output_dir else None)
        record["paths"] = paths_for(runtime)
        result = record["result"]
        if args.command in ("publish-history", "notify-history"):
            result.update(history_updated=False, history_changed=False,
                          signal_written=False)
            with locked_store(runtime.paths.project_dir / ".arc/runtime-reporting"):
                if args.command == "publish-history":
                    publish_history(runtime, args.source_repo, args.ref, result,
                                    preview=args.preview)
                else:
                    notify_history(runtime, result, preview=args.preview)
        else:
            result["phase"] = "validate_input"
            allowed = TRACEABILITY_METHODS if args.command == "traceability" else EVENT_METHODS
            if args.method not in allowed:
                raise ValueError(f"unsupported official {args.command} method: "
                                 f"{args.method}; use methods to list choices")
            content = (sys.stdin.read() if args.json_file == "-" else
                       Path(args.json_file).read_text() if args.json_file else "{}")
            kwargs = json.loads(content)
            if not isinstance(kwargs, dict):
                raise ValueError("--json-file must contain a JSON object of SDK keyword arguments")
            if args.command == "traceability":
                with locked_stores(runtime.paths.traceability_dir,
                                   runtime.paths.runner_events_path.parent,
                                   first=runtime.paths.project_dir / ".arc/runtime-reporting"):
                    check_tables(runtime.paths.traceability_dir)
                    result["phase"] = "invoke_sdk"
                    invoked_sdk = True
                    result["value"] = getattr(runtime.traceability, args.method)(**kwargs)
            else:
                writes_state = args.method.startswith(("mark_design_", "mark_implementation_",
                                                       "mark_test_"))
                lock_dirs = [runtime.paths.runner_events_path.parent]
                if writes_state:
                    lock_dirs.append(runtime.paths.traceability_dir)
                with locked_stores(*lock_dirs,
                                   first=runtime.paths.project_dir / ".arc/runtime-reporting"):
                    if writes_state:
                        check_tables(runtime.paths.traceability_dir)
                    result["phase"] = "invoke_sdk"
                    invoked_sdk = True
                    result["value"] = getattr(runtime.events, args.method)(**kwargs)
            result["phase"] = "completed"
        record["status"] = "completed"
    except Exception as exc:
        record["error"] = error_info(exc)
        if (record["result"].get("history_updated") or
                record["result"].get("repository_initialized") or
                record["result"].get("phase") in ("update_ref", "write_signal") or
                invoked_sdk and getattr(args, "method", None) not in READ_ONLY_METHODS):
            record["status"] = "partial"
    if runtime is not None:
        try:
            record_operation(runtime, record)
        except OSError as exc:
            record["diagnostic_error"] = error_info(exc)
    if args.command == "publish-history" and record["status"] == "completed":
        legacy = {"status": "published" if record["result"]["history_changed"]
                  else "unchanged", "commit": record["result"]["selected_commit"]}
    elif args.command in ("traceability", "events") and record["status"] == "completed":
        legacy = {"status": "completed", "result": record["result"]["value"]}
    else:
        legacy = None
    return emit(record, json_mode=args.json, legacy=legacy)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("guide", help="show how to add this tool to a Harness")
    for name in ("version", "methods"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true")
    for name in ("publish-history", "notify-history"):
        command = commands.add_parser(name)
        command.add_argument("--preview", action="store_true")
        command.add_argument("--output-dir", type=Path)
        command.add_argument("--json", action="store_true")
        if name == "publish-history":
            command.add_argument("--source-repo", type=Path, required=True)
            command.add_argument("--ref", required=True)
    for scope in ("traceability", "events"):
        command = commands.add_parser(scope)
        command.add_argument("method")
        command.add_argument("--json-file", type=str)
        command.add_argument("--output-dir", type=Path)
        command.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "guide":
        print(GUIDE)
        return 0
    if args.command == "version":
        value = {"api_version": API_VERSION, "sdk": VERSION}
        print(json.dumps(value) if args.json else VERSION)
        return 0
    if args.command == "methods":
        entries = []
        for scope, cls, names in (("traceability", TraceabilityStore, TRACEABILITY_METHODS),
                                  ("events", EventClient, EVENT_METHODS)):
            for name in sorted(names):
                method = getattr(cls, name)
                signature = inspect.signature(method)
                signature = signature.replace(parameters=list(
                    signature.parameters.values())[1:])
                entries.append({"scope": scope, "method": name,
                                "signature": str(signature)})
        if args.json:
            print(json.dumps({"api_version": API_VERSION, "methods": entries}))
        else:
            for entry in entries:
                print(f"{entry['scope']} {entry['method']}{entry['signature']}")
        return 0

    if args.command in ("traceability", "events"):
        allowed = TRACEABILITY_METHODS if args.command == "traceability" else EVENT_METHODS
        if args.method not in allowed:
            parser.error(f"unsupported official {args.command} method: {args.method}; "
                         "use methods to list choices")

    if not args.output_dir and not any(os.environ.get(name, "").strip() for name in
                                       ("ARCBENCH_OUTPUT_DIR", "ARCBENCH_PROJECT_DIR",
                                        "ARCBENCH_TEMPLATE_DIR")):
        parser.error("Runner output path is missing; pass --output-dir or set ARCBENCH_OUTPUT_DIR")
    return run_operation(args)


if __name__ == "__main__":
    sys.exit(main())
