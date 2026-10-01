from __future__ import annotations
import math
import os
from pathlib import Path
import pytest
from svc_cli.double.compiler import (
    MAX_MODULE_BYTES,
    MAX_YAML_DEPTH,
    MAX_YAML_NODES,
    compile_scenario,
)
from svc_cli.double.model import strict_json_value
from svc_cli.errors import SvcError

from ..support.scenarios import LANGUAGE_FIXTURES, one_interaction, write_module


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("alias.double.yaml", "unsupported-double-yaml-feature"),
        ("duplicate-key.double.yaml", "invalid-double-yaml"),
        ("multi-doc.double.yaml", "multiple-double-yaml-documents"),
        ("unknown-key.double.yaml", "unknown-double-key"),
    ],
)
def test_invalid_fixture_corpus_has_stable_diagnostics(name: str, code: str) -> None:
    with pytest.raises(SvcError) as caught:
        compile_scenario(LANGUAGE_FIXTURES / "invalid" / name)

    assert caught.value.code == code
    assert Path(caught.value.details["module"]).name == name
    assert caught.value.details["line"] >= 1
    assert caught.value.details["column"] >= 1


@pytest.mark.parametrize(
    ("claim", "code", "feature"),
    [
        ("!private tagged", "unsupported-double-yaml-feature", "tag"),
        ("{<<: {hidden: true}}", "unsupported-double-yaml-feature", "merge-key"),
    ],
)
def test_explicit_yaml_tags_and_merge_keys_are_rejected(
    tmp_path: Path, claim: str, code: str, feature: str
) -> None:
    module = write_module(
        tmp_path,
        one_interaction().replace("one boundary claim", claim),
    )

    with pytest.raises(SvcError) as caught:
        compile_scenario(module)

    assert caught.value.code == code
    assert caught.value.details["feature"] == feature


def test_parser_byte_depth_and_node_bounds_are_enforced(tmp_path: Path) -> None:
    too_large = tmp_path / "large.double.yaml"
    too_large.write_bytes(b"#" * (MAX_MODULE_BYTES + 1))
    with pytest.raises(SvcError, match="byte bound") as caught:
        compile_scenario(too_large)
    assert caught.value.code == "module-too-large"
    assert caught.value.details["max_bytes"] == MAX_MODULE_BYTES

    too_deep = tmp_path / "deep.double.yaml"
    too_deep.write_text("x: " + "[" * (MAX_YAML_DEPTH + 1) + "]" * (MAX_YAML_DEPTH + 1))
    with pytest.raises(SvcError) as caught:
        compile_scenario(too_deep)
    assert caught.value.code == "double-yaml-too-deep"
    assert caught.value.details["max_depth"] == MAX_YAML_DEPTH

    too_many = tmp_path / "nodes.double.yaml"
    too_many.write_text("x:\n" + "  - x\n" * MAX_YAML_NODES)
    with pytest.raises(SvcError) as caught:
        compile_scenario(too_many)
    assert caught.value.code == "double-yaml-too-many-nodes"
    assert caught.value.details["max_nodes"] == MAX_YAML_NODES


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_runtime_json_boundary_rejects_non_finite_numbers(value: float) -> None:
    assert not math.isfinite(value)
    with pytest.raises(TypeError, match="finite"):
        strict_json_value(value)


def test_yaml_reader_errors_and_symlink_loops_are_structured(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.double.yaml"
    invalid.write_bytes(b"\x00")
    with pytest.raises(SvcError) as caught:
        compile_scenario(invalid)
    assert caught.value.code == "invalid-double-yaml"

    loop = tmp_path / "loop.double.yaml"
    try:
        os.symlink(loop.name, loop)
    except OSError:
        pytest.skip("host cannot create symlinks")
    with pytest.raises(SvcError) as caught:
        compile_scenario(loop)
    assert caught.value.code == "double-module-unavailable"
