"""Tiny black-box Consumer used only by the scenario-double acceptance test."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


CLOCK = "2026-08-10T02:00:00Z"


def _json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    value = json.loads(handler.rfile.read(length))
    if not isinstance(value, dict):
        raise ValueError("request body must be an object")
    return value


def main() -> int:
    ready_path = Path(sys.argv[1])
    provider_path = Path(sys.argv[2])
    orders: dict[str, dict[str, str]] = {}

    class ConsumerHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:
            try:
                if self.path == "/orders/pay":
                    authored = _json(self)
                    external_id = str(authored["externalId"])
                    request_id = str(authored["requestId"])
                    provider_request = urllib.request.Request(
                        provider_origin
                        + "/v1/payments?observed-at=2026-08-10T02%3A00%3A00Z&trace=trace-001",
                        data=json.dumps(
                            {"externalId": external_id}, separators=(",", ":")
                        ).encode(),
                        headers={
                            "Content-Type": "application/json",
                            "X-Request-Id": request_id,
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(
                        provider_request, timeout=5
                    ) as response:
                        payment = json.loads(response.read())
                    orders[external_id] = {
                        "paymentId": str(payment["paymentId"]),
                        "status": "pending",
                    }
                    self._send(202, {"orderId": external_id})
                    return
                if self.path == "/webhooks/payment":
                    event = _json(self)
                    external_id = str(event["externalId"])
                    order = orders.get(external_id)
                    if order is None or order["paymentId"] != event.get("paymentId"):
                        self._send(409, {"error": "event-does-not-match-order"})
                        return
                    order["status"] = "paid"
                    self._send(204, None)
                    return
                self._send(404, {"error": "not-found"})
            except (KeyError, TypeError, ValueError, urllib.error.URLError):
                self._send(502, {"error": "consumer-boundary-failed"})

        def do_GET(self) -> None:
            prefix = "/orders/"
            if not self.path.startswith(prefix):
                self._send(404, {"error": "not-found"})
                return
            order = orders.get(self.path.removeprefix(prefix))
            if order is None:
                self._send(404, {"error": "order-not-found"})
                return
            self._send(200, {"status": order["status"]})

        def _send(self, status: int, value: dict[str, str] | None) -> None:
            raw = (
                b""
                if value is None
                else json.dumps(value, separators=(",", ":")).encode()
            )
            self.send_response_only(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            if raw:
                self.wfile.write(raw)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), ConsumerHandler)
    server.daemon_threads = True
    host, port = server.server_address[:2]
    ready_path.write_text(f"http://{host}:{port}", encoding="utf-8")
    deadline = time.monotonic() + 10
    while not provider_path.is_file():
        if time.monotonic() >= deadline:
            return 4
        time.sleep(0.02)
    provider_origin = provider_path.read_text(encoding="utf-8")
    server.serve_forever(poll_interval=0.05)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
