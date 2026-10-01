"""Translate the published ARC-Bench local Runner result to experiment-result.json.

This is a bench adapter. The experiment controller never imports this module.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit
from zipfile import ZipFile

if __package__:
    from .arc_artifacts import verify as verify_application
    from .docker_workspace import Workspace, observe, selected_endpoint, error_text
else:
    from arc_artifacts import verify as verify_application
    from docker_workspace import Workspace, observe, selected_endpoint, error_text
from lab.docker_endpoint import environment as docker_environment

OTEL_NAMES = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_PROTOCOL",
              "OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_COMPRESSION", *(
                  f"OTEL_EXPORTER_OTLP_{signal}_{setting}"
                  for signal in ("TRACES", "LOGS", "METRICS")
                  for setting in ("ENDPOINT", "PROTOCOL", "HEADERS", "COMPRESSION")))
EXCLUDED_SOURCE = {".arc", ".factory26", ".git", "requirements", "node_modules", ".cache", "dist", "build"}
CONTAINER_LINE = re.compile(r"^Container: (arcbench-local-[0-9a-f]{12})$", re.MULTILINE)
EVENT_SEQUENCE = 0


def emit(kind, **details):
    global EVENT_SEQUENCE
    directory = os.environ.get("EXPERIMENT_EVENT_DIR")
    if not directory:
        return
    EVENT_SEQUENCE += 1
    path = Path(directory) / "arc-bench.jsonl"
    try:
        with path.open("a") as stream:
            stream.write(json.dumps({"schema_version": 1, "producer": "arc-bench-adapter",
                                     "run_id": os.environ.get("EXPERIMENT_RUN_ID"),
                                     "seq": EVENT_SEQUENCE, "time": time.time(), "kind": kind,
                                     **details}, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"ARC evidence event failed: {exc}", file=sys.stderr)


def instrument_entry(agent, destination, *, file_telemetry=False):
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
    shutil.copy2(Path(__file__).with_name('arc_artifacts.py'), destination / 'arc_artifacts.py')
    if file_telemetry:
        from lab import otlp
        import google.protobuf
        import google.rpc
        import opentelemetry.proto
        support = destination / 'collector-support'
        support.mkdir()
        shutil.copy2(otlp.__file__, support / 'otlp.py')
        (support / 'collector.py').write_text('''import json, secrets, signal, sys
from pathlib import Path
from threading import Event
from otlp import connect, initialize, new_session, receiver
database=Path(sys.argv[1])/'telemetry.sqlite'
initialize(database)
session=new_session(database,'arc-adapter')
token=secrets.token_urlsafe(24)
stopped=Event()
signal.signal(signal.SIGTERM,lambda *_: stopped.set())
with receiver() as server:
    server.register(token,database,session)
    print(json.dumps({'endpoint':f'http://127.0.0.1:{server.server_port}','token':token}),flush=True)
    stopped.wait()
with connect(database) as db: db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
''')
        for module in (google.protobuf, google.rpc, opentelemetry.proto):
            source = Path(next(iter(module.__path__)))
            target = support.joinpath(*module.__name__.split('.'))
            shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.so', '*.pyd'))
    (destination / 'main.py').write_text('''import argparse, json, os, signal, subprocess, sys, time
from pathlib import Path
from arc_artifacts import copy_snapshot
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--output-dir',type=Path,required=True)
args,_=parser.parse_known_args()
result=args.output_dir/'.arc/adapter-agent-result.json'
result.parent.mkdir(parents=True,exist_ok=True)
process=None
code=None
cleanup='not-started'
collector=None
environment=dict(os.environ)
support=Path(__file__).parent/'collector-support'
if support.is_dir():
    import select
    telemetry=args.output_dir/'.arc/adapter-telemetry'
    telemetry.mkdir(parents=True,exist_ok=True)
    collector_environment=dict(environment,PYTHONPATH=str(support))
    collector=subprocess.Popen([sys.executable,str(support/'collector.py'),str(telemetry)],
                               env=collector_environment,stdout=subprocess.PIPE,
                               stderr=(telemetry/'collector.log').open('w'),text=True,start_new_session=True)
    if not select.select([collector.stdout],[],[],20)[0]:
        collector.terminate()
        collector.wait(timeout=5)
        raise RuntimeError('workspace collector did not announce its binding')
    binding=json.loads(collector.stdout.readline())
    collector.stdout.close()
    endpoint=binding['endpoint']
    headers='x-experiment-token='+binding['token']
    for name in tuple(environment):
        if name.startswith('OTEL_EXPORTER_OTLP_'): environment.pop(name)
    environment.update(OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,OTEL_EXPORTER_OTLP_PROTOCOL='http/protobuf',
                       OTEL_EXPORTER_OTLP_HEADERS=headers,OTEL_EXPORTER_OTLP_COMPRESSION='none')
    for name in ('TRACES','LOGS','METRICS'):
        prefix='OTEL_EXPORTER_OTLP_'+name
        environment[prefix+'_ENDPOINT']=endpoint+'/v1/'+name.lower()
        environment[prefix+'_PROTOCOL']='http/protobuf'
        environment[prefix+'_HEADERS']=headers
        environment[prefix+'_COMPRESSION']='none'
try:
    process=subprocess.Popen([sys.executable,str(Path(__file__).parent/'agent/main.py'),*sys.argv[1:]],start_new_session=True,env=environment)
    code=process.wait()
except BaseException as exc:
    result.write_text(json.dumps({'status':'failed','exit_code':code,'error':str(exc)})+'\\n')
    raise
finally:
    if process is not None:
        try:
            os.killpg(process.pid,signal.SIGTERM)
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                try: os.killpg(process.pid,0)
                except ProcessLookupError: break
                time.sleep(.1)
            else:
                os.killpg(process.pid,signal.SIGKILL)
            cleanup='signalled'
        except ProcessLookupError:
            cleanup='already-exited'
    if collector is not None:
        collector.terminate()
        try: collector.wait(timeout=20)
        except subprocess.TimeoutExpired:
            collector.kill()
            collector.wait()
        if collector.returncode:
            result.write_text(json.dumps({'status':'failed','collector_exit_code':collector.returncode})+'\\n')
            raise RuntimeError('workspace collector did not stop cleanly')
if code:
    result.write_text(json.dumps({'status':'failed','exit_code':code,'process_group_cleanup':cleanup})+'\\n')
    raise SystemExit(code)
try:
    receipt=copy_snapshot(args.output_dir,args.output_dir.parent/'.lab-artifacts')
except BaseException as exc:
    result.write_text(json.dumps({'status':'failed','exit_code':code,'process_group_cleanup':cleanup,'publication_error':str(exc)})+'\\n')
    raise
result.write_text(json.dumps({'status':'completed','exit_code':code,'process_group_cleanup':cleanup,'application_sha256':receipt['sha256']})+'\\n')
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


def noop_package(workspace, script, receipt):
    output = workspace / "frozen-evaluator.zip"
    with ZipFile(output, "w") as archive:
        archive.write(script, "main.py")
        archive.write(Path(__file__).with_name("arc_artifacts.py"), "arc_artifacts.py")
        archive.write(receipt, "expected-application.json")
        archive.writestr("requirements.txt", "")
    return output


def reported_scenario(report, scenario):
    titles = []
    def walk(suite):
        for spec in suite.get("specs", []):
            titles.extend(spec.get("title", "") for _ in spec.get("tests", []))
        for child in suite.get("suites", []):
            walk(child)
    for suite in report.get("suites", []):
        walk(suite)
    return len(titles) == 1 and len([title for title in titles if title.startswith(scenario + " ::")]) == 1


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
        value = os.environ.get(name, "")
        if host is None:
            continue
        if value and name.endswith("_ENDPOINT"):
            original = urlsplit(value)
            if not host or any(character in host for character in "/:@"):
                raise ValueError("container OTLP host must be a hostname or IPv4 address")
            value = urlunsplit((original.scheme, f"{host}:{original.port}", original.path, "", ""))
        if value:
            lines.append(f"{name}={value}")
    output.write_text("\n".join(lines) + "\n")
    output.chmod(0o600)


def resource_observation(resource_path, *, cleanup=False):
    return observe(resource_path, cleanup=cleanup)


def resource_command(workspace, action):
    records = [resource_observation(path, cleanup=action == "cleanup")
               for path in sorted(workspace.glob("*.resource.json"))]
    receipt = workspace / 'docker-workspace.json'
    if receipt.is_file():
        records.append(Workspace(receipt).finish(cleanup=action == "cleanup"))
    result = {"workspace": str(workspace), "resources": records}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if all(row["status"] in ({"absent", "removed", "not-applicable"} if action == "cleanup" else
                                     {"absent", "owned", "not-applicable"}) for row in records) else 2


def write_resource(path, value):
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, ensure_ascii=False) + "\n")
    temporary.replace(path)


def execute_run(args, endpoint, owner_token):
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if args.selection:
        selected_tests = workspace / "scenario-tests"
        shutil.copytree(args.tests, selected_tests, ignore=shutil.ignore_patterns("selections"))
        shutil.copy2(args.selection, selected_tests / "selection.json")
        args.tests = selected_tests
    result_path = workspace / "experiment-result.json"
    base = [sys.executable, str(args.runner / "local_submit.py"), "run",
            "--competition", args.competition, "--task", args.task,
            "--requirements-dir", str(args.requirements)]
    for flag in ('memory', 'cpus'):
        if getattr(args, flag):
            base.extend(['--' + flag, getattr(args, flag)])
    image_id = None
    if not args.prepare_only:
        if not args.image:
            raise ValueError("a built local Runner image is required")
        image = json.loads(subprocess.check_output(endpoint["argv"] + ["image", "inspect", args.image],
                                                       env=docker_environment(endpoint), text=True))[0]
        image_id = image["Id"]
        if image.get("Architecture") != "amd64":
            raise ValueError("the published ARC-Bench Runner requires linux/amd64")
    transport = Workspace.create(workspace, endpoint, image_id, owner_token=owner_token) if image_id and endpoint['remote'] else None
    file_telemetry = bool(endpoint and endpoint['remote'] and not args.container_otlp_host)
    ownership = transport.value['labels'] if transport else {
        'io.factory26.experiment': os.environ.get('EXPERIMENT_ID', 'standalone'),
        'io.factory26.run': os.environ.get('EXPERIMENT_RUN_ID', workspace.parent.name),
        'io.factory26.attempt': os.environ.get('EXPERIMENT_ATTEMPT', '1'),
        'io.factory26.owner': secrets.token_hex(16)}
    def invoke(command, name):
        environment = dict(os.environ)
        for variable in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "FACTORY26_API_KEY"):
            environment.pop(variable, None)
        stdout_path = workspace / f"{name}.stdout.log"
        stderr_path = workspace / f"{name}.stderr.log"
        owned_workspace = Path(command[command.index("--workspace") + 1]).resolve()
        resource = workspace / f"{name}.resource.json"
        facts = {"workspace": str(owned_workspace), "image_id": image_id,
                 "runner": str(args.runner.resolve()), "state": "not-started", "endpoint": endpoint,
                 "labels": {**ownership, 'io.factory26.stage': name}}
        if transport:
            facts['transport'] = str(transport.path)
        write_resource(resource, facts)
        emit("stage-started", stage=name, resource=str(resource))
        if image_id:
            command = [sys.executable, str(Path(__file__).with_name('docker_workspace.py')),
                       '--resource', str(resource), '--runner', str(args.runner / 'local_submit.py'), '--', *command[2:]]
        process = None
        previous = signal.getsignal(signal.SIGTERM)
        def interrupt(_number, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupt)
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                process = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE, stderr=stderr)
                for line in iter(process.stdout.readline, b""):
                    stdout.write(line)
                    stdout.flush()
                    match = CONTAINER_LINE.search(line.decode(errors="replace"))
                    if match:
                        # The wrapper owns the receipt; stdout only supplies the existing event notification.
                        emit("resource-acquired", stage=name, name=match.group(1), resource=str(resource))
                exit_code = process.wait()
                emit("stage-ended", stage=name, exit_code=exit_code)
                return exit_code
        except BaseException as exc:
            emit("error", stage=name, error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            # Wait for the Runner wrapper to stop its exact container and recover output before fallback cleanup.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            observation = resource_observation(resource, cleanup=True)
            with (workspace / "container-cleanup.jsonl").open("a") as stream:
                stream.write(json.dumps(observation, ensure_ascii=False) + "\n")
            emit("resource-released", stage=name, observation=observation)
            signal.signal(signal.SIGTERM, previous)

    if args.application:
        expected = verify_application(args.application, args.application_receipt)
        no_op = noop_package(workspace, args.noop_script, args.application_receipt)
        official = workspace / "official"
        command = base + ["--agent", str(no_op), "--template", str(args.application),
                          "--tests-dir", str(args.tests), "--workspace", str(official),
                          "--image", image_id]
        code = invoke(command, "evaluation")
        witness = official / "template/.arc/frozen-source.json"
        actual = json.loads(witness.read_text()) if witness.is_file() else None
        upstream = official / "local-result.json"
        evaluation = json.loads(upstream.read_text()) if upstream.is_file() else None
        passed, failed, total = (evaluation.get(key) for key in ("passed", "failed", "total")) if evaluation else (None, None, None)
        complete = (code == 0 and actual is not None and actual.get("sha256") == expected["sha256"]
                    and evaluation is not None and evaluation.get("evaluation_status") == "completed"
                    and all(type(value) is int and value >= 0 for value in (passed, failed, total))
                    and total > 0 and passed + failed == total)
        if args.expected_tests is not None:
            complete = complete and total == args.expected_tests
        if args.expected_scenario:
            report = official / "template/.arc/playwright-report.json"
            complete = complete and report.is_file() and reported_scenario(
                json.loads(report.read_text()), args.expected_scenario)
        result = {"schema_version": 1, "status": "completed" if complete else "failed",
                  "mode": "application-evaluation", "runner_exit_code": code, "image_id": image_id,
                  "application_sha256": expected["sha256"], "loaded_application_sha256": actual.get("sha256") if actual else None,
                  "evaluation": evaluation, "source_run_id": args.source_run_id}
        if complete:
            result["summary"] = {name: evaluation.get(name) for name in ("passed", "failed", "total", "score")}
        else:
            result["error"] = ("application witness does not match frozen input" if actual and
                               actual.get("sha256") != expected["sha256"] else
                               "local Runner did not complete the selected evaluation")
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 0 if complete else 1

    with tempfile.TemporaryDirectory(prefix="experiment-arc-env-") as temporary:
        env_file = Path(temporary) / "model.env"
        model_args = []
        wrapped_env = os.environ.get("ARC_MODEL_ENV_FILE")
        if wrapped_env and args.env_file and Path(wrapped_env).resolve() != args.env_file.resolve():
            raise ValueError("model env was provided both by gateway wrapper and --env-file")
        source_env = Path(wrapped_env) if wrapped_env else args.env_file
        if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
            model_environment(source_env, env_file, None if file_telemetry else (args.container_otlp_host or "host.docker.internal"))
            model_args = ["--env-file", str(env_file)]
        elif source_env:
            model_args = ["--env-file", str(source_env)]
        if (args.separate_evaluation or args.requirements_only) and not args.prepare_only:
            if not args.requirements_only and args.noop_script is None:
                raise ValueError("--noop-script is required for separate evaluation")
            generation = workspace / "official-generation"
            instrumented = instrument_entry(args.agent, workspace / 'observed-agent', file_telemetry=file_telemetry)
            generation_command = base + ["--agent", str(instrumented), "--workspace", str(generation),
                                         "--image", image_id] + model_args
            generation_code = invoke(generation_command, "generation")
            entry = generation / "template/.arc/adapter-agent-result.json"
            if entry.is_file():
                entry_result = json.loads(entry.read_text())
            else:
                entry_result = {"status": "failed", "error": "Agent entry produced no terminal process result"}
            app = generation / ".lab-artifacts/application"
            receipt_path = generation / ".lab-artifacts/receipt.json"
            # Runner 还会部署应用，其退出码可能表示部署失败。
            # 用独立入口结果判断生成，再让下一阶段对冻结应用部署和评分。
            ready = (entry_result.get("status") == "completed" and
                     receipt_path.is_file() and
                     all((app / part / "package.json").is_file() for part in ("frontend", "backend")))
            if receipt_path.is_file():
                emit("artifact-published", stage="generation", receipt=str(receipt_path))
            if not ready:
                result = {"schema_version": 1, "status": "failed", "stage": "generation",
                          "generation_exit_code": generation_code, "generation": entry_result,
                          "image_id": image_id, "error": "Agent generation did not produce a complete application"}
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
                return 1
            if args.requirements_only:
                upstream = generation / "local-result.json"
                runner_result = json.loads(upstream.read_text()) if upstream.is_file() else None
                complete = (generation_code == 0 and runner_result is not None and
                            runner_result.get("evaluation_status") == "skipped" and
                            runner_result.get("container_exit_code") == 0)
                result = {"schema_version": 1, "status": "completed" if complete else "failed",
                          "mode": "requirements-only", "generation_exit_code": generation_code,
                          "generation": entry_result, "image_id": image_id,
                          "evaluation": runner_result, "score": None}
                if not complete:
                    result["error"] = "local Runner did not complete generation and deployment"
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
                return 0 if complete else 1
            frozen = json.loads(receipt_path.read_text())["sha256"]
            verify_application(app, receipt_path)
            no_op = noop_package(workspace, args.noop_script, receipt_path)
            official = workspace / "official-evaluation"
            evaluation_command = base + ["--agent", str(no_op), "--template", str(app),
                                         "--tests-dir", str(args.tests), "--workspace", str(official),
                                         "--image", image_id]
            evaluation_code = invoke(evaluation_command, "evaluation")
            witness = official / "template/.arc/frozen-source.json"
            loaded_hash = json.loads(witness.read_text())["sha256"] if witness.is_file() else None
        else:
            official = workspace / "official"
            instrumented = instrument_entry(args.agent, workspace / 'observed-agent', file_telemetry=file_telemetry) if not args.prepare_only else args.agent
            command = base + ["--agent", str(instrumented), "--workspace", str(official)] + model_args
            if args.tests is not None:
                command += ["--tests-dir", str(args.tests)]
            if args.prepare_only:
                command.append("--prepare-only")
            else:
                command.extend(("--image", image_id))
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
        complete = (evaluation_code == 0 and evaluation.get("evaluation_status") == "completed" and
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


def run(args):
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if (workspace / 'docker-workspace.json').exists():
        raise ValueError('workspace already has a transport receipt; use reconcile/cleanup instead of rerunning')
    endpoint = None if args.prepare_only else selected_endpoint()
    owner_token = secrets.token_hex(16)
    if endpoint:
        write_resource(workspace / 'docker-endpoint.json', endpoint)
    try:
        return execute_run(args, endpoint, owner_token)
    except BaseException as error:
        write_resource(workspace / 'experiment-result.json', {
            'schema_version': 1, 'status': 'cancelled' if isinstance(error, KeyboardInterrupt) else 'failed',
            'error': error_text(error), 'stage': 'execution-or-recovery'})
        raise
    finally:
        receipt = workspace / 'docker-workspace.json'
        if receipt.is_file() and json.loads(receipt.read_text()).get('labels', {}).get('io.factory26.owner') == owner_token:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            outcome = Workspace(receipt).finish(cleanup=True)
            write_resource(workspace / 'workspace-cleanup.json', outcome)
            emit('workspace-released', observation=outcome)


def main():
    if sys.argv[1:2] == ["resource"]:
        resource_parser = argparse.ArgumentParser(description="Inspect or clean registered ARC containers")
        resource_parser.add_argument("action", choices=("inspect", "cleanup"))
        resource_parser.add_argument("--workspace", type=Path, required=True)
        resource_args = resource_parser.parse_args(sys.argv[2:])
        return resource_command(resource_args.workspace.resolve(strict=True), resource_args.action)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--agent", type=Path)
    parser.add_argument("--application", type=Path)
    parser.add_argument("--application-receipt", type=Path)
    parser.add_argument("--source-run-id")
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--tests", type=Path)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--requirements-only", action="store_true")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--competition", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--image")
    parser.add_argument("--memory", help="pass the Docker memory limit to the official local runner")
    parser.add_argument("--cpus", help="pass the Docker CPU quota to the official local runner")
    parser.add_argument("--expected-tests", type=int)
    parser.add_argument("--expected-scenario")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--container-otlp-host", help="explicit collector host; remote default collects workspace files")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--separate-evaluation", action="store_true",
                        help="generate without tests, then score the frozen application with a no-op agent")
    parser.add_argument("--noop-script", type=Path)
    args = parser.parse_args()
    if bool(args.agent) == bool(args.application):
        parser.error("provide exactly one of --agent or --application")
    if args.application and (args.application_receipt is None or args.noop_script is None or args.tests is None):
        parser.error("application evaluation needs receipt, noop script and tests")
    if args.requirements_only != (args.tests is None):
        parser.error("--requirements-only requires --tests to be omitted, and vice versa")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
