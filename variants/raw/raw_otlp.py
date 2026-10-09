"""Export native agent JSON events as opaque OTLP log bodies."""

import json
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen


def varint(value):
    output = bytearray()
    while value > 127:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def field(number, value):
    return varint(number << 3 | 2) + varint(len(value)) + value


def attribute(key, value):
    return field(1, key.encode()) + field(2, field(1, value.encode()))


class LogExporter:
    def __init__(self, evidence, core, model):
        self.evidence = Path(evidence)
        self.core = core
        self.model = model
        self.endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").rstrip("/")
        self.headers = dict(part.split("=", 1) for part in
                            os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "").split(",") if "=" in part)
        self.pending = []
        self.last_flush = time.monotonic()

    def add(self, line):
        if not self.endpoint:
            return
        try:
            event = json.loads(line)
            kind = str(event.get("type", "unknown")) if isinstance(event, dict) else "unknown"
        except ValueError:
            kind = "unparsed"
        if kind == "message_update":
            return  # Token deltas remain in events.jsonl; OTLP carries process transitions.
        self.pending.append(b"\x09" + int(time.time_ns()).to_bytes(8, "little") +
                            field(5, field(1, line.encode(errors="replace"))) +
                            field(6, attribute("event.type", kind)))
        if len(self.pending) >= 16 or time.monotonic() - self.last_flush >= 2:
            self.flush()

    def flush(self):
        if not self.pending or not self.endpoint:
            return
        try:
            resource = field(1, attribute("service.name", "raw-" + self.core)) + field(1, attribute("model", self.model))
            scope = field(1, field(1, b"raw-core-wrapper")) + b"".join(field(2, row) for row in self.pending)
            payload = field(1, field(1, resource) + field(2, scope))
            request = Request(self.endpoint + "/v1/logs", data=payload,
                              headers={"Content-Type": "application/x-protobuf", **self.headers})
            with urlopen(request, timeout=3) as response:
                if response.status != 200:
                    raise RuntimeError(f"OTLP HTTP {response.status}")
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}\n"
            try:
                with (self.evidence / "otlp-errors.log").open("a") as output:
                    output.write(message)
            except OSError as diagnostic_error:
                # Optional telemetry must not replace the native agent outcome.
                try:
                    sys.stderr.write(message + f"OTLP diagnostic write failed: {type(diagnostic_error).__name__}: {diagnostic_error}\n")
                except (OSError, ValueError):
                    pass
        finally:
            self.pending.clear()
            self.last_flush = time.monotonic()
