from __future__ import annotations
import json
import os
import signal
from pathlib import Path
import pytest
import svc_cli.double.service as double_service
from svc_cli.double.model import (
    RunObservation,
)
from svc_cli.double.runtime import ResponderServer
from svc_cli.double.service import (
    DoubleRunStore,
    emit_event,
    observe_run,
    stop_run,
)

from ..support.http import (
    callback_server,
    http_payment,
    wait_until_closed,
)
from ..support.runs import carrier_pid, cleanup_run, file_bytes, start_double_run
from ..support.scenarios import (
    FIRST_EXTERNAL_ID,
    FIRST_REQUEST_ID,
    SECOND_EXTERNAL_ID,
    SECOND_REQUEST_ID,
    build_engine,
)


def test_service_detached_boundary_event_and_sealed_authority(tmp_path: Path) -> None:
    with callback_server() as (callback_origin, deliveries):
        started, run_root, _execution_root = start_double_run(
            tmp_path, callback_origin, seed=123
        )
        run_id = started.run_id
        stopped = False
        try:
            status, response = http_payment(started.responder_url)
            assert status == 201
            payment_id = response["paymentId"]

            emitted = emit_event(run_id, "payment.succeeded", run_root=run_root)
            assert emitted.status == "acknowledged"
            assert emitted.http_status == 204
            assert len(deliveries) == 1
            assert deliveries[0]["path"] == "/webhooks/payment"
            assert deliveries[0]["body"] == {
                "externalId": FIRST_EXTERNAL_ID,
                "paymentId": payment_id,
            }

            active = observe_run(run_id, run_root=run_root)
            assert active.authority == "active-carrier"
            assert active.control_status == "available"
            assert active.observation.sealed is False
            assert active.observation.bindings == {
                "external_id": FIRST_EXTERNAL_ID,
                "payment_id": payment_id,
                "request_id": FIRST_REQUEST_ID,
            }
            assert [entry.status for entry in active.observation.journal.entries] == [
                "matched",
                "acknowledged",
            ]

            first_stop = stop_run(run_id, run_root=run_root)
            stopped = True
            assert first_stop.status == "stopped"
            assert first_stop.sealed is True
            assert first_stop.idempotent is False
            sealed = observe_run(run_id, run_root=run_root)
            assert sealed.authority == "sealed-snapshot"
            assert sealed.control_status == "not-required"
            assert sealed.observation == first_stop.observation

            repeated = stop_run(run_id, run_root=run_root)
            assert repeated.status == "stopped"
            assert repeated.sealed is True
            assert repeated.idempotent is True
            assert repeated.observation == first_stop.observation
        finally:
            if not stopped:
                cleanup_run(run_id, run_root, _execution_root)


def test_event_consumer_can_reenter_the_responder_before_acknowledging() -> None:
    responder: dict[str, str] = {}

    def reenter_responder() -> None:
        status, _response = http_payment(responder["origin"])
        assert status == 201

    with callback_server(during_delivery=reenter_responder) as (
        callback_origin,
        deliveries,
    ):
        engine = build_engine(123, target_origin=callback_origin)
        server = ResponderServer(engine)
        server.start()
        responder["origin"] = server.url
        try:
            status, _response = http_payment(server.url)
            assert status == 201

            emitted = engine.emit("payment.succeeded")

            assert emitted.status == "acknowledged"
            assert emitted.http_status == 204
            assert len(deliveries) == 1
            assert [
                entry.status
                for entry in engine.observation(
                    run_id="run", sealed=False
                ).journal.entries
            ] == ["matched", "matched", "acknowledged"]
        finally:
            server.stop()


def test_observe_classifies_a_concurrent_sealed_control_result_as_final_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with callback_server() as (callback_origin, _deliveries):
        started, run_root, execution_root = start_double_run(
            tmp_path, callback_origin, seed=123
        )
        try:
            store = DoubleRunStore(run_root)
            record = store.read_record(started.run_id)
            unsealed = store.read_observation(record)
            sealed = unsealed.model_copy(update={"status": "stopped", "sealed": True})

            def sealed_control_result(
                *args: object, **kwargs: object
            ) -> dict[str, object]:
                return {"observation": sealed.model_dump(mode="json")}

            with monkeypatch.context() as patch:
                patch.setattr(double_service, "_control_request", sealed_control_result)
                observed = observe_run(started.run_id, run_root=run_root)

            assert observed.authority == "sealed-snapshot"
            assert observed.control_status == "not-required"
            assert observed.observation.sealed is True
        finally:
            cleanup_run(started.run_id, run_root, execution_root)


def test_control_failure_rereads_a_concurrently_sealed_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with callback_server() as (callback_origin, _deliveries):
        started, run_root, execution_root = start_double_run(
            tmp_path, callback_origin, seed=123
        )
        restore_projection: tuple[Path, RunObservation] | None = None
        try:
            store = DoubleRunStore(run_root)
            record = store.read_record(started.run_id)
            unsealed = store.read_observation(record)
            sealed = unsealed.model_copy(update={"status": "stopped", "sealed": True})
            observation_path = Path(record.observation_path)
            restore_projection = (observation_path, unsealed)

            def seal_then_disappear(*args: object, **kwargs: object) -> None:
                observation_path.write_text(
                    json.dumps(sealed.model_dump(mode="json")), encoding="utf-8"
                )
                return None

            with monkeypatch.context() as patch:
                patch.setattr(double_service, "_control_request", seal_then_disappear)
                observed = observe_run(started.run_id, run_root=run_root)
            observation_path.write_text(
                json.dumps(unsealed.model_dump(mode="json")), encoding="utf-8"
            )
            with monkeypatch.context() as patch:
                patch.setattr(double_service, "_control_request", seal_then_disappear)
                stopped = stop_run(started.run_id, run_root=run_root)

            assert observed.authority == "sealed-snapshot"
            assert observed.control_status == "not-required"
            assert stopped.status == "stopped"
            assert stopped.sealed is True
            assert stopped.idempotent is True
        finally:
            if restore_projection is not None:
                path, observation = restore_projection
                path.write_text(
                    json.dumps(observation.model_dump(mode="json")), encoding="utf-8"
                )
            cleanup_run(started.run_id, run_root, execution_root)


def test_two_active_runs_keep_replay_bindings_and_stop_isolated(tmp_path: Path) -> None:
    with callback_server() as (callback_origin, _deliveries):
        first, run_root, _execution_root = start_double_run(
            tmp_path, callback_origin, seed=123
        )
        second = None
        stopped: set[str] = set()
        try:
            second, _same_run_root, _same_execution_root = start_double_run(
                tmp_path, callback_origin, seed=456
            )
            assert first.run_id != second.run_id
            assert first.responder_url != second.responder_url
            assert first.scenario_digest == second.scenario_digest
            assert first.run_context_digest != second.run_context_digest
            assert first.replay.seed == 123
            assert second.replay.seed == 456

            first_status, first_response = http_payment(first.responder_url)
            second_status, second_response = http_payment(
                second.responder_url,
                external_id=SECOND_EXTERNAL_ID,
                request_id=SECOND_REQUEST_ID,
            )
            assert first_status == second_status == 201
            assert first_response != second_response

            first_observation = observe_run(first.run_id, run_root=run_root).observation
            second_observation = observe_run(
                second.run_id, run_root=run_root
            ).observation
            assert first_observation.bindings["external_id"] == FIRST_EXTERNAL_ID
            assert second_observation.bindings["external_id"] == SECOND_EXTERNAL_ID
            assert (
                first_observation.bindings["payment_id"]
                != second_observation.bindings["payment_id"]
            )

            assert stop_run(first.run_id, run_root=run_root).status == "stopped"
            stopped.add(first.run_id)
            retry_status, retry_response = http_payment(
                second.responder_url,
                external_id=SECOND_EXTERNAL_ID,
                request_id=SECOND_REQUEST_ID,
            )
            assert retry_status == 201
            assert retry_response == second_response
            still_active = observe_run(second.run_id, run_root=run_root)
            assert still_active.authority == "active-carrier"
            assert still_active.observation.journal.total == 2
        finally:
            for result in (first, second):
                if result is not None and result.run_id not in stopped:
                    cleanup_run(result.run_id, run_root, _execution_root)


def test_control_unavailable_preserves_files_without_pid_authority(
    tmp_path: Path,
) -> None:
    with callback_server() as (callback_origin, _deliveries):
        started, run_root, execution_root = start_double_run(
            tmp_path, callback_origin, seed=123
        )
        store = DoubleRunStore(run_root)
        record = store.read_record(started.run_id)
        carrier_terminated = False
        try:
            os.kill(carrier_pid(started.run_id, execution_root), signal.SIGTERM)
            wait_until_closed(record.control_url)
            carrier_terminated = True
            before = file_bytes(Path(record.run_directory))

            observed = observe_run(started.run_id, run_root=run_root)
            stopped = stop_run(started.run_id, run_root=run_root)

            assert observed.authority == "unsealed-projection"
            assert observed.control_status == "control-unavailable"
            assert observed.observation.sealed is False
            assert stopped.status == "control-unavailable"
            assert stopped.sealed is False
            assert stopped.idempotent is False
            assert stopped.observation == observed.observation
            assert file_bytes(Path(record.run_directory)) == before
            assert b"carrier_pid" not in before["record.json"]
        finally:
            if not carrier_terminated:
                cleanup_run(started.run_id, run_root, execution_root)
