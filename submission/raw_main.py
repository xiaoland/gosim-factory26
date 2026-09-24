"""Direct Pi or Codex baseline entry for the official local Runner."""

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from raw_otlp import LogExporter


ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "raw-config.json").read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def restore_executables():
    for relative in json.loads((ROOT / "runtime-executables.json").read_text()):
        path = ROOT / relative
        path.chmod(path.stat().st_mode | 0o111)


def prompt(requirements, output):
    return f"""请只依据 {requirements} 内的公开需求，独立实现 Web 应用。在 {output} 内工作，阅读 requirements.md、requirements.yaml 和参考材料，覆盖所有明确需求、场景与初始数据，并自行做必要的检查。

交付目录应包含 frontend/package.json 的 build 脚本和 backend/package.json 的 start 脚本，应用运行目标为 Node 20。后端在 HOST=0.0.0.0、PORT=3000 时服务前端和 API。保留现有 requirements/ 和 .arc/，不要写入 .factory26/ 或 deploy.sh。完成后停止自建服务。

不得读取、搜索或使用外部验收测试、benchmark 实现、参考应用及历史评分。可以安装应用依赖，但不要 push、发布或修改外部系统。无需询问人工；常规歧义自行判断并在最终说明中记录。"""


def stream(command, cwd, env, instruction, evidence, exporter, send_stdin=False, append=False):
    mode = "a" if append else "w"
    with (evidence / "events.jsonl").open(mode) as events, (evidence / "stderr.log").open(mode) as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE if send_stdin else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=stderr, text=True,
                                   start_new_session=True)
        if send_stdin:
            process.stdin.write(instruction)
            process.stdin.close()
        terminal = None
        for line in process.stdout:
            events.write(line)
            events.flush()
            exporter.add(line.rstrip("\n"))
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if CONFIG["backend"] == "pi" and event.get("type") == "message_end":
                message = event.get("message") or {}
                if message.get("role") == "assistant":
                    terminal = message.get("stopReason")
            elif CONFIG["backend"] == "codex" and event.get("type") in ("turn.completed", "turn.failed"):
                terminal = event["type"]
        code = process.wait()
        stop_group(process)
    exporter.flush()
    return code, terminal


def codex_proxy(evidence, env):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    proxy = evidence / "adapter"
    proxy.mkdir()
    config = {"model_list": [{"model_name": CONFIG["model"],
              "litellm_params": {"model": "openai/" + CONFIG["model"],
              "api_base": env["OPENAI_BASE_URL"], "api_key": "os.environ/OPENAI_API_KEY",
              "use_chat_completions_api": True,
              "extra_body": CONFIG["chat_parameters"]}, "model_info": {"mode": "chat"}}],
              "litellm_settings": {"telemetry": False,
                                   "callbacks": ["raw_responses_compat.proxy_handler_instance"]}}
    write_json(proxy / "config.json", config)
    adapter_env = dict(env, PYTHONPATH=str(ROOT) + ":" + str(ROOT / "runtime/python"))
    with (proxy / "adapter.log").open("w") as log:
        process = subprocess.Popen([str(ROOT / "runtime/bin/litellm"), "--config", str(proxy / "config.json"),
                                    "--host", "127.0.0.1", "--port", str(port)],
                                   env=adapter_env, stdout=log, stderr=log, start_new_session=True)
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Codex Responses adapter exited; see adapter.log")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health/liveliness", timeout=1) as response:
                    if response.status == 200:
                        return process, f"http://127.0.0.1:{port}/v1"
            except OSError:
                pass
            time.sleep(.2)
        raise RuntimeError("Codex Responses adapter did not become ready")
    except BaseException:
        stop_group(process)
        raise


def run(requirements, output):
    if not requirements.is_dir() or not (requirements / "requirements.yaml").is_file():
        raise ValueError("public requirements directory is missing")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("FACTORY26_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY or FACTORY26_API_KEY is required")
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://api.arc-bench.com/v1"
    output.mkdir(parents=True, exist_ok=True)
    evidence = output / ".arc/raw"
    evidence.mkdir(parents=True, exist_ok=True)
    restore_executables()
    env = dict(os.environ, OPENAI_API_KEY=api_key, OPENAI_BASE_URL=base_url)
    env.update(HOME=str(evidence / "home"), XDG_CONFIG_HOME=str(evidence / "home/.config"),
               TMPDIR=str(evidence / "tmp"), PATH=str(ROOT / "runtime/bin") + ":/usr/local/bin:/usr/bin:/bin",
               PI_OFFLINE="1", FACTORY26_API_KEY=api_key)
    for directory in (evidence / "home", evidence / "tmp"):
        directory.mkdir(parents=True, exist_ok=True)
    exporter = LogExporter(evidence, CONFIG["backend"], CONFIG["model"])
    instruction = prompt(requirements, output)
    write_json(evidence / "identity.json", {"backend": CONFIG["backend"], "model": CONFIG["model"],
                                         "chat_parameters": CONFIG["chat_parameters"],
                                         "base_url": base_url,
                                         "runtime_source_sha256": CONFIG["runtime_source_sha256"]})
    adapter = None
    try:
        if CONFIG["backend"] == "pi":
            native = evidence / "home/.pi/agent"
            native.mkdir(parents=True)
            write_json(native / "models.json", {"providers": {"raw": {
                "baseUrl": base_url, "apiKey": "$FACTORY26_API_KEY",
                "api": "openai-completions", "models": [CONFIG["descriptor"]]}}})
            env["PI_CODING_AGENT_DIR"] = str(native)
            thinking = ("off" if CONFIG["chat_parameters"]["thinking"]["type"] == "disabled"
                        else CONFIG["chat_parameters"].get("reasoning_effort", "high"))
            command = [str(ROOT / "runtime/bin/pi"), "--provider", "raw", "--model", CONFIG["model"],
                       "--thinking", thinking, "--mode", "json", "--print", "--no-extensions",
                       "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files",
                       "--session", str(evidence / "session.jsonl"), instruction]
        else:
            native = evidence / "home/.codex"
            native.mkdir(parents=True)
            env["CODEX_HOME"] = str(native)
            adapter, endpoint = codex_proxy(evidence, env)
            (native / "config.toml").write_text(
                f'model = {json.dumps(CONFIG["model"])}\nmodel_provider = "raw"\n'
                'approval_policy = "never"\nsandbox_mode = "danger-full-access"\nweb_search = "disabled"\n'
                'model_reasoning_effort = "none"\n'
                'model_reasoning_summary = "none"\n[model_providers.raw]\nname = "Raw baseline"\n'
                f'base_url = {json.dumps(endpoint)}\nenv_key = "OPENAI_API_KEY"\nwire_api = "responses"\n')
            command = [str(ROOT / "runtime/bin/codex"), "exec", "--json", "--skip-git-repo-check",
                       "--sandbox", "danger-full-access", "-m", CONFIG["model"], "-"]
        code, terminal = stream(command, output, env, instruction, evidence, exporter,
                                send_stdin=CONFIG["backend"] == "codex")
        completed = code == 0 and terminal == ("stop" if CONFIG["backend"] == "pi" else "turn.completed")
        write_json(evidence / "entry-result.json", {"status": "completed" if completed else "failed",
                                                  "exit_code": code, "terminal": terminal})
        return 0 if completed else 1
    except BaseException as exc:
        write_json(evidence / "entry-result.json", {"status": "failed",
                                                 "error": f"{type(exc).__name__}: {exc}"})
        raise
    finally:
        if adapter is not None:
            stop_group(adapter)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return run(args.requirements.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
