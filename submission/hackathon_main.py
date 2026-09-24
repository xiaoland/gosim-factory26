"""Native Pi/Codex entry for the four local Hackathon configurations."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from threading import Event, Thread

import raw_main
from raw_otlp import LogExporter
from native_browser import install as install_browser


ROOT = Path(__file__).resolve().parent
CONFIG = raw_main.CONFIG
MAX_PI_CONTINUATIONS = 8
ROLES = {
    "explorer": ("glm-5.3-flash", "Read the public requirements and current application. Return concrete findings; do not edit files."),
    "executor": ("glm-5.3-flash", "Implement one bounded part of the application. Coordinate files with the parent and validate the result."),
    "browser_operator": ("deepseek-v4-flash-vision-exp", "Inspect reference images and the running application with agent-browser. Report screenshots, console errors and reproducible behavior. Do not read benchmark tests."),
    "advisor": ("kimi-k3", "Give a read-only independent judgment on requirements, design or a failure. Identify decisive evidence and risks."),
}


def write_roles(native, backend, svc, browser_skill, svc_skill):
    role_dir = native / "agents"
    role_dir.mkdir(parents=True, exist_ok=True)
    for name, (model, instruction) in ROLES.items():
        if svc and name != "browser_operator":
            instruction += " The SVC skill is available for planning and verification when useful."
        if backend == "codex":
            data = (f'name = {json.dumps(name)}\n'
                    f'description = {json.dumps(instruction)}\n'
                    f'model = {json.dumps(model)}\n'
                    'model_reasoning_effort = "none"\n'
                    f'developer_instructions = {json.dumps(instruction)}\n')
            (role_dir / f"{name}.toml").write_text(data)
        else:
            skill = svc_skill if svc and name != "browser_operator" else browser_skill if name == "browser_operator" else None
            tools = "read, grep, find, ls, bash, edit, write" if name == "executor" else "read, grep, find, ls, bash"
            data = (f"---\nname: {name}\ndescription: {instruction}\nmodel: gateway/{model}\n"
                    f"tools: {tools}\ninheritProjectContext: false\n"
                    + (f"skillPath: {skill}\nskills: {skill.name}\n" if skill else "")
                    + f"---\n\n{instruction}\n")
            (role_dir / f"{name}.md").write_text(data)


def child_events(native, evidence, stop):
    """Keep native child sessions intact and mirror their JSONL into OTLP."""
    exporter = LogExporter(evidence, CONFIG["backend"] + "-session", "mixed")
    positions = {}
    while True:
        for path in native.rglob("*.jsonl"):
            if not path.is_file():
                continue
            try:
                with path.open(errors="replace") as stream:
                    stream.seek(positions.get(path, 0))
                    for line in stream:
                        exporter.add(json.dumps({"session": str(path.relative_to(native)),
                                                 "event": line.rstrip("\n")}, ensure_ascii=False))
                    positions[path] = stream.tell()
            except OSError as exc:
                with (evidence / "otlp-errors.log").open("a") as output:
                    output.write(f"{path}: {exc}\n")
        if stop.wait(2):
            break
    exporter.flush()


def run(requirements, output):
    if not (requirements / "requirements.yaml").is_file():
        raise ValueError("public requirements.yaml is missing")
    gateway = os.environ.get("GATEWAY_URL", "")
    token = os.environ.get("GATEWAY_TOKEN", "")
    if not gateway.startswith("http://") or not token:
        raise ValueError("GATEWAY_URL and GATEWAY_TOKEN are required")
    output.mkdir(parents=True, exist_ok=True)
    evidence = output / ".arc/hackathon"
    evidence.mkdir(parents=True, exist_ok=True)
    raw_main.restore_executables()
    home = evidence / "home"
    tmp = evidence / "tmp"
    home.mkdir(exist_ok=True)
    tmp.mkdir(exist_ok=True)
    browser_bin = install_browser(evidence, ROOT / "runtime")
    backend = CONFIG["backend"]
    svc = CONFIG["svc"]
    env = dict(os.environ)
    for name in ("OPENAI_API_KEY", "FACTORY26_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "DEEPSEEK_API_KEY"):
        env.pop(name, None)
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"), TMPDIR=str(tmp),
               PATH=str(browser_bin) + ":" + str(ROOT / "runtime/bin") + ":/usr/local/bin:/usr/bin:/bin",
               NODE_PATH=str(ROOT / "runtime/node_modules"), PI_OFFLINE="1")
    browser_skill = home / ".agents/skills/agent-browser"
    browser_skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "skills/agent-browser", browser_skill)
    svc_skill = home / ".agents/skills/svc"
    if svc:
        shutil.copytree(ROOT / "skills/svc", svc_skill)
    instruction = raw_main.prompt(requirements, output) + (
        "\n可调用 explorer、executor、browser_operator、advisor 四种原生子代理：先让 explorer 梳理需求，"
        "让 advisor 检查关键设计，让 executor 承担有界实现，让 browser_operator 对参考图和运行页面取证。"
        "交互浏览使用 agent-browser；对生成应用可自行用 playwright-core 编写 Playwright 功能检查，"
        "Chrome 路径可由 which chromium 查得。"
        + ("可按需使用 SVC skill；不要把 SVC 文件复制进交付应用。" if svc else "")
    )
    raw_main.write_json(evidence / "identity.json", {
        "backend": backend, "svc": svc, "models": {name: model for name, (model, _) in ROLES.items()},
        "main_model": "glm-5.3-flash", "gateway_url": gateway,
        "runtime_source_sha256": CONFIG["runtime_source_sha256"],
    })
    if backend == "pi":
        native = home / ".pi/agent"
        native.mkdir(parents=True)
        models = []
        for model, context in (("glm-5.3-flash", 1000000), ("kimi-k3", 262144),
                               ("deepseek-v4-flash-vision-exp", 128000)):
            models.append({"id": model, "name": model, "api": "openai-completions",
                           "reasoning": False, "input": ["text", "image"],
                           "contextWindow": context, "maxTokens": 16384,
                           "compat": {"supportsDeveloperRole": False,
                                      "supportsStrictMode": False,
                                      "maxTokensField": "max_tokens"}})
        raw_main.write_json(native / "models.json", {"providers": {"gateway": {
            "baseUrl": gateway, "apiKey": "$GATEWAY_TOKEN", "api": "openai-completions",
            "models": models}}})
        write_roles(native, backend, svc, browser_skill, svc_skill)
        env["PI_CODING_AGENT_DIR"] = str(native)
        command = [str(ROOT / "runtime/bin/pi"), "--provider", "gateway", "--model", "glm-5.3-flash",
                   "--thinking", "off", "--mode", "json", "--print", "--no-prompt-templates",
                   "--no-themes", "--no-context-files", "--extension",
                   str(ROOT / "runtime/node_modules/pi-subagents/index.ts"),
                   "--skill", str(browser_skill / "SKILL.md")]
        if svc:
            command += ["--skill", str(svc_skill / "SKILL.md")]
        command += ["--session", str(evidence / "session.jsonl"), instruction]
    else:
        native = home / ".codex"
        native.mkdir(parents=True)
        env["CODEX_HOME"] = str(native)
        write_roles(native, backend, svc, browser_skill, svc_skill)
        (native / "config.toml").write_text(
            'model = "glm-5.3-flash"\nmodel_provider = "gateway"\n'
            'model_reasoning_effort = "none"\nmodel_reasoning_summary = "none"\n'
            'approval_policy = "never"\nsandbox_mode = "danger-full-access"\nweb_search = "disabled"\n'
            '[features]\nmulti_agent = true\n[agents]\nenabled = true\n'
            'max_concurrent_threads_per_session = 4\n[model_providers.gateway]\n'
            f'name = "Local gateway"\nbase_url = {json.dumps(gateway)}\n'
            'env_key = "GATEWAY_TOKEN"\nwire_api = "responses"\n')
        command = [str(ROOT / "runtime/bin/codex"), "exec", "--json", "--skip-git-repo-check",
                   "--sandbox", "danger-full-access", "-m", "glm-5.3-flash", "-"]
    stop = Event()
    watcher = Thread(target=child_events, args=(native, evidence, stop), daemon=True)
    watcher.start()
    try:
        exporter = LogExporter(evidence, backend, "glm-5.3-flash")
        for continuation in range(MAX_PI_CONTINUATIONS + 1 if backend == "pi" else 1):
            code, terminal = raw_main.stream(command, output, env, instruction, evidence,
                                             exporter, send_stdin=backend == "codex",
                                             append=continuation > 0)
            if backend != "pi" or code != 0 or terminal != "length" or continuation == MAX_PI_CONTINUATIONS:
                break
            command[-1] = ("上一轮模型输出达到长度上限。继续当前会话中未完成的实现工作；"
                           "不要重新阅读整份需求。先完成必要代码，再验证并交付应用。")
        completed = code == 0 and terminal == ("stop" if backend == "pi" else "turn.completed")
        raw_main.write_json(evidence / "entry-result.json", {
            "status": "completed" if completed else "failed", "exit_code": code,
            "terminal": terminal, "continuations": continuation})
        return 0 if completed else 1
    except BaseException as exc:
        raw_main.write_json(evidence / "entry-result.json", {
            "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        raise
    finally:
        stop.set()
        watcher.join(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return run(args.requirements.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
