"""Run one local model gateway for native Pi and Codex Hackathon variants."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "glm-5.3-flash": "GLM",
    "kimi-k3": "KIMI",
    "kimi-k2.7-code": "KIMI",
    "deepseek-v4-flash": "DEEPSEEK",
    "deepseek-v4-flash-vision-exp": "DEEPSEEK",
}


def read_secrets(path):
    path = path.resolve(strict=True)
    if path.stat().st_mode & 0o077:
        raise ValueError("model secrets must have mode 600")
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"invalid secret assignment: {name}")
        values[name.strip()] = value.strip().strip('"').strip("'")
    for vendor in MODELS.values():
        for suffix in ("API_KEY", "BASE_URL"):
            if not values.get(f"{vendor}_{suffix}"):
                raise ValueError(f"missing {vendor}_{suffix}")
    return values


def read_assignments(path):
    path = Path(path).resolve(strict=True)
    if path.stat().st_mode & 0o077:
        raise ValueError("client environment file must have mode 600")
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name.strip()):
            raise ValueError(f"invalid client environment variable: {name}")
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def write_private(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        output.write(content)
    path.chmod(0o600)


def binding_resource(service_state, run_dir, run_id, action):
    state = Path(service_state).resolve(strict=True)
    marker = Path(run_dir) / ".private/gateway-binding.json"
    if not marker.is_file():
        return {"status": "not-registered"}
    binding = json.loads(marker.read_text())
    service = json.loads((state / "service.json").read_text())
    if binding.get("run_id") != run_id or binding.get("service_id") != service["service_id"]:
        return {"status": "ownership-mismatch"}
    path = state / "bindings" / f"{binding['binding_id']}.json"
    revoked = state / "revoked" / path.name
    if path.is_file():
        saved = json.loads(path.read_text())
        if saved.get("run_id") != run_id or saved.get("service_id") != service["service_id"]:
            return {"status": "ownership-mismatch"}
        if action == "cleanup":
            path.rename(revoked)
            return {"status": "revoked", "binding_id": binding["binding_id"]}
        return {"status": "active", "binding_id": binding["binding_id"]}
    return {"status": "revoked" if revoked.is_file() else "absent",
            "binding_id": binding["binding_id"]}


def export_otlp(service_state, run_id, run_dir):
    """Send only persisted gateway rows for this run; keep the cursor on failure."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT")
    headers = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_HEADERS", "")
    if not endpoint or not headers:
        return {"status": "unavailable", "reason": "run-scoped OTLP logs endpoint is absent"}
    source = Path(service_state) / "request-metadata.jsonl"
    cursor = Path(run_dir) / "artifacts/gateway-export.json"
    cursor.parent.mkdir(parents=True, exist_ok=True)
    start = json.loads(cursor.read_text())["offset"] if cursor.is_file() else 0
    if not source.is_file():
        return {"status": "unavailable", "reason": "gateway request log is absent"}
    from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
    rows = []
    end = start
    with source.open("rb") as stream:
        stream.seek(start)
        while line := stream.readline():
            if not line.endswith(b"\n"):
                break
            try:
                row = json.loads(line)
            except ValueError as exc:
                return {"status": "failed", "error": f"invalid gateway row at byte {end}: {exc}"}
            if row.get("run_id") == run_id:
                rows.append(row)
            end = stream.tell()
    if not rows:
        cursor.write_text(json.dumps({"offset": end}) + "\n")
        return {"status": "empty", "offset": end}
    request = ExportLogsServiceRequest()
    resource = request.resource_logs.add()
    attribute = resource.resource.attributes.add()
    attribute.key = "service.name"
    attribute.value.string_value = "factory26-model-gateway"
    scope = resource.scope_logs.add()
    scope.scope.name = "factory26.gateway.raw"
    for row in rows:
        record = scope.log_records.add()
        record.time_unix_nano = row.get("time_ns", 0)
        record.body.string_value = json.dumps(row, ensure_ascii=False)
    header_values = dict(item.split("=", 1) for item in headers.split(",") if "=" in item)
    payload = request.SerializeToString()
    try:
        with urlopen(Request(endpoint, data=payload, method="POST", headers={
                "Content-Type": "application/x-protobuf", **header_values}), timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"OTLP receiver returned HTTP {response.status}")
    except Exception as exc:
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                "records": len(rows), "offset": start}
    cursor.write_text(json.dumps({"offset": end}) + "\n")
    return {"status": "sent", "records": len(rows), "offset": end}


def wrap(argv):
    parser = argparse.ArgumentParser(description="Bind one external command to a local gateway run")
    parser.add_argument("--service-state", type=Path, required=True)
    parser.add_argument("--url-env", required=True)
    parser.add_argument("--key-env", required=True)
    parser.add_argument("--env-file-var", required=True)
    parser.add_argument("--client-env", type=Path)
    parser.add_argument("--include-var", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    names = [args.url_env, args.key_env, args.env_file_var, *args.include_var]
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) for name in names):
        raise ValueError("environment variable names must be plain identifiers")
    if args.url_env == args.key_env:
        raise ValueError("URL and key variables must be different")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("wrapper needs an external argv after --")
    run_id = os.environ.get("EXPERIMENT_RUN_ID")
    run_dir = os.environ.get("EXPERIMENT_RUN_DIR")
    if not run_id or not run_dir:
        raise ValueError("wrapper needs EXPERIMENT_RUN_ID and EXPERIMENT_RUN_DIR")
    state = args.service_state.expanduser().resolve(strict=True)
    service = json.loads((state / "service.json").read_text())
    service_env = read_assignments(state / "gateway.env")
    bindings = state / "bindings"
    token = secrets.token_urlsafe(32)
    binding_id = hashlib.sha256(token.encode()).hexdigest()
    binding = bindings / f"{binding_id}.json"
    private = Path(run_dir) / ".private"
    private.mkdir(mode=0o700, exist_ok=True)
    values = read_assignments(args.client_env) if args.client_env else {}
    selected = {name: values[name] for name in args.include_var if name in values}
    selected[args.url_env] = service_env["GATEWAY_URL"]
    selected[args.key_env] = token
    if any("\n" in value or "\r" in value for value in selected.values()):
        raise ValueError("client environment values must be single-line")
    temporary = private / f"gateway-{binding_id[:16]}.env"
    write_private(binding, json.dumps({"run_id": run_id, "service_id": service["service_id"],
                                        "created_at": time.time()}, ensure_ascii=False) + "\n")
    try:
        write_private(private / "gateway-binding.json", json.dumps({
            "run_id": run_id, "service_id": service["service_id"], "binding_id": binding_id},
            ensure_ascii=False) + "\n")
        write_private(temporary, "".join(f"{name}={value}\n" for name, value in selected.items()))
        env = dict(os.environ)
        env[args.env_file_var] = str(temporary)
        code = subprocess.call(command, env=env)
        try:
            exported = export_otlp(state, run_id, run_dir)
            (Path(run_dir) / "artifacts/gateway-export-result.json").write_text(
                json.dumps(exported, ensure_ascii=False) + "\n")
        except Exception as exc:
            print(f"gateway OTLP export failed; raw log retained: {type(exc).__name__}: {exc}", file=sys.stderr)
        return code
    finally:
        (state / "revoked").mkdir(exist_ok=True)
        if binding.exists():
            binding.rename(state / "revoked" / binding.name)
        temporary.unlink(missing_ok=True)


def main():
    if sys.argv[1:2] == ["wrap"]:
        return wrap(sys.argv[2:])
    if sys.argv[1:2] == ["export-otlp"]:
        parser = argparse.ArgumentParser(description="Resend saved run-scoped gateway diagnostics")
        parser.add_argument("--service-state", type=Path, required=True)
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--run-dir", type=Path, required=True)
        args = parser.parse_args(sys.argv[2:])
        result = export_otlp(args.service_state, args.run_id, args.run_dir)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in ("sent", "empty") else 2
    if sys.argv[1:2] == ["resource"]:
        parser = argparse.ArgumentParser(description="Inspect or revoke one registered run binding")
        parser.add_argument("action", choices=("inspect", "cleanup"))
        parser.add_argument("--service-state", type=Path, required=True)
        parser.add_argument("--run-dir", type=Path, required=True)
        parser.add_argument("--run-id", required=True)
        args = parser.parse_args(sys.argv[2:])
        result = binding_resource(args.service_state, args.run_dir, args.run_id, args.action)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in ("not-registered", "active", "revoked", "absent") else 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secrets", type=Path, default=ROOT / ".secrets/models.env")
    parser.add_argument("--runtime", type=Path, required=True,
                        help="Codex Linux runtime directory with bundled LiteLLM")
    parser.add_argument("--python", default="python3.12", help="Python ABI used to build LiteLLM")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--port", type=int, default=4010)
    parser.add_argument("--preserve-parameters", action="store_true",
                        help="保留客户端推理、采样和输出参数，用于按现有配方运行")
    parser.add_argument("--container-host", default="172.17.0.1",
                        help="Docker bridge address of the WSL host")
    args = parser.parse_args()
    state = args.state.resolve()
    state.mkdir(parents=True, exist_ok=True)
    state.chmod(0o700)
    if (state / "gateway.json").exists():
        raise FileExistsError(f"gateway state already exists; choose a new state directory: {state}")
    (state / "bindings").mkdir(mode=0o700)
    (state / "revoked").mkdir(mode=0o700)
    source = state / "code"
    source.mkdir(mode=0o700)
    for name in ("hackathon_gateway_compat.py", "responses_compat.py"):
        shutil.copy2(Path(__file__).with_name(name), source / name)
    token = secrets.token_urlsafe(32)
    config = {
        "model_list": [{
            "model_name": model,
            "litellm_params": {
                "model": "openai/" + model,
                "api_base": "os.environ/" + vendor + "_BASE_URL",
                "api_key": "os.environ/" + vendor + "_API_KEY",
                "use_chat_completions_api": True,
            },
            "model_info": {"mode": "chat"},
        } for model, vendor in MODELS.items()],
        "general_settings": {"master_key": "os.environ/LITELLM_MASTER_KEY",
                             "custom_auth": "hackathon_gateway_compat.user_api_key_auth"},
        "litellm_settings": {
            "telemetry": False,
            "callbacks": ["hackathon_gateway_compat.proxy_handler_instance"],
        },
    }
    (state / "gateway.json").write_text(json.dumps(config, indent=2) + "\n")
    (state / "gateway.env").write_text(
        f"GATEWAY_URL=http://{args.container_host}:{args.port}/v1\nGATEWAY_TOKEN={token}\n"
    )
    (state / "gateway.env").chmod(0o600)
    (state / "service.json").write_text(json.dumps({"service_id": secrets.token_hex(12),
        "port": args.port, "preserve_parameters": args.preserve_parameters,
        "callback_sha256": hashlib.sha256((source / "hackathon_gateway_compat.py").read_bytes()).hexdigest()}, indent=2) + "\n")
    runtime = args.runtime.resolve(strict=True)
    env = dict(os.environ, **read_secrets(args.secrets), LITELLM_MASTER_KEY=token,
               GATEWAY_REQUEST_LOG=str(state / "request-metadata.jsonl"),
               GATEWAY_BINDINGS_DIR=str(state / "bindings"),
               GATEWAY_PRESERVE_PARAMETERS="1" if args.preserve_parameters else "0")
    env["PYTHONPATH"] = ":".join((str(source), str(ROOT / "submission"),
                                    str(runtime / "python")))
    command = [args.python, str(runtime / "bin/litellm"), "--config", str(state / "gateway.json"),
               "--host", "0.0.0.0", "--port", str(args.port)]
    with (state / "gateway.log").open("a") as log:
        return subprocess.call(command, env=env, stdout=log, stderr=log)


if __name__ == "__main__":
    raise SystemExit(main())
