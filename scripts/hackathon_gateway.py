"""Run one local model gateway for native Pi and Codex Hackathon variants."""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "glm-5.3-flash": "GLM",
    "kimi-k3": "KIMI",
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secrets", type=Path, default=ROOT / ".secrets/models.env")
    parser.add_argument("--runtime", type=Path, required=True,
                        help="Codex Linux runtime directory with bundled LiteLLM")
    parser.add_argument("--python", default="python3.12", help="Python ABI used to build LiteLLM")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--port", type=int, default=4010)
    parser.add_argument("--container-host", default="172.17.0.1",
                        help="Docker bridge address of the WSL host")
    args = parser.parse_args()
    state = args.state.resolve()
    state.mkdir(parents=True, exist_ok=True)
    state.chmod(0o700)
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
        "general_settings": {"master_key": "os.environ/LITELLM_MASTER_KEY"},
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
    runtime = args.runtime.resolve(strict=True)
    env = dict(os.environ, **read_secrets(args.secrets), LITELLM_MASTER_KEY=token,
               GATEWAY_REQUEST_LOG=str(state / "request-metadata.jsonl"))
    env["PYTHONPATH"] = ":".join((str(ROOT / "submission"), str(ROOT / "scripts"),
                                    str(runtime / "python")))
    command = [args.python, str(runtime / "bin/litellm"), "--config", str(state / "gateway.json"),
               "--host", "0.0.0.0", "--port", str(args.port)]
    with (state / "gateway.log").open("a") as log:
        return subprocess.call(command, env=env, stdout=log, stderr=log)


if __name__ == "__main__":
    raise SystemExit(main())
