"""Standalone ARC-Bench SDK command for any Python Agent package."""

import argparse
from contextlib import contextmanager
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


VERSION = "arcbench-agent-runtime 0.1.0 (official starter 2026-09-25)"
GUIDE = """ARC-Bench traceability reporting

Put this file in the Agent ZIP and give its absolute path to the Agent through
your Harness's normal instructions or tool mechanism. Resolve it relative to
the Agent entry file, because local wrappers may use a different working dir.
Python >=3.10 is required.
Use Runner-provided ARCBENCH_* paths; outside a Runner pass --output-dir.
All agents writing the same run should call this file, which serializes SDK
operations against that run's traceability store.

Examples (JSON is the official SDK method's keyword arguments):
  printf '%s' '{"interface_id":"api.users","req_ids":["REQ-1"],"type":"api","content":"GET /users","file_path":"backend/users.py"}' | python3 /absolute/path/arc-runtime.pyz traceability upsert_interface --json-file -
  printf '%s' '{"node_id":"REQ-1"}' | python3 /absolute/path/arc-runtime.pyz events mark_implementation_done --json-file -
  python3 /absolute/path/arc-runtime.pyz methods
  python3 /absolute/path/arc-runtime.pyz publish-history --source-repo /path/to/repo --ref refs/heads/delivery

Only report relationships and test outcomes supported by work that happened.
The official evaluation score is separate from these Agent declarations.
"""

TRACEABILITY_METHODS = {
    name for name, method in inspect.getmembers(TraceabilityStore, inspect.isfunction)
    if not name.startswith("_") and name not in {"table_path", "init_db", "init_store"}
}
EVENT_METHODS = {
    name for name, method in inspect.getmembers(EventClient, inspect.isfunction)
    if name.startswith("mark_") or name == "notify_traceability_changed"
}


@contextmanager
def locked_store(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".arc-runtime.lock").open("a") as stream:
        # ponytail: advisory store lock covers users of this command, not direct SDK writers.
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def check_tables(directory):
    # Upstream read_json treats a corrupt table as empty; never overwrite it.
    for name in TABLE_NAMES:
        path = directory / (name + ".json")
        if path.exists():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ValueError(f"{path}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}: official table must be a JSON object")


def report(runtime, scope, method, status, error=None):
    path = runtime.paths.project_dir / ".arc/runtime-reporting/operations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": time.time(), "sdk": VERSION, "scope": scope, "method": method,
              "status": status, "traceability_dir": str(runtime.paths.traceability_dir),
              "runner_events_path": str(runtime.paths.runner_events_path)}
    if error:
        record["error"] = error
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")


def publish_history(runtime, source_repo, ref, *, preview=False):
    """Expose a selected commit's real ancestry without changing application files."""
    source = source_repo.resolve(strict=True)
    project = runtime.paths.project_dir
    if source == project:
        raise ValueError("source repository and Runner project directory must differ")
    def git(directory, *arguments):
        result = subprocess.run(["git", "-C", str(directory), *arguments],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or
                               f"git {arguments[0]} failed ({result.returncode})")
        return result.stdout.strip()

    oid = git(source, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
    git_dir = project / ".git"
    if not git_dir.exists():
        git(project, "init", "-q", "-b", "arc-delivery")
        git(project, "config", "arcbench.history-publisher", "1")
    else:
        marker = subprocess.run(["git", "-C", str(project), "config", "--get",
                                 "arcbench.history-publisher"], capture_output=True, text=True)
        if marker.returncode or marker.stdout.strip() != "1":
            raise ValueError(f"Runner project already has an unmanaged Git repository: {project}")
    current = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "HEAD"],
                             capture_output=True, text=True)
    if current.returncode == 0 and current.stdout.strip() == oid:
        if preview:
            git(project, "read-tree", oid)
            runtime.events.notify_commit_history_changed("delivery_application_published", preview=True)
        return {"status": "unchanged", "commit": oid}
    git(project, "fetch", "--no-tags", "--quiet", str(source), oid)
    git(project, "update-ref", "refs/heads/arc-delivery", oid)
    git(project, "symbolic-ref", "HEAD", "refs/heads/arc-delivery")
    if preview:
        git(project, "read-tree", oid)
    runtime.events.notify_commit_history_changed("delivery_history_published", preview=preview)
    return {"status": "published", "commit": oid}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("guide", help="show how to add this tool to a Harness")
    commands.add_parser("version", help="show the bundled official SDK version")
    commands.add_parser("methods", help="list available official SDK methods and signatures")
    history = commands.add_parser("publish-history", help="publish real Git ancestry to Runner project")
    history.add_argument("--source-repo", type=Path, required=True)
    history.add_argument("--ref", required=True)
    history.add_argument("--preview", action="store_true", help="also refresh the delivered application preview")
    history.add_argument("--output-dir", type=Path, help="explicit Runner output root outside ARC-Bench")
    for scope in ("traceability", "events"):
        command = commands.add_parser(scope, help=f"call an official {scope} method")
        command.add_argument("method")
        command.add_argument("--json-file", type=str, help="JSON object of SDK keyword arguments; - reads stdin")
        command.add_argument("--output-dir", type=Path, help="explicit Runner output root outside ARC-Bench")
    args = parser.parse_args(argv)
    if args.command == "guide":
        print(GUIDE)
        return 0
    if args.command == "version":
        print(VERSION)
        return 0
    if args.command == "methods":
        for scope, cls, names in (("traceability", TraceabilityStore, TRACEABILITY_METHODS),
                                  ("events", EventClient, EVENT_METHODS)):
            for name in sorted(names):
                signature = inspect.signature(getattr(cls, name))
                signature = signature.replace(parameters=list(signature.parameters.values())[1:])
                print(f"{scope} {name}{signature}")
        return 0

    if args.command == "publish-history":
        if not args.output_dir and not any(os.environ.get(name, "").strip() for name in
                                           ("ARCBENCH_OUTPUT_DIR", "ARCBENCH_PROJECT_DIR", "ARCBENCH_TEMPLATE_DIR")):
            parser.error("Runner output path is missing; pass --output-dir or set ARCBENCH_OUTPUT_DIR")
        try:
            runtime = AgentRuntime.from_env(project_dir=str(args.output_dir) if args.output_dir else None)
            with locked_store(runtime.paths.project_dir / ".arc/runtime-reporting"):
                result = publish_history(runtime, args.source_repo, args.ref, preview=args.preview)
                if result["status"] == "published" or args.preview:
                    try:
                        report(runtime, "git", "publish_history", result["status"])
                    except OSError as logging_error:
                        print(f"ARC diagnostic write failed after Git publication: {logging_error}", file=sys.stderr)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"ARC Git history publication: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    allowed = TRACEABILITY_METHODS if args.command == "traceability" else EVENT_METHODS
    if args.method not in allowed:
        parser.error(f"unsupported official {args.command} method: {args.method}; use methods to list choices")
    if not args.output_dir and not any(os.environ.get(name, "").strip() for name in
                                       ("ARCBENCH_OUTPUT_DIR", "ARCBENCH_PROJECT_DIR", "ARCBENCH_TEMPLATE_DIR")):
        parser.error("Runner output path is missing; pass --output-dir or set ARCBENCH_OUTPUT_DIR")
    try:
        content = (sys.stdin.read() if args.json_file == "-" else Path(args.json_file).read_text()
                   if args.json_file else "{}")
        kwargs = json.loads(content)
        if not isinstance(kwargs, dict):
            raise ValueError("--json-file must contain a JSON object of SDK keyword arguments")
        runtime = AgentRuntime.from_env(project_dir=str(args.output_dir) if args.output_dir else None)
        with locked_store(runtime.paths.traceability_dir):
            try:
                check_tables(runtime.paths.traceability_dir)
                result = getattr(getattr(runtime, args.command), args.method)(**kwargs)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                try:
                    report(runtime, args.command, args.method, "failed", error)
                except OSError as logging_error:
                    print(f"ARC diagnostic write failed: {logging_error}", file=sys.stderr)
                raise
            try:
                report(runtime, args.command, args.method, "completed")
            except OSError as logging_error:
                print(f"ARC diagnostic write failed after SDK success: {logging_error}", file=sys.stderr)
        print(json.dumps({"status": "completed", "result": result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"ARC SDK {args.command}.{args.method}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
