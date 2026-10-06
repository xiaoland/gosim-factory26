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
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "harness/model-gateway.json"


def read_assignments(path):
    """Read a private dotenv or provider-env JSON without exposing values."""
    path = Path(path).resolve(strict=True)
    if path.stat().st_mode & 0o077:
        raise ValueError("client environment file must have mode 600")
    if path.suffix == '.json':
        value = json.loads(path.read_text())
        if isinstance(value, dict) and set(value) == {'environment'}:
            value = value['environment']
        if not isinstance(value, dict) or not value:
            raise ValueError("provider environment JSON must be a non-empty object")
        values = value
    else:
        values = {}
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            name, separator, value = line.partition("=")
            if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name.strip()):
                raise ValueError(f"invalid client environment variable: {name}")
            values[name.strip()] = value.strip().strip('"').strip("'")
    if any(not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
           or not isinstance(secret, str) for name, secret in values.items()):
        raise ValueError("provider environment contains an invalid name or value type")
    return values


def write_private(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        output.write(content)
    path.chmod(0o600)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_catalog(path, routes, aliases=None):
    """Select the explicitly activated aliases and ordered deployments."""
    catalog = json.loads(Path(path).read_text())
    entries = catalog.get("model_list")
    if not isinstance(entries, list) or not entries:
        raise ValueError("gateway catalog needs a non-empty native LiteLLM model_list")
    grouped = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("model_name"), str):
            raise ValueError("gateway catalog contains an invalid model entry")
        info = entry.get("model_info", {})
        deployment = info.get("factory26_deployment_id") if isinstance(info, dict) else None
        if not deployment:
            raise ValueError(f"gateway catalog entry lacks factory26_deployment_id: {entry.get('model_name')}")
        params = entry.get("litellm_params", {})
        for field in ("api_base", "api_key"):
            value = params.get(field, "")
            if not isinstance(value, str) or not value.startswith("os.environ/"):
                raise ValueError(f"gateway catalog {field} must reference an environment variable")
            if not value.removeprefix("os.environ/").isidentifier():
                raise ValueError(f"gateway catalog {field} has an invalid environment reference")
        grouped.setdefault(entry["model_name"], []).append((deployment, entry))
    selected = {}
    active = set(aliases) if aliases else set(grouped)
    unknown_aliases = active - set(grouped)
    if unknown_aliases:
        raise ValueError(f"selected unknown catalog alias: {sorted(unknown_aliases)}")
    for alias in sorted(active):
        candidates = grouped[alias]
        wanted = routes.get(alias)
        if wanted:
            wanted = wanted if isinstance(wanted, list) else [wanted]
            matches = [entry for wanted_id in wanted for deployment, entry in candidates
                       if deployment == wanted_id]
            if len(matches) != len(wanted) or len({entry['model_info']['factory26_deployment_id'] for entry in matches}) != len(wanted):
                raise ValueError(f"route {alias}={wanted!r} does not select each deployment exactly once")
            selected[alias] = matches
            continue
        defaults = [entry for deployment, entry in candidates
                    if entry.get("model_info", {}).get("factory26_default") is True]
        if len(defaults) != 1:
            raise ValueError(f"alias {alias!r} needs one explicit default or --route ALIAS=DEPLOYMENT_ID")
        selected[alias] = defaults
    unknown = set(routes) - set(grouped)
    if unknown:
        raise ValueError(f"route selects unknown catalog alias: {sorted(unknown)}")
    config = {key: value for key, value in catalog.items() if key != "model_list"}
    config["model_list"] = [dict(entry, litellm_params=dict(entry["litellm_params"], order=order))
                          for entries in selected.values() for order, entry in enumerate(entries)]
    snapshot = []
    for alias, entries in selected.items():
        for order, entry in enumerate(entries):
            info = entry["model_info"]
            params = entry["litellm_params"]
            snapshot.append({"alias": alias, "order": order,
                             "deployment_id": info["factory26_deployment_id"],
                             "provider": info["factory26_provider"], "plan": info["factory26_plan"],
                             "wire_model": params["model"].removeprefix("openai/"),
                             "base_url_env": params["api_base"].removeprefix("os.environ/"),
                             "model_info": {key: info[key] for key in
                                            ("contextWindow", "maxTokens", "compat") if key in info}})
    return config, sorted(snapshot, key=lambda row: row["alias"])


def binding_resource(service_state, run_dir, run_id, action):
    state = Path(service_state).resolve(strict=True)
    marker = Path(run_dir) / ".private/gateway-binding.json"
    if not marker.is_file():
        return {"status": "not-registered"}
    binding = json.loads(marker.read_text())
    service = json.loads((state / "service.json").read_text())
    gateway_path = state / "gateway.json"
    if service.get("config_sha256") and service["config_sha256"] != digest(gateway_path):
        raise ValueError("gateway configuration changed after service preparation")
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
            if row.get("run_id") == run_id or row.get("attempt_id") == run_id:
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
    legacy_run_id = os.environ.get("EXPERIMENT_RUN_ID")
    attempt_id = os.environ.get("FACTORY26_EXP_ATTEMPT_ID") or legacy_run_id
    run_dir = os.environ.get("FACTORY26_EXP_ATTEMPT_DIR") or os.environ.get("EXPERIMENT_RUN_DIR")
    experiment_id = os.environ.get("FACTORY26_EXP_EXPERIMENT_ID") or os.environ.get("EXPERIMENT_ID")
    incarnation = os.environ.get("FACTORY26_EXP_INCARNATION")
    if not attempt_id or not run_dir:
        raise ValueError("wrapper needs FACTORY26_EXP_ATTEMPT_ID/DIR or legacy EXPERIMENT_RUN_ID/DIR")
    run_id = legacy_run_id or attempt_id
    state = args.service_state.expanduser().resolve(strict=True)
    service = json.loads((state / "service.json").read_text())
    if service.get("config_sha256") != digest(state / "gateway.json"):
        raise ValueError("gateway configuration changed after service preparation")
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
    write_private(binding, json.dumps({"run_id": run_id, "legacy_run_id": legacy_run_id,
                                        "attempt_id": attempt_id, "experiment_id": experiment_id,
                                        "incarnation": incarnation, "service_id": service["service_id"],
                                        "config_sha256": service["config_sha256"],
                                        "created_at": time.time()}, ensure_ascii=False) + "\n")
    try:
        write_private(private / "gateway-binding.json", json.dumps({
            "run_id": run_id, "legacy_run_id": legacy_run_id,
            "attempt_id": attempt_id, "experiment_id": experiment_id,
            "incarnation": incarnation, "config_sha256": service["config_sha256"],
            "service_id": service["service_id"], "binding_id": binding_id},
            ensure_ascii=False) + "\n")
        write_private(temporary, "".join(f"{name}={value}\n" for name, value in selected.items()))
        env = dict(os.environ)
        env[args.env_file_var] = str(temporary)
        code = subprocess.call(command, env=env)
        try:
            exported = export_otlp(state, attempt_id, run_dir)
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
    parser.add_argument("--listen-host", default="0.0.0.0",
                        help="网关监听地址；远端容器可使用明确可达的宿主地址")
    parser.add_argument("--preserve-parameters", action="store_true",
                        help="保留客户端推理、采样和输出参数，用于按现有配方运行")
    parser.add_argument("--gateway-config", type=Path, default=DEFAULT_CATALOG,
                        help="原生 LiteLLM model_list catalog")
    parser.add_argument("--route", action="append", default=[], metavar="ALIAS=DEPLOYMENT_ID[,DEPLOYMENT_ID...]",
                        help="为稳定 alias 选择按顺序排列的一个或多个 deployment")
    parser.add_argument("--alias", action="append", default=[], metavar="ALIAS",
                        help="只激活列出的稳定 alias；避免目录其它 alias 被隐式装配")
    parser.add_argument("--model-vendor", action="append", default=[], metavar="MODEL=VENDOR",
                        help=argparse.SUPPRESS)
    parser.add_argument("--prepare-only", action="store_true",
                        help="只生成并读回网关配置，不启动 LiteLLM")
    parser.add_argument("--container-host", default="172.17.0.1",
                        help="Docker bridge address of the WSL host")
    args = parser.parse_args()
    if args.model_vendor:
        raise ValueError("--model-vendor 已移除；请使用 --gateway-config 与 --route ALIAS=DEPLOYMENT_ID")
    routes = {}
    for route in args.route:
        alias, separator, deployment = route.partition("=")
        if not separator or not alias or not deployment or alias in routes:
            raise ValueError(f"invalid route {route!r}; expected unique ALIAS=DEPLOYMENT_ID[,DEPLOYMENT_ID...]")
        routes[alias] = [item for item in deployment.split(",") if item]
    config, snapshot = prepare_catalog(args.gateway_config.resolve(strict=True), routes, args.alias)
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
    config.setdefault("general_settings", {}).update(
        master_key="os.environ/LITELLM_MASTER_KEY",
        custom_auth="hackathon_gateway_compat.user_api_key_auth")
    config.setdefault("litellm_settings", {}).update(
        telemetry=False, callbacks=["hackathon_gateway_compat.proxy_handler_instance"])
    config["model_list"] = [dict(entry, litellm_params=dict(entry["litellm_params"],
        use_chat_completions_api=True), model_info=dict(entry.get("model_info", {}))) for entry in config["model_list"]]
    (state / "gateway.json").write_text(json.dumps(config, indent=2) + "\n")
    (state / "gateway.env").write_text(
        f"GATEWAY_URL=http://{args.container_host}:{args.port}/v1\nGATEWAY_TOKEN={token}\n"
    )
    (state / "gateway.env").chmod(0o600)
    config_sha256 = digest(state / "gateway.json")
    (state / "service.json").write_text(json.dumps({"service_id": secrets.token_hex(12),
        "port": args.port, "listen_host": args.listen_host,
        "preserve_parameters": args.preserve_parameters,
        "config_sha256": config_sha256,
        "callback_sha256": hashlib.sha256((source / "hackathon_gateway_compat.py").read_bytes()).hexdigest()}, indent=2) + "\n")
    runtime = args.runtime.resolve(strict=True)
    secret_values = read_assignments(args.secrets)
    selected_refs = set()
    for entry in config["model_list"]:
        for field in ("api_base", "api_key"):
            selected_refs.add(entry["litellm_params"][field].removeprefix("os.environ/"))
    missing = sorted(name for name in selected_refs if not secret_values.get(name))
    if missing:
        raise ValueError(f"selected gateway deployment references missing environment variables: {missing}")
    for entry in config["model_list"]:
        reference = entry["litellm_params"]["api_base"]
        prefix = "os.environ/"
        if not reference.startswith(prefix):
            raise ValueError("gateway catalog api_base must use an environment reference")
        entry["litellm_params"]["api_base"] = secret_values[reference.removeprefix(prefix)]
    (state / "gateway.json").write_text(json.dumps(config, indent=2) + "\n")
    config_sha256 = digest(state / "gateway.json")
    service_record = json.loads((state / "service.json").read_text())
    service_record["config_sha256"] = config_sha256
    (state / "service.json").write_text(json.dumps(service_record, indent=2) + "\n")
    for row in snapshot:
        row["endpoint"] = secret_values[row["base_url_env"]]
        endpoint = urlsplit(row["endpoint"])
        if endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
            raise ValueError(f"gateway endpoint is not a public HTTP URL: {row['alias']}")
    snapshot_record = {"catalog_sha256": digest(args.gateway_config),
                       "config_sha256": digest(state / "gateway.json"), "routes": snapshot}
    (state / "routing-snapshot.json").write_text(json.dumps(snapshot_record, indent=2) + "\n")
    env = dict(os.environ, **secret_values, LITELLM_MASTER_KEY=token,
               GATEWAY_REQUEST_LOG=str(state / "request-metadata.jsonl"),
               GATEWAY_BINDINGS_DIR=str(state / "bindings"))
    env["PYTHONPATH"] = ":".join((str(source), str(ROOT / "submission"),
                                    str(runtime / "python")))
    if args.prepare_only:
        loaded = json.loads((state / "routing-snapshot.json").read_text())
        if loaded["config_sha256"] != digest(state / "gateway.json"):
            raise ValueError("prepared gateway routing snapshot failed readback")
        print(json.dumps(loaded, ensure_ascii=False))
        return 0
    command = [args.python, str(runtime / "bin/litellm"), "--config", str(state / "gateway.json"),
               "--host", args.listen_host, "--port", str(args.port)]
    with (state / "gateway.log").open("a") as log:
        return subprocess.call(command, env=env, stdout=log, stderr=log)


if __name__ == "__main__":
    raise SystemExit(main())
