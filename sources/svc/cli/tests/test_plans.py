from __future__ import annotations

import os
from pathlib import Path

import pytest

import svc_cli.plans as plans
from svc_cli.errors import SvcError
from svc_cli.plans import LocalPlan, apply_local_plan, make_delete, make_write


def _plan(root: Path, *mutations: plans.PlannedFileMutation) -> LocalPlan:
    return LocalPlan("test", root, "1.0.0", mutations)


def test_file_state_signature_names_absence_content_and_intended_mode(
    tmp_path: Path,
) -> None:
    mutation = make_write(tmp_path, "new.txt", "create", "test", b"new\n")

    assert mutation.before.state == "absent"
    assert mutation.after.state == "file"
    assert mutation.after.sha256
    if os.name == "nt":
        assert mutation.after.posix_mode is None
    else:
        assert mutation.after.posix_mode == 0o644


def test_rollback_restores_exact_existing_mode_after_later_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = tmp_path / "existing.txt"
    existing.write_bytes(b"before\n")
    existing.chmod(0o640)
    transaction = _plan(
        tmp_path,
        make_write(tmp_path, "existing.txt", "refresh", "test", b"after\n"),
        make_write(tmp_path, "later.txt", "create", "test", b"later\n"),
    )
    original = plans._commit_mutation
    calls = 0

    def fail_second(
        path: Path,
        mutation: plans.PlannedFileMutation,
        content: bytes | None,
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected")
        original(path, mutation, content)

    monkeypatch.setattr(plans, "_commit_mutation", fail_second)

    with pytest.raises(SvcError) as raised:
        apply_local_plan(transaction, transaction.digest)

    assert raised.value.details["rollback"] == {
        "status": "succeeded",
        "restored_paths": ["existing.txt"],
        "preserved_external_paths": [],
        "unrestored_paths": [],
    }
    assert existing.read_bytes() == b"before\n"
    if os.name != "nt":
        assert existing.stat().st_mode & 0o777 == 0o640


def test_delete_is_verified_and_rollback_recreates_exact_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retired = tmp_path / "retired.txt"
    retired.write_bytes(b"owned\n")
    retired.chmod(0o600)
    transaction = _plan(
        tmp_path,
        make_delete(tmp_path, "retired.txt", "delete", "retire"),
        make_write(tmp_path, "later.txt", "create", "test", b"later\n"),
    )
    original = plans._commit_mutation
    calls = 0

    def fail_second(
        path: Path,
        mutation: plans.PlannedFileMutation,
        content: bytes | None,
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected")
        original(path, mutation, content)

    monkeypatch.setattr(plans, "_commit_mutation", fail_second)

    with pytest.raises(SvcError) as raised:
        apply_local_plan(transaction, transaction.digest)

    assert raised.value.details["rollback"]["restored_paths"] == ["retired.txt"]
    assert retired.read_bytes() == b"owned\n"
    if os.name != "nt":
        assert retired.stat().st_mode & 0o777 == 0o600

    deletion = _plan(tmp_path, make_delete(tmp_path, "retired.txt", "delete", "retire"))
    assert apply_local_plan(deletion, deletion.digest).status == "applied"
    assert not retired.exists()


def test_interrupt_after_atomic_effect_is_reconciled_and_rolled_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transaction = _plan(
        tmp_path,
        make_write(tmp_path, "created.txt", "create", "test", b"created\n"),
    )
    original = plans._commit_mutation

    def interrupt_after_effect(
        path: Path,
        mutation: plans.PlannedFileMutation,
        content: bytes | None,
    ) -> None:
        original(path, mutation, content)
        raise KeyboardInterrupt

    monkeypatch.setattr(plans, "_commit_mutation", interrupt_after_effect)

    with pytest.raises(SvcError) as raised:
        apply_local_plan(transaction, transaction.digest)

    assert raised.value.code == "apply-interrupted"
    assert raised.value.details["repository_effect"] == "restored"
    assert raised.value.details["rollback"]["restored_paths"] == ["created.txt"]
    assert not (tmp_path / "created.txt").exists()


def test_interrupt_before_repository_mutation_reports_no_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transaction = _plan(
        tmp_path,
        make_write(tmp_path, "created.txt", "create", "test", b"created\n"),
    )

    def interrupt_staging(*args: object, **kwargs: object) -> dict[str, bytes]:
        raise KeyboardInterrupt

    monkeypatch.setattr(plans, "_stage_after_content", interrupt_staging)

    with pytest.raises(SvcError) as raised:
        apply_local_plan(transaction, transaction.digest)

    assert raised.value.code == "apply-interrupted"
    assert raised.value.details == {"repository_effect": "none"}
    assert not (tmp_path / "created.txt").exists()


def test_platform_without_posix_mode_omits_and_does_not_verify_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(plans, "_supports_posix_mode", lambda: False)
    mutation = make_write(tmp_path, "portable.txt", "create", "test", b"ok\n")
    transaction = _plan(tmp_path, mutation)

    assert mutation.before.posix_mode is None
    assert mutation.after.posix_mode is None
    assert apply_local_plan(transaction, transaction.digest).status == "applied"


def test_rollback_failure_names_unrestored_path_and_uncertain_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = tmp_path / "existing.txt"
    existing.write_bytes(b"before\n")
    transaction = _plan(
        tmp_path,
        make_write(tmp_path, "existing.txt", "refresh", "test", b"after\n"),
    )

    def fail_postcondition(plan: LocalPlan) -> None:
        raise SvcError("postcondition-failed", "injected")

    def fail_restore(path: Path, mutation: plans.PlannedFileMutation) -> None:
        raise OSError("cannot restore")

    monkeypatch.setattr(plans, "_verify_postconditions", fail_postcondition)
    monkeypatch.setattr(plans, "_restore_before", fail_restore)

    with pytest.raises(SvcError) as raised:
        apply_local_plan(transaction, transaction.digest)

    assert raised.value.details["repository_effect"] == "uncertain"
    assert raised.value.details["rollback"]["status"] == "failed"
    assert raised.value.details["rollback"]["unrestored_paths"] == ["existing.txt"]
