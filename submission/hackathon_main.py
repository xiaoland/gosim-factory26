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


ROOT = Path(__file__).resolve().parent
CONFIG = raw_main.CONFIG
MODEL_INFO = json.loads((ROOT / "hackathon_models.json").read_text())
ROLES = {
    "explorer": ("glm-5.3-flash", "调查影响当前决定的信息问题，返回有来源、可采用的结论。"),
    "executor": ("glm-5.3-flash", "完成一个有明确效果范围和反馈入口的局部实现或修复。"),
    "browser_operator": ("deepseek-v4-flash-vision-exp", "通过图片或实际页面回答视觉、交互或复现问题。"),
    "advisor": ("kimi-k3", "对问题定义、方案选择或具体失败提供独立判断。"),
}


def write_roles(native, backend, svc, skills):
    role_dir = native / "agents"
    role_dir.mkdir(parents=True, exist_ok=True)
    methods = {"explorer": "explore", "executor": "implementation", "advisor": "design"}
    for name, (model, description) in ROLES.items():
        instruction = (ROOT / "agents" / f"{name}.md").read_text()
        selected = ["agent-browser"] if name == "browser_operator" else ["exploration-tools"]
        if name == "executor":
            selected.append("agent-browser")
        # Supply the small tool guides directly; full SVC stays navigable by skill.
        for skill in selected:
            source = skills / skill / "SKILL.md"
            instruction += f"\n工具指引来源：{source}（相对链接基于 {source.parent}）。\n{source.read_text()}"
        if svc and name in methods:
            selected.append("svc")
            source = skills / "svc/references/methods" / methods[name] / "index.md"
            instruction += f"\nSVC 方法来源：{source}（相对链接基于 {source.parent}）。\n{source.read_text()}"
            instruction += f"\n按问题查阅完整技能入口：{skills / 'svc/SKILL.md'}。\n"
        if backend == "codex":
            data = (f'name = {json.dumps(name)}\n'
                    f'description = {json.dumps(description)}\n'
                    f'model = {json.dumps(model)}\n'
                    'model_reasoning_effort = "none"\n'
                    f'developer_instructions = {json.dumps(instruction)}\n')
            (role_dir / f"{name}.toml").write_text(data)
        else:
            tools = "read, grep, find, ls, bash, edit, write" if name == "executor" else "read, grep, find, ls, bash"
            data = (f"---\nname: {name}\ndescription: {json.dumps(description)}\nmodel: gateway/{model}\n"
                    f"tools: {tools}\ninheritProjectContext: false\ninheritSkills: false\n"
                    'defaultContext: fresh\nsystemPromptMode: append\nextensions: ""\n'
                    f"skillPath: {json.dumps(str(skills))}\nskills: {', '.join(selected)}\n"
                    f"---\n\n{instruction}\n")
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
    if not gateway or not token:
        raise ValueError("GATEWAY_URL and GATEWAY_TOKEN are required")
    output.mkdir(parents=True, exist_ok=True)
    evidence = output / ".arc/hackathon"
    evidence.mkdir(parents=True, exist_ok=True)
    raw_main.restore_executables()
    home = evidence / "home"
    tmp = evidence / "tmp"
    home.mkdir(exist_ok=True)
    tmp.mkdir(exist_ok=True)
    backend = CONFIG["backend"]
    svc = CONFIG["svc"]
    env = dict(os.environ)
    for name in ("OPENAI_API_KEY", "FACTORY26_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "DEEPSEEK_API_KEY"):
        env.pop(name, None)
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"), TMPDIR=str(tmp),
               PATH=str(ROOT / "runtime/bin") + ":/usr/local/bin:/usr/bin:/bin",
               AGENT_BROWSER_EXECUTABLE_PATH=str(ROOT / "runtime/bin/chromium"),
               AGENT_BROWSER_SOCKET_DIR=str(evidence / "b"),
               NODE_PATH=str(ROOT / "runtime/node_modules"), PI_OFFLINE="1")
    browser_skill = home / ".agents/skills/agent-browser"
    browser_skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "skills/agent-browser", browser_skill)
    exploration_skill = home / ".agents/skills/exploration-tools"
    shutil.copytree(ROOT / "skills/exploration-tools", exploration_skill)
    env["MCPORTER_CONFIG"] = str(exploration_skill / "assets/mcporter.json")
    svc_skill = home / ".agents/skills/svc"
    if svc:
        shutil.copytree(ROOT / "skills/svc", svc_skill)
    instruction = raw_main.prompt(requirements, output) + (
        "\n可调用 explorer、executor、browser_operator、advisor 四种原生子代理。根据当前问题选择直接完成或委派，角色没有固定交接顺序。"
        "子代理不继承主会话历史；给出目标、必要事实和材料入口、效果与文件边界、可用反馈及返回要求。"
        "子代理负责局部反馈和修复，你负责整体判断与集成，后续信息通过消息补充。"
        "交互浏览使用 agent-browser；对生成应用可自行用 playwright-core 编写 Playwright 功能检查，"
        "Chrome 路径可由 which chromium 查得。"
        + ("可按需使用 SVC skill；不要把 SVC 文件复制进交付应用。" if svc else "")
    )
    instruction += ("Pi 委派调用显式设置 context:\"fresh\"。" if backend == "pi" else
                    "Codex 委派按实际工具协议显式设置 fork_context:false（V1）或 fork_turns:\"none\"（V2），不复制父历史。")
    raw_main.write_json(evidence / "identity.json", {
        "backend": backend, "svc": svc, "models": {name: model for name, (model, _) in ROLES.items()},
        "main_model": "glm-5.3-flash", "gateway_url": gateway,
        "runtime_source_sha256": CONFIG["runtime_source_sha256"],
    })
    if backend == "pi":
        native = home / ".pi/agent"
        native.mkdir(parents=True)
        models = []
        for model, info in MODEL_INFO.items():
            models.append({"id": model, "name": model, "api": "openai-completions",
                           "reasoning": False, "input": ["text", "image"],
                           **info,
                           "compat": {"supportsDeveloperRole": False,
                                      "supportsStrictMode": False,
                                      "maxTokensField": "max_tokens"}})
        raw_main.write_json(native / "models.json", {"providers": {"gateway": {
            "baseUrl": gateway, "apiKey": "$GATEWAY_TOKEN", "api": "openai-completions",
            "models": models}}})
        write_roles(native, backend, svc, browser_skill.parent)
        raw_main.write_json(native / "settings.json", {"packages": [], "subagents": {"disableBuiltins": True}})
        env["PI_CODING_AGENT_DIR"] = str(native)
        command = [str(ROOT / "runtime/bin/pi"), "--provider", "gateway", "--model", "glm-5.3-flash",
                   "--thinking", "off", "--mode", "json", "--print", "--no-prompt-templates",
                   "--no-themes", "--no-context-files", "--extension",
                   str(ROOT / "runtime/node_modules/pi-subagents/index.ts"),
                   "--skill", str(browser_skill / "SKILL.md"),
                   "--skill", str(exploration_skill / "SKILL.md")]
        if svc:
            command += ["--skill", str(svc_skill / "SKILL.md")]
        command += ["--session", str(evidence / "session.jsonl"), instruction]
    else:
        native = home / ".codex"
        native.mkdir(parents=True)
        env["CODEX_HOME"] = str(native)
        write_roles(native, backend, svc, browser_skill.parent)
        (native / "config.toml").write_text(
            'model = "glm-5.3-flash"\nmodel_provider = "gateway"\n'
            'model_reasoning_effort = "none"\nmodel_reasoning_summary = "none"\n'
            'approval_policy = "never"\nsandbox_mode = "danger-full-access"\nweb_search = "disabled"\n'
            '[features]\nmulti_agent = true\n[agents]\nenabled = true\n'
            '[model_providers.gateway]\n'
            f'name = "Local gateway"\nbase_url = {json.dumps(gateway)}\n'
            'env_key = "GATEWAY_TOKEN"\nwire_api = "responses"\n')
        command = [str(ROOT / "runtime/bin/codex"), "exec", "--json", "--skip-git-repo-check",
                   "--sandbox", "danger-full-access", "-m", "glm-5.3-flash", "-"]
    stop = Event()
    watcher = Thread(target=child_events, args=(native, evidence, stop), daemon=True)
    watcher.start()
    try:
        exporter = LogExporter(evidence, backend, "glm-5.3-flash")
        continuation = 0
        while True:
            code, terminal = raw_main.stream(command, output, env, instruction, evidence,
                                             exporter, send_stdin=backend == "codex",
                                             append=continuation > 0)
            if backend != "pi" or code != 0 or terminal != "length":
                break
            continuation += 1
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
