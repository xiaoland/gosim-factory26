from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest
from svc_cli.double.compiler import (
    compile_scenario,
)
from svc_cli.errors import SvcError

from ..support.scenarios import one_interaction, write_module


def test_managed_assets_are_snapshotted_and_workspace_escape_is_rejected(
    tmp_path: Path,
) -> None:
    managed = tmp_path / "managed.json"
    managed.write_text('{"provider":"value"}', encoding="utf-8")
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            $bsl:\n"
                "              kind: managed\n"
                "              source: managed.json\n"
                "              media-type: application/json\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].response.body
    assert body is not None and body.template == {"provider": "value"}
    assert body.nodes[0].managed_snapshot is not None
    assert body.nodes[0].managed_snapshot.sha256 == scenario.snapshots[0].sha256

    outside = tmp_path.parent / "outside-double.json"
    outside.write_text("{}", encoding="utf-8")
    escaped = module.read_text(encoding="utf-8").replace(
        "managed.json", "../outside-double.json"
    )
    module.write_text(escaped, encoding="utf-8")
    with pytest.raises(SvcError) as caught:
        compile_scenario(module)
    assert caught.value.code == "double-local-path-outside-workspace"


def test_managed_raw_body_preserves_exact_bytes(tmp_path: Path) -> None:
    payload = b"\x00provider\xffbytes\n"
    (tmp_path / "payload.bin").write_bytes(payload)
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          raw:\n"
                "            $bsl:\n"
                "              kind: managed\n"
                "              source: payload.bin\n"
                "              media-type: application/octet-stream\n"
            )
        ),
    )

    scenario = compile_scenario(module)

    body = scenario.interactions[0].response.body
    assert body is not None and body.kind == "raw" and body.raw is not None
    assert body.raw.bytes == len(payload)
    assert body.raw == scenario.snapshots[0]


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-double-symlink.json"
    outside.write_text("{}", encoding="utf-8")
    link = tmp_path / "managed.json"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("host cannot create symlinks")
    module = write_module(
        tmp_path,
        one_interaction(
            response=(
                "        status: 200\n"
                "        body:\n"
                "          structured:\n"
                "            $bsl: {kind: managed, source: managed.json, media-type: application/json}\n"
            )
        ),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "double-local-path-outside-workspace"


def test_compile_inspects_materializer_without_executing_it(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed"
    script = tmp_path / "materializer.py"
    script.write_text(
        "from pathlib import Path\nPath('executed').write_text('unexpected')\n",
        encoding="utf-8",
    )
    response = (
        "        status: 200\n"
        "        materializer:\n"
        f"          argv: [{sys.executable!r}, materializer.py]\n"
        "          cwd: .\n"
        "          env: {}\n"
        "          timeout-ms: 2000\n"
        "          max-output-bytes: 1048576\n"
    )
    module = write_module(tmp_path, one_interaction(response=response))

    scenario = compile_scenario(module)

    assert scenario.uses_materializer is True
    assert not sentinel.exists()
    materializer = scenario.interactions[0].response.materializer
    assert materializer is not None
    assert materializer.argv[0] == str(Path(sys.executable).resolve())
    assert "materializer-egress: not-enforced" in scenario.nonclaims


def test_event_materializer_owns_query_headers_and_body(tmp_path: Path) -> None:
    scenario = one_interaction() + (
        "  events:\n"
        "    - name: callback\n"
        "      target: consumer.callback\n"
        "      provenance: {kind: synthetic, source: https://example.invalid/callback}\n"
        "      request:\n"
        "        method: POST\n"
        "        path: /callback\n"
        "        query: {signature: authored-but-dead}\n"
        "        materializer:\n"
        f"          argv: [{sys.executable!r}]\n"
        "          cwd: .\n"
        "          env: {}\n"
        "          timeout-ms: 2000\n"
        "          max-output-bytes: 1048576\n"
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(write_module(tmp_path, scenario))

    assert caught.value.code == "invalid-double-materializer"


def test_materializer_cwd_does_not_make_digest_workspace_address_dependent(
    tmp_path: Path,
) -> None:
    response = (
        "        status: 200\n"
        "        materializer:\n"
        f"          argv: [{sys.executable!r}, materializer.py]\n"
        "          cwd: .\n"
        "          env: {}\n"
        "          timeout-ms: 2000\n"
        "          max-output-bytes: 1048576\n"
    )
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
        write_module(root, one_interaction(response=response))

    first = compile_scenario(roots[0] / "scenario.double.yaml")
    second = compile_scenario(roots[1] / "scenario.double.yaml")

    assert first.interactions[0].response.materializer is not None
    assert second.interactions[0].response.materializer is not None
    assert (
        first.interactions[0].response.materializer.cwd
        != second.interactions[0].response.materializer.cwd
    )
    assert first.scenario_digest == second.scenario_digest


def test_provider_capture_requires_explicit_sanitization(tmp_path: Path) -> None:
    module = write_module(
        tmp_path,
        one_interaction().replace(
            "{kind: synthetic, source: https://example.invalid/call}",
            "{kind: provider-capture, source: capture.json}",
        ),
    )
    (tmp_path / "capture.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == "unsanitized-double-capture"
