"""Private detached carrier for one active double run."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import tempfile
import threading
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from .materialization import MaterializationContext, strict_json_loads
from .model import Replay, Scenario, TargetBinding
from .runtime import BoundaryEngine, ResponderServer


_MAX_CONTROL_BODY = 65_536


class Carrier:
    def __init__(self, run_directory: Path, manifest: dict[str, Any]) -> None:
        required = {
            "schema_version",
            "run_id",
            "scenario",
            "replay",
            "run_context_digest",
            "targets",
            "control_capability",
        }
        if set(manifest) != required or manifest.get("schema_version") != 1:
            raise ValueError("carrier manifest fields are invalid")
        self.run_directory = run_directory
        self.run_id = str(manifest["run_id"])
        self.scenario = Scenario.model_validate_json(_json_bytes(manifest["scenario"]))
        self.replay = Replay.model_validate_json(_json_bytes(manifest["replay"]))
        self.targets = tuple(
            TargetBinding.model_validate_json(_json_bytes(item))
            for item in manifest["targets"]
        )
        self.capability = str(manifest["control_capability"])
        if len(self.capability) < 32:
            raise ValueError("control capability is invalid")
        self.context = MaterializationContext(
            replay=self.replay,
            scenario_name=self.scenario.name,
            scenario_digest=self.scenario.scenario_digest,
            run_context_digest=str(manifest["run_context_digest"]),
        )
        self.engine = BoundaryEngine(self.scenario, self.context, self.targets)
        self.responder = ResponderServer(self.engine)
        self.control = ThreadingHTTPServer(("127.0.0.1", 0), _control_handler(self))
        self.control.daemon_threads = True
        self._operation_lock = threading.RLock()
        self._sealed_observation: dict[str, Any] | None = None

    @property
    def control_url(self) -> str:
        host, port = self.control.server_address[:2]
        if isinstance(host, bytes):
            host = host.decode("ascii")
        return f"http://{host}:{port}"

    def run(self) -> int:
        self.responder.start()
        self._write_projection(sealed=False)
        _atomic_json(
            self.run_directory / "bootstrap.json",
            {
                "schema_version": 1,
                "run_id": self.run_id,
                "scenario_digest": self.scenario.scenario_digest,
                "run_context_digest": self.context.run_context_digest,
                "responder_url": self.responder.url,
                "control_url": self.control_url,
            },
        )
        try:
            self.control.serve_forever(poll_interval=0.05)
        finally:
            self.control.server_close()
        return 0

    def authorized(self, header: str | None) -> bool:
        expected = f"Bearer {self.capability}"
        return header is not None and hmac.compare_digest(header, expected)

    def ready_payload(self) -> dict[str, Any]:
        observation = self.engine.observation(run_id=self.run_id, sealed=False)
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "scenario_digest": self.scenario.scenario_digest,
            "run_context_digest": self.context.run_context_digest,
            "responder_url": self.responder.url,
            "observation": observation.model_dump(mode="json"),
        }

    def observe_payload(self) -> dict[str, Any]:
        with self._operation_lock:
            observation = self._sealed_observation or self._write_projection(
                sealed=False
            )
            return {
                "schema_version": 1,
                "operation": "observe",
                "observation": observation,
            }

    def emit_payload(self, event: str) -> dict[str, Any]:
        with self._operation_lock:
            result = self.engine.emit(event).model_copy(update={"run_id": self.run_id})
            if self._sealed_observation is None:
                self._write_projection(sealed=False)
            return {
                "schema_version": 1,
                "operation": "emit",
                "result": result.model_dump(mode="json"),
            }

    def stop_payload(self) -> dict[str, Any]:
        with self._operation_lock:
            if self._sealed_observation is not None:
                return {
                    "schema_version": 1,
                    "operation": "stop",
                    "observation": self._sealed_observation,
                }
            self.responder.stop()
            self._sealed_observation = self._write_projection(sealed=True)
            return {
                "schema_version": 1,
                "operation": "stop",
                "observation": self._sealed_observation,
            }

    def settle_after_response(self) -> None:
        threading.Thread(
            target=self.control.shutdown,
            name="svc-double-control-stop",
            daemon=True,
        ).start()

    def _write_projection(self, *, sealed: bool) -> dict[str, Any]:
        observation = self.engine.observation(run_id=self.run_id, sealed=sealed)
        value = observation.model_dump(mode="json")
        _atomic_json(self.run_directory / "observation.json", value)
        return value


def _control_handler(carrier: Carrier) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:
            self.close_connection = True
            if not carrier.authorized(self.headers.get("Authorization")):
                self._send(403, {"error": "control-unauthorized"})
                return
            if self.headers.get("Transfer-Encoding") is not None:
                self._send(400, {"error": "control-request-invalid"})
                return
            lengths = self.headers.get_all("Content-Length", failobj=[])
            if len(lengths) > 1:
                self._send(400, {"error": "control-request-invalid"})
                return
            try:
                length = int(lengths[0]) if lengths else 0
            except ValueError:
                self._send(400, {"error": "control-request-invalid"})
                return
            if length < 0 or length > _MAX_CONTROL_BODY:
                self._send(400, {"error": "control-request-invalid"})
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                self._send(400, {"error": "control-request-invalid"})
                return
            try:
                if self.path == "/v1/ready" and raw == b"":
                    payload = carrier.ready_payload()
                elif self.path == "/v1/observe" and raw == b"":
                    payload = carrier.observe_payload()
                elif self.path == "/v1/emit":
                    value = strict_json_loads(raw, code="control-request-invalid")
                    if (
                        not isinstance(value, dict)
                        or set(value) != {"event"}
                        or not isinstance(value["event"], str)
                    ):
                        raise ValueError("emit request is invalid")
                    payload = carrier.emit_payload(value["event"])
                elif self.path == "/v1/stop" and raw == b"":
                    payload = carrier.stop_payload()
                    self._send(200, payload)
                    carrier.settle_after_response()
                    return
                else:
                    self._send(404, {"error": "control-operation-unknown"})
                    return
            except Exception as error:
                self._send(
                    409,
                    {
                        "schema_version": 1,
                        "error": {
                            "code": getattr(error, "code", "control-operation-failed"),
                            "message": str(error),
                        },
                    },
                )
                return
            self._send(200, payload)

        def _send(self, status: int, payload: dict[str, Any]) -> None:
            raw = json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            self.send_response_only(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(
                value,
                stream,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with suppress(FileNotFoundError):
            os.unlink(temporary)


def _read_manifest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = strict_json_loads(raw, code="carrier-manifest-invalid")
    if not isinstance(value, dict):
        raise ValueError("carrier manifest must be an object")
    return cast(dict[str, Any], value)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-directory", type=Path, required=True)
    args = parser.parse_args(argv)
    run_directory = args.run_directory.resolve(strict=True)
    if not run_directory.is_dir():
        raise ValueError("run directory is invalid")
    try:
        carrier = Carrier(
            run_directory, _read_manifest(run_directory / "manifest.json")
        )
        return carrier.run()
    except (OSError, ValueError, ValidationError) as error:
        _atomic_json(
            run_directory / "bootstrap-failed.json",
            {"schema_version": 1, "reason": str(error)},
        )
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
