"""Local OTLP/HTTP protobuf receiver and durable, run-scoped batch store.

The payload is deliberately opaque. Its meaning belongs to the sender and to
the analysis program that reads it, not to the experiment controller.
"""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sqlite3
from threading import Lock, Thread
import time


SIGNALS = {"/v1/traces": "traces", "/v1/logs": "logs", "/v1/metrics": "metrics"}
MAX_BATCH_BYTES = 16 * 1024 * 1024


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=30)
    try:
        db.execute("PRAGMA busy_timeout=30000")
        yield db
        db.commit()
    except BaseException:
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


def list_batches(path, signal=None, since=None, until=None):
    clauses, parameters = [], []
    if signal:
        clauses.append("signal=?"); parameters.append(signal)
    if since is not None:
        clauses.append("received_at>=?"); parameters.append(since)
    if until is not None:
        clauses.append("received_at<?"); parameters.append(until)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(path) as db:
        rows = db.execute("SELECT id, signal, received_at, length(payload) FROM batches" + where +
                          " ORDER BY id", parameters)
        return [dict(id=row[0], signal=row[1], received_at=row[2], bytes=row[3]) for row in rows]


def read_batch(path, batch_id):
    with connect(path) as db:
        row = db.execute("SELECT signal, payload FROM batches WHERE id=?", (batch_id,)).fetchone()
    if row is None:
        raise KeyError(batch_id)
    return row


class Receiver(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.runs = {}
        self.runs_lock = Lock()

    def register(self, token, database):
        with self.runs_lock:
            self.runs[token] = database


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, message=b""):
        self.send_response(code)
        self.send_header("Content-Type", "application/x-protobuf" if code == 200 else "text/plain")
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def do_POST(self):
        signal = SIGNALS.get(self.path)
        if signal is None:
            return self.respond(404, b"unknown OTLP signal path")
        token = self.headers.get("x-experiment-token", "")
        with self.server.runs_lock:
            database = self.server.runs.get(token)
        if database is None:
            return self.respond(403, b"unknown run token")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/x-protobuf":
            return self.respond(415, b"OTLP/HTTP protobuf is required")
        if self.headers.get("Content-Encoding", "identity").lower() != "identity":
            return self.respond(415, b"compressed OTLP is unsupported")
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.respond(411, b"Content-Length is required")
        if not 0 <= size <= MAX_BATCH_BYTES:
            return self.respond(413, b"OTLP batch exceeds size limit")
        payload = self.rfile.read(size)
        if len(payload) != size:
            return self.respond(400, b"incomplete OTLP batch")
        try:
            with connect(database) as db:
                db.execute("INSERT INTO batches(signal, received_at, payload) VALUES (?, ?, ?)",
                           (signal, time.time(), payload))
        except sqlite3.Error as exc:
            return self.respond(500, str(exc).encode("utf-8", errors="replace"))
        # An empty Export*ServiceResponse is a valid protobuf response for all three signals.
        self.respond(200)

    def log_message(self, _format, *_args):
        pass


@contextmanager
def receiver(host="127.0.0.1"):
    server = Receiver((host, 0))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
