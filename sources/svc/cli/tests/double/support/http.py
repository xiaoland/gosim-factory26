from __future__ import annotations

import json
import socket
import threading
import time
import urllib.parse
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Iterator

import urllib3

from svc_cli.double.materialization import compact_json
from svc_cli.double.runtime import BoundaryEngine

from .scenarios import (
    FIRST_EXTERNAL_ID,
    FIRST_REQUEST_ID,
    payment_target,
)


def engine_request(
    engine: BoundaryEngine,
    *,
    external_id: str = FIRST_EXTERNAL_ID,
    request_id: str = FIRST_REQUEST_ID,
    target: str | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], bytes]:
    return engine.handle_request(
        method="POST",
        target=target or payment_target(),
        headers={"content-type": "application/json", "x-request-id": request_id},
        raw_body=(compact_json({"externalId": external_id}) if body is None else body),
    )


def http_payment(
    origin: str,
    *,
    external_id: str = FIRST_EXTERNAL_ID,
    request_id: str = FIRST_REQUEST_ID,
) -> tuple[int, dict[str, object]]:
    response = urllib3.PoolManager(retries=False).request(
        "POST",
        origin + payment_target(),
        body=compact_json({"externalId": external_id}),
        headers={"Content-Type": "application/json", "X-Request-Id": request_id},
        redirect=False,
        retries=False,
        timeout=urllib3.Timeout(total=5),
        preload_content=True,
    )
    value = json.loads(response.data)
    assert isinstance(value, dict)
    return response.status, value


@contextmanager
def callback_server(
    *, during_delivery: Callable[[], None] | None = None
) -> Iterator[tuple[str, list[dict[str, object]]]]:
    deliveries: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            deliveries.append(
                {
                    "path": self.path,
                    "headers": {
                        name.lower(): value for name, value in self.headers.items()
                    },
                    "body": json.loads(body),
                }
            )
            if during_delivery is not None:
                during_delivery()
            self.send_response_only(204)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}", deliveries
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def wait_until_closed(origin: str) -> None:
    parsed = urllib.parse.urlsplit(origin)
    assert parsed.hostname is not None and parsed.port is not None
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            connection = socket.create_connection(
                (parsed.hostname, parsed.port), timeout=0.05
            )
        except OSError:
            return
        connection.close()
        time.sleep(0.02)
    raise AssertionError(f"carrier control remained reachable: {origin}")
