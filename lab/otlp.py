"""Run-scoped OTLP/HTTP protobuf receiver and raw SQLite batch store.

The collector validates only protocol envelopes. Agent semantics belong to
the producer and the analysis program.
"""

from contextlib import contextmanager
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import signal
from threading import Event, Lock, Thread
import time
import zlib

# The submission copies this receiver and its Python-only protobuf dependencies.
_bundled_deps = Path(__file__).resolve().parent / "otlp-deps"
if _bundled_deps.is_dir():
    sys.path.insert(0, str(_bundled_deps))
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


SIGNALS = {"/v1/traces": "traces", "/v1/logs": "logs", "/v1/metrics": "metrics"}
DEFAULT_MAX_BATCH_BYTES = 64 * 1024 * 1024


@contextmanager
def connect(path, *, readonly=False):
    path = Path(path).resolve()
    if readonly and not path.is_file():
        raise FileNotFoundError(path)
    db = sqlite3.connect(path.as_uri() + "?mode=ro" if readonly else path, uri=readonly, timeout=30)
    try:
        db.execute("PRAGMA busy_timeout=30000")
        yield db
        if not readonly:
            db.commit()
    except BaseException:
        if not readonly:
            db.rollback()
        raise
    finally:
        db.close()


def initialize(path):
    with connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS batches ("
                   "id INTEGER PRIMARY KEY, signal TEXT NOT NULL, received_at REAL NOT NULL, "
                   "payload BLOB NOT NULL)")
        db.execute("CREATE INDEX IF NOT EXISTS batches_signal_time "
                   "ON batches(signal, received_at)")
        db.execute("CREATE TABLE IF NOT EXISTS sessions ("
                   "id TEXT PRIMARY KEY, opened_at REAL NOT NULL, purpose TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS batch_meta ("
                   "batch_id INTEGER PRIMARY KEY, session_id TEXT, sha256 TEXT, "
                   "wire_bytes INTEGER, encoding TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS receive_errors ("
                   "id INTEGER PRIMARY KEY, session_id TEXT, observed_at REAL, signal TEXT, "
                   "http_status INTEGER, reason TEXT)")


def new_session(path, purpose="execution"):
    initialize(path)
    session = secrets.token_hex(12)
    with connect(path) as db:
        db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (session, time.time(), purpose))
    return session


def list_batches(path, signal=None, since=None, until=None, *, after_id=None, until_id=None, limit=None):
    clauses, parameters = [], []
    if signal:
        clauses.append("b.signal=?"); parameters.append(signal)
    if since is not None:
        clauses.append("b.received_at>=?"); parameters.append(since)
    if until is not None:
        clauses.append("b.received_at<?"); parameters.append(until)
    if after_id is not None:
        clauses.append("b.id>?"); parameters.append(after_id)
    if until_id is not None:
        clauses.append("b.id<=?"); parameters.append(until_id)
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("limit must be a positive integer")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(path, readonly=True) as db:
        has_meta = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='batch_meta'").fetchone()
        query = ("SELECT b.id, b.signal, b.received_at, length(b.payload)" +
                 (", m.session_id, m.sha256, m.wire_bytes, m.encoding" if has_meta else "") +
                 " FROM batches b" + (" LEFT JOIN batch_meta m ON m.batch_id=b.id" if has_meta else "") +
                 where + " ORDER BY b.id")
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)
        rows = db.execute(query, parameters)
        names = ("id", "signal", "received_at", "bytes", "session_id", "sha256", "wire_bytes", "encoding")
        return [dict(zip(names if has_meta else names[:4], row)) for row in rows]


def database_for_run(run):
    """Prefer the archived local collector when a packaged Braid run produced one."""
    run = Path(run).resolve()
    if (run / "native/manifest.json").is_file():
        return run / "telemetry.sqlite"
    candidates = [path.resolve() for stage in ("official-generation", "official", "official-evaluation")
                  for path in (run / "workspace" / stage / "template" / ".factory26").glob("*/telemetry.sqlite")]
    if any(not path.is_relative_to(run) for path in candidates):
        raise ValueError("archived telemetry database escapes run directory")
    if len(candidates) > 1:
        raise ValueError("multiple archived telemetry databases; select the generation run directly")
    return candidates[0] if candidates else run / "telemetry.sqlite"


def read_batch(path, batch_id):
    with connect(path, readonly=True) as db:
        row = db.execute("SELECT signal, payload FROM batches WHERE id=?", (batch_id,)).fetchone()
    if row is None:
        raise KeyError(batch_id)
    return row


def list_receive_errors(path, *, after_id=0, limit=None):
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("error limit must be a positive integer")
    with connect(path, readonly=True) as db:
        try:
            query = ("SELECT id, session_id, observed_at, signal, http_status, reason "
                     "FROM receive_errors WHERE id>? ORDER BY id")
            params = [after_id]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            rows = db.execute(query, params)
            return [dict(zip(("id", "session_id", "observed_at", "signal", "http_status", "reason"), row))
                    for row in rows]
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return []
            raise


def export_batches(path, output, *, signal=None, after_id=None, until_id=None, limit=None):
    """One read transaction fixes the batch list and bytes while writers continue."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with connect(path, readonly=True) as db:
        db.execute("BEGIN")
        filters, args = [], []
        if signal:
            filters.append("signal=?"); args.append(signal)
        if after_id is not None:
            filters.append("id>?"); args.append(after_id)
        if until_id is not None:
            filters.append("id<=?"); args.append(until_id)
        query = "SELECT id, signal, received_at, payload FROM batches"
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY id"
        if limit is not None:
            if type(limit) is not int or limit < 1:
                raise ValueError("limit must be positive")
            query += " LIMIT ?"
            args.append(limit)
        records = []
        for batch_id, batch_signal, received_at, payload in db.execute(query, args):
            name = f"{batch_id:08d}-{batch_signal}.pb"
            (output / name).write_bytes(payload)
            records.append({"id": batch_id, "signal": batch_signal, "received_at": received_at,
                            "file": name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
    (output / "manifest.json").write_text(json.dumps({"batches": records}, indent=2) + "\n")
    return records


def _protobuf_type(signal):
    if signal == "traces":
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
        return ExportTraceServiceRequest
    if signal == "logs":
        from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
        return ExportLogsServiceRequest
    from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
    return ExportMetricsServiceRequest


def _decode(payload, encoding, limit):
    if encoding == "identity":
        return payload
    if encoding != "gzip":
        raise ValueError(f"unsupported content encoding: {encoding}")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        body = decoder.decompress(payload, limit + 1)
        if len(body) > limit or decoder.unconsumed_tail:
            raise OverflowError("decompressed OTLP batch exceeds size limit")
        body += decoder.flush(limit + 1 - len(body))
    except zlib.error as exc:
        raise ValueError(f"invalid gzip body: {exc}") from exc
    if len(body) > limit:
        raise OverflowError("decompressed OTLP batch exceeds size limit")
    if not decoder.eof:
        raise ValueError("incomplete gzip body")
    return body


class Receiver(ThreadingHTTPServer):
    daemon_threads = False

    def __init__(self, address, *, max_batch_bytes=DEFAULT_MAX_BATCH_BYTES, read_timeout=30):
        super().__init__(address, Handler)
        self.runs = {}
        self.runs_lock = Lock()
        self.max_batch_bytes = max_batch_bytes
        self.read_timeout = read_timeout

    def register(self, token, database, session=None):
        with self.runs_lock:
            self.runs[token] = (database, session)


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(self.server.read_timeout)

    @contextmanager
    def measure(self, stage):
        self._stage = stage
        started = time.monotonic()
        try:
            yield
        finally:
            self._timing[f"{stage}_ms"] = round((time.monotonic() - started) * 1000, 3)

    def respond(self, code, message=""):
        self._timing["http_status"] = code
        with self.measure("response_write"):
            if code == 200:
                body = b""  # Empty Export*ServiceResponse is valid for every signal.
            else:
                from google.rpc.status_pb2 import Status
                grpc_code = {400: 3, 403: 16, 404: 12, 411: 3, 413: 8, 415: 12, 503: 14}.get(code, 13)
                body = Status(code=grpc_code, message=message).SerializeToString()
            self.send_response(code)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def reject(self, code, reason, signal=None, binding=None):
        self._timing["failure_stage"] = self._stage
        if binding is not None:
            database, session = binding
            try:
                with connect(database) as db:
                    db.execute("INSERT INTO receive_errors (session_id, observed_at, signal, http_status, reason) "
                               "VALUES (?, ?, ?, ?, ?)", (session, time.time(), signal, code, reason))
            except (OSError, sqlite3.Error) as exc:
                print(f"OTLP receive diagnostic could not persist: {exc}; original: {reason}", file=sys.stderr)
        else:
            print(f"OTLP unassigned receive error {code}: {reason}", file=sys.stderr)
        self.respond(code, reason)

    def do_POST(self):
        started = time.monotonic()
        self._stage = "validation"
        self._timing = {"event": "otlp_request_timing", "started_at": time.time(),
                        "signal": SIGNALS.get(self.path), "session_id": None,
                        "wire_bytes": None, "payload_bytes": None, "batch_id": None,
                        "http_status": None, "failure_stage": None,
                        "read_ms": None, "decode_ms": None, "persist_ms": None,
                        "response_write_ms": None}
        try:
            return self._receive_post()
        except BaseException:
            self._timing["failure_stage"] = self._stage
            raise
        finally:
            self._timing["finished_at"] = time.time()
            self._timing["total_ms"] = round((time.monotonic() - started) * 1000, 3)
            try:
                sys.stderr.write(json.dumps(self._timing, separators=(",", ":")) + "\n")
                sys.stderr.flush()
            except Exception:
                pass  # Logging must not change the OTLP response or mask its original error.

    def _receive_post(self):
        signal = self._timing["signal"]
        if signal is None:
            return self.reject(404, "unknown OTLP signal path")
        token = self.headers.get("x-experiment-token", "")
        with self.server.runs_lock:
            binding = self.server.runs.get(token)
        if binding is None:
            return self.reject(403, "unknown run token", signal)
        self._timing["session_id"] = binding[1]
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/x-protobuf":
            return self.reject(415, "OTLP/HTTP protobuf is required", signal, binding)
        encoding = self.headers.get("Content-Encoding", "identity").lower()
        if encoding not in ("identity", "gzip"):
            return self.reject(415, f"unsupported content encoding: {encoding}", signal, binding)
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.reject(411, "Content-Length is required", signal, binding)
        if size < 0 or size > self.server.max_batch_bytes:
            return self.reject(413, "OTLP batch exceeds size limit", signal, binding)
        try:
            with self.measure("read"):
                wire = self.rfile.read(size)
        except TimeoutError:
            return self.reject(400, "OTLP body read timed out", signal, binding)
        self._timing["wire_bytes"] = len(wire)
        if len(wire) != size:
            return self.reject(400, "incomplete OTLP batch", signal, binding)
        try:
            with self.measure("decode"):
                from google.protobuf.message import DecodeError
                payload = _decode(wire, encoding, self.server.max_batch_bytes)
                self._timing["payload_bytes"] = len(payload)
                _protobuf_type(signal)().ParseFromString(payload)
        except OverflowError as exc:
            return self.reject(413, str(exc), signal, binding)
        except (ValueError, DecodeError) as exc:
            return self.reject(400, f"invalid OTLP envelope: {exc}", signal, binding)
        database, session = binding
        try:
            with self.measure("persist"):
                with connect(database) as db:
                    cursor = db.execute("INSERT INTO batches(signal, received_at, payload) VALUES (?, ?, ?)",
                                        (signal, time.time(), payload))
                    db.execute("INSERT INTO batch_meta VALUES (?, ?, ?, ?, ?)",
                               (cursor.lastrowid, session, hashlib.sha256(payload).hexdigest(), len(wire), encoding))
        except (OSError, sqlite3.Error) as exc:
            return self.reject(503, f"OTLP persistence failed: {exc}", signal, binding)
        self._timing["batch_id"] = cursor.lastrowid
        self.respond(200)

    def log_message(self, _format, *_args):
        pass


@contextmanager
def receiver(host="127.0.0.1", *, max_batch_bytes=DEFAULT_MAX_BATCH_BYTES, read_timeout=30):
    for signal in SIGNALS.values():
        _protobuf_type(signal)  # Fail startup when protocol dependencies are unavailable.
    from google.rpc.status_pb2 import Status  # noqa: F401
    server = Receiver((host, 0), max_batch_bytes=max_batch_bytes, read_timeout=read_timeout)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def serve_run(run):
    """Serve one generation run; stdout's first line is a private parent-process handshake."""
    run = Path(run).resolve(strict=True)
    database = run / "telemetry.sqlite"
    session = new_session(database, "generation")
    token = secrets.token_urlsafe(24)
    with receiver() as server:
        server.register(token, database, session)
        stopped = Event()
        signal.signal(signal.SIGTERM, lambda *_: stopped.set())
        print(json.dumps({"endpoint": f"http://127.0.0.1:{server.server_port}",
                          "token": token, "session": session}), flush=True)
        try:
            stopped.wait()
        except KeyboardInterrupt:
            pass
    with connect(database) as db:
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve-run", type=Path, required=True)
    serve_run(parser.parse_args().serve_run)
