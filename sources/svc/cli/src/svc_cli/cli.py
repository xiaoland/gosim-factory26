"""Console interface for the packaged SVC corpus and project integration runtime."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Any, Literal, Never, Sequence, TextIO, cast

from ._execution import ExecutionStore
from .analysis.cli import register as register_analysis
from .analysis.cli import run as run_analysis
from .analysis.protocol import AnalysisProtocolError
from .cli_output.lookup import project_lookup
from .cli_output.double import (
    DoubleDiagnosticOutput,
    DoubleEmitRuntimeUnavailableOutput,
    DoubleEmitOutput,
    DoubleJournalEntryOutput,
    DoubleJournalFactsOutput,
    DoubleJournalOutput,
    DoubleObserveRuntimeUnavailableOutput,
    DoubleObserveOutput,
    DoubleReplayOutput,
    DoubleRunObservationOutput,
    DoubleRuntimeUnavailableOutput,
    DoubleSnapshotOutput,
    DoubleStartRuntimeUnavailableOutput,
    DoubleStartOutput,
    DoubleStopRuntimeUnavailableOutput,
    DoubleStopOutput,
    DoubleTargetOutput,
    DoubleValidateRuntimeUnavailableOutput,
    DoubleValidateOutput,
)
from .cli_output.dev import (
    project_dev_ensure,
    project_dev_identity,
    project_dev_status,
    project_dev_stop,
)
from .cli_output.project import (
    project_init_apply,
    project_init_plan,
    project_status,
)
from .cli_output.run import project_run_receipt, run_exit_code
from .cli_output.upgrade import project_upgrade_apply, project_upgrade_plan
from .cli_delivery import deliver_error, deliver_result
from .errors import SvcError
from .dev.runtime import (
    DevEnsureResult,
    DevIdentityResult,
    DevStatusResult,
    DevStopResult,
    DevTargetFailure,
    DevTargetObservation,
    ensure_target,
    inspect_dev_identity,
    inspect_dev_status,
    stop_target,
)
from .dev.readiness import ProbeObservation
from .lookup import (
    LOOKUP_DISCOVERY_HINT,
    CorpusLookup,
    LookupQuery,
    LookupResponse,
)
from .cli_output.model import (
    CliUsageOutput,
    dump_machine_output,
    unscoped_machine_object,
)
from .output_schema import RegisteredMachineOutput, read_output_schema
from .project import (
    ConfigurationUnavailableStatus,
    InitApplyResult,
    InitPlan,
    ProjectInvalidStatus,
    ProjectStatusInspection,
    apply_init,
    inspect_status,
    plan_init,
)
from .run.runtime import (
    execute_entry,
    follow_run,
    inspect_run,
)
from .release import catalog, runtime_version
from .upgrade import (
    UpgradeApplyResult,
    UpgradePlan,
    apply_upgrade,
    plan_upgrade,
)
from .telemetry.cli import register as register_telemetry
from .telemetry.cli import run as run_telemetry


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONFLICT = 3
EXIT_FAILURE = 4


class CliUsageError(ValueError):
    """Argument grammar error raised without argparse writing side effects."""


class OutputSchemaRequested(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


class OutputSchemaAction(argparse.Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        *,
        schema_key: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(option_strings, dest, nargs=0, **kwargs)
        self.schema_key = schema_key

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> Never:
        raise OutputSchemaRequested(self.schema_key)


class SvcArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise CliUsageError(message)


def _add_output_schema(parser: argparse.ArgumentParser, key: str) -> None:
    parser.add_argument(
        "--json-schema",
        action=OutputSchemaAction,
        schema_key=key,
        help="Emit the packaged JSON Schema for this command's machine output",
    )


def _add_machine_output(
    parser: argparse.ArgumentParser,
    key: str,
    json_help: str,
    *,
    schema_first: bool = False,
) -> None:
    def add_json() -> None:
        parser.add_argument(
            "--json",
            action="store_true",
            dest="json_output",
            help=json_help,
        )

    if schema_first:
        _add_output_schema(parser, key)
        add_json()
    else:
        add_json()
        _add_output_schema(parser, key)


def _uint64_argument(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "must be an unsigned 64-bit integer"
        ) from error
    if not 0 <= parsed <= 18_446_744_073_709_551_615:
        raise argparse.ArgumentTypeError("must be an unsigned 64-bit integer")
    return parsed


_DOUBLE_HELP_FORMATTER = argparse.RawDescriptionHelpFormatter
_DOUBLE_TRUST_NOTICE = """Trust boundary:
  The Consumer test remains the product oracle. A double proves only the
  declared boundary behavior; it does not prove provider behavior or
  currentness. An external materializer is unsandboxed Consumer-owned code;
  its egress, state, determinism, and provider fidelity are not claimed.

Agent rule:
  Do not use double merely to make a test pass. If an invented fixture or
  event, a permissive matcher, materializer state or nondeterminism, or missing
  independent provider evidence could reduce test credibility or validity,
  report the concern and obtain user confirmation before proceeding.

Result protocol:
  Exit 0 means the command objective was met, 2 is command misuse, 3 is a
  resolved boundary non-success, and 4 is an infrastructure/internal failure.
  Use --json for the compact machine result and --json-schema for its schema.

Optional runtime:
  pip install 'sustainable-vibe-coding[double]'"""


def _double_help_epilog(command_help: str) -> str:
    return f"{command_help}\n\n{_DOUBLE_TRUST_NOTICE}"


def _parser() -> argparse.ArgumentParser:
    parser = SvcArgumentParser(
        prog="svc",
        description="Local Sustainable Vibe Coding corpus and project integration CLI.",
        epilog=f"For local SVC guidance: {LOOKUP_DISCOVERY_HINT}",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {runtime_version()}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup = subparsers.add_parser(
        "lookup",
        help="Browse, search, or read the packaged SVC Corpus",
        description=(
            "Browse, search, or read packaged SVC Corpus guidance. Lookup does not "
            "document SVC CLI usage; use svc <command> --help for command contracts."
        ),
        epilog=(
            "--list browses one logical directory level. --keyword ranks concept "
            "candidates; --regex returns exact path/content matches. --path prints one "
            "exact document or a concept directory's index as raw Markdown. Search can "
            "validly return no matches. "
            "Default text is for Agent/Human reading; --json is compact scripts/CI output."
        ),
    )
    lookup_group = lookup.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument(
        "--list",
        nargs="?",
        const="",
        dest="list_prefix",
        metavar="PREFIX",
        help="List immediate children of one logical Corpus directory",
    )
    lookup_group.add_argument(
        "--path",
        help=(
            "Read one canonical Markdown path or concept directory "
            "(a/b or a/b/ resolves to a/b/index.md)"
        ),
    )
    lookup_group.add_argument(
        "--keyword",
        help="Rank bounded lexical candidates in the selected scope",
    )
    lookup_group.add_argument(
        "--regex",
        help="Return bounded exact regular-expression matches",
    )
    lookup.add_argument("--scope", choices=("path", "both"))
    lookup.add_argument(
        "--limit", type=_lookup_limit, help="Maximum keyword results (1-50)"
    )
    _add_machine_output(
        lookup,
        "lookup",
        "Emit compact mode-specific JSON for scripts and CI",
        schema_first=True,
    )

    init = subparsers.add_parser(
        "init",
        help="Establish or repair bounded project integration (plan-first)",
        description=(
            "Plan first-time establishment or repair of bounded SVC project integration. "
            "Without --apply, inspect a non-mutating plan. With --apply, SVC recomputes "
            "the plan and applies it only when PLAN_DIGEST still selects the exact state."
        ),
        epilog=(
            "Owned effects: create a missing minimal svc.json; maintain SVC-marked blocks "
            "in .gitignore, AGENTS.md, and docs/index.md; retire a clean legacy SVC CLI "
            "Skill. Existing configuration, Corpus baseline, svc.local.json, and unmarked "
            "Consumer content are not rewritten. Use svc upgrade for Corpus adoption."
        ),
    )
    init.add_argument("repo", nargs="?", default=".", help="Project directory")
    init.add_argument("--apply", metavar="PLAN_DIGEST")
    _add_machine_output(init, "init", "Emit compact scripts/CI JSON")

    status = subparsers.add_parser(
        "status",
        help="Inspect CLI, config, Corpus baseline, and managed integration state",
        description=(
            "Inspect project SVC state without probing dev targets or changing files. "
            "Non-healthy results include one primary continuation and exit 3; --json "
            "emits the complete compact scripts/CI projection."
        ),
    )
    status.add_argument("repo", nargs="?", default=".", help="Project directory")
    _add_machine_output(
        status, "status", "Emit the complete compact scripts/CI projection"
    )

    upgrade = subparsers.add_parser(
        "upgrade",
        help="Plan or apply Corpus-baseline adoption",
        description=(
            "Plan or apply project adoption of the installed Corpus baseline."
        ),
        epilog=(
            "Plans reference guidance for Agent/Human document work; apply "
            "records only the reviewed baseline. This command does not update the CLI."
        ),
    )
    upgrade.add_argument("repo", nargs="?", default=".", help="Project directory")
    upgrade.add_argument("--apply", metavar="PLAN_DIGEST")
    _add_machine_output(upgrade, "upgrade", "Emit compact scripts/CI JSON")

    dev = subparsers.add_parser(
        "dev", help="Observe, ensure, or stop declared consumer dev capabilities"
    )
    dev_commands = dev.add_subparsers(dest="dev_command", required=True)
    dev_status = dev_commands.add_parser(
        "status",
        help="Observe one or all declared dev targets without starting them",
        description=(
            "Execute the selected target readiness probes and report qualified runtime "
            "state. Consumer-owned exec probes may run code, but status never invokes a "
            "provisioner, stop action, or process takeover. Omit TARGET to inspect all."
        ),
        epilog=(
            "Resolved snapshots use stdout: exit 0 only when every selected target is "
            "ready, otherwise 3. Invalid requests and infrastructure errors use stderr. "
            "Default text is Agent/Human-oriented; --json is the compact scripts/CI projection."
        ),
    )
    dev_status.add_argument("target", nargs="?")
    dev_status.add_argument("--repo", default=".")
    _add_machine_output(
        dev_status,
        "dev-status",
        "Emit the complete compact scripts/CI projection",
    )
    dev_identity = dev_commands.add_parser(
        "identity",
        help="Show the resolved workspace identity used for dev coordination",
    )
    dev_identity.add_argument(
        "--repo", default=".", help="Workspace directory (default: current directory)"
    )
    _add_machine_output(
        dev_identity,
        "dev-identity",
        "Emit compact exact identity JSON for scripts and CI",
        schema_first=True,
    )
    dev_ensure = dev_commands.add_parser(
        "ensure",
        help="Reuse, join, or start exactly one declared dev target",
        description=(
            "Make one declared target ready. Ensure may execute its Consumer-owned "
            "provisioner, waits for declared readiness, refuses an unhealthy responder, "
            "and leaves a ready long-running capability running after this CLI exits."
        ),
        epilog=(
            "Live start/join facts use stderr and the terminal capability result uses "
            "stdout. Exit 0 means ready, 3 means a resolved non-ready boundary, 4 means "
            "execution infrastructure failure, and caller Ctrl+C returns 130."
        ),
    )
    dev_ensure.add_argument("target")
    dev_ensure.add_argument(
        "--repo", default=".", help="Workspace directory (default: current directory)"
    )
    _add_machine_output(
        dev_ensure,
        "dev-ensure",
        "Emit one compact terminal scripts/CI result and suppress live progress",
        schema_first=True,
    )
    dev_stop = dev_commands.add_parser(
        "stop",
        help="Run the declared bounded stop action for exactly one dev target",
        description=(
            "Stop exactly one declared dev target through its target-local stop action. "
            "SVC never infers cleanup from a recorded PID. The final readiness probe "
            "qualifies the result; native action output remains in the reported log."
        ),
        epilog=(
            "Live owner/join facts use stderr and the terminal stop result uses stdout. "
            "Exit 0 means the action succeeded and readiness is false; expected manual, "
            "failed, still-ready, or unverified results exit 3; infrastructure failure "
            "is 4; caller Ctrl+C is 130."
        ),
    )
    dev_stop.add_argument("target")
    dev_stop.add_argument(
        "--repo", default=".", help="Workspace directory (default: current directory)"
    )
    _add_machine_output(
        dev_stop,
        "dev-stop",
        "Emit one compact terminal scripts/CI result and suppress live progress",
        schema_first=True,
    )
    run = subparsers.add_parser(
        "run",
        help="Execute, follow, or inspect one declared bounded run",
        description=(
            "Execute one named bounded project command, replay and wait for one exact "
            "execution with --follow, or observe it without replay/wait using --inspect. "
            "Same active entry intent converges; a later explicit entry invocation reruns."
        ),
        epilog=(
            "Default execute/follow preserves native stdout/stderr and writes SVC lifecycle "
            "text to stderr. Inspect text uses stdout. --json suppresses native/live output "
            "and emits one compact receipt. Execution IDs and logs are workspace-local. "
            "Owner Ctrl+C interrupts its run; follower Ctrl+C only detaches that caller. "
            "Child exits pass through, while successful inspect exits 0."
        ),
    )
    run.add_argument("entry", nargs="?")
    run_selection = run.add_mutually_exclusive_group()
    run_selection.add_argument(
        "--follow", metavar="EXECUTION_ID", help="Replay native output and wait"
    )
    run_selection.add_argument(
        "--inspect", metavar="EXECUTION_ID", help="Observe facts without replay or wait"
    )
    run.add_argument(
        "--repo", default=".", help="Workspace directory (default: current directory)"
    )
    _add_machine_output(
        run,
        "run",
        "Emit one compact receipt and suppress native/live display",
        schema_first=True,
    )

    double = subparsers.add_parser(
        "double",
        help="Experiment with one strict external HTTP boundary scenario",
        description="""EXPERIMENTAL: validate or run one claim-scoped external-system
boundary from a strict *.double.yaml BSL module. SVC serves only declared
responses and emits a named inbound event only when explicitly requested.""",
        epilog=_double_help_epilog(
            """Typical lifecycle:
  svc double validate checkout.double.yaml
  svc double start checkout.double.yaml --target app=http://127.0.0.1:9010
  svc double emit RUN_ID payment.succeeded
  svc double observe RUN_ID
  svc double stop RUN_ID

Start reports the responder endpoint and RUN_ID. Point the real Consumer at
that endpoint; the Consumer test drives the product and owns its assertions.
Event target names and event names must already be declared by the module."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_commands = double.add_subparsers(dest="double_command", required=True)
    double_validate = double_commands.add_parser(
        "validate",
        help="Compile one BSL module without starting a process or materializer",
        description="""EXPERIMENTAL: strictly compile one *.double.yaml BSL module and
report its scenario digest, fidelity boundary, non-claims, and any diagnostic.
This starts no responder and does not execute an external materializer.
Validation proves declaration mechanics, not provider behavior or currentness.""",
        epilog=_double_help_epilog(
            """Example:
  svc double validate checkout.double.yaml

MODULE is the exact local boundary-scenario file to compile. Referenced
contracts and assets must be local and remain inside its workspace."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_validate.add_argument(
        "module", type=Path, metavar="MODULE", help="Exact *.double.yaml BSL module"
    )
    _add_machine_output(
        double_validate,
        "double-validate",
        "Emit the compact validation result",
        schema_first=True,
    )
    double_start = double_commands.add_parser(
        "start",
        help="Start one fresh detached loopback boundary run",
        description="""EXPERIMENTAL: strictly compile MODULE and start one fresh detached
boundary run. Start reports a loopback responder endpoint and a canonical UUIDv4
RUN_ID; point the real Consumer at that endpoint. Runs are never reused.""",
        epilog=_double_help_epilog(
            """Example:
  svc double start checkout.double.yaml --seed 42 \\
    --clock 2026-08-11T10:00:00Z \\
    --target app=http://127.0.0.1:9010

Every event target declared by MODULE must have one exact NAME=ORIGIN binding.
By default, origins must be numeric loopback. A remote origin also requires
module policy and the matching --allow-remote-target NAME; delivery never
redirects or retries."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_start.add_argument(
        "module", type=Path, metavar="MODULE", help="Exact *.double.yaml BSL module"
    )
    double_start.add_argument(
        "--seed",
        type=_uint64_argument,
        help="Unsigned 64-bit replay seed (default: generate and report one)",
    )
    double_start.add_argument(
        "--clock",
        help="Fixed RFC3339 UTC replay clock ending in Z (default: now and report it)",
    )
    double_start.add_argument(
        "--target",
        action="append",
        default=[],
        metavar="NAME=ORIGIN",
        help="Bind one declared event target name to its delivery origin",
    )
    double_start.add_argument(
        "--allow-remote-target",
        action="append",
        default=[],
        metavar="NAME",
        help="Explicitly consent to one remotely bound declared target",
    )
    _add_machine_output(
        double_start,
        "double-start",
        "Emit the compact start receipt",
        schema_first=True,
    )
    double_emit = double_commands.add_parser(
        "emit",
        help="Explicitly deliver one named event through its active carrier",
        description="""EXPERIMENTAL: ask the active carrier for RUN_ID to materialize and
deliver one EVENT already declared by the started module. Emit cannot invent a
payload or select a new target, and it never runs automatically after a response.""",
        epilog=_double_help_epilog(
            """Example:
  svc double emit RUN_ID payment.succeeded

RUN_ID is the canonical UUIDv4 returned by start. EVENT is one exact declared
event name. Its target was bound by start; delivery makes one attempt with no
redirect or retry. The Consumer still owns acknowledgement and product
assertions."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_emit.add_argument(
        "run_id", metavar="RUN_ID", help="Canonical UUIDv4 returned by start"
    )
    double_emit.add_argument(
        "event", metavar="EVENT", help="Exact event name declared by the started module"
    )
    _add_machine_output(
        double_emit,
        "double-emit",
        "Emit the compact event delivery result",
        schema_first=True,
    )
    double_observe = double_commands.add_parser(
        "observe",
        help="Read bounded active or sealed boundary evidence",
        description="""EXPERIMENTAL: read bounded responder, binding, event-delivery, and
journal facts for one active or gracefully sealed RUN_ID. Observation is boundary
evidence, never a Consumer test verdict or proof of provider fidelity.""",
        epilog=_double_help_epilog(
            """Example:
  svc double observe RUN_ID

RUN_ID is the canonical UUIDv4 returned by start. The active carrier is authority
while reachable; after graceful stop, its sealed snapshot is authority. An
unavailable carrier returns the last explicitly unsealed projection, not a guess."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_observe.add_argument(
        "run_id", metavar="RUN_ID", help="Canonical UUIDv4 returned by start"
    )
    _add_machine_output(
        double_observe,
        "double-observe",
        "Emit the compact observation result",
        schema_first=True,
    )
    double_stop = double_commands.add_parser(
        "stop",
        help="Gracefully seal one run through its private control capability",
        description="""EXPERIMENTAL: ask the active carrier for RUN_ID to close its
responder, settle owned work, and seal the final bounded observation. Repeating
stop reads the sealed result; SVC never treats a recorded PID as authority.""",
        epilog=_double_help_epilog(
            """Example:
  svc double stop RUN_ID

RUN_ID is the canonical UUIDv4 returned by start. A successful stop makes the
sealed snapshot authoritative. If authenticated control is unavailable, SVC
reports the last unsealed projection and does not invent terminal state."""
        ),
        formatter_class=_DOUBLE_HELP_FORMATTER,
    )
    double_stop.add_argument(
        "run_id", metavar="RUN_ID", help="Canonical UUIDv4 returned by start"
    )
    _add_machine_output(
        double_stop,
        "double-stop",
        "Emit the compact stop result",
        schema_first=True,
    )

    register_telemetry(subparsers)
    register_analysis(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    try:
        args = parser.parse_args(raw_argv)
        if args.command == "run":
            selected = sum(
                value is not None for value in (args.entry, args.follow, args.inspect)
            )
            if selected != 1:
                raise CliUsageError(
                    "svc run requires exactly one entry, --follow ID, or --inspect ID"
                )
    except OutputSchemaRequested as request:
        _emit_unscoped_json(read_output_schema(request.key))
        return EXIT_OK
    except CliUsageError as error:
        if raw_argv[:1] == ["analysis"] or "--json" in raw_argv:
            _emit_json(CliUsageOutput(message=str(error)), stream=sys.stderr)
        else:
            print(f"svc: invalid-cli-usage: {error}", file=sys.stderr)
            if not raw_argv or raw_argv[:1] == ["lookup"]:
                print(f"Hint: {LOOKUP_DISCOVERY_HINT}", file=sys.stderr)
        return EXIT_USAGE
    json_output = bool(getattr(args, "json_output", False))
    try:
        if args.command == "lookup":
            if args.limit is not None and (
                args.list_prefix is not None or args.path is not None
            ):
                raise SvcError(
                    "invalid-lookup-options",
                    "--limit does not apply to --list or --path.",
                )
            if args.scope is not None and args.keyword is None and args.regex is None:
                raise SvcError(
                    "invalid-lookup-options",
                    "--scope applies only to --keyword or --regex.",
                )
            lookup_limit = args.limit if args.limit is not None else 10
            scope = cast(Literal["path", "both"], args.scope or "both")
            if args.list_prefix is not None:
                query = LookupQuery("list", args.list_prefix, limit=lookup_limit)
            elif args.path is not None:
                query = LookupQuery("path", args.path, limit=lookup_limit)
            elif args.keyword is not None:
                query = LookupQuery("keyword", args.keyword, scope, lookup_limit)
            else:
                query = LookupQuery("regex", args.regex, scope, lookup_limit)
            response = CorpusLookup(catalog()).lookup(query)
            return deliver_result(
                response,
                json_output=json_output,
                project=project_lookup,
                render=_render_lookup,
                exit_code=EXIT_OK,
            )

        if args.command == "status":
            status_payload = inspect_status(Path(args.repo))
            return deliver_result(
                status_payload,
                json_output=json_output,
                project=project_status,
                render=_render_status,
                exit_code=EXIT_OK if status_payload.healthy else EXIT_CONFLICT,
            )

        if args.command == "upgrade":
            upgrade_plan = plan_upgrade(Path(args.repo))
            if args.apply:
                upgrade_payload = apply_upgrade(upgrade_plan, args.apply)
                return deliver_result(
                    upgrade_payload,
                    json_output=json_output,
                    project=project_upgrade_apply,
                    render=_render_upgrade_apply,
                    exit_code=EXIT_OK,
                )
            return deliver_result(
                upgrade_plan,
                json_output=json_output,
                project=project_upgrade_plan,
                render=_render_upgrade_plan,
                exit_code=(
                    EXIT_CONFLICT
                    if upgrade_plan.status in {"migration-required", "blocked"}
                    else EXIT_OK
                ),
            )

        if args.command == "dev":
            if args.dev_command == "identity":
                identity_payload = inspect_dev_identity(Path(args.repo))
                return deliver_result(
                    identity_payload,
                    json_output=json_output,
                    project=project_dev_identity,
                    render=_render_dev_identity,
                    exit_code=EXIT_OK,
                )
            if args.dev_command == "status":
                dev_status_payload = inspect_dev_status(Path(args.repo), args.target)
                return deliver_result(
                    dev_status_payload,
                    json_output=json_output,
                    project=project_dev_status,
                    render=_render_dev_status,
                    exit_code=(
                        EXIT_OK if dev_status_payload.healthy else EXIT_CONFLICT
                    ),
                )
            if args.dev_command == "stop":
                stop_payload = stop_target(
                    Path(args.repo),
                    args.target,
                    on_selected=None if json_output else _emit_dev_stop_selected,
                )
                return deliver_result(
                    stop_payload,
                    json_output=json_output,
                    project=project_dev_stop,
                    render=_render_dev_stop,
                    exit_code=_dev_stop_exit_code(stop_payload),
                )
            ensure_payload = ensure_target(
                Path(args.repo),
                args.target,
                on_selected=None if json_output else _emit_dev_ensure_selected,
            )
            return deliver_result(
                ensure_payload,
                json_output=json_output,
                project=project_dev_ensure,
                render=_render_dev_ensure,
                exit_code=_dev_ensure_exit_code(ensure_payload),
            )

        if args.command == "double":
            return _run_double(args, json_output)

        if args.command == "run":
            return _run_declared(args, json_output)

        if args.command == "analysis":
            return run_analysis(args)

        if args.command == "telemetry":
            return run_telemetry(args, json_output)

        local_plan = plan_init(Path(args.repo))
        if args.apply:
            init_payload = apply_init(local_plan, args.apply)
            return deliver_result(
                init_payload,
                json_output=json_output,
                project=project_init_apply,
                render=_render_init_apply,
                exit_code=EXIT_OK,
            )
        return deliver_result(
            local_plan,
            json_output=json_output,
            project=project_init_plan,
            render=_render_init_plan,
            exit_code=EXIT_CONFLICT if local_plan.blockers else EXIT_OK,
        )
    except SvcError as error:
        return deliver_error(
            error,
            json_output=json_output,
            render=_render_error,
            exit_code=_exit_code(error),
        )
    except AnalysisProtocolError as error:
        _emit_unscoped_json(
            error.as_dict(version=3),
            stream=sys.stderr,
        )
        return _analysis_exit_code(error)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        failure = SvcError("invalid-release", str(error))
        return deliver_error(
            failure,
            json_output=json_output,
            render=_render_error,
            exit_code=EXIT_FAILURE,
        )


def _run_double(args: argparse.Namespace, json_output: bool) -> int:
    command = cast(
        Literal[
            "double validate",
            "double start",
            "double emit",
            "double observe",
            "double stop",
        ],
        f"double {args.double_command}",
    )
    try:
        from .double.service import (
            emit_event,
            observe_run,
            start_run,
            stop_run,
            validate_module,
        )
    except ModuleNotFoundError as error:
        optional_roots = {
            "attrs",
            "cel_expr_python",
            "jsonschema",
            "referencing",
            "rpds",
            "ruamel",
        }
        missing = (error.name or "").partition(".")[0]
        if missing not in optional_roots:
            raise SvcError(
                "double-runtime-import-failed",
                "The installed double runtime is incomplete.",
                {"missing_module": error.name or "unknown"},
            ) from error
        unavailable_types = {
            "double validate": DoubleValidateRuntimeUnavailableOutput,
            "double start": DoubleStartRuntimeUnavailableOutput,
            "double emit": DoubleEmitRuntimeUnavailableOutput,
            "double observe": DoubleObserveRuntimeUnavailableOutput,
            "double stop": DoubleStopRuntimeUnavailableOutput,
        }
        unavailable = unavailable_types[command]()
        return _deliver_double_output(
            unavailable,
            json_output=json_output,
            render=lambda stream: _render_double_unavailable(unavailable, stream),
            exit_code=EXIT_CONFLICT,
        )

    try:
        if args.double_command == "validate":
            validate_result = validate_module(args.module)
            validate_output = _project_double_validate(validate_result)
            return _deliver_double_output(
                validate_output,
                json_output=json_output,
                render=lambda stream: _render_double_validate(validate_output, stream),
                exit_code=EXIT_OK if validate_output.valid else EXIT_CONFLICT,
            )
        if args.double_command == "start":
            start_result = start_run(
                args.module,
                seed=args.seed,
                clock=args.clock,
                target_values=tuple(args.target),
                allow_remote_names=tuple(args.allow_remote_target),
            )
            start_output = _project_double_start(start_result)
            return _deliver_double_output(
                start_output,
                json_output=json_output,
                render=lambda stream: _render_double_start(start_output, stream),
                exit_code=EXIT_OK,
            )
        if args.double_command == "emit":
            emit_result = emit_event(args.run_id, args.event)
            emit_output = DoubleEmitOutput(
                run_id=emit_result.run_id,
                event=emit_result.event,
                status=emit_result.status,
                target=emit_result.target,
                http_status=emit_result.http_status,
                reason=emit_result.reason,
            )
            return _deliver_double_output(
                emit_output,
                json_output=json_output,
                render=lambda stream: _render_double_emit(emit_output, stream),
                exit_code=(
                    EXIT_OK if emit_output.status == "acknowledged" else EXIT_CONFLICT
                ),
            )
        if args.double_command == "observe":
            observe_result = observe_run(args.run_id)
            observe_output = DoubleObserveOutput(
                observation=_project_double_observation(observe_result.observation),
                authority=observe_result.authority,
                control_status=observe_result.control_status,
            )
            return _deliver_double_output(
                observe_output,
                json_output=json_output,
                render=lambda stream: _render_double_observe(observe_output, stream),
                exit_code=(
                    EXIT_CONFLICT
                    if observe_output.control_status == "control-unavailable"
                    else EXIT_OK
                ),
            )
        stop_result = stop_run(args.run_id)
        if stop_result.observation is None:
            raise SvcError(
                "double-control-protocol-invalid",
                "Double stop result has no observation authority.",
            )
        stop_output = DoubleStopOutput(
            run_id=stop_result.run_id,
            status=stop_result.status,
            sealed=stop_result.sealed,
            idempotent=stop_result.idempotent,
            observation=_project_double_observation(stop_result.observation),
        )
        return _deliver_double_output(
            stop_output,
            json_output=json_output,
            render=lambda stream: _render_double_stop(stop_output, stream),
            exit_code=(EXIT_OK if stop_output.status == "stopped" else EXIT_CONFLICT),
        )
    except SvcError:
        raise
    except Exception as error:
        raise SvcError(
            "double-internal-error",
            "The double operation failed inside its runtime boundary.",
            {"exception": type(error).__name__},
        ) from error


def _deliver_double_output(
    output: RegisteredMachineOutput,
    *,
    json_output: bool,
    render: Any,
    exit_code: int,
) -> int:
    if json_output:
        _emit_json(output)
    else:
        render(sys.stdout)
    return exit_code


def _project_double_validate(result: Any) -> DoubleValidateOutput:
    diagnostic = result.diagnostic
    return DoubleValidateOutput(
        module=result.module,
        scenario_name=result.scenario_name,
        claim=result.claim,
        valid=result.valid,
        scenario_digest=result.scenario_digest,
        fidelity=result.fidelity,
        nonclaims=result.nonclaims,
        snapshots=tuple(
            DoubleSnapshotOutput(
                logical_path=item.logical_path,
                sha256=item.sha256,
                bytes=item.bytes,
            )
            for item in result.snapshots
        ),
        diagnostic=(
            None
            if diagnostic is None
            else DoubleDiagnosticOutput(
                code=diagnostic.code,
                message=diagnostic.message,
                path=diagnostic.path,
                line=diagnostic.line,
                column=diagnostic.column,
            )
        ),
    )


def _project_double_start(result: Any) -> DoubleStartOutput:
    return DoubleStartOutput(
        run_id=result.run_id,
        module=result.module,
        scenario_name=result.scenario_name,
        responder_url=result.responder_url,
        scenario_digest=result.scenario_digest,
        run_context_digest=result.run_context_digest,
        replay=_project_double_replay(result.replay),
        targets=tuple(_project_double_target(item) for item in result.targets),
        nonclaims=result.nonclaims,
    )


def _project_double_observation(observation: Any) -> DoubleRunObservationOutput:
    entries: list[DoubleJournalEntryOutput] = []
    for item in observation.journal.entries:
        facts = item.facts
        diagnostics: list[str] = []
        reason = facts.get("reason")
        if isinstance(reason, str):
            diagnostics.append(reason)
        mismatch = facts.get("mismatch")
        if isinstance(mismatch, list):
            for candidate in mismatch[:8]:
                if not isinstance(candidate, dict):
                    continue
                interaction = candidate.get("interaction")
                reasons = candidate.get("reasons")
                if isinstance(interaction, str) and isinstance(reasons, list):
                    diagnostics.extend(
                        f"{interaction}: {value}"
                        for value in reasons[:8]
                        if isinstance(value, str)
                    )
        http_status = facts.get("http_status", facts.get("response_status"))
        body_hash = facts.get("body_sha256")
        entries.append(
            DoubleJournalEntryOutput(
                sequence=item.sequence,
                at=item.at,
                kind=item.kind,
                status=item.status,
                facts=DoubleJournalFactsOutput(
                    interaction=_string_fact(facts, "interaction"),
                    event=_string_fact(facts, "event"),
                    method=_string_fact(facts, "method"),
                    path=_string_fact(facts, "path"),
                    target=_string_fact(facts, "target"),
                    http_status=(http_status if type(http_status) is int else None),
                    request_sha256=(
                        body_hash
                        if item.kind == "request" and isinstance(body_hash, str)
                        else None
                    ),
                    response_sha256=_string_fact(facts, "response_sha256"),
                    diagnostics=tuple(diagnostics),
                ),
            )
        )
    return DoubleRunObservationOutput(
        run_id=observation.run_id,
        scenario_name=observation.scenario_name,
        status=observation.status,
        sealed=observation.sealed,
        responder_url=observation.responder_url,
        scenario_digest=observation.scenario_digest,
        run_context_digest=observation.run_context_digest,
        replay=_project_double_replay(observation.replay),
        targets=tuple(_project_double_target(item) for item in observation.targets),
        bindings=tuple(sorted(observation.bindings)),
        journal=DoubleJournalOutput(
            total=observation.journal.total,
            retained=observation.journal.retained,
            omitted=observation.journal.omitted,
            entries=tuple(entries),
        ),
        nonclaims=observation.nonclaims,
        failure=observation.failure,
    )


def _project_double_replay(replay: Any) -> DoubleReplayOutput:
    return DoubleReplayOutput(
        seed=replay.seed,
        clock=replay.clock,
        generators=replay.generators,
        validators=replay.validators,
        runtime=replay.runtime,
    )


def _project_double_target(target: Any) -> DoubleTargetOutput:
    return DoubleTargetOutput(
        name=target.name, origin=target.origin, remote=target.remote
    )


def _string_fact(facts: dict[str, Any], name: str) -> str | None:
    value = facts.get(name)
    return value if isinstance(value, str) else None


def _render_double_unavailable(
    output: DoubleRuntimeUnavailableOutput, stream: TextIO
) -> None:
    print("Double runtime is not installed.", file=stream)
    print(f"Continue: {output.continuation}", file=stream)


def _render_double_validate(output: DoubleValidateOutput, stream: TextIO) -> None:
    if not output.valid:
        assert output.diagnostic is not None
        print(f"Invalid double module: {output.module}", file=stream)
        print(f"{output.diagnostic.code}: {output.diagnostic.message}", file=stream)
        return
    print(f"Valid double scenario: {output.scenario_name}", file=stream)
    print(f"Claim: {output.claim}", file=stream)
    print(f"Scenario digest: {output.scenario_digest}", file=stream)
    print(f"Fidelity: {', '.join(output.fidelity) or 'none'}", file=stream)
    print(f"Non-claims: {', '.join(output.nonclaims) or 'none'}", file=stream)


def _render_double_start(output: DoubleStartOutput, stream: TextIO) -> None:
    print(f"Double run ready: {output.run_id}", file=stream)
    print(f"Responder: {output.responder_url}", file=stream)
    print(f"Scenario: {output.scenario_name} ({output.scenario_digest})", file=stream)
    print(f"Run context: {output.run_context_digest}", file=stream)
    print(
        f"Replay: --seed {output.replay.seed} --clock {output.replay.clock}",
        file=stream,
    )
    print(f"Non-claims: {', '.join(output.nonclaims)}", file=stream)


def _render_double_emit(output: DoubleEmitOutput, stream: TextIO) -> None:
    print(f"Event {output.event}: {output.status}", file=stream)
    if output.target is not None:
        print(f"Target: {output.target}", file=stream)
    if output.http_status is not None:
        print(f"Acknowledgement HTTP status: {output.http_status}", file=stream)
    if output.reason is not None:
        print(f"Reason: {output.reason}", file=stream)


def _render_double_observe(output: DoubleObserveOutput, stream: TextIO) -> None:
    observation = output.observation
    print(f"Double run {observation.run_id}: {observation.status}", file=stream)
    print(
        f"Authority: {output.authority}; sealed: {str(observation.sealed).lower()}",
        file=stream,
    )
    print(
        "Journal: "
        f"{observation.journal.retained} retained / "
        f"{observation.journal.total} total / "
        f"{observation.journal.omitted} omitted",
        file=stream,
    )
    print(f"Bindings: {', '.join(observation.bindings) or 'none'}", file=stream)


def _render_double_stop(output: DoubleStopOutput, stream: TextIO) -> None:
    print(f"Double run {output.run_id}: {output.status}", file=stream)
    print(f"Sealed: {str(output.sealed).lower()}", file=stream)
    print(f"Idempotent replay: {str(output.idempotent).lower()}", file=stream)


def _run_declared(args: argparse.Namespace, json_output: bool) -> int:
    callback = None if json_output else _emit_run_selected
    stdout_sink = None if json_output else _binary_output(sys.stdout)
    stderr_sink = None if json_output else _binary_output(sys.stderr)
    if args.follow is not None:
        command = "run follow"
        outcome = follow_run(
            Path(args.repo),
            args.follow,
            stdout_sink=stdout_sink,
            stderr_sink=stderr_sink,
            on_selected=callback,
        )
    elif args.inspect is not None:
        command = "run inspect"
        outcome = inspect_run(Path(args.repo), args.inspect)
    else:
        command = "run"
        outcome = execute_entry(
            Path(args.repo),
            args.entry,
            stdout_sink=stdout_sink,
            stderr_sink=stderr_sink,
            on_selected=callback,
        )
    payload = project_run_receipt(outcome, cast(Any, command))
    if json_output:
        _emit_json(payload)
    else:
        _emit_run_terminal(outcome, inspect=args.inspect is not None)
    return run_exit_code(outcome, inspect=args.inspect is not None)


def _emit_run_selected(record: Any, role: str) -> None:
    store = ExecutionStore()
    print(f"svc run {record.subject}: {role} {record.execution_id}", file=sys.stderr)
    print(f"cwd: {record.cwd}", file=sys.stderr)
    print(f"$ {_display_argv(record.argv)}", file=sys.stderr)
    print(
        "logs: "
        f"stdout {store.log_path(record, 'stdout')}; "
        f"stderr {store.log_path(record, 'stderr')}",
        file=sys.stderr,
    )


def _render_dev_stop(payload: DevStopResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    write(
        f"svc dev {payload.target}: {payload.status}; "
        f"instance {payload.workspace.instance}; scope {payload.capability.scope}"
    )
    attempt = payload.attempt
    if attempt is not None:
        write(f"$ {_display_argv(attempt.argv)}")
        role = attempt.caller_role
        state = attempt.state
        detail = f", exit {attempt.exit_code}" if attempt.exit_code is not None else ""
        write(f"Execution: {attempt.execution_id} ({role}), {state}{detail}")
        log = attempt.logs.merged
        write(f"Stop log: {log.path}")
        if payload.status == "stop-failed" and log.bytes:
            tail = _file_tail(Path(log.path))
            if tail:
                write("Stop output (tail):")
                for line in tail.splitlines():
                    write(f"  {line}")
    if payload.probe is not None:
        disposition = "ready" if payload.probe.healthy else "not ready"
        write(
            f"Final probe: {payload.probe.kind} {payload.probe.reason} — {disposition}"
        )
    elif payload.probe_error is not None:
        write(
            "Final probe: unverified — "
            f"{payload.probe_error.code}: {payload.probe_error.message}"
        )


def _render_dev_identity(payload: DevIdentityResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    workspace = payload.workspace
    write("svc dev identity")
    write(f"instance: {workspace.instance}")
    write(f"root: {workspace.root}")
    write(f"repository: {workspace.repository_kind} {workspace.repository_id}")
    write(f"worktree: {workspace.worktree_id}")
    write(f"namespace: {workspace.namespace_id}")


def _render_dev_ensure(payload: DevEnsureResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    if payload.caller_status == "detached":
        assert payload.attempt is not None
        write(
            f"svc dev {payload.target}: detached from start "
            f"{payload.attempt.execution_id}; scope {payload.capability.scope}"
        )
        write(f"Execution state: {payload.attempt.state}")
        write(f"Startup log: {payload.attempt.logs.merged.path}")
        return
    ready = payload.ready is True
    lead = "ready" if ready else payload.status
    outcome = f" ({payload.status})" if ready else ""
    write(
        f"svc dev {payload.target}: {lead}{outcome}; "
        f"instance {payload.workspace.instance}; scope {payload.capability.scope}"
    )
    if payload.probe is not None:
        write(f"Probe: {payload.probe.kind} {_probe_text_detail(payload.probe)}")
    if not ready and payload.probe_argv is not None:
        write(f"$ {_display_argv(payload.probe_argv)}")
    if payload.access:
        for value in payload.access:
            write(f"Access: {value}")
    elif payload.probe is not None:
        if payload.probe.output:
            output = payload.probe.output
            preview, omitted = _text_preview(output)
            write("Probe output:")
            for line in preview.splitlines() or [preview]:
                write(f"  {line}")
            if omitted or payload.probe.output_truncated:
                write("  … output truncated; use --json for the bounded capture")
        elif not ready and payload.probe.kind == "exec":
            write("Probe output: empty")
    if payload.attempt is not None:
        write(
            f"Execution: {payload.attempt.execution_id} "
            f"({payload.attempt.caller_role}), {payload.attempt.state}"
        )
        write(f"Startup log: {payload.attempt.logs.merged.path}")
    if payload.status == "manual-action-required":
        write(
            "No SVC command can provision this target; follow the Consumer "
            "project's guidance."
        )


def _emit_dev_ensure_selected(record: Any, caller_role: str, log_path: str) -> None:
    if caller_role == "owner":
        print(
            f"svc dev {record.subject}: starting `{_display_argv(record.argv)}`",
            file=sys.stderr,
        )
    else:
        print(
            f"svc dev {record.subject}: joining existing start {record.execution_id}",
            file=sys.stderr,
        )
    print(f"Waiting for readiness; startup log: {log_path}", file=sys.stderr)


def _emit_dev_stop_selected(record: Any, caller_role: str, log_path: str) -> None:
    if caller_role == "owner":
        print(
            f"svc dev {record.subject}: stopping `{_display_argv(record.argv)}`",
            file=sys.stderr,
        )
    else:
        print(
            f"svc dev {record.subject}: joining stop {record.execution_id}",
            file=sys.stderr,
        )
    print(f"Waiting for stop; log: {log_path}", file=sys.stderr)


def _dev_ensure_exit_code(payload: DevEnsureResult) -> int:
    if payload.status == "interrupted" or payload.caller_status == "detached":
        return 130
    return EXIT_OK if payload.ready is True else EXIT_CONFLICT


def _render_dev_status(payload: DevStatusResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    status = payload.status
    if status in {"invalid-configuration", "not-configured"}:
        write(f"svc dev status: {status}; instance {payload.workspace.instance}")
        if payload.reason is not None:
            write(f"Reason: {payload.reason}")
        if status == "not-configured":
            write("No dev targets are declared in svc.json.")
        return
    targets = payload.targets or ()
    ready_count = sum(
        1
        for entry in targets
        if isinstance(entry, DevTargetObservation) and entry.probe.healthy
    )
    write(
        f"svc dev status: {status} — {ready_count}/{len(targets)} ready; "
        f"instance {payload.workspace.instance}"
    )
    ensure_targets: list[str] = []
    for entry in targets:
        if isinstance(entry, DevTargetFailure):
            write(
                f"error      {entry.target}  {entry.error.code}: {entry.error.message}"
            )
            continue
        disposition = "ready" if entry.probe.healthy else "not-ready"
        detail = _probe_text_detail(entry.probe)
        continuation = entry.continuation
        suffix = f"; {continuation}" if continuation is not None else ""
        write(
            f"{disposition:<10} {entry.target}  {entry.capability.scope}  "
            f"{entry.probe.kind} {detail}{suffix}"
        )
        if not entry.probe.healthy and entry.probe_argv is not None:
            write(f"  $ {_display_argv(entry.probe_argv)}")
        for value in entry.access:
            write(f"  Access: {value}")
        if entry.probe.output:
            preview, omitted = _text_preview(entry.probe.output)
            write("  Probe output:")
            for line in preview.splitlines() or [preview]:
                write(f"    {line}")
            if omitted or entry.probe.output_truncated:
                write("    … output truncated; use --json for the bounded capture")
        elif entry.probe.kind == "exec" and not entry.probe.healthy:
            write("  Probe output: empty")
        if continuation == "ensure":
            ensure_targets.append(entry.target)
    if ensure_targets:
        selected = ensure_targets[0] if len(ensure_targets) == 1 else "<target>"
        write(
            "Ensure one: "
            f"svc dev ensure {shlex.quote(selected)} --repo "
            f"{shlex.quote(str(payload.workspace.root))}"
        )


def _probe_text_detail(probe: ProbeObservation) -> str:
    if probe.kind == "exec" and probe.exit_code is not None:
        return f"exit {probe.exit_code}"
    if probe.kind == "http" and probe.status_code is not None:
        return f"status {probe.status_code}"
    return probe.reason


def _text_preview(value: str, limit: int = 1_200) -> tuple[str, bool]:
    if len(value) <= limit:
        return value.rstrip("\n"), False
    return value[:limit].rstrip("\n"), True


def _file_tail(path: Path, limit: int = 1_200) -> str | None:
    try:
        with path.open("rb") as stream:
            size = stream.seek(0, os.SEEK_END)
            stream.seek(max(0, size - limit))
            value = stream.read(limit)
    except OSError:
        return None
    return value.decode("utf-8", errors="replace").rstrip("\n") or None


def _dev_stop_exit_code(payload: DevStopResult) -> int:
    if payload.caller_status in {"interrupted", "detached"}:
        return 130
    return EXIT_OK if payload.status == "stopped" else EXIT_CONFLICT


def _emit_run_terminal(outcome: Any, *, inspect: bool) -> None:
    stream = sys.stdout if inspect else sys.stderr
    if outcome.detached:
        suffix = f" {outcome.record.execution_id}" if outcome.record is not None else ""
        print(f"svc run {outcome.entry}: detached{suffix}", file=stream)
        if outcome.record is not None and outcome.store is not None:
            _emit_run_logs(outcome.store, outcome.record, stream=stream)
        return
    record = outcome.record
    if record is None:
        return
    duration = (
        f" in {record.duration_ms / 1000:.1f}s"
        if record.duration_ms is not None
        else ""
    )
    prefix = (
        f"svc run inspect: {record.subject} —"
        if inspect
        else f"svc run {record.subject}:"
    )
    detail = f" {record.exit_code}" if record.state == "exited" else ""
    print(
        f"{prefix} {record.state}{detail}{duration} ({outcome.caller_role})",
        file=stream,
    )
    print(f"execution: {record.execution_id}", file=stream)
    if inspect:
        print(f"$ {_display_argv(record.argv)}", file=stream)
        print(f"cwd: {record.cwd}", file=stream)
    if outcome.store is not None:
        _emit_run_logs(outcome.store, record, stream=stream)
    if record.failure_reason:
        print(f"reason: {record.failure_reason}", file=stream)


def _emit_run_logs(store: Any, record: Any, *, stream: Any) -> None:
    stdout = store.log_reference(record, "stdout")
    stderr = store.log_reference(record, "stderr")
    print(
        "logs: "
        f"stdout {stdout.path} ({stdout.bytes:,} bytes); "
        f"stderr {stderr.path} ({stderr.bytes:,} bytes)",
        file=stream,
    )


def _display_argv(argv: Sequence[str]) -> str:
    return (
        subprocess.list2cmdline(list(argv))
        if os.name == "nt"
        else shlex.join(list(argv))
    )


class _TextBinaryAdapter:
    def __init__(self, stream: Any) -> None:
        self.stream = stream

    def write(self, data: bytes) -> int:
        text = data.decode("utf-8", errors="replace")
        self.stream.write(text)
        return len(data)

    def flush(self) -> None:
        self.stream.flush()


def _binary_output(stream: Any) -> Any:
    return getattr(stream, "buffer", None) or _TextBinaryAdapter(stream)


def _lookup_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("--limit must be an integer") from error
    if not 1 <= limit <= 50:
        raise argparse.ArgumentTypeError("--limit must be between 1 and 50")
    return limit


def _render_upgrade_plan(plan: UpgradePlan, stream: TextIO) -> None:
    write = partial(print, file=stream)
    write(f"svc upgrade: {plan.status}")
    write(f"Repository: {plan.repo}")
    if plan.status == "noop":
        write(f"Corpus: baseline {plan.corpus.project_version} (current)")
        return
    if plan.status == "blocked":
        write("No changes can be applied.")
        _emit_blockers(plan.blockers, stream)
        write("Next: resolve the blocker, then recompute the plan:")
        write(f"  svc upgrade {shlex.quote(str(plan.repo))}")
        return

    assert plan.corpus.releases is not None
    write(f"Corpus: baseline {plan.corpus.from_version} -> {plan.corpus.to_version}")
    paths = [
        guide.path for release in plan.corpus.releases for guide in release.guides or ()
    ]
    if paths:
        write("\nRead required guidance:")
        for path in paths:
            write(f"  svc lookup --path {shlex.quote(path)}")

    write(f"\nWould change ({len(plan.mutations)}):")
    for operation in plan.mutations:
        write(f"  {operation.action} {operation.path} - {operation.reason}")
    assert plan.digest is not None
    if plan.status == "migration-required":
        write("\nAfter completing the migration guidance, apply this exact plan:")
    else:
        write("\nApply this exact plan:")
    write(f"  svc upgrade {shlex.quote(str(plan.repo))} --apply {plan.digest}")


def _render_upgrade_apply(payload: UpgradeApplyResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    write("svc upgrade: applied")
    write(f"Repository: {payload.repo}")
    write(
        f"Corpus: baseline {payload.corpus.from_version} -> {payload.corpus.to_version}"
    )
    write(f"Applied plan: {payload.plan_digest}")
    if payload.migration.disposition == "caller-asserted":
        write(
            "Migration guidance: asserted complete by caller; project-owned work not verified by SVC"
        )
    else:
        write("Migration guidance: not required")
    write(f"\nChanged ({len(payload.operations)}):")
    for operation in payload.operations:
        write(f"  {operation.action} {operation.path}")
    write(f"\nVerification: {payload.verification.scope} {payload.verification.status}")
    write("Next observation:")
    write(f"  svc status {shlex.quote(payload.repo)}")


def _render_init_plan(plan: InitPlan, stream: TextIO) -> None:
    write = partial(print, file=stream)
    suffix = "; no changes can be applied" if plan.status == "blocked" else ""
    write(f"svc init: {plan.status}{suffix}")
    write(f"Repository: {plan.repo}")
    write(
        "Intent: "
        + (
            "establish project integration"
            if plan.intent == "establish"
            else "repair managed integration"
        )
    )
    write(f"Corpus: {plan.corpus_version}")
    baseline = plan.corpus_baseline
    if baseline.disposition == "create":
        write(f"Corpus baseline: create {baseline.version}")
    else:
        write(f"Corpus baseline: {baseline.version or 'unavailable'} (unchanged)")
    if plan.status == "blocked":
        write()
        _emit_blockers(plan.blockers, stream)
        write("Next: resolve the blocker, then recompute the plan:")
        write(f"  svc init {shlex.quote(str(plan.repo))}")
        return
    if plan.status == "noop":
        write("Managed integration is current; no changes.")
        return
    write(f"\nWould change ({len(plan.mutations)}):")
    for mutation in plan.mutations:
        surface, extent, reason = _init_operation_text(mutation.path)
        write(f"  {mutation.action:7} {mutation.path} ({extent}) - {reason}")
    assert plan.digest is not None
    write("\nApply exact plan:")
    write(f"  svc init {shlex.quote(str(plan.repo))} --apply {plan.digest}")


def _render_init_apply(payload: InitApplyResult, stream: TextIO) -> None:
    write = partial(print, file=stream)
    write(f"svc init: {payload.status}")
    write(f"Repository: {payload.repo}")
    write(f"Corpus: {payload.corpus_version}")
    if payload.corpus_baseline.disposition == "create":
        write(f"Corpus baseline: created {payload.corpus_baseline.version}")
    else:
        write(
            "Corpus baseline: "
            f"{payload.corpus_baseline.version or 'unavailable'} (unchanged)"
        )
    write(f"Applied plan: {payload.plan_digest}")
    if payload.operations:
        write(f"\nChanged ({len(payload.operations)}):")
        past = {
            "create": "created",
            "append": "appended",
            "refresh": "refreshed",
            "delete": "deleted",
        }
        for operation in payload.operations:
            _, extent, _ = _init_operation_text(operation.path)
            write(f"  {past[operation.action]:9} {operation.path} ({extent})")
    else:
        write("Changed: none; no managed operation required a write")
    write("\nVerification: all planned path postconditions passed")
    write("Next observation:")
    write(f"  svc status {shlex.quote(str(payload.repo))}")


def _init_operation_text(path: str) -> tuple[str, str, str]:
    values = {
        "svc.json": ("project-state", "whole file", "establish minimal project state"),
        ".gitignore": (
            "local-config-ignore",
            "SVC local-config ignore block",
            "maintain local overlay privacy",
        ),
        "AGENTS.local.md": (
            "local-agent-instructions",
            "whole file",
            "create Consumer-owned local Agent guidance",
        ),
        "AGENTS.md": ("agent-router", "SVC navigation block", "update Agent router"),
        "docs/index.md": (
            "docs-navigation",
            "SVC navigation block",
            "update documentation navigation",
        ),
        ".agents/skills/svc/SKILL.md": (
            "legacy-cli-skill",
            "clean generated file",
            "retire CLI Skill",
        ),
    }
    return values[path]


def _render_status(payload: ProjectStatusInspection, stream: TextIO) -> None:
    write = partial(print, file=stream)
    installed = payload.installed_cli_version or "source-tree"
    project_version = payload.corpus.project_version or "absent"
    lead = "healthy" if payload.healthy else payload.status
    write(
        f"SVC {lead} — CLI {installed} ({payload.resource_mode}); "
        f"Corpus {payload.corpus.available_version}; project baseline {project_version} "
        f"({payload.corpus.status}); configuration {payload.configuration.status}"
    )
    if not payload.healthy:
        write(f"Next: {payload.next.action} — {payload.next.reason}")
        if payload.next.command is not None:
            write("  " + shlex.join(payload.next.command))
    project_message = (
        payload.project.message
        if isinstance(payload.project, ProjectInvalidStatus)
        else None
    )
    configuration_message = (
        payload.configuration.message
        if isinstance(payload.configuration, ConfigurationUnavailableStatus)
        else None
    )
    message = project_message or configuration_message
    if message:
        write(f"Configuration: {message}")
    anomalies = payload.integration.anomalies
    if anomalies:
        write(
            f"Integration: {payload.integration.status} "
            f"({len(anomalies)} anomalous surface(s))"
        )
        for item in anomalies:
            write(f"  {item.status:16} {item.path} ({item.kind})")
    write(
        f"Workspace: {payload.workspace.root} ({payload.workspace.repository_kind}; "
        f"worktree {payload.workspace.worktree_id}; "
        f"instance {payload.workspace.instance})"
    )
    if payload.dev.targets:
        write("Dev: " + ", ".join(payload.dev.targets))
    if payload.run.entries:
        write("Run: " + ", ".join(payload.run.entries))


def _render_lookup(response: LookupResponse, stream: TextIO) -> None:
    write = partial(print, file=stream)
    if response.query.mode == "path":
        assert response.document is not None
        content = response.document.content
        write(content, end="" if content.endswith("\n") else "\n")
        return
    if response.query.mode == "list":
        for entry in response.entries:
            if entry.kind == "directory":
                write(f"{entry.path:<40} {entry.document_count} documents")
            else:
                write(f"{entry.path:<40} {entry.title}")
        write("\nExpand: svc lookup --list <directory>")
        write("Read:   svc lookup --path <document-or-directory>")
        return
    if response.query.mode == "keyword":
        if not response.candidates:
            write(f"No SVC Corpus matches for: {response.query.value}")
            return
        for candidate in response.candidates:
            write(f"{candidate.entry.path:<40} {candidate.entry.title}")
            if candidate.excerpt is not None:
                write(f"  {candidate.excerpt}")
            else:
                write("  [path match]")
    else:
        if not response.matches:
            write(f"No SVC Corpus matches for: {response.query.value}")
            return
        for match in response.matches:
            if match.surface == "path":
                write(f"[path] {match.entry.path}")
            else:
                write(
                    f"{match.entry.path}:{match.line}:{match.column}: {match.excerpt}"
                )
    if response.truncated:
        write(f"Results truncated at --limit {response.query.limit}.")
    write("\nRead one: svc lookup --path <document-or-directory>")


def _emit_blockers(blockers: Sequence[Any], stream: TextIO) -> None:
    write = partial(print, file=stream)
    if not blockers:
        return
    write("Blockers:")
    for blocker in blockers:
        path = getattr(blocker, "path", None)
        location = f" {path}:" if path else ""
        write(f"  {blocker.code}:{location} {blocker.message}")


def _render_error(error: SvcError, stream: TextIO) -> None:
    write = partial(print, file=stream)
    write(f"svc: {error.code}: {error.message}")
    details = dict(error.details)
    hint = details.pop("hint", None)
    labels = {
        "reason": "Reason",
        "path": "Path",
        "repo": "Repository",
        "task_id": "Task ID",
        "target": "Target",
        "entry": "Entry",
        "expected": "Expected",
        "actual": "Actual",
        "execution_id": "Execution",
    }
    rendered: set[str] = set()
    for key, label in labels.items():
        value = details.get(key)
        if isinstance(value, (str, int, float, bool)):
            write(f"{label}: {value}")
            rendered.add(key)
    for key, label in (
        ("available_entries", "Available entries"),
        ("available_targets", "Available targets"),
    ):
        value = details.get(key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            write(f"{label}: {', '.join(value) if value else 'none'}")
            rendered.add(key)
    rollback = details.get("rollback")
    if isinstance(rollback, dict) and isinstance(rollback.get("status"), str):
        write(f"Rollback: {rollback['status']}")
        rendered.add("rollback")
    if set(details) - rendered:
        write("Structured details: rerun with --json.")
    if isinstance(hint, str):
        write(f"Hint: {hint}")


def _emit_json(payload: RegisteredMachineOutput, stream: Any | None = None) -> None:
    output = stream or sys.stdout
    dump_machine_output(payload, output)


def _emit_unscoped_json(payload: dict[str, Any], stream: Any | None = None) -> None:
    output = stream or sys.stdout
    dump_machine_output(unscoped_machine_object(payload), output)


def _exit_code(error: SvcError) -> int:
    if error.code in {
        "invalid-document-path",
        "invalid-directory-prefix",
        "invalid-lookup-options",
        "invalid-lookup-regex",
        "invalid-task-id",
    }:
        return EXIT_USAGE
    if error.code == "apply-interrupted":
        rollback = error.details.get("rollback")
        if isinstance(rollback, dict) and rollback.get("status") == "failed":
            return EXIT_FAILURE
        return 130
    if error.code in {
        "apply-failed",
        "double-carrier-exited",
        "double-carrier-launch-failed",
        "double-carrier-readiness-invalid",
        "double-carrier-readiness-timeout",
        "double-control-protocol-invalid",
        "double-control-unavailable",
        "double-internal-error",
        "double-observation-invalid",
        "double-observation-mismatch",
        "double-observation-unreadable",
        "double-run-collision",
        "double-run-record-invalid",
        "double-run-record-mismatch",
        "double-run-record-unreadable",
        "double-runtime-import-failed",
        "double-storage-failed",
        "execution-capture-failed",
        "execution-coordination-invalid",
        "execution-coordination-mismatch",
        "execution-launch-failed",
        "execution-log-unreadable",
        "execution-record-invalid",
        "execution-state-invalid",
        "execution-state-unreadable",
        "invalid-corpus",
        "invalid-execution-coordination",
        "invalid-release",
        "postcondition-failed",
        "staging-failed",
        "output-write-failed",
        "execution-storage-failed",
        "task-packet-inventory-failed",
        "task-packet-parent-unavailable",
        "task-packet-parent-unsafe",
        "task-packet-template-invalid",
        "task-packet-template-unavailable",
        "task-packet-write-failed",
    }:
        return EXIT_FAILURE
    return EXIT_CONFLICT


def _analysis_exit_code(error: AnalysisProtocolError) -> int:
    if error.code in {
        "invalid-cli-usage",
        "invalid-analysis-request-json",
        "invalid-query-request",
        "invalid-read-request",
        "analysis-request-too-large",
    }:
        return EXIT_USAGE
    if error.code in {
        "cursor-scope-mismatch",
        "invalid-cursor",
        "invalid-reference",
        "reference-kind-mismatch",
        "reference-not-found",
        "reference-scope-mismatch",
        "query-page-budget-too-small",
    }:
        return EXIT_CONFLICT
    return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
