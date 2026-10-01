from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

import svc_cli.project as project
from svc_cli.errors import SvcError
from svc_cli.catalog import sha256_bytes
from svc_cli.integration import local_config_ignore_body, navigation_body
from svc_cli.project import (
    AGENTS_FILE,
    CODEX_SKILL_FILE,
    DOCS_INDEX_FILE,
    PROJECT_FILE,
    apply_init,
    inspect_status,
    parse_project_state,
    plan_init,
    render_project_state,
)


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_legacy_skill(root: Path, *, modified: bool = False) -> Path:
    body = b"# Historical generated SVC Skill\n"
    digest = sha256_bytes(body)
    skill = root / CODEX_SKILL_FILE
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_bytes(
        body + f"<!-- svc:generated skill sha256={digest} -->\n".encode("ascii")
    )
    if modified:
        skill.write_bytes(skill.read_bytes().replace(b"Historical", b"Modified"))
    return skill


def test_generated_guidance_separates_cli_discovery_from_corpus_navigation() -> None:
    agent = navigation_body(AGENTS_FILE)
    docs = navigation_body(DOCS_INDEX_FILE)

    assert "svc --help" in agent
    assert "svc <command> --help" in agent
    assert "svc lookup --help" in docs
    assert "svc lookup --list" not in docs
    assert "Human authorization" not in agent + docs
    assert "svc adopt" not in agent + docs


def test_init_apply_produces_a_healthy_idempotent_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = plan_init(root)
        result = apply_init(first, first.digest)
        assert result.status == "applied"
        assert (
            parse_project_state((root / PROJECT_FILE).read_bytes()).corpus_version
            == first.target_version
        )
        assert not (root / CODEX_SKILL_FILE).exists()
        assert (root / DOCS_INDEX_FILE).is_file()
        assert b"svc:begin local-config" in (root / ".gitignore").read_bytes()
        assert not (root / "svc.local.json").exists()
        initial_status = inspect_status(root)
        assert initial_status.healthy
        assert initial_status.run.status == "not-declared"
        assert initial_status.run.entries == ()

        repeat = plan_init(root)
        assert repeat.status == "noop"
        snapshot = tree_bytes(root)
        assert apply_init(repeat, repeat.digest).status == "noop"
        assert tree_bytes(root) == snapshot


def test_init_preserves_unmarked_consumer_content_and_creates_docs_index() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = b"# Consumer rules\n\nKeep this verbatim.\n"
        docs = b"# Existing docs\n\nKeep this too.\n"
        (root / AGENTS_FILE).write_bytes(agents)
        (root / "docs").mkdir()
        (root / DOCS_INDEX_FILE).write_bytes(docs)

        plan = plan_init(root)
        apply_init(plan, plan.digest)
        assert (root / AGENTS_FILE).read_bytes().startswith(agents)
        assert (root / DOCS_INDEX_FILE).read_bytes().startswith(docs)
        assert b"svc:begin -->" in (root / AGENTS_FILE).read_bytes()
        assert b"svc:begin navigation" in (root / DOCS_INDEX_FILE).read_bytes()


def test_modified_generated_surface_blocks_without_overwrite(
    tmp_path: Path,
) -> None:
    initial = plan_init(tmp_path)
    apply_init(initial, initial.digest)
    surface = tmp_path / AGENTS_FILE
    content = surface.read_bytes()
    old = b"svc --help"
    new = b"secret svc --help"
    assert old in content
    surface.write_bytes(content.replace(old, new, 1))
    before = tree_bytes(tmp_path)

    plan = plan_init(tmp_path)

    assert "generated-guidance-drift" in {blocker.code for blocker in plan.blockers}
    with pytest.raises(SvcError, match="unresolved blockers"):
        apply_init(plan, plan.digest)
    assert tree_bytes(tmp_path) == before


def test_legacy_skill_is_preserved_as_consumer_owned() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = write_legacy_skill(root)
        plan = plan_init(root)
        assert not any(item.path == CODEX_SKILL_FILE for item in plan.mutations)
        apply_init(plan, plan.digest)
        assert skill.exists()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = write_legacy_skill(root, modified=True)
        plan = plan_init(root)
        assert not plan.blockers
        apply_init(plan, plan.digest)
        assert skill.exists()


def test_unowned_existing_skill_is_ignored_and_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = root / CODEX_SKILL_FILE
        skill.parent.mkdir(parents=True)
        skill.write_text("# My own skill\n", encoding="utf-8")
        plan = plan_init(root)
        assert not plan.blockers
        apply_init(plan, plan.digest)
        assert skill.read_text(encoding="utf-8") == "# My own skill\n"


def test_stale_plan_detects_consumer_change_before_any_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stale = plan_init(root)
        (root / AGENTS_FILE).write_text(
            "concurrent consumer change\n", encoding="utf-8"
        )
        with pytest.raises(SvcError, match="changed after planning"):
            apply_init(stale, stale.digest)
        assert not (root / PROJECT_FILE).exists()


def test_status_reports_corpus_relation_and_upgrade_continuation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        initial = plan_init(root)
        apply_init(initial, initial.digest)
        (root / PROJECT_FILE).write_bytes(render_project_state("11.0.1"))
        status = inspect_status(root)
        assert status.status == "actionable"
        assert status.project.status == "corpus-behind"
        assert status.corpus.status == "behind"
        assert status.corpus.project_version == "11.0.1"
        assert status.corpus.available_version == initial.target_version
        assert status.next.action == "plan-project-upgrade"
        assert status.next.command is not None
        assert status.next.command == ("svc", "upgrade", str(root.resolve()))
        assert not status.healthy


def test_status_does_not_compare_cli_distribution_to_corpus_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        initial = plan_init(root)
        apply_init(initial, initial.digest)
        cli_version = "0.0.0" if initial.target_version != "0.0.0" else "0.0.1"
        with monkeypatch.context() as patch:
            patch.setattr(
                project, "installed_distribution_version", lambda: cli_version
            )
            status = inspect_status(root)
        assert status.installed_cli_version == cli_version
        assert status.available_corpus_version == initial.target_version
        assert status.runtime.status == "installed"
        assert status.status == "healthy"
        assert status.healthy


def test_status_makes_unadopted_state_and_init_plan_explicit(
    tmp_path: Path,
) -> None:
    before = tree_bytes(tmp_path)

    status = inspect_status(tmp_path)

    assert status.status == "unadopted"
    assert status.project.status == "missing"
    assert status.configuration.status == "not-configured"
    assert status.dev.status == "unavailable"
    assert status.dev.targets == ()
    assert status.run.status == "unavailable"
    assert status.run.entries == ()
    assert status.next.action == "plan-integration-establishment"
    assert status.next.command == ("svc", "init", str(tmp_path))
    assert not status.healthy
    assert tree_bytes(tmp_path) == before


def test_status_reports_malformed_project_state_without_suggesting_init(
    tmp_path: Path,
) -> None:
    (tmp_path / PROJECT_FILE).write_bytes(b"{not-json")
    before = tree_bytes(tmp_path)

    status = inspect_status(tmp_path)

    assert status.status == "malformed"
    assert status.next.action == "repair-project-configuration"
    assert status.next.command is None
    assert tree_bytes(tmp_path) == before


def test_status_summarizes_declarations_without_executing_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = plan_init(tmp_path)
    apply_init(initial, initial.digest)
    (tmp_path / PROJECT_FILE).write_text(
        json.dumps(
            {
                "schema_version": 3,
                "corpus_version": initial.target_version,
                "dev": {
                    "targets": {
                        "web": {
                            "probe": {"kind": "exec", "argv": ["unreachable-probe"]},
                            "provision": {"kind": "manual"},
                        },
                        "api": {
                            "probe": {"kind": "exec", "argv": ["unreachable-probe"]},
                            "provision": {"kind": "manual"},
                        },
                    },
                },
                "run": {
                    "z-last": {"argv": ["never-start-this"]},
                    "a-first": {"argv": ["never-start-this-either"]},
                },
            }
        ),
        encoding="utf-8",
    )

    def unexpected_probe(*args: object, **kwargs: object) -> object:
        raise AssertionError("root status must not probe declared dev targets")

    monkeypatch.setattr("svc_cli.dev.runtime.probe_target", unexpected_probe)
    status = inspect_status(tmp_path)

    assert status.status == "healthy"
    assert status.dev.status == "declared"
    assert status.dev.targets == ("api", "web")
    assert status.run.status == "declared"
    assert status.run.entries == ("a-first", "z-last")
    assert status.next.action == "continue"
    assert status.configuration.status == "current"
    assert status.configuration.effective.digest


def test_init_manages_only_a_clean_local_config_ignore_section() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = b"node_modules\r\nsvc.local.json\r\n"
        (root / ".gitignore").write_bytes(original)
        plan = plan_init(root)
        apply_init(plan, plan.digest)
        ignored = (root / ".gitignore").read_bytes()
        assert ignored.startswith(original)
        assert local_config_ignore_body().encode() in ignored.replace(b"\r\n", b"\n")
        assert b"\r\n" in ignored

        drifted = ignored.replace(
            b"AGENTS.local.md\r\n# svc:end local-config",
            b"private-AGENTS.local.md\r\n# svc:end local-config",
        )
        (root / ".gitignore").write_bytes(drifted)
        blocked = plan_init(root)
        assert "managed-ignore-drift" in {item.code for item in blocked.blockers}


def test_unsupported_schema_and_corpus_ahead_block_init_writes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        legacy = b'{\n  "schema_version": 1,\n  "svc_version": "10.0.0"\n}\n'
        (root / PROJECT_FILE).write_bytes(legacy)
        blocked = plan_init(root)
        assert "invalid-project-state" in {item.code for item in blocked.blockers}
        assert (root / PROJECT_FILE).read_bytes() == legacy

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / PROJECT_FILE).write_bytes(render_project_state("17.0.0"))
        blocked = plan_init(root)
        assert "corpus-baseline-ahead" in {item.code for item in blocked.blockers}


def test_invalid_local_overlay_blocks_init_without_rewriting_it() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        initial = plan_init(root)
        apply_init(initial, initial.digest)
        local = root / "svc.local.json"
        local.write_text('{"schema_version": 2}\n', encoding="utf-8")
        before = local.read_bytes()
        blocked = plan_init(root)
        assert "invalid-project-configuration" in {
            item.code for item in blocked.blockers
        }
        with pytest.raises(SvcError):
            apply_init(blocked, blocked.digest)
        assert local.read_bytes() == before


def test_apply_preserves_existing_consumer_file_mode_and_rejects_mode_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agents = root / AGENTS_FILE
        agents.write_text("# Consumer\n", encoding="utf-8")
        os.chmod(agents, 0o640)
        plan = plan_init(root)
        os.chmod(agents, 0o600)
        with pytest.raises(SvcError) as raised:
            apply_init(plan, plan.digest)
        assert raised.value.code == "stale-plan"
        os.chmod(agents, 0o640)
        apply_init(plan, plan.digest)
        assert agents.stat().st_mode & 0o777 == 0o640
