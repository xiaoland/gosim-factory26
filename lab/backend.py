"""Small run-record Backend used by ``lab serve``.

The Backend owns only durable run metadata and OTLP batches.  Variant/native
files remain producer-owned and are exposed through manifest links.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import os
import sqlite3
from pathlib import Path
from threading import Lock
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from . import otlp


_PUBLIC_MANIFEST_FIELDS = {
    "run_id", "label", "variant", "harness", "target", "task", "stage", "route",
    "competition", "program_version", "source_run", "lifecycle", "archived", "braid_run_id",
    "model_recipe", "model_routes",
}
_PUBLIC_STATUS_FIELDS = {
    "lifecycle", "activity", "brief", "last_activity_at", "as_of", "observed_at", "reason",
    "evidence", "native", "spend", "resource", "resources", "cost", "coverage", "error",
}


class BackendHTTPError(RuntimeError):
    """Bounded remote response diagnostic without copying response headers."""
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail
        super().__init__(f"Console HTTP {status}: {detail}")


def _portable_value(value):
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if (normalized in {"token", "collector_token", "registration_token", "secret",
                               "secret_value", "api_key", "environment", "env", "config_env"}
                    or normalized.endswith("_token") or normalized.endswith("_secret")
                    or normalized.endswith("_token_file") or normalized.endswith("_secret_file")):
                continue
            if normalized in {"path", "source", "run_root", "workspace", "harness", "records"} and isinstance(child, str) and child.startswith("/"):
                continue
            result[key] = _portable_value(child)
        return result
    if isinstance(value, list):
        return [_portable_value(child) for child in value]
    return value


def publish_run(service_url: str, manifest: dict, *, status=None, records=None,
                token=None, collector_token=None, timeout=15) -> dict:
    """Publish one saved run/status snapshot to a configured Console Backend.

    Only the manifest identity and explicitly supplied record summaries cross
    the wire; producer-local absolute paths are removed from the portable copy.
    """
    portable = {key: manifest[key] for key in _PUBLIC_MANIFEST_FIELDS if key in manifest}
    portable = _portable_value(portable)
    safe_status = _portable_value({key: status[key] for key in _PUBLIC_STATUS_FIELDS
                                   if isinstance(status, dict) and key in status}) if isinstance(status, dict) else None
    body = {"manifest": portable}
    if safe_status is not None:
        body["status"] = safe_status
    if isinstance(records, dict):
        body["record_summaries"] = _portable_value({key: records[key] for key in
                                                     {"resources", "resource-latest", "logs", "cost", "evaluations", "result-save", "automatic-evaluations", "workspace"}
                                                     if key in records})
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip"}
    if token:
        headers["x-experiment-token"] = token
    if collector_token:
        headers["x-collector-token"] = collector_token
    request = Request(service_url.rstrip("/") + "/api/runs/register",
                      data=gzip.compress(json.dumps(body, ensure_ascii=False).encode(), compresslevel=1),
                      headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        detail = exc.read(16 * 1024).decode("utf-8", errors="replace")
        raise BackendHTTPError(exc.code, detail) from exc


def register_run(service_url: str, manifest: dict, *, registration_token: str,
                 collector_token: str, status=None, records=None, timeout=15) -> dict:
    """Register one run and return the producer-only OTLP environment.

    Tokens are used in request headers and returned only to the caller for
    process environment assembly; they are never included in the manifest or
    the returned Console row.
    """
    if not collector_token:
        raise ValueError("collector_token is required for per-run binding")
    row = publish_run(service_url, manifest, status=status, records=records,
                      token=registration_token, collector_token=collector_token,
                      timeout=timeout)
    collector_url = service_url.rstrip("/")
    return {"run_id": row.get("run_id") or manifest.get("run_id"),
            "collector_url": collector_url,
            # Producers append /v1/{traces,logs,metrics} themselves.
            "otlp_endpoint": collector_url,
            "otlp_protocol": "http/protobuf",
            "otlp_headers": "x-experiment-token=" + collector_token,
            "console": row}


def saved_record_summaries(run: str | Path) -> dict:
    """Read the producer's bounded saved facts for one publish operation.

    This deliberately consumes records/status.json and producer-owned native,
    resource and cost records; it never polls a provider or enters a live DB.
    """
    root = Path(run).expanduser().resolve()
    records = root / "records"
    result = {}
    for name in ("status", "resource-latest", "cost", "evaluations", "automatic-evaluations", "result-save"):
        path = records / f"{name}.json"
        if path.is_file():
            try:
                result[name] = json.loads(path.read_text())
            except (OSError, ValueError) as exc:
                result[name] = {"source": str(path), "error": f"{type(exc).__name__}: {exc}"}
    for name in ("resources", "cost"):
        directory = records / name
        if directory.is_dir():
            result[name] = []
            for path in sorted(directory.glob("*.json"))[:500]:
                try:
                    result[name].append(json.loads(path.read_text()))
                except (OSError, ValueError) as exc:
                    result[name].append({"source": str(path), "error": f"{type(exc).__name__}: {exc}"})
    # Logs are facts for the Console, but never ship an unbounded transcript.
    log_paths = sorted(set(records.glob("*.log")) | set((records / "logs").glob("*.log")) |
                       set(root.glob("*.log")) | set(root.glob("stdout*.log")) |
                       set(root.glob("stderr*.log")))
    state = json.loads((root / 'manifest.json').read_text())
    if state.get('native_scope_id'):
        producer = root / 'data/harness' / state['native_scope_id'] / 'producers' / state['run_id']
        log_paths = sorted(set(log_paths) | set(producer.glob('*.log')))
    for path in log_paths[:32]:
        try:
            with path.open('rb') as stream:
                size = stream.seek(0, 2)
                stream.seek(max(0, size - 65536))
                data = stream.read(65536).decode(errors='replace')
            result.setdefault("logs", []).append({"source": str(path.relative_to(root)), "bytes": size,
                                                    "tail": data, "truncated": size > 65536})
        except OSError as exc:
            result.setdefault("logs", []).append({"source": str(path.relative_to(root)), "bytes": None,
                                                   "error": f"{type(exc).__name__}: {exc}"})
    saved = result.get("result-save") or {}
    if saved.get("saved") is True:
        workspace = root / "data/workspace"
        files, errors = [], []
        if not workspace.is_dir():
            errors.append("saved workspace directory is missing")
        excluded = {".git", "node_modules", ".factory26"}
        def read_error(exc):
            errors.append(f"{type(exc).__name__}: {exc}")
        for directory, dirs, names in os.walk(workspace, onerror=read_error, followlinks=False):
            dirs[:] = sorted(name for name in dirs if name not in excluded)
            for name in sorted(names):
                path = Path(directory) / name
                try:
                    files.append({"path": str(path.relative_to(workspace)),
                                  "bytes": path.lstat().st_size, "symlink": path.is_symlink()})
                except OSError as exc:
                    read_error(exc)
                if len(files) > 500:
                    break
            if len(files) > 500:
                break
        result["workspace"] = {"source": "data/workspace", "as_of": saved.get("as_of"),
                               "storage_root": saved.get("storage_root"), "files": files[:500],
                               "truncated": len(files) > 500, "excluded_directories": sorted(excluded),
                               "errors": errors, "contents_available": False}
    return result


def publish_saved_run(service_url: str, run: str | Path, *, token=None,
                      collector_token=None, timeout=15) -> dict:
    """Publish the current saved manifest/status snapshot without live polling."""
    root = Path(run).expanduser().resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    summaries = saved_record_summaries(root)
    return publish_run(service_url, manifest, status=summaries.get("status"),
                       records=summaries, token=token,
                       collector_token=collector_token, timeout=timeout)


class Backend:
    def __init__(self, root: Path, *, import_root: Path | None = None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "backend.sqlite"
        self.import_root = Path(import_root or self.root / "imports").resolve()
        self.import_root.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, manifest TEXT NOT NULL, registered_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS projections (run_id TEXT PRIMARY KEY, payload TEXT NOT NULL, published_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS collector_tokens (run_id TEXT PRIMARY KEY, token TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS imported_batches ("
                       "run_id TEXT NOT NULL, source_digest TEXT NOT NULL, source_batch_id INTEGER NOT NULL, "
                       "target_batch_id INTEGER, imported_at REAL NOT NULL, PRIMARY KEY(run_id, source_digest, source_batch_id))")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=30)
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def register_manifest(self, manifest: Path | dict) -> dict:
        value = json.loads(Path(manifest).read_text()) if isinstance(manifest, (str, Path)) else dict(manifest)
        run_id = value.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id in {".", ".."} or any(char in run_id for char in "/\\\x00\n\r"):
            raise ValueError("manifest.run_id is required")
        value.pop("collector_token", None)
        # A portable producer manifest has no Mac/runner paths. The service
        # owns its copy of records and telemetry, so OTLP always has a local
        # destination even when the producer only publishes status summaries.
        run_root = self.root / "runs" / run_id
        records_root = run_root / "records"
        records_root.mkdir(parents=True, exist_ok=True)
        records = dict(value.get("records") or {})
        records["root"] = str(records_root)
        value["records"] = records
        value.setdefault("telemetry_database", str(records_root / "telemetry.sqlite"))
        records.setdefault("braid_projection", str(records_root / "braid-projection.json"))
        now = time.time()
        with self._lock, self._connect() as db:
            db.execute("INSERT INTO runs(run_id,manifest,registered_at) VALUES(?,?,?) ON CONFLICT(run_id) DO UPDATE SET manifest=excluded.manifest", (run_id, json.dumps(value, ensure_ascii=False), now))
        return value

    def bind_collector_token(self, run_id: str, token: str):
        if not token:
            return
        with self._lock, self._connect() as db:
            db.execute("INSERT INTO collector_tokens(run_id,token) VALUES(?,?) ON CONFLICT(run_id) DO UPDATE SET token=excluded.token", (run_id, token))

    def run_for_token(self, token: str):
        with self._connect() as db:
            row = db.execute("SELECT run_id FROM collector_tokens WHERE token=?", (token,)).fetchone()
        return row[0] if row else None

    def runs(self, *, include_archived=False):
        with self._connect() as db:
            rows = db.execute("SELECT run_id,manifest FROM runs ORDER BY registered_at DESC").fetchall()
        result = []
        for run_id, raw in rows:
            manifest = json.loads(raw)
            saved_status = {}
            status_path = self._record_path(manifest, "status")
            if status_path and status_path.is_file():
                try:
                    saved_status = json.loads(status_path.read_text())
                    if isinstance(saved_status, dict):
                        manifest["status"] = saved_status
                except (OSError, ValueError) as exc:
                    manifest["status_error"] = f"{type(exc).__name__}: {exc}"
            lifecycle = saved_status.get("lifecycle") or manifest.get("lifecycle")
            archived = saved_status.get("archived") if "archived" in saved_status else manifest.get("archived")
            if not include_archived and (archived or lifecycle == "completed"):
                continue
            result.append(self.brief(manifest))
        return result

    @staticmethod
    def brief(manifest):
        status = manifest.get("status") if isinstance(manifest.get("status"), dict) else {}
        run_id = manifest.get("run_id")
        return {"id": run_id, "run_id": run_id, "label": manifest.get("label") or run_id,
                "harness": manifest.get("harness") or manifest.get("variant") or "unknown",
                "mode": "archive" if status.get("archived", manifest.get("archived")) else "live",
                "writable": False, "controllable": False,
                "coverage": status.get("coverage", manifest.get("coverage", [])), "read_check": "saved-archive",
                "access_error": None} | {key: manifest.get(key) for key in ("variant", "target", "task", "stage", "lifecycle", "archived") if key in manifest} | {
            "lifecycle": status.get("lifecycle", manifest.get("lifecycle")),
            "archived": status.get("archived", manifest.get("archived", False)),
            "activity": status.get("activity"), "as_of": status.get("as_of"), "reason": status.get("error")
        }

    def run(self, run_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT manifest FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        manifest = json.loads(row[0])
        status_path = self._record_path(manifest, "status")
        if status_path and status_path.is_file():
            try:
                manifest["status"] = json.loads(status_path.read_text())
            except (OSError, ValueError) as exc:
                manifest["status_error"] = f"{type(exc).__name__}: {exc}"
        return manifest

    @staticmethod
    def _records_root(manifest):
        records = manifest.get("records")
        if isinstance(records, dict) and records.get("root"):
            return Path(records["root"]).resolve()
        if isinstance(manifest.get("run_root"), str):
            return (Path(manifest["run_root"]).resolve() / "records")
        return None

    def record_json(self, run_id: str, name: str, default=None):
        manifest = self.run(run_id)
        path = self._record_path(manifest, name)
        if path is None:
            root = self._records_root(manifest)
            path = root / f"{name}.json" if root else None
        if path is None or not path.is_file():
            summaries = manifest.get("record_summaries") if isinstance(manifest.get("record_summaries"), dict) else {}
            if name == "resource-latest" and "resources" in summaries:
                value = summaries["resources"]
                return value[-1] if isinstance(value, list) and value else value
            return summaries.get(name, default)
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            return {"status": "unknown", "error": f"{type(exc).__name__}: {exc}", "source": str(path)}

    def record_listing(self, run_id: str, name: str, *, limit=100):
        manifest = self.run(run_id)
        root = self._records_root(manifest)
        rows = []
        cap = min(max(int(limit), 1), 500)
        directory = root / name if root else None
        paths = []
        if directory and directory.is_dir():
            paths.extend(sorted(directory.glob("*.json")) + sorted(directory.glob("*.jsonl")))
        if root and name == "logs":
            paths.extend(sorted(root.glob("*.log")) + sorted(root.glob("logs-*.txt")))
        if root and name == "cost":
            paths.extend(path for path in (root / "cost.json", root / "cost.jsonl") if path.is_file())
        if root:
            paths.extend(path for path in (root / f"{name}.json", root / f"{name}.jsonl") if path.is_file())
        if not paths:
            summary = manifest.get("record_summaries", {}).get(name) if isinstance(manifest.get("record_summaries"), dict) else None
            status = manifest.get("status") if isinstance(manifest.get("status"), dict) else {}
            if name in {"resources", "resource"} and status.get("resources") is not None:
                return [{"kind": "resources", "source": "records/status.json", "data": status["resources"]},
                        {"kind": "native", "source": "records/status.json", "data": status.get("native")}]
            if name == "cost" and status.get("spend") is not None:
                spend = status["spend"]
                if isinstance(spend, dict):
                    return [{"kind": "spend", "status": spend.get("status", "unknown"),
                             "amount": spend.get("value", spend.get("cost")),
                             "currency": spend.get("currency"), "source": "records/status.json",
                             "scope": spend.get("scope"), "kind": spend.get("kind", "provider-account-window"),
                             "as_of": spend.get("as_of"), "reason": spend.get("reason"),
                             "note": spend.get("note"), "data": spend}]
            if name == "cost":
                return [{"kind": "spend", "status": "unknown", "source": "records/status.json", "scope": None,
                         "kind": "provider-account-window", "as_of": None, "reason": None,
                         "note": "未保存 spend 事实；不能从运行生命周期推导费用"}]
            if summary is None and name == "evaluations" and isinstance(manifest.get("record_summaries"), dict):
                summary = manifest["record_summaries"].get("automatic-evaluations")
            if isinstance(summary, list):
                return summary[:cap]
            if summary is not None:
                return [summary]
        for path in paths[:cap]:
            try:
                if path.suffix in {".jsonl", ".log", ".txt"}:
                    for line in path.read_text().splitlines()[:cap - len(rows)]:
                        if line.strip():
                            try:
                                rows.append(json.loads(line))
                            except ValueError:
                                rows.append({"source": str(path), "line": line[:4000]})
                else:
                    rows.append(json.loads(path.read_text()))
            except (OSError, ValueError) as exc:
                rows.append({"source": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return rows

    def _record_path(self, manifest, name):
        path = manifest.get("records", {}).get(name) if isinstance(manifest.get("records"), dict) else None
        if not path:
            return None
        path = Path(path)
        if not path.is_absolute():
            root = self._records_root(manifest)
            if root and path.parts and path.parts[0] == root.name:
                path = root.parent / path
            else:
                path = root / path if root else path
        return path.resolve()

    def batches(self, run_id, *, after=0, limit=100):
        manifest = self.run(run_id)
        database = manifest.get("telemetry_database") or manifest.get("records", {}).get("telemetry")
        if not database:
            return []
        path = Path(database)
        if not path.is_absolute():
            root = self._records_root(manifest)
            path = root.parent / path if root and path.parts and path.parts[0] == root.name else (root / path if root else path)
        if not path.is_file():
            return []
        return otlp.list_batches(path, after_id=after, limit=min(max(int(limit), 1), 500))

    def import_batches(self, run_id: str, source: Path) -> dict:
        """Import numbered ``*-{signal}.pb`` files idempotently into a run DB."""
        manifest = self.run(run_id)
        database_value = manifest.get("telemetry_database") or manifest.get("records", {}).get("telemetry")
        if not database_value:
            raise ValueError("manifest has no telemetry destination")
        database = Path(database_value)
        if not database.is_absolute():
            root = self._records_root(manifest)
            database = root.parent / database if root and database.parts and database.parts[0] == root.name else (root / database if root else database)
        otlp.initialize(database)
        imported = 0
        conflicts = []
        for path in sorted(Path(source).glob("*.pb")):
            name = path.name
            signal = next((s for s in ("traces", "logs", "metrics") if name.endswith(f"-{s}.pb")), None)
            if not signal:
                continue
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            # Historical imports may carry the producer timestamp between the
            # batch id and signal (``0001-1791124180.12-logs.pb``).
            parts = path.stem.split("-")
            received_at = float(parts[-2]) if len(parts) >= 3 else time.time()
            with self._lock, otlp.connect(database) as db:
                prior = db.execute("SELECT batch_id,sha256 FROM batch_meta WHERE sha256=?", (digest,)).fetchone()
                if prior:
                    continue
                db.execute("INSERT INTO batches(signal,received_at,payload) VALUES(?,?,?)", (signal, received_at, payload))
                batch_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                db.execute("INSERT INTO batch_meta(batch_id,sha256,wire_bytes,encoding) VALUES(?,?,?,?)", (batch_id, digest, len(payload), "identity"))
                imported += 1
        return {"run_id": run_id, "imported": imported, "conflicts": conflicts}

    def import_database(self, run_id: str, source: Path) -> dict:
        """Import a Hosted raw SQLite collector snapshot without its UI."""
        source = Path(source).resolve(strict=True)
        source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        imported = 0
        skipped = 0
        errors = []
        after_id = 0
        target = self.run(run_id)
        database = Path(target["telemetry_database"])
        otlp.initialize(database)
        with otlp.connect(database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS imported_source_batches ("
                       "source_digest TEXT NOT NULL, source_batch_id INTEGER NOT NULL, "
                       "target_batch_id INTEGER NOT NULL, imported_at REAL NOT NULL, "
                       "PRIMARY KEY(source_digest, source_batch_id))")
        while True:
            batches = otlp.list_batches(source, after_id=after_id, limit=500)
            if not batches:
                break
            for batch in batches:
                source_id = int(batch["id"])
                after_id = source_id
                try:
                    payload = otlp.read_batch(source, source_id)[1]
                    with otlp.connect(database) as db:
                        prior = db.execute("SELECT target_batch_id FROM imported_source_batches WHERE source_digest=? AND source_batch_id=?",
                                           (source_digest, source_id)).fetchone()
                        if prior:
                            skipped += 1
                            continue
                        digest = hashlib.sha256(payload).hexdigest()
                        duplicate = db.execute("SELECT batch_id FROM batch_meta WHERE sha256=?", (digest,)).fetchone()
                        if duplicate:
                            target_id = duplicate[0]
                        else:
                            cursor = db.execute("INSERT INTO batches(signal,received_at,payload) VALUES(?,?,?)",
                                                (batch["signal"], batch["received_at"], payload))
                            target_id = cursor.lastrowid
                            db.execute("INSERT INTO batch_meta VALUES(?,?,?,?,?)",
                                       (target_id, batch.get("session_id"), digest,
                                        batch.get("wire_bytes") or len(payload), batch.get("encoding") or "identity"))
                        db.execute("INSERT INTO imported_source_batches VALUES(?,?,?,?)",
                                   (source_digest, source_id, target_id, time.time()))
                    with self._lock, self._connect() as db:
                        db.execute("INSERT OR IGNORE INTO imported_batches VALUES(?,?,?,?,?)",
                                   (run_id, source_digest, source_id, target_id, time.time()))
                    imported += 1
                except Exception as exc:
                    errors.append({"source": str(source), "source_digest": source_digest,
                                   "source_batch_id": source_id, "error": f"{type(exc).__name__}: {exc}"})
            if len(batches) < 500:
                break
        return {"run_id": run_id, "imported": imported, "skipped": skipped,
                "source": str(source), "source_digest": source_digest, "errors": errors,
                "complete": not errors}
