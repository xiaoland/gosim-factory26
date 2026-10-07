"""ArcBench self-test submission adapter.

The self-test site is deliberately kept separate from the official ARC
submission service.  Its public browser client uses a small three-request
protocol: request a signed upload URL, PUT the ZIP, then submit the upload
identity.  This module records each request/response without retrying the
final POST, because the site counts submissions even when the response is
lost.
"""

from __future__ import annotations

import hashlib
import json
import os
import ctypes
from pathlib import Path
import shutil
import sqlite3
import ssl
import subprocess
import tempfile
import time
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile

from .run_layout import storage_path


API_DEFAULT = "https://arcbench-selftest-web.vercel.app"
MAX_PACKAGE_BYTES = 50 * 1024 * 1024
DOCKERFILE = """FROM node:20.19.3-bookworm-slim
WORKDIR /app
ADD app-runtime.tar.gz /app/
ENV HOST=0.0.0.0 PORT=3000
EXPOSE 3000
WORKDIR /app/backend
CMD [\"npm\", \"run\", \"start\"]
"""


def _https_context():
    """Use an available system CA bundle when Python's default is stale."""
    candidates = (
        os.environ.get("SSL_CERT_FILE"),
        os.environ.get("NIX_SSL_CERT_FILE"),
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    )
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            return ssl.create_default_context(cafile=candidate)
        except (OSError, ssl.SSLError):
            continue
    return ssl.create_default_context()


def _manifest(run):
    return json.loads((Path(run) / "manifest.json").read_text(encoding="utf-8"))


def _target(run):
    value = _manifest(run).get("target_config") or {}
    if value.get("kind") != "self-test":
        raise ValueError("self-test adapter requires target_config.kind=self-test")
    return value


def _record(run, name, value):
    path = Path(run) / "records" / "self-test" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _cookie_domain_matches(cookie_domain, host):
    cookie_domain = cookie_domain.lower().lstrip(".")
    host = host.lower().rstrip(".")
    return host == cookie_domain or host.endswith("." + cookie_domain)


def _cookie_file_has_live_cookie(path, target):
    """Return whether a private Netscape export can authenticate this target.

    This is intentionally a metadata-only check.  It never logs or returns a
    cookie value, and lets a materialized Helium export be reused without
    asking Keychain again for every request in one run.
    """
    host = urlparse(str(target.get("api_base") or API_DEFAULT)).hostname
    scheme = urlparse(str(target.get("api_base") or API_DEFAULT)).scheme
    if not host or not path.is_file():
        return False
    now = int(time.time())
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        elif line.startswith("#") or not line:
            continue
        fields = line.split("\t")
        if len(fields) < 7 or not _cookie_domain_matches(fields[0], host):
            continue
        try:
            expires = int(fields[4])
        except ValueError:
            continue
        if expires and expires <= now:
            continue
        if fields[3].upper() == "TRUE" and scheme != "https":
            continue
        return True
    return False


def _cookie_file(target):
    filename = target.get("cookie_file")
    env_name = target.get("cookie_file_env", "FACTORY26_SELFTEST_COOKIE_FILE")
    if not filename:
        filename = os.environ.get(env_name)
    if not filename and target.get("cookie_source") == "helium":
        private_default = Path(__file__).resolve().parents[2] / ".secrets" / "self-test" / "helium.cookies.txt"
        if _cookie_file_has_live_cookie(private_default, target):
            filename = str(private_default)
        else:
            # A stale export is replaced only once during preparation.  The
            # resulting private file is then reused by every request below.
            filename = _materialize_helium_cookie_file(target)
    if not filename:
        private_default = Path(__file__).resolve().parents[2] / ".secrets" / "self-test" / "helium.cookies.txt"
        if private_default.is_file():
            filename = str(private_default)
    if not filename:
        raise RuntimeError(
            "self-test Helium credentials are unavailable on this execution host; "
            "automatic runs must use the Mac relay or a sealed private handoff"
        )
    path = Path(filename).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"self-test cookie file does not exist on this execution host: {path}")
    return path


def _helium_cookie_root(target):
    configured = target.get("helium_profile")
    if configured:
        return Path(configured).expanduser().resolve(strict=True)
    if os.uname().sysname != "Darwin":
        return None
    root = Path.home() / "Library" / "Application Support" / "net.imput.helium"
    return root if root.is_dir() else None


def _keychain_secret(target):
    """Read only Helium's named Chromium storage key through macOS ACLs.

    The keychain item is explicitly scoped to Helium.  A CLI request normally
    causes the system Keychain prompt because the item trusts the signed
    Helium application, not this Python process.  Do not retry indefinitely or
    fall back to another browser's keychain item.
    """
    try:
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-a", "Helium",
             "-s", "Helium Storage Key", "-w"],
            check=False, capture_output=True,
            timeout=float(target.get("keychain_timeout_seconds", 60)),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Helium Storage Key Keychain authorization is pending; approve the macOS "
            "Keychain prompt for this read, then retry self-test"
        ) from exc
    if result.returncode or not result.stdout.strip():
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"Helium Storage Key could not be read from Keychain: {detail or 'no value returned'}")
    return result.stdout.rstrip(b"\r\n")


def _commoncrypto_decrypt(key, ciphertext):
    """Decrypt Chromium AES-CBC data without putting key material in argv.

    Helium runs on macOS, where CommonCrypto is part of libSystem.  Loading
    the documented ``CCCrypt`` entry point through ctypes keeps both the
    derived key and the Chromium key in process memory only.  Linux/WSL
    evaluators receive the already-filtered cookie export and never decrypt a
    Helium database.
    """
    if os.uname().sysname != "Darwin":
        return None
    decrypt = None
    for library_name in (None, "/usr/lib/libSystem.B.dylib"):
        try:
            commoncrypto = ctypes.CDLL(library_name)
            decrypt = commoncrypto.CCCrypt
            break
        except (AttributeError, OSError):
            continue
    if decrypt is None:
        raise RuntimeError("Helium cookie decryption unavailable: CommonCrypto CCCrypt could not be loaded")
    decrypt.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    decrypt.restype = ctypes.c_int
    key_buffer = (ctypes.c_ubyte * len(key)).from_buffer(key)
    input_buffer = ctypes.create_string_buffer(ciphertext)
    output_buffer = ctypes.create_string_buffer(len(ciphertext) + 16)
    moved = ctypes.c_size_t()
    status = decrypt(
        1,  # kCCDecrypt
        0,  # kCCAlgorithmAES
        1,  # kCCOptionPKCS7Padding; CBC is the default AES mode
        ctypes.cast(key_buffer, ctypes.c_void_p), len(key),
        ctypes.c_char_p(b" " * 16),
        ctypes.cast(input_buffer, ctypes.c_void_p), len(ciphertext),
        ctypes.cast(output_buffer, ctypes.c_void_p), len(output_buffer),
        ctypes.byref(moved),
    )
    if status != 0:
        raise RuntimeError(f"Helium cookie AES-CBC decryption failed: CCCrypt status {status}")
    return output_buffer.raw[:moved.value]


def _decrypt_chromium_v10(value, key, host, database_version=None):
    if not value.startswith(b"v10"):
        return None
    derived = bytearray(hashlib.pbkdf2_hmac("sha1", key, b"saltysalt", 1003, 16))
    try:
        plaintext = _commoncrypto_decrypt(derived, value[3:])
    finally:
        derived[:] = b"\x00" * len(derived)
    if plaintext is None:
        return None
    # Chromium's modern cookie schema stores a SHA-256(host_key) prefix in
    # some v10 records.  Detect the prefix instead of blindly decoding it as
    # part of the cookie value; the database meta version is retained as the
    # provenance signal for this compatibility branch.
    digest = hashlib.sha256(host.encode("utf-8")).digest()
    if plaintext.startswith(digest):
        plaintext = plaintext[len(digest):]
    try:
        return plaintext.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return None


def _materialize_helium_cookie_file(target):
    """Materialize only the self-test site's cookies into private WorkSSD data."""
    root = _helium_cookie_root(target)
    if root is None:
        return None
    host = urlparse(str(target.get("api_base") or API_DEFAULT)).hostname
    if not host:
        raise ValueError("self-test target api_base has no hostname")
    key = bytearray(_keychain_secret(target))
    rows = []
    try:
        for database in sorted(root.glob("*/Cookies")):
            descriptor = None
            temporary = None
            try:
                descriptor, temporary_name = tempfile.mkstemp(prefix="helium-cookies-", suffix=".sqlite",
                                                              dir=_work_temp_dir())
                os.close(descriptor)
                descriptor = None
                temporary = Path(temporary_name)
                shutil.copy2(database, temporary)
                connection = sqlite3.connect(f"file:{temporary}?mode=ro", uri=True)
                meta = {}
                try:
                    meta = dict(connection.execute("SELECT key, value FROM meta").fetchall())
                except sqlite3.DatabaseError:
                    pass
                database_version = meta.get("version")
                query = ("SELECT host_key, name, path, expires_utc, is_secure, is_httponly, encrypted_value "
                         "FROM cookies WHERE host_key LIKE ?")
                for row in connection.execute(query, (f"%{host}",)):
                    cookie_host, name, path, expires_utc, secure, http_only, encrypted = row
                    if not _cookie_domain_matches(cookie_host, host):
                        continue
                    if expires_utc and expires_utc > 0:
                        expires = int(expires_utc / 1_000_000 - 11644473600)
                        if expires <= int(time.time()):
                            continue
                    else:
                        expires = 0
                    value = _decrypt_chromium_v10(bytes(encrypted), key, cookie_host, database_version)
                    if value is None:
                        continue
                    rows.append((cookie_host, bool(http_only), path or "/", bool(secure), expires, name, value))
                connection.close()
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    finally:
        key[:] = b"\x00" * len(key)
    if not rows:
        raise RuntimeError("Helium has no decryptable, unexpired self-test cookies for the target site")
    destination = Path(__file__).resolve().parents[2] / ".secrets" / "self-test" / "helium.cookies.txt"
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    storage_path(destination)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.chmod(0o600)
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write("# Netscape HTTP Cookie File\n")
        for cookie_host, http_only, path, secure, expires, name, value in rows:
            domain = ("#HttpOnly_" if http_only else "") + cookie_host
            stream.write("\t".join((domain, "TRUE" if cookie_host.startswith(".") else "FALSE",
                                    path, "TRUE" if secure else "FALSE", str(expires), name, value)) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, destination)
    return str(destination)


def _work_temp_dir():
    root = Path(os.environ.get("FACTORY26_TEMP_ROOT", Path(__file__).resolve().parents[2] / ".tmp")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    storage_path(root)
    return root


def _cookie_header(target):
    path = _cookie_file(target)
    host = urlparse(str(target.get("api_base") or API_DEFAULT)).hostname
    if not host:
        raise ValueError("self-test target api_base has no hostname")
    cookies = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        # Netscape exports reserve ordinary comments for metadata, but
        # Chromium prefixes HttpOnly cookie domains with #HttpOnly_.
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        elif line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 7 or not _cookie_domain_matches(fields[0], host):
            continue
        try:
            expires = int(fields[4])
        except ValueError:
            continue
        if expires and expires <= int(time.time()):
            continue
        if fields[3].upper() == "TRUE" and urlparse(str(target.get("api_base") or API_DEFAULT)).scheme != "https":
            continue
        cookies.append(f"{fields[5]}={fields[6]}")
    if not cookies:
        raise ValueError(f"self-test cookie file has no Netscape cookies: {path}")
    return "; ".join(cookies), str(path)


def _http_json(run, target, method, path, *, body=None, headers=None, record=None):
    base = str(target.get("api_base") or API_DEFAULT).rstrip("/")
    cookie, cookie_path = _cookie_header(target)
    request_headers = {"Accept": "application/json", "Cookie": cookie}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request_headers.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    request = Request(base + path, data=data, headers=request_headers, method=method)
    if method == "POST" and path == "/api/submit":
        _record(run, "submit-intent.json", {"method": method, "path": path,
                                           "request_sha256": hashlib.sha256(data or b"").hexdigest(),
                                           "as_of": time.time()})
    try:
        with urlopen(request, timeout=float(target.get("timeout_seconds", 60)), context=_https_context()) as response:
            raw = response.read()
            status = response.status
            response_headers = dict(response.headers.items())
    except HTTPError as error:
        raw = error.read()
        status = error.code
        response_headers = dict(error.headers.items())
    except URLError as error:
        value = {"method": method, "path": path, "status": None,
                 "request_sha256": hashlib.sha256(data or b"").hexdigest(),
                 "cookie_file": cookie_path, "error": str(error), "as_of": time.time()}
        if record:
            _record(run, record, value)
        raise RuntimeError(f"self-test {method} {path} transport error: {error}") from error
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {"raw_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    recorded_payload = payload
    if isinstance(payload, dict) and "uploadUrl" in payload:
        recorded_payload = {**payload, "uploadUrl": "[redacted]"}
    value = {"method": method, "path": path, "status": status,
             "request_sha256": hashlib.sha256(data or b"").hexdigest(),
             "response_sha256": hashlib.sha256(raw).hexdigest(),
             "response_headers": {key: value for key, value in response_headers.items()
                                   if key.lower() not in {"set-cookie", "authorization"}},
             "response": recorded_payload, "cookie_file": cookie_path, "as_of": time.time()}
    if record:
        _record(run, record, value)
    if status < 200 or status >= 300:
        raise RuntimeError(f"self-test {method} {path} returned HTTP {status}: {payload}")
    return payload


def _package_root(run):
    value = _manifest(run)
    configured = value.get("self_test_package") or value.get("evaluation", {}).get("package")
    if configured:
        package = Path(configured).expanduser().resolve(strict=True)
        if package.is_file():
            return package
    candidate = Path(run) / "inputs" / "self-test.zip"
    if candidate.is_file():
        return candidate
    return None


def _docker_runtime(application, destination):
    """Build Linux production dependencies and frontend assets once.

    The resulting tar is what the self-test service's network-disabled build
    consumes.  The build uses a temporary WorkSSD context and leaves the app
    source untouched.
    """
    application = Path(application).resolve(strict=True)
    root = _work_temp_dir()
    with tempfile.TemporaryDirectory(prefix="self-test-build-", dir=root) as directory:
        context = Path(directory)
        shutil.copytree(application, context / "app", symlinks=True)
        dockerfile = Path(__file__).with_name("self_test_build.Dockerfile")
        tag = "factory26-self-test-runtime:" + hashlib.sha256(str(application).encode()).hexdigest()[:16]
        subprocess.run(["docker", "build", "--platform", "linux/amd64", "--file", str(dockerfile), "--tag", tag, str(context)], check=True)
        created = subprocess.check_output(["docker", "create", "--platform", "linux/amd64", tag], text=True).strip()
        try:
            subprocess.run(["docker", "cp", f"{created}:/app-runtime.tar.gz", str(destination)], check=True)
        finally:
            subprocess.run(["docker", "rm", created], check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    return Path(destination)


def package(application, output, *, runtime_archive=None):
    """Create the platform ZIP for an immutable application snapshot."""
    application = Path(application).resolve(strict=True)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="self-test-package-", dir=output.parent))
    created = False
    try:
        runtime = staging / "app-runtime.tar.gz"
        if runtime_archive:
            shutil.copy2(Path(runtime_archive).resolve(strict=True), runtime)
        else:
            _docker_runtime(application, runtime)
        with ZipFile(output, "x", ZIP_DEFLATED) as archive:
            created = True
            archive.writestr("Dockerfile", DOCKERFILE)
            archive.write(runtime, "app-runtime.tar.gz")
        size = output.stat().st_size
        if size > MAX_PACKAGE_BYTES:
            output.unlink(missing_ok=True)
            raise ValueError(f"self-test package exceeds the 50 MB platform limit: {size} bytes")
        return {"path": str(output), "bytes": size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "runtime_sha256": hashlib.sha256(runtime.read_bytes()).hexdigest()}
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _validate_package(package_path):
    package_path = Path(package_path).resolve(strict=True)
    size = package_path.stat().st_size
    if size > MAX_PACKAGE_BYTES:
        raise ValueError(f"self-test package exceeds the 50 MB platform limit: {size} bytes")
    with ZipFile(package_path) as archive:
        names = set(archive.namelist())
        if "Dockerfile" not in names:
            raise ValueError("self-test package must contain a root Dockerfile")
    return size


def start(run):
    run = Path(run).resolve()
    target = _target(run)
    manifest = _manifest(run)
    # Resolve and validate the private auth material before the potentially
    # slow Docker build.  _cookie_file reuses an existing unexpired export;
    # only a stale/missing Helium export reaches Keychain preparation.
    _cookie_header(target)
    package_path = _package_root(run)
    if package_path is None:
        from .evaluate import _application_root
        package_path = run / "inputs" / "self-test.zip"
        package_info = package(_application_root(run / "inputs" / "application"), package_path,
                               runtime_archive=target.get("runtime_archive"))
    else:
        owned_package = run / "inputs" / "self-test.zip"
        if package_path.resolve() != owned_package.resolve():
            shutil.copy2(package_path, owned_package)
            package_path = owned_package
        _validate_package(package_path)
        package_info = {"path": str(package_path), "bytes": package_path.stat().st_size,
                        "sha256": hashlib.sha256(package_path.read_bytes()).hexdigest()}
    _record(run, "package.json", package_info)
    task = manifest.get("task_config", {}).get("platform_task")
    if not task or not task.endswith("-req-test"):
        raise ValueError(f"self-test requires a *-req-test platform task, got {task!r}")
    upload = _http_json(run, target, "POST", "/api/upload-url",
                        body={"taskId": task, "size": package_info["bytes"]}, record="upload-url.json")
    upload_id = upload.get("id")
    upload_url = upload.get("uploadUrl")
    if not isinstance(upload_id, str) or not isinstance(upload_url, str):
        raise RuntimeError(f"self-test upload-url response lacks id/uploadUrl: {upload}")
    cookie, cookie_path = _cookie_header(target)
    request = Request(upload_url, data=package_path.read_bytes(),
                      headers={"Content-Type": "application/zip"}, method="PUT")
    try:
        with urlopen(request, timeout=float(target.get("timeout_seconds", 60)), context=_https_context()) as response:
            upload_status = response.status
            upload_bytes = response.read()
    except (HTTPError, URLError) as error:
        if isinstance(error, HTTPError):
            upload_status = error.code
            upload_bytes = error.read()
        else:
            upload_status = None
            upload_bytes = b""
        _record(run, "package-upload.json", {"status": upload_status,
                 "package_sha256": package_info["sha256"], "response_sha256": hashlib.sha256(upload_bytes).hexdigest(),
                 "cookie_file": cookie_path, "error": str(error), "as_of": time.time()})
        raise RuntimeError(f"self-test package upload failed: {error}") from error
    _record(run, "package-upload.json", {"status": upload_status,
             "package_sha256": package_info["sha256"], "response_sha256": hashlib.sha256(upload_bytes).hexdigest(),
             "cookie_file": cookie_path, "as_of": time.time()})
    if not 200 <= upload_status < 300:
        raise RuntimeError(f"self-test package upload returned HTTP {upload_status}")
    submitted = _http_json(run, target, "POST", "/api/submit", body={"uploadId": upload_id}, record="submit.json")
    submission_id = submitted.get("id")
    if not isinstance(submission_id, str):
        raise RuntimeError(f"self-test submit response lacks id: {submitted}")
    identity = {"submission_id": submission_id, "task": task,
                "url": str(target.get("api_base") or API_DEFAULT).rstrip("/") + "/submissions/" + submission_id,
                "package": package_info, "submitted_at": time.time()}
    _record(run, "identity.json", identity)
    return {"lifecycle": "running", "activity": "submitted", "platform": identity,
            "as_of": identity["submitted_at"]}


def observe(run):
    run = Path(run).resolve()
    target = _target(run)
    identity_path = run / "records" / "self-test" / "identity.json"
    if not identity_path.is_file():
        return {"lifecycle": "unknown", "activity": "unknown", "as_of": time.time(),
                "error": "self-test identity is not saved"}
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    submission_id = identity["submission_id"]
    value = _http_json(run, target, "GET", f"/api/submissions/{submission_id}", record="status.json")
    submission = value.get("submission") if isinstance(value, dict) else None
    submission = submission if isinstance(submission, dict) else value
    status = submission.get("status", "unknown") if isinstance(submission, dict) else "unknown"
    if status in {"queued", "running"}:
        lifecycle, activity = "running", status
    elif status in {"passed", "failed", "completed"}:
        lifecycle, activity = "completed", status
    elif status in {"error", "rejected"}:
        lifecycle, activity = "failed", status
    else:
        lifecycle, activity = "unknown", status
    result = {"lifecycle": lifecycle, "activity": activity, "self_test": submission,
              "platform": identity, "as_of": time.time()}
    if lifecycle == "completed":
        _record(run, "result.json", result)
    return result


def save(run):
    run = Path(run).resolve()
    identity = run / "records" / "self-test" / "identity.json"
    if not identity.is_file():
        return {"saved": False, "scope": [], "gaps": ["self-test submission identity unavailable"],
                "as_of": time.time()}
    package_path = _package_root(run)
    return {"saved": True, "scope": ["inputs/self-test.zip", "records/self-test"],
            "package": str(package_path) if package_path else None,
            "gaps": ["self-test service exposes result records but no workspace export"],
            "as_of": time.time()}


def control(run, action):
    raise ValueError(f"self-test does not support {action}; use stop only for the owning generation run")
