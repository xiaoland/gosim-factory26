"""Dev-owned HTTP, TCP, and exec readiness evaluation."""

from __future__ import annotations

import ipaddress
import socket
import ssl
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Iterable, Literal, Protocol, TypeAlias

import urllib3

from ..config import ExecProbe, HttpProbe, TargetConfig, TcpProbe
from ..errors import SvcError
from ..model import ValueModel
from ..workspace import WorkspaceIdentity
from .identity import (
    interpolate_dev_argv,
    interpolate_dev_value,
    require_worktree_provenance,
)


class _HTTPResponse(Protocol):
    status: int

    def close(self) -> None: ...


ProbeKind: TypeAlias = Literal["http", "tcp", "exec"]
ProbeReason: TypeAlias = Literal[
    "accepted-status",
    "unexpected-status",
    "connected",
    "timeout",
    "unreachable",
    "deadline-exhausted",
    "exec-start-failed",
    "zero-exit",
    "nonzero-exit",
    "output-limit",
]


class ProbeObservation(ValueModel):
    kind: ProbeKind
    healthy: bool
    reason: ProbeReason
    endpoint_identity: str
    responded: bool = False
    status_code: int | None = None
    exit_code: int | None = None
    output: str | None = None
    output_bytes: int | None = None
    output_truncated: bool | None = None


class ResolvedProbe(ValueModel):
    kind: ProbeKind
    endpoint_identity: str
    url: str | None = None
    host: str | None = None
    argv: tuple[str, ...] | None = None


def resolve_probe(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    *,
    target_name: str,
) -> ResolvedProbe:
    """Resolve identity-bearing probe inputs without performing probe I/O."""

    probe = target.probe
    if isinstance(probe, HttpProbe):
        url = interpolate_dev_value(probe.url, workspace, target=target_name)
        require_worktree_provenance(target.scope, url, workspace)
        return ResolvedProbe(kind="http", endpoint_identity=url, url=url)
    if isinstance(probe, TcpProbe):
        host = interpolate_dev_value(probe.host, workspace, target=target_name)
        endpoint = f"tcp://{host}:{probe.port}"
        require_worktree_provenance(target.scope, endpoint, workspace)
        return ResolvedProbe(kind="tcp", endpoint_identity=endpoint, host=host)
    argv = interpolate_dev_argv(probe.argv, workspace, target=target_name)
    endpoint = "exec:" + "\0".join(argv)
    require_worktree_provenance(target.scope, endpoint, workspace)
    return ResolvedProbe(kind="exec", endpoint_identity=endpoint, argv=argv)


def probe_target(
    target: TargetConfig,
    workspace: WorkspaceIdentity,
    *,
    target_name: str,
    timeout: float | None = None,
) -> ProbeObservation:
    probe = target.probe
    resolved = resolve_probe(target, workspace, target_name=target_name)
    effective_timeout = (
        min(probe.timeout, timeout) if timeout is not None else probe.timeout
    )
    if effective_timeout <= 0:
        return ProbeObservation(
            kind=probe.kind,
            healthy=False,
            reason="deadline-exhausted",
            endpoint_identity=resolved.endpoint_identity,
        )
    if isinstance(probe, HttpProbe):
        assert resolved.url is not None
        return probe_http(probe, resolved.url, timeout=effective_timeout)
    if isinstance(probe, TcpProbe):
        assert resolved.host is not None
        return probe_tcp(probe, resolved.host, timeout=effective_timeout)
    assert resolved.argv is not None
    cwd = resolve_dev_cwd(workspace.root, probe.cwd, workspace, target_name)
    return probe_exec(probe, resolved.argv, cwd, timeout=effective_timeout)


def probe_http(
    probe: HttpProbe,
    url: str,
    *,
    timeout: float,
    opener: Callable[[str, str, dict[str, str], float], _HTTPResponse] | None = None,
    resolver: Callable[[str, int], Iterable[str]] | None = None,
) -> ProbeObservation:
    parsed = _validate_http_url(url)
    port = parsed.port or _default_port(parsed.scheme)
    addresses = _resolve_addresses(parsed.hostname or "", port, resolver)
    _enforce_address_scope(addresses, probe.network_scope)
    deadline = time.monotonic() + timeout
    path = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    headers = {"Host": parsed.netloc}
    try:
        if opener is not None:
            response = opener(probe.method, path, headers, timeout)
            try:
                status = int(response.status)
            finally:
                response.close()
        else:
            status = _pinned_http_status(
                probe, parsed, addresses, path, headers, deadline
            )
    except (urllib3.exceptions.HTTPError, OSError, ssl.SSLError, TimeoutError) as error:
        return ProbeObservation(
            kind="http",
            healthy=False,
            reason=_network_error_reason(error),
            endpoint_identity=url,
        )
    lower, upper = probe.success_status
    healthy = lower <= status <= upper
    return ProbeObservation(
        kind="http",
        healthy=healthy,
        reason="accepted-status" if healthy else "unexpected-status",
        endpoint_identity=url,
        responded=True,
        status_code=status,
    )


def probe_tcp(
    probe: TcpProbe,
    host: str,
    *,
    timeout: float,
    resolver: Callable[[str, int], Iterable[str]] | None = None,
) -> ProbeObservation:
    addresses = _resolve_addresses(host, probe.port, resolver)
    _enforce_address_scope(addresses, probe.network_scope)
    endpoint = f"tcp://{host}:{probe.port}"
    deadline = time.monotonic() + timeout
    last_error: OSError | None = None
    for address in addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return ProbeObservation(
                kind="tcp",
                healthy=False,
                reason="timeout",
                endpoint_identity=endpoint,
            )
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        try:
            with socket.socket(family, socket.SOCK_STREAM) as connection:
                connection.settimeout(remaining)
                connection.connect((address, probe.port))
            return ProbeObservation(
                kind="tcp",
                healthy=True,
                reason="connected",
                endpoint_identity=endpoint,
                responded=True,
            )
        except OSError as error:
            last_error = error
    return ProbeObservation(
        kind="tcp",
        healthy=False,
        reason=_network_error_reason(last_error),
        endpoint_identity=endpoint,
    )


def probe_exec(
    probe: ExecProbe, argv: tuple[str, ...], cwd: Path, *, timeout: float
) -> ProbeObservation:
    captured = bytearray()
    overflow = False
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            close_fds=True,
        )
    except OSError:
        return ProbeObservation(
            kind="exec",
            healthy=False,
            reason="exec-start-failed",
            endpoint_identity="exec:" + "\0".join(argv),
        )
    assert process.stdout is not None
    output = process.stdout

    def drain() -> None:
        nonlocal overflow
        while chunk := output.read(8_192):
            remaining = probe.output_limit - len(captured)
            if remaining > 0:
                captured.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow = True

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        reader.join(timeout=1)
        process.stdout.close()
        return ProbeObservation(
            kind="exec",
            healthy=False,
            reason="timeout",
            endpoint_identity="exec:" + "\0".join(argv),
            output=_decode_probe_output(captured),
            output_bytes=len(captured),
            output_truncated=overflow,
        )
    reader.join(timeout=1)
    process.stdout.close()
    return ProbeObservation(
        kind="exec",
        healthy=code == 0 and not overflow,
        reason="zero-exit"
        if code == 0 and not overflow
        else "nonzero-exit"
        if code
        else "output-limit",
        endpoint_identity="exec:" + "\0".join(argv),
        exit_code=code,
        output=_decode_probe_output(captured),
        output_bytes=len(captured),
        output_truncated=overflow,
    )


def _decode_probe_output(captured: bytearray) -> str | None:
    if not captured:
        return None
    return bytes(captured).decode("utf-8", errors="replace")


def resolve_dev_cwd(
    root: Path,
    configured: str | None,
    workspace: WorkspaceIdentity,
    target: str,
) -> Path:
    value = interpolate_dev_value(configured or ".", workspace, target=target)
    candidate = (
        (root / value).resolve()
        if not Path(value).is_absolute()
        else Path(value).resolve()
    )
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise SvcError(
            "dev-cwd-escapes-workspace",
            "Dev command working directory escapes the workspace.",
        ) from error
    if not candidate.is_dir():
        raise SvcError(
            "dev-cwd-not-directory",
            "Dev command working directory does not exist.",
            {"cwd": value},
        )
    return candidate


def _pinned_http_status(
    probe: HttpProbe,
    parsed: urllib.parse.SplitResult,
    addresses: Iterable[str],
    path: str,
    headers: dict[str, str],
    deadline: float,
) -> int:
    port = parsed.port or _default_port(parsed.scheme)
    last_error: BaseException | None = None
    for address in addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("HTTP readiness deadline exhausted")
        if parsed.scheme == "https":
            pool: urllib3.HTTPConnectionPool = urllib3.HTTPSConnectionPool(
                address,
                port,
                assert_hostname=False if probe.insecure_tls else parsed.hostname,
                server_hostname=parsed.hostname,
                cert_reqs=ssl.CERT_NONE if probe.insecure_tls else ssl.CERT_REQUIRED,
                retries=False,
            )
        else:
            pool = urllib3.HTTPConnectionPool(address, port, retries=False)
        try:
            response = pool.urlopen(
                probe.method,
                path,
                headers=headers,
                retries=False,
                redirect=False,
                assert_same_host=False,
                timeout=urllib3.Timeout(
                    total=remaining, connect=remaining, read=remaining
                ),
                preload_content=False,
            )
            try:
                return int(response.status)
            finally:
                response.close()
        except (
            urllib3.exceptions.HTTPError,
            OSError,
            ssl.SSLError,
            TimeoutError,
        ) as error:
            last_error = error
        finally:
            pool.close()
    if last_error is not None:
        raise last_error
    raise OSError("no probe address was attempted")


def _validate_http_url(value: str) -> urllib.parse.SplitResult:
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise SvcError(
            "invalid-http-probe-url",
            "HTTP probe URL must be an absolute HTTP(S) URL without credentials or fragments.",
        )
    try:
        _ = parsed.port
    except ValueError as error:
        raise SvcError(
            "invalid-http-probe-url", "HTTP probe URL has an invalid port."
        ) from error
    return parsed


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _resolve_addresses(
    host: str,
    port: int,
    resolver: Callable[[str, int], Iterable[str]] | None = None,
) -> tuple[str, ...]:
    if resolver is not None:
        addresses = tuple(resolver(host, port))
    else:
        try:
            addresses = tuple(
                sorted(
                    {
                        str(entry[4][0])
                        for entry in socket.getaddrinfo(
                            host, port, type=socket.SOCK_STREAM
                        )
                    }
                )
            )
        except socket.gaierror as error:
            raise SvcError(
                "probe-address-unresolved",
                "Dev probe hostname could not be resolved.",
                {"host": host},
            ) from error
    if not addresses:
        raise SvcError(
            "probe-address-unresolved",
            "Dev probe hostname resolved to no addresses.",
            {"host": host},
        )
    return addresses


def _enforce_address_scope(addresses: Iterable[str], network_scope: str) -> None:
    if network_scope == "remote":
        return
    non_loopback = [
        address
        for address in addresses
        if not ipaddress.ip_address(address).is_loopback
    ]
    if non_loopback:
        raise SvcError(
            "remote-probe-not-allowed",
            "Dev probe resolves outside loopback without explicit remote scope.",
            {"addresses": non_loopback},
        )


def _network_error_reason(
    error: BaseException | None,
) -> Literal["timeout", "unreachable"]:
    if isinstance(
        error, (socket.timeout, TimeoutError, urllib3.exceptions.TimeoutError)
    ):
        return "timeout"
    return "unreachable"
