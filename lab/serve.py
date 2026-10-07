"""Single-process static Console, OTLP receiver and run Backend API."""
from __future__ import annotations

import gzip
import json
import mimetypes
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import otlp
from .backend import Backend


class App:
    def __init__(self, config: dict):
        self.config = config
        root = Path(config["service_root"]).resolve()
        self.backend = Backend(root, import_root=root / "imports")
        self.import_root = self.backend.import_root
        self.static = Path(config.get("static_root", "")).resolve() if config.get("static_root") else None
        self.max_batch = int(config.get("max_batch_bytes", otlp.DEFAULT_MAX_BATCH_BYTES))
        self.tokens = {str(k): str(v) for k, v in config.get("tokens", {}).items()}
        self.registration_token = config.get("registration_token")
        token_file = config.get("registration_token_file")
        if not self.registration_token and token_file:
            self.registration_token = Path(token_file).read_text().strip()
        self._braid_busy = set()
        self._braid_lock = threading.Lock()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._materialize_loop, name="braid-projection", daemon=True)
        if config.get("braid_worker", True):
            self._worker.start()

    def register(self, manifest):
        token = manifest.get("collector_token") if isinstance(manifest, dict) else None
        value = self.backend.register_manifest(manifest)
        if token:
            self.backend.bind_collector_token(value["run_id"], str(token))
            self.tokens[token] = value["run_id"]

    def _materialize_loop(self):
        while not self._stop.wait(30):
            for run in self.backend.runs(include_archived=True):
                run_id = run["run_id"]
                with self._braid_lock:
                    if run_id in self._braid_busy:
                        continue
                    self._braid_busy.add(run_id)
                projection = None
                try:
                    manifest = self.backend.run(run_id)
                    database = manifest.get("telemetry_database") or manifest.get("records", {}).get("telemetry")
                    if database and not Path(database).is_absolute():
                        root = self.backend._records_root(manifest)
                        value = Path(database)
                        database = str(root.parent / value if root and value.parts and value.parts[0] == root.name else (root / value if root else value))
                    projection_path = self.backend._record_path(manifest, "braid_projection")
                    projection = str(projection_path) if projection_path else None
                    if database and projection:
                        from sources.braid.viewer.reader import materialize
                        braid_run_id = manifest.get("braid_run_id") or manifest.get("native_run_id")
                        materialize(Path(database), Path(projection), braid=self.config.get("braid", "braid"), run_id=braid_run_id,
                                    experiment_run_id=run_id,
                                    cache=Path(projection).parent / "braid-cache")
                except (OSError, ValueError, KeyError, RuntimeError) as exc:
                    if projection:
                        error_path = Path(projection).with_name("braid-error.json")
                        error_path.write_text(json.dumps({"run_id": run_id, "error": f"{type(exc).__name__}: {exc}", "as_of": time.time()}))
                finally:
                    with self._braid_lock:
                        self._braid_busy.discard(run_id)


def _json(handler, value, status=200):
    body = json.dumps(value, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server: "Server"

    def do_GET(self):
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        parts = [part for part in parsed.path.split("/") if part]
        try:
            if parts[:2] == ["api", "runs"]:
                if len(parts) == 2:
                    return _json(self, self.server.app.backend.runs(include_archived=query.get("all", ["0"])[0] == "1"))
                run_id = parts[2]
                if len(parts) >= 4 and parts[3] == "braid":
                    return self._braid(run_id, parts[4:])
                if len(parts) >= 4 and parts[3] == "resources":
                    items = self.server.app.backend.record_listing(run_id, "resources") or self.server.app.backend.record_listing(run_id, "resource")
                    return _json(self, {"run_id": run_id, "items": items, "latest": self.server.app.backend.record_json(run_id, "resource-latest")})
                if len(parts) >= 4 and parts[3] == "logs":
                    return _json(self, {"run_id": run_id, "items": self.server.app.backend.record_listing(run_id, "logs")})
                if len(parts) >= 4 and parts[3] == "cost":
                    return _json(self, {"run_id": run_id, "items": self.server.app.backend.record_listing(run_id, "cost")})
                if len(parts) >= 4 and parts[3] == "evaluations":
                    return _json(self, {"run_id": run_id, "items": self.server.app.backend.record_listing(run_id, "evaluations")})
                return _json(self, self.server.app.backend.run(run_id))
            if parsed.path.startswith("/api/"):
                return _json(self, {"error": "unknown endpoint"}, 404)
            return self._static(parsed.path)
        except KeyError:
            _json(self, {"error": "run not found"}, 404)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _json(self, {"error": f"{type(exc).__name__}: {exc}"}, 400)

    def _braid(self, run_id, tail):
        manifest = self.server.app.backend.run(run_id)
        projection_path = self.server.app.backend._record_path(manifest, "braid_projection")
        projection = str(projection_path) if projection_path else None
        if projection and Path(projection).is_file():
            from sources.braid.viewer.reader import artifact_page, read_projection
            query = parse_qs(urlsplit(self.path).query)
            if tail and tail[0] in {"artifact", "body"}:
                name = query.get("name", [""])[0]
                artifact = next((item for item in read_projection(Path(projection)).get("artifacts", []) if item.get("file") == name), None)
                if not artifact:
                    return _json(self, {"error": "artifact not found"}, 404)
                return _json(self, artifact_page(Path(artifact["path"]), offset=int(query.get("offset", [0])[0]), bytes_=int(query.get("bytes", [65536])[0])))
            value = read_projection(Path(projection), cursor=int(query.get("cursor", [0])[0]), limit=int(query.get("limit", [50])[0]))
            return _json(self, value)
        return _json(self, {"run_id": run_id, "status": "not-persisted", "items": [], "coverage": "unknown"})

    def _static(self, path):
        root = self.server.app.static
        if not root:
            return _json(self, {"error": "static UI is not configured"}, 404)
        relative = Path(path.lstrip("/")) if path != "/" else Path("index.html")
        target = (root / relative).resolve()
        if not target.is_file() or not target.is_relative_to(root):
            target = root / "index.html"
        body = target.read_bytes()
        self.send_response(200)
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith(("text/", "application/javascript", "application/json")) else ""))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlsplit(self.path)
        if parsed.path in otlp.SIGNALS:
            return self._otlp(parsed.path)
        if parsed.path == "/api/runs/register":
            return self._register()
        if parsed.path == "/api/import":
            return self._import()
        return _json(self, {"error": "unknown endpoint"}, 404)

    def _otlp(self, path):
        token = self.headers.get("x-experiment-token", "")
        run_id = self.server.app.tokens.get(token) or self.server.app.backend.run_for_token(token)
        if not run_id:
            return _json(self, {"error": "unknown run token"}, 403)
        size = int(self.headers.get("Content-Length", "-1"))
        if size < 0 or size > self.server.app.max_batch:
            return _json(self, {"error": "invalid batch size"}, 413)
        wire = self.rfile.read(size)
        encoding = self.headers.get("Content-Encoding", "identity").lower()
        try:
            wire = otlp._decode(wire, encoding, self.server.app.max_batch)
        except OverflowError as exc:
            return _json(self, {"error": str(exc)}, 413)
        except ValueError as exc:
            return _json(self, {"error": str(exc)}, 400)
        signal = otlp.SIGNALS[path]
        manifest = self.server.app.backend.run(run_id)
        database_value = manifest.get("telemetry_database") or manifest.get("records", {}).get("telemetry")
        if not database_value:
            return _json(self, {"error": "run has no telemetry destination"}, 409)
        database = Path(database_value)
        if not database.is_absolute():
            root = self.server.app.backend._records_root(manifest)
            database = root.parent / database if root and database.parts and database.parts[0] == root.name else (root / database if root else database)
        try:
            otlp._protobuf_type(signal)().ParseFromString(wire)
        except Exception as exc:
            return _json(self, {"error": f"invalid protobuf: {exc}"}, 400)
        try:
            otlp.persist_batch(database, signal, wire, session=run_id, wire_bytes=size,
                               encoding=encoding)
        except sqlite3.Error as exc:
            return _json(self, {"error": f"{type(exc).__name__}: {exc}"}, 503)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _import(self):
        size = int(self.headers.get("Content-Length", "-1"))
        if size < 0 or size > 64 * 1024:
            return _json(self, {"error": "invalid request size"}, 413)
        try:
            body = json.loads(self.rfile.read(size))
            run_id = body["run_id"]
            source = (self.server.app.import_root / Path(body["source"]).name).resolve()
            if not source.is_dir() or not source.is_relative_to(self.server.app.import_root):
                raise ValueError("source must be a configured import directory")
            database = source / "telemetry.sqlite"
            if database.is_file():
                return _json(self, self.server.app.backend.import_database(run_id, database))
            return _json(self, self.server.app.backend.import_batches(run_id, source))
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _json(self, {"error": f"{type(exc).__name__}: {exc}"}, 400)

    def _register(self):
        if self.server.app.registration_token and self.headers.get("x-experiment-token") != self.server.app.registration_token:
            return _json(self, {"error": "registration token required"}, 403)
        size = int(self.headers.get("Content-Length", "-1"))
        if size < 0 or size > self.server.app.max_batch:
            return _json(self, {"error": "invalid request size"}, 413)
        try:
            payload = otlp._decode(self.rfile.read(size),
                                   self.headers.get("Content-Encoding", "identity").lower(),
                                   self.server.app.max_batch)
            body = json.loads(payload)
            manifest = body.get("manifest", body)
            if not isinstance(manifest, dict) or not manifest.get("run_id"):
                raise ValueError("manifest.run_id is required")
            collector_token = manifest.get("collector_token") or self.headers.get("x-collector-token")
            if isinstance(body.get("status"), dict):
                manifest = dict(manifest)
                manifest["status"] = body["status"]
            if isinstance(body.get("record_summaries"), dict):
                manifest = dict(manifest)
                manifest["record_summaries"] = body["record_summaries"]
            value = self.server.app.backend.register_manifest(manifest)
            if collector_token:
                self.server.app.backend.bind_collector_token(value["run_id"], str(collector_token))
                self.server.app.tokens[str(collector_token)] = value["run_id"]
            return _json(self, self.server.app.backend.brief(value), 201)
        except OverflowError as exc:
            return _json(self, {"error": str(exc)}, 413)
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
            return _json(self, {"error": f"{type(exc).__name__}: {exc}"}, 400)

    def log_message(self, *_args):
        pass


class Server(ThreadingHTTPServer):
    request_queue_size = 64

    def __init__(self, address, app):
        super().__init__(address, Handler)
        self.app = app
        self.daemon_threads = True
        self._slots = threading.BoundedSemaphore(int(app.config.get("max_workers", 32)))

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            request.close()
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()


def serve(config_path: Path):
    config = json.loads(Path(config_path).read_text())
    app = App(config)
    for manifest in config.get("manifests", []):
        app.register(manifest)
    server = Server((config.get("host", "127.0.0.1"), int(config.get("port", 8765))), app)
    print(json.dumps({"host": server.server_address[0], "port": server.server_address[1], "service_root": str(app.backend.root)}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
