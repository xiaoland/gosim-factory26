from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from svc_cli.cli import EXIT_CONFLICT, EXIT_OK, main
from svc_cli_test_support.project_contract import write_project_config


def invoke_text(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            code = main(arguments)
        except SystemExit as error:
            code = int(error.code or 0)
    return code, stdout.getvalue(), stderr.getvalue()


def assert_compact_json(raw: str) -> dict[str, object]:
    assert raw.endswith("\n")
    assert raw.count("\n") == 1
    return json.loads(raw)


def test_machine_json_is_compact_for_results_and_errors() -> None:
    code, stdout, stderr = invoke_text(["lookup", "--list", "--json"])

    assert (code, stderr) == (EXIT_OK, "")
    assert assert_compact_json(stdout)["command"] == "lookup"

    with tempfile.TemporaryDirectory() as tmp:
        code, stdout, stderr = invoke_text(["status", tmp, "--json"])

    assert (code, stderr) == (EXIT_CONFLICT, "")
    assert assert_compact_json(stdout)["status"] == "unadopted"

    code, stdout, stderr = invoke_text(["status", "--unknown", "--json"])

    assert (code, stdout) == (2, "")
    assert assert_compact_json(stderr)["code"] == "invalid-cli-usage"

    code, stdout, stderr = invoke_text(["lookup", "--path", "../invalid.md", "--json"])

    assert (code, stdout) == (2, "")
    assert assert_compact_json(stderr)["error"]["code"] == "invalid-document-path"


def test_output_schema_discovery_is_compact_and_bypasses_command_selection() -> None:
    for arguments in (
        ["lookup", "--json-schema"],
        ["init", "--json-schema"],
        ["dev", "ensure", "--json-schema"],
        ["run", "--json-schema"],
    ):
        code, stdout, stderr = invoke_text(arguments)
        schema = assert_compact_json(stdout)

        assert (code, stderr) == (EXIT_OK, "")
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["x-svc-result-schema-version"] >= 1
        if arguments[0] == "init":
            assert schema["x-svc-result-schema-version"] == 3


def test_help_is_self_sufficient_and_removed_commands_are_absent() -> None:
    code, stdout, stderr = invoke_text(["--help"])
    assert code == EXIT_OK
    assert stderr == ""
    assert "svc lookup --help" in stdout
    assert "self-update" not in stdout
    assert "    task " not in stdout

    code, stdout, stderr = invoke_text(["lookup", "--help"])
    assert code == EXIT_OK
    assert stderr == ""
    assert "--list" in stdout
    assert "--path" in stdout
    assert "--regex" in stdout
    assert "SVC CLI usage" in stdout
    assert "concept directory" in stdout

    code, stdout, stderr = invoke_text(["lookup", "--list"])
    assert code == EXIT_OK
    assert stderr == ""
    assert "Expand: svc lookup --list <directory>" in stdout

    code, stdout, stderr = invoke_text(["analysis", "--help"])
    assert (code, stderr) == (EXIT_OK, "")
    assert "Analysis method:" in stdout
    assert "performance conclusion" in stdout
    assert "calling Agent owns task intent" in stdout

    code, stdout, stderr = invoke_text(["telemetry", "--help"])
    assert (code, stderr) == (EXIT_OK, "")
    assert "does not interpret task" in stdout
    assert "performance" in stdout

    code, stdout, stderr = invoke_text(["upgrade", "--help"])
    assert (code, stderr) == (EXIT_OK, "")
    assert "--target" not in stdout
    assert "does not update the CLI" in stdout
    assert "Agent/Human document work" in stdout

    code, stdout, stderr = invoke_text(["dev", "--help"])
    assert (code, stderr) == (EXIT_OK, "")
    assert "setup" not in stdout

    code, _, stderr = invoke_text([])
    assert code == 2
    assert "Hint: Use `svc lookup --help`" in stderr


def test_dev_identity_text_describes_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, stdout, stderr = invoke_text(["dev", "identity", "--repo", str(root)])
        assert (code, stderr) == (EXIT_OK, "")
        assert "svc dev identity\ninstance:" in stdout
        assert f"root: {root.resolve()}" in stdout
        assert "repository: non-git " in stdout
        assert "worktree:" in stdout and "namespace:" in stdout


def test_dev_ensure_text_exposes_probe_and_manual_continuation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        diagnostic = '{"code":"RECEIPT_MISSING","ready":false}'
        write_project_config(
            root,
            dev_targets={
                "builder": {
                    "scope": "repository",
                    "probe": {
                        "kind": "exec",
                        "argv": [
                            sys.executable,
                            "-c",
                            f"print({diagnostic!r}); raise SystemExit(1)",
                        ],
                    },
                    "provision": {"kind": "manual"},
                    "access": ["offline-receipt"],
                }
            },
        )

        code, stdout, stderr = invoke_text(
            ["dev", "ensure", "builder", "--repo", str(root)]
        )
        assert (code, stderr) == (EXIT_CONFLICT, "")
        assert "svc dev builder: manual-action-required" in stdout
        assert "Probe: exec exit 1" in stdout
        assert "Access: offline-receipt" in stdout
        assert "No SVC command can provision this target" in stdout


def test_root_status_text_exposes_its_primary_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        code, stdout, stderr = invoke_text(["status", tmp])

        assert (code, stderr) == (EXIT_CONFLICT, "")
        assert "SVC unadopted" in stdout
        assert "plan-integration-establishment" in stdout
        assert "svc init" in stdout


def test_init_apply_text_renders_every_planned_surface() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        code, stdout, stderr = invoke_text(["init", tmp, "--json"])
        plan = assert_compact_json(stdout)

        assert (code, stderr) == (EXIT_OK, "")
        code, stdout, stderr = invoke_text(
            ["init", tmp, "--apply", str(plan["plan_digest"])]
        )

        assert (code, stderr) == (EXIT_OK, "")
        assert "created   AGENTS.local.md (whole file)" in stdout
        assert "Verification: all planned path postconditions passed" in stdout


def test_run_json_is_one_receipt_and_suppresses_native_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project_config(
            root,
            run_entries={
                "fails": {
                    "argv": [
                        sys.executable,
                        "-c",
                        "import sys; print('native'); print('diagnostic', file=sys.stderr); sys.exit(7)",
                    ],
                    "env": {"PRIVATE_VALUE": "must-not-appear"},
                }
            },
        )
        code, stdout, stderr = invoke_text(
            ["run", "fails", "--repo", str(root), "--json"]
        )
        assert (code, stderr) == (7, "")
        payload = assert_compact_json(stdout)
        assert payload["state"] == "exited"
        assert payload["exit_code"] == 7
        assert stdout.count("\n") == 1
        assert "must-not-appear" not in stdout
        assert "workspace_instance" in payload
        assert payload["logs"]["stdout"]["bytes"] == len("native\n")
        assert payload["logs"]["stderr"]["bytes"] == len("diagnostic\n")

        execution_id = str(payload["execution_id"])
        code, inspected_stdout, inspected_stderr = invoke_text(
            ["run", "--inspect", execution_id, "--repo", str(root), "--json"]
        )
        assert (code, inspected_stderr) == (EXIT_OK, "")
        inspected = assert_compact_json(inspected_stdout)
        assert inspected["command"] == "run inspect"
        assert inspected["execution_id"] == execution_id

        code, inspect_text, inspect_errors = invoke_text(
            ["run", "--inspect", execution_id, "--repo", str(root)]
        )
        assert (code, inspect_errors) == (EXIT_OK, "")
        assert "svc run inspect: fails — exited 7" in inspect_text
        assert f"execution: {execution_id}" in inspect_text
        assert "$ " in inspect_text and "cwd:" in inspect_text
        assert "logs: stdout " in inspect_text and "stderr " in inspect_text


def test_run_text_keeps_native_channels_and_wrapper_facts_separate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project_config(
            root,
            run_entries={
                "channels": {
                    "argv": [
                        sys.executable,
                        "-c",
                        "import sys; print('native-out'); print('native-err', file=sys.stderr)",
                    ]
                }
            },
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "svc_cli.cli",
                "run",
                "channels",
                "--repo",
                str(root),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        assert completed.returncode == 0
        assert completed.stdout == "native-out\n"
        assert "native-err\n" in completed.stderr
        assert "svc run channels: owner" in completed.stderr
        assert "$ " in completed.stderr
        assert "svc run channels: exited 0" in completed.stderr
        assert "logs: stdout " in completed.stderr


def test_run_grammar_requires_exactly_one_selector() -> None:
    code, stdout, stderr = invoke_text(["run", "--json"])
    assert (code, stdout) == (2, "")
    assert assert_compact_json(stderr)["code"] == "invalid-cli-usage"

    code, stdout, stderr = invoke_text(["run", "check", "--follow", "bad", "--json"])
    assert (code, stdout) == (2, "")
    assert assert_compact_json(stderr)["code"] == "invalid-cli-usage"
