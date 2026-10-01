"""Read native JSONL only from identities returned by the registered Braid CLI."""

import json
from pathlib import Path
import subprocess
import sys

import docker_runtime


# Run this same reader in the registered Docker namespace; paths never come from HTTP input.
READER = r'''
import json, os, re, sys

request = json.load(sys.stdin)
path, expected, provider, offset = (request[k] for k in ("path", "native_id", "provider", "offset"))
if offset < 0:
    raise ValueError("原生记录偏移不得为负")
secrets = [v for k, v in os.environ.items() if len(v) >= 8 and re.search(r"(?i)(api.?key|token|secret|password)", k)]
def redact(value):
    if isinstance(value, dict):
        return {k: "[已隐藏凭据]" if re.fullmatch(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|token|authorization|password|secret|credential)", k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[已隐藏凭据]")
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [已隐藏凭据]", value)
        value = re.sub(r"\b(?:sk|ghp|gho|github_pat)-?[A-Za-z0-9_-]{20,}\b", "[已隐藏凭据]", value)
        value = re.sub(r"(?i)((?:[a-z0-9_]*(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret))[\"']?\s*[=:]\s*[\"']?)([^\s\"',;]+)", r"\1[已隐藏凭据]", value)
    return value
with open(path, "rb") as stream:
    header = json.loads(stream.readline(8 * 1024 * 1024))
    actual = header.get("id") if provider == "pi" else header.get("payload", {}).get("id") if provider == "codex" else None
    if not expected or actual != expected:
        raise ValueError(f"原生会话身份不匹配：CLI={expected!r}，文件header={actual!r}，provider={provider!r}")
    size = os.fstat(stream.fileno()).st_size
    if offset > size:
        raise ValueError(f"原生文件已缩短：偏移{offset}，当前长度{size}")
    if offset:
        stream.seek(offset - 1)
        if stream.read(1) != b"\n":
            raise ValueError("原生记录偏移不在JSONL行边界")
    stream.seek(offset)
    entries, waiting = [], False
    while len(entries) < 50 and (stream.tell() - offset < 1024 * 1024 or not entries):
        start = stream.tell()
        line = stream.readline(8 * 1024 * 1024 + 1)
        if not line:
            break
        if len(line) > 8 * 1024 * 1024:
            raise ValueError(f"原生记录在字节{start}超过8MiB读取边界；未截断或跳过")
        if not line.endswith(b"\n"):
            stream.seek(start)
            waiting = True
            break
        try:
            value = json.loads(line)
            entries.append({"offset": start, "value": redact(value)})
        except (ValueError, UnicodeDecodeError) as error:
            entries.append({"offset": start, "error": str(error), "raw": redact(line.decode("utf-8", "replace"))})
    next_offset = stream.tell()
print(json.dumps({"entries": entries, "next_offset": next_offset, "size": size, "eof": next_offset >= size, "waiting": waiting}, ensure_ascii=False))
'''


def read_page(run, record, offset):
    path = record.get("native_session_path")
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ValueError("CLI 未提供此会话的有效原生文件路径")
    request = {"path": path, "native_id": record.get("native_session_id"),
               "provider": record.get("provider"), "offset": offset}
    if run["docker"] is not None:
        command = docker_runtime.base_command(run["docker"]) + ["exec", "-i", run["docker"]["cli_container"], "python3", "-c", READER]
    else:
        command = [sys.executable, "-E", "-s", "-c", READER]
    try:
        result = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True,
                                timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"原生会话读取未确认：{error}") from error
    if result.returncode:
        raise RuntimeError(f"原生会话读取退出码 {result.returncode}: {result.stderr.strip()}\n{result.stdout.strip()}")
    return json.loads(result.stdout)
