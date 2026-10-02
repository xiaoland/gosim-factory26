"""Durable records, exact ownership and public errors for the exp protocol."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import time

from lab.control import process_identity, process_state

SCHEMA = 1
TERMINAL = {'exited', 'stopped', 'failed', 'unknown'}


class Blocked(RuntimeError):
    """A required fact or capability is unavailable; no new execution is implied."""


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value):
        raise ValueError(f'invalid exp identifier: {value!r}')
    return value


def new_id(prefix):
    return prefix + '-' + secrets.token_hex(12)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def record(kind, **fields):
    return {'kind': 'factory26.exp.' + kind, 'schema_version': SCHEMA, **fields}


def require(value, kind):
    if not isinstance(value, dict) or value.get('kind') != 'factory26.exp.' + kind or value.get('schema_version') != SCHEMA:
        raise ValueError(f'new exp {kind} schema required; legacy evidence is read-only via history/import')
    return value


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name('.' + path.name + '.' + secrets.token_hex(8))
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            os.chmod(temporary, 0o600)
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(path, *, blocking=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as stream:
        os.chmod(path, 0o600)
        fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield


def error(exc):
    value = {'type': type(exc).__name__, 'message': str(exc), 'observed_at': time.time()}
    for name in ('returncode', 'status', 'detail', 'stdout', 'stderr', 'output'):
        item = getattr(exc, name, None)
        if item is not None:
            value[name] = item.decode(errors='replace') if isinstance(item, bytes) else item
    return value


def member(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or '\\' in value:
        raise ValueError(f'unsafe artifact member: {value!r}')
    return path.as_posix()


def request(attempt_id, action, parameters, request_id=None, *, incarnation=None):
    return record('request', request_id=identifier(request_id or new_id('request')),
                  attempt_id=identifier(attempt_id), action=action, parameters=parameters,
                  parameters_sha256=canonical(parameters), expected_incarnation=incarnation,
                  created_at=time.time())


def public(value):
    """Private deployment and credential values never form a public projection."""
    if isinstance(value, dict):
        return {k: public(v) for k, v in value.items() if not re.search(
            r'^(?:.*api[_-]?key|(?:.*[_-])?(?:token|password|cookie|secret)|authorization|credential_values|private_environment)$', k, re.I)}
    if isinstance(value, list):
        return [public(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'(https?://)[^\s/@:]+:[^\s/@]+@', r'\1[redacted]@', value)
        value = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+', r'\1[redacted]', value)
        return re.sub(r'(?i)((?:api[_-]?key|password|access_token)\s*[=:]\s*)[^\s,;]+', r'\1[redacted]', value)
    return value
