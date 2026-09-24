"""Translate the published ARC-Bench local Runner result to experiment-result.json.

This is a bench adapter. The experiment controller never imports this module.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit, urlunsplit
from zipfile import ZipFile

OTEL_NAMES = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_PROTOCOL",
              "OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_COMPRESSION")
EXCLUDED_SOURCE = {".arc", ".factory26", ".git", "requirements", "node_modules", ".cache", "dist", "build"}


def instrument_entry(agent, destination):
    """在副本外记录标准入口的终态，不修改原制品及其清单。

    原入口保留在 agent/ 子目录，其代码不变，参数与标准输出原样传递。
    这里只观察进程，不解释任意 Harness 的私有会话或交付格式。
    """
    original = destination / 'agent'
    if agent.is_dir():
        shutil.copytree(agent, original)
    else:
        original.mkdir(parents=True)
        with ZipFile(agent) as archive:
            archive.extractall(original)
    shutil.copy2(original / 'requirements.txt', destination / 'requirements.txt')
    (destination / 'main.py').write_text('''import argparse, json, subprocess, sys
from pathlib import Path
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--output-dir',type=Path,required=True)
args,_=parser.parse_known_args()
result=args.output_dir/'.arc/adapter-agent-result.json'
result.parent.mkdir(parents=True,exist_ok=True)
try:
    code=subprocess.call([sys.executable,str(Path(__file__).parent/'agent/main.py'),*sys.argv[1:]])
except BaseException as exc:
    result.write_text(json.dumps({'status':'failed','error':str(exc)})+'\\n')
    raise
result.write_text(json.dumps({'status':'completed' if code==0 else 'failed','exit_code':code})+'\\n')
raise SystemExit(code)
''')
    return destination


def source_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if set(relative.parts) & EXCLUDED_SOURCE or relative.name in {".env", ".env.local", ".env.production"}:
            continue
        if relative.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.as_posix().encode() + b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def container_endpoint(host):
    endpoint = urlsplit(os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
    if not host or any(character in host for character in "/:@"):
        raise ValueError("container OTLP host must be a hostname or IPv4 address")
    return urlunsplit((endpoint.scheme, f"{host}:{endpoint.port}", endpoint.path, "", ""))


def model_environment(base, output, host):
    lines = []
    if base:
        if Path(base).stat().st_mode & 0o077:
            raise ValueError("model environment file must have mode 600")
        for line in Path(base).read_text().splitlines():
            if line.split("=", 1)[0].strip() not in OTEL_NAMES:
                lines.append(line)
    for name in OTEL_NAMES:
        value = container_endpoint(host) if name == "OTEL_EXPORTER_OTLP_ENDPOINT" else os.environ.get(name, "")
        if value:
            lines.append(f"{name}={value}")
    output.write_text("\n".join(lines) + "\n")
    output.chmod(0o600)


def run(args):
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    result_path = workspace / "experiment-result.json"
    base = [sys.executable, str(args.runner / "local_submit.py"), "run",
            "--competition", args.competition, "--task", args.task,
            "--requirements-dir", str(args.requirements)]
    image_id = None
    if not args.prepare_only:
        if not args.image:
            raise ValueError("a built local Runner image is required")
        image = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image], text=True))[0]
        image_id = image["Id"]
        if image.get("Architecture") != "amd64":
            raise ValueError("the published ARC-Bench Runner requires linux/amd64")
    def invoke(command, name):
        environment = dict(os.environ)
        for variable in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "FACTORY26_API_KEY"):
            environment.pop(variable, None)
        with (workspace / f"{name}.stdout.log").open("wb") as stdout, \
             (workspace / f"{name}.stderr.log").open("wb") as stderr:
            return subprocess.run(command, env=environment, stdout=stdout, stderr=stderr).returncode

    with tempfile.TemporaryDirectory(prefix="experiment-arc-env-") as temporary:
        env_file = Path(temporary) / "model.env"
        model_args = []
        if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
            model_environment(args.env_file, env_file, args.container_otlp_host)
            model_args = ["--env-file", str(env_file)]
        elif args.env_file:
            model_args = ["--env-file", str(args.env_file)]
        if args.separate_evaluation and not args.prepare_only:
            if args.noop_script is None:
                raise ValueError("--noop-script is required for separate evaluation")
            generation = workspace / "official-generation"
            instrumented = instrument_entry(args.agent, workspace / 'observed-agent')
            generation_command = base + ["--agent", str(instrumented), "--workspace", str(generation),
                                         "--image", args.image] + model_args
            generation_code = invoke(generation_command, "generation")
            entry = generation / "template/.arc/adapter-agent-result.json"
            if entry.is_file():
                entry_result = json.loads(entry.read_text())
            else:
                entry_result = {"status": "failed", "error": "Agent entry produced no terminal process result"}
            app = generation / "template"
            # Runner 还会部署应用，其退出码可能表示部署失败。
            # 用独立入口结果判断生成，再让下一阶段对冻结应用部署和评分。
            ready = (entry_result.get("status") == "completed" and
                     all((app / part / "package.json").is_file() for part in ("frontend", "backend")))
            if not ready:
                result = {"schema_version": 1, "status": "failed", "stage": "generation",
                          "generation_exit_code": generation_code, "generation": entry_result,
                          "image_id": image_id, "error": "Agent generation did not produce a complete application"}
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
                return 1
            frozen = source_hash(app)
            no_op = workspace / "frozen-evaluator.zip"
            with ZipFile(no_op, "w") as archive:
                archive.write(args.noop_script, "main.py")
                archive.writestr("requirements.txt", "")
            official = workspace / "official-evaluation"
            evaluation_command = base + ["--agent", str(no_op), "--template", str(app),
                                         "--tests-dir", str(args.tests), "--workspace", str(official),
                                         "--image", args.image]
            evaluation_code = invoke(evaluation_command, "evaluation")
            witness = official / "template/.arc/frozen-source.json"
            loaded_hash = json.loads(witness.read_text())["sha256"] if witness.is_file() else None
        else:
            official = workspace / "official"
            command = base + ["--agent", str(args.agent), "--tests-dir", str(args.tests),
                              "--workspace", str(official)] + model_args
            if args.prepare_only:
                command.append("--prepare-only")
            else:
                command.extend(("--image", args.image))
            evaluation_code = invoke(command, "runner")
            generation_code = None
            entry_result = None
            frozen = loaded_hash = None
    upstream = official / "local-result.json"
    if args.prepare_only:
        result = {"schema_version": 1, "status": "completed" if evaluation_code == 0 else "failed",
                  "mode": "prepare-only", "runner_exit_code": evaluation_code,
                  "evaluation": None, "image_id": None}
    elif upstream.is_file():
        evaluation = json.loads(upstream.read_text())
        passed, failed, total = (evaluation.get(key) for key in ("passed", "failed", "total"))
        complete = (evaluation.get("evaluation_status") == "completed" and
                    all(type(value) is int and value >= 0 for value in (passed, failed, total)) and
                    total > 0 and passed + failed == total)
        if args.expected_tests is not None:
            complete = complete and total == args.expected_tests
        if args.separate_evaluation:
            complete = complete and loaded_hash == frozen
        result = {"schema_version": 1, "status": "completed" if complete else "failed",
                  "runner_exit_code": evaluation_code, "image_id": image_id,
                  "evaluation": evaluation}
        if args.separate_evaluation:
            result.update(generation_exit_code=generation_code, generation=entry_result,
                          frozen_source_sha256=frozen, evaluated_source_sha256=loaded_hash)
        if complete:
            result["summary"] = {key: evaluation.get(key) for key in
                                 ("passed", "failed", "total", "test_pass_rate", "score")}
        if not complete:
            result["error"] = ("frozen application identity changed before evaluation"
                               if args.separate_evaluation and loaded_hash != frozen else
                               "local Runner did not return a complete evaluation")
    else:
        result = {"schema_version": 1, "status": "failed", "runner_exit_code": evaluation_code,
                  "image_id": image_id, "error": "local Runner produced no local-result.json"}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if result["status"] == "completed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--tests", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--competition", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--image")
    parser.add_argument("--expected-tests", type=int)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--container-otlp-host", default="host.docker.internal")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--separate-evaluation", action="store_true",
                        help="generate without tests, then score the frozen application with a no-op agent")
    parser.add_argument("--noop-script", type=Path)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
