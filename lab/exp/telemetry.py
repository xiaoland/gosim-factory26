"""Attempt-owned durable OTLP envelopes and identity-based transport ingestion."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
from threading import Thread, Lock
import time

from .core import atomic, record, read, canonical, Blocked
from lab.otlp import SIGNALS, _decode, _protobuf_type


@contextmanager
def database(path, *, readonly=False):
    path = Path(path)
    if readonly:
        db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    else:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(path, timeout=30)
        db.execute('PRAGMA synchronous=FULL')
    try:
        if not readonly:
            db.execute('CREATE TABLE IF NOT EXISTS batches (seq INTEGER PRIMARY KEY, metadata TEXT NOT NULL, payload BLOB NOT NULL, wire BLOB NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS errors (seq INTEGER PRIMARY KEY, metadata TEXT NOT NULL, wire BLOB NOT NULL)')
        yield db
        if not readonly:
            db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


class Collector:
    def __init__(self, directory, attempt_id, *, cap_bytes, max_batch_bytes=64 * 1024 * 1024):
        self.root = Path(directory) / 'telemetry'
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (self.root / 'binding.json').exists():
            raise Blocked('collector binding already exists; a lost epoch cannot be silently reopened')
        self.binding = record('stream', attempt_id=attempt_id, stream_id=secrets.token_hex(16),
                              collector_epoch=secrets.token_hex(16), opened_at=time.time())
        self.path = self.root / 'raw.sqlite'
        with database(self.path):
            pass
        self.cap = cap_bytes
        self.max_batch = max_batch_bytes
        self.lock = Lock()
        self.token = secrets.token_urlsafe(32)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.connection.settimeout(30)
                signal = SIGNALS.get(self.path)
                status, reason = 200, ''
                wire = b''
                try:
                    if self.headers.get('x-experiment-token') != owner.token:
                        status = 403
                        raise ValueError('unknown collector credential')
                    if signal is None:
                        status = 404
                        raise ValueError('unknown OTLP signal path')
                    if self.headers.get('Content-Type', '').split(';')[0] != 'application/x-protobuf':
                        status = 415
                        raise ValueError('OTLP/HTTP protobuf required')
                    try:
                        size = int(self.headers['Content-Length'])
                    except (TypeError, ValueError):
                        status = 411
                        raise ValueError('Content-Length required')
                    if size < 0 or size > owner.max_batch:
                        status = 413
                        raise ValueError('OTLP wire batch exceeds cap')
                    wire = self.rfile.read(size)
                    if len(wire) != size:
                        status = 400
                        raise ValueError('incomplete OTLP batch')
                    encoding = self.headers.get('Content-Encoding', 'identity').lower()
                    payload = _decode(wire, encoding, owner.max_batch)
                    _protobuf_type(signal)().ParseFromString(payload)
                    with owner.lock, database(owner.path) as db:
                        used = db.execute('SELECT COALESCE(SUM(length(payload)+length(wire)),0) FROM batches').fetchone()[0] + db.execute('SELECT COALESCE(SUM(length(metadata)+length(wire)),0) FROM errors').fetchone()[0]
                        if used + len(payload) + len(wire) > owner.cap:
                            status = 507
                            raise ValueError('attempt telemetry storage cap exhausted')
                        seq = db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM batches').fetchone()[0]
                        meta = record('batch', **{k: owner.binding[k] for k in ('attempt_id', 'stream_id', 'collector_epoch')},
                                      batch_seq=seq, signal=signal, received_at=time.time(),
                                      producer_timestamp=self.headers.get('x-producer-timestamp'),
                                      sha256=hashlib.sha256(payload).hexdigest(), wire_sha256=hashlib.sha256(wire).hexdigest(),
                                      bytes=len(payload), wire_bytes=len(wire), encoding=encoding)
                        db.execute('INSERT INTO batches VALUES (?,?,?,?)', (seq, json.dumps(meta), payload, wire))
                except Exception as exc:
                    status = status if status != 200 else (503 if isinstance(exc, (OSError, sqlite3.Error)) else 400)
                    reason = f'{type(exc).__name__}: {exc}'
                    try:
                        with owner.lock, database(owner.path) as db:
                            meta = record('receive_error', attempt_id=attempt_id, stream_id=owner.binding['stream_id'],
                                          collector_epoch=owner.binding['collector_epoch'], observed_at=time.time(),
                                          signal=signal, http_status=status, reason=reason,
                                          received_wire_bytes=len(wire), wire_sha256=hashlib.sha256(wire).hexdigest())
                            used = db.execute('SELECT COALESCE(SUM(length(payload)+length(wire)),0) FROM batches').fetchone()[0] + db.execute('SELECT COALESCE(SUM(length(metadata)+length(wire)),0) FROM errors').fetchone()[0]
                            if used + len(wire) + len(json.dumps(meta).encode()) > owner.cap:
                                raise OverflowError('receive-error storage cap exhausted; response is not acknowledged')
                            db.execute('INSERT INTO errors(metadata,wire) VALUES (?,?)', (json.dumps(meta), wire))
                    except Exception as persist_exc:
                        atomic(owner.root / 'persistence-error.json', record('receive_error', reason=str(persist_exc), original=reason))
                        status = 503
                body = b'' if status == 200 else reason.encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/x-protobuf' if status == 200 else 'text/plain')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        for signal in SIGNALS.values():
            _protobuf_type(signal)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = False
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.binding['receiver_endpoint'] = f'http://127.0.0.1:{self.server.server_port}'
        atomic(self.root / 'binding.json', self.binding)
        atomic(self.root / 'credential.json', {'token': self.token})
        self.thread.start()

    def environment(self):
        return {'OTEL_EXPORTER_OTLP_ENDPOINT': self.binding['receiver_endpoint'],
                'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/protobuf',
                'OTEL_EXPORTER_OTLP_HEADERS': f'x-experiment-token={self.token}'}

    def close(self, *, producer_flush='unknown'):
        self.server.shutdown()
        self.server.server_close()  # Joins in-flight handlers before sealing the durable cutoff.
        self.thread.join()
        with database(self.path) as db:
            last = db.execute('SELECT COALESCE(MAX(seq),0) FROM batches').fetchone()[0]
            errors = db.execute('SELECT COALESCE(MAX(seq),0) FROM errors').fetchone()[0]
        atomic(self.root / 'seal.json', record('collector_seal', **{k: self.binding[k] for k in ('attempt_id', 'stream_id', 'collector_epoch')},
                                             final_batch_seq=last, final_receive_error_seq=errors,
                                             producer_flush=producer_flush, sealed_at=time.time()))
        return read(self.root / 'seal.json')


def batches(attempt_dir, after=0, until=None):
    path = Path(attempt_dir) / 'telemetry/raw.sqlite'
    if not path.exists():
        return []
    with database(path, readonly=True) as db:
        rows = db.execute('SELECT metadata FROM batches WHERE seq>? AND (? IS NULL OR seq<=?) ORDER BY seq', (after, until, until))
        return [json.loads(row[0]) for row in rows]


def snapshot(attempt_dir):
    root = Path(attempt_dir) / 'telemetry'
    if not (root / 'binding.json').exists():
        return {'coverage': 'unavailable', 'collector_seal': 'unknown'}
    result = read(root / 'binding.json')
    with database(root / 'raw.sqlite', readonly=True) as db:
        result['last_batch_seq'] = db.execute('SELECT COALESCE(MAX(seq),0) FROM batches').fetchone()[0]
        result['last_receive_error_seq'] = db.execute('SELECT COALESCE(MAX(seq),0) FROM errors').fetchone()[0]
    result['seal'] = read(root / 'seal.json') if (root / 'seal.json').exists() else None
    result['coverage'] = 'sealed' if result['seal'] else 'open_or_lost'
    return result


def export(attempt_dir, destination, after=0, until=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    root = Path(attempt_dir) / 'telemetry'
    binding = read(root / 'binding.json')
    records, errors = [], []
    with database(root / 'raw.sqlite', readonly=True) as db:
        db.execute('BEGIN')
        for seq, text, payload, wire in db.execute('SELECT seq,metadata,payload,wire FROM batches WHERE seq>? AND (? IS NULL OR seq<=?) ORDER BY seq', (after, until, until)):
            meta = json.loads(text)
            meta['payload_file'] = f'{seq}.pb'
            meta['wire_file'] = f'{seq}.wire'
            (destination / meta['payload_file']).write_bytes(payload)
            (destination / meta['wire_file']).write_bytes(wire)
            records.append(meta)
        for text, seq, wire in db.execute('SELECT metadata,seq,wire FROM errors ORDER BY seq'):
            meta = json.loads(text) | {'receive_error_seq': seq, 'wire_file': f'error-{seq}.wire'}
            (destination / meta['wire_file']).write_bytes(wire)
            errors.append(meta)
    manifest = record('telemetry_transport', binding=binding, batches=records, receive_errors=errors,
                      seal=read(root / 'seal.json') if (root / 'seal.json').exists() else None,
                      exported_at=time.time())
    atomic(destination / 'manifest.json', manifest)
    return manifest


def _transport_member(root, value):
    from .core import member
    root = Path(root)
    if root.is_symlink():
        raise ValueError('telemetry transport root cannot redirect through a link')
    root = root.resolve(strict=True)
    path = root
    for part in Path(member(value)).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('telemetry transport member cannot traverse links')
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError('telemetry transport member is not an ordinary bounded file')
    return path


def ingest(destination, transport):
    """Consume source identities once; preserve mismatching retransfers as conflicts."""
    destination, transport = Path(destination), Path(transport)
    manifest = read(_transport_member(transport, 'manifest.json'))
    from .core import require, member
    require(manifest, 'telemetry_transport')
    destination.mkdir(parents=True, exist_ok=True)
    accepted, repeated, conflicts = [], [], []
    db = sqlite3.connect(destination / 'ingestion.sqlite', timeout=30)
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS batches(identity TEXT PRIMARY KEY, digest TEXT NOT NULL, metadata TEXT NOT NULL, payload BLOB NOT NULL, wire BLOB NOT NULL, ingested_at REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS transfers(digest TEXT PRIMARY KEY, manifest TEXT NOT NULL, ingested_at REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS receive_errors(identity TEXT PRIMARY KEY, metadata TEXT NOT NULL, wire BLOB NOT NULL, ingested_at REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS conflicts(identity TEXT, metadata TEXT, payload BLOB, wire BLOB, observed_at REAL)')
    try:
        db.execute('BEGIN IMMEDIATE')
        for meta in manifest['batches']:
            require(meta, 'batch')
            if any(meta[key] != manifest['binding'][key] for key in ('attempt_id', 'stream_id', 'collector_epoch')):
                raise ValueError('telemetry source batch does not bind its stream transport')
            identity = canonical([meta[k] for k in ('attempt_id', 'stream_id', 'collector_epoch', 'batch_seq')])
            payload = _transport_member(transport, meta['payload_file']).read_bytes()
            wire = _transport_member(transport, meta['wire_file']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != meta['sha256'] or hashlib.sha256(wire).hexdigest() != meta['wire_sha256']:
                raise ValueError(f'telemetry transport digest mismatch: {identity}')
            envelope_digest = canonical({k: v for k, v in meta.items() if k not in ('payload_file', 'wire_file')})
            previous = db.execute('SELECT digest FROM batches WHERE identity=?', (identity,)).fetchone()
            if previous and previous[0] != envelope_digest:
                db.execute('INSERT INTO conflicts VALUES (?,?,?,?,?)', (identity, json.dumps(meta), payload, wire, time.time()))
                conflicts.append(identity)
            elif previous:
                repeated.append(identity)
            else:
                db.execute('INSERT INTO batches VALUES (?,?,?,?,?,?)', (identity, envelope_digest, json.dumps(meta), payload, wire, time.time()))
                accepted.append(identity)
        for meta in manifest['receive_errors']:
            if any(meta[key] != manifest['binding'][key] for key in ('attempt_id', 'stream_id', 'collector_epoch')):
                raise ValueError('telemetry receive error does not bind its stream transport')
            wire = _transport_member(transport, meta['wire_file']).read_bytes()
            if hashlib.sha256(wire).hexdigest() != meta['wire_sha256']:
                raise ValueError('telemetry receive-error wire digest differs')
            identity = canonical([meta[k] for k in ('attempt_id', 'stream_id', 'collector_epoch', 'receive_error_seq')])
            previous = db.execute('SELECT metadata FROM receive_errors WHERE identity=?', (identity,)).fetchone()
            if previous and canonical(json.loads(previous[0])) != canonical(meta):
                db.execute('INSERT INTO conflicts VALUES (?,?,?,?,?)', (identity, json.dumps(meta), b'', wire, time.time()))
                conflicts.append(identity)
            elif not previous:
                db.execute('INSERT INTO receive_errors VALUES (?,?,?,?)', (identity, json.dumps(meta), wire, time.time()))
        db.execute('INSERT OR IGNORE INTO transfers VALUES (?,?,?)', (canonical(manifest), json.dumps(manifest), time.time()))
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    receipt = record('telemetry_ingestion', accepted=accepted, repeated=repeated, conflicts=conflicts,
                     ingested_at=time.time(), transport_sha256=canonical(manifest), seal=manifest.get('seal'))
    atomic(destination / ('ingestion-' + receipt['transport_sha256'] + '.json'), receipt)
    if conflicts:
        raise Blocked(f'conflicting source telemetry batches retained: {conflicts}')
    return receipt


def finalize_sources(attempt_dir):
    """Consume only the producer's explicit relative stream roots, with seals independent."""
    from .core import require, member, identifier, new_id
    root = Path(attempt_dir).resolve()
    sources = [{'name': 'supervisor', 'relative_path': '.'}]
    manifest_path = root / 'telemetry-sources.json'
    if manifest_path.exists():
        sources.extend(require(read(manifest_path), 'telemetry_sources')['sources'])
    destination = root / 'telemetry-transports'
    destination.mkdir(exist_ok=True)
    facts = []
    names = set()
    for source in sources:
        name = identifier(source['name'])
        if name in names:
            raise ValueError('telemetry source names must be unique')
        names.add(name)
        path = root / member(source['relative_path'])
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('telemetry source escapes attempt domain')
        if not (path / 'telemetry/binding.json').exists():
            facts.append({'name': name, 'coverage': 'unavailable'})
            continue
        state = snapshot(path)
        transport_path = destination / name
        if transport_path.exists():
            old = transport_path / 'manifest.json'
            previous = read(old) if old.exists() else {}
            if (previous.get('binding') == read(path / 'telemetry/binding.json') and previous.get('seal') == state.get('seal')
                    and max((row['batch_seq'] for row in previous.get('batches', [])), default=0) == state['last_batch_seq']
                    and max((row['receive_error_seq'] for row in previous.get('receive_errors', [])), default=0) == state['last_receive_error_seq']):
                manifest = previous
            else:
                transport_path = destination / (name + '-' + new_id('reentry'))
                manifest = export(path, transport_path)
        else:
            manifest = export(path, transport_path)
        facts.append({'name': name, 'snapshot': state, 'transport': str(transport_path.relative_to(root)),
                      'batch_count': len(manifest['batches'])})
    atomic(destination / 'sources.json', record('telemetry_sources', sources=facts, finalized_at=time.time()))
    return facts
