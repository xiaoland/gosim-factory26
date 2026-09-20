#!/usr/bin/env python3
"""Codex app-server / Pi、SVC / braid 与官方 ARC-bench 的单任务实验入口。"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import shlex
import signal
import socket
import subprocess
import tempfile
import tarfile
import time
import urllib.request
import uuid
import sources

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "third_party/arc-bench"


def save(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def phase(path, metadata, name, log=None, **fields):
    now = time.time()
    metadata.update(phase=name, phase_started_at=now, updated_at=now, phase_log=log, **fields)
    save(path, metadata)


def capture(*args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()
            and not {"node_modules", ".git", "__pycache__"}.intersection(p.relative_to(folder).parts)}


def signal_group(proc, sig):
    try:
        os.killpg(proc.pid,sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can retain only inaccessible zombie group members after exit.
        states=capture('ps','-ax','-o','pgid=,stat=').splitlines()
        if any(line.split()[0]==str(proc.pid) and not line.split()[1].startswith('Z')
               for line in states if len(line.split())==2):
            raise


def stop(proc):
    signal_group(proc,signal.SIGTERM)
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: pass
    signal_group(proc,signal.SIGKILL)
    proc.wait()


def workspace_processes(work):
    """Include app-server tool jobs that start their own process sessions."""
    found=[]
    if platform.system()=='Linux':
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit(): continue
            try:
                cwd=(entry/'cwd').resolve(strict=True)
                if cwd.is_relative_to(work): found.append(int(entry.name))
            except (OSError,RuntimeError): pass
    else:
        result=subprocess.run(['lsof','-a','-u',str(os.getuid()),'-d','cwd','-F','pn'],capture_output=True,text=True)
        if result.returncode not in (0,1): raise RuntimeError('cannot inspect workspace processes')
        pid=None
        for line in result.stdout.splitlines():
            if line.startswith('p'): pid=int(line[1:])
            elif line.startswith('n') and pid and Path(line[1:]).is_relative_to(work): found.append(pid)
    return [pid for pid in found if pid!=os.getpid()]


def cleanup_workspace(work):
    pids=workspace_processes(work)
    for pid in pids:
        try: os.kill(pid,signal.SIGTERM)
        except ProcessLookupError: pass
    if pids: time.sleep(.2)
    for pid in workspace_processes(work):
        try: os.kill(pid,signal.SIGKILL)
        except ProcessLookupError: pass
    remaining=workspace_processes(work)
    if remaining: raise RuntimeError(f'workspace processes remain after cleanup: {remaining}')
    return pids


def sandbox_profile(denied, readonly):
    return '(version 1)\n(allow default)\n' + ''.join(
        f'(deny file-read* file-write* (subpath {json.dumps(str(p.resolve()))}))\n'
        for p in denied) + f'(deny file-write* (subpath {json.dumps(str(readonly.resolve()))}))\n'


def api_key():
    path = Path.home() / ".config/factory26/llm.env"
    for line in path.read_text().splitlines():
        if line.startswith("FACTORY26_API_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise RuntimeError(f"请先在 {path} 填写 FACTORY26_API_KEY")


def pi_usage(session):
    entries = [json.loads(line) for line in session.read_text().splitlines()]
    messages = [entry.get("message", {}) for entry in entries]
    assistants = [m for m in messages if m.get("role") == "assistant"]
    usages = [m["usage"] for m in assistants if isinstance(m.get("usage"), dict)]
    summaries = [entry for entry in entries if entry.get("type") in ("compaction", "branch_summary")]
    usages += [entry["usage"] for entry in summaries if isinstance(entry.get("usage"), dict)]
    if not assistants or assistants[-1].get("stopReason") != "stop":
        raise RuntimeError("Pi 未正常完成；参阅原生 session 和 stderr")
    totals = {key: sum(u[key] for u in usages) if usages and all(key in u for u in usages) else None
              for key in ("input", "output", "cacheRead", "cacheWrite", "reasoning", "totalTokens")}
    return {"assistant_responses": len(assistants), "tokens": totals, "estimated_cost": None,
            "summary_events_without_usage": sum(not isinstance(e.get("usage"), dict) for e in summaries)}


def codex_usage(sessions):
    totals=[]
    for session in sessions:
        usage=None
        for line in session.read_text().splitlines():
            event=json.loads(line)
            payload=event.get('payload',{})
            if event.get('type')=='event_msg' and payload.get('type')=='token_count':
                usage=(payload.get('info') or {}).get('total_token_usage') or usage
        if usage is not None: totals.append(usage)
    if len(totals)!=len(sessions) or not totals:
        return {'sessions':len(sessions),'tokens':None,'estimated_cost':None}
    keys=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
    native={key:sum(u[key] for u in totals) if all(key in u for u in totals) else None for key in keys}
    return {'sessions':len(sessions),'native_tokens':native,'estimated_cost':None}


def isolation_prefix(work, inputs):
    denied = [ROOT, Path.home() / '.codex', Path.home() / '.pi', Path.home() / '.config/factory26']
    if platform.system() == 'Darwin':
        profile = work / 'isolation.sb'
        profile.write_text(sandbox_profile(denied, inputs))
        return ['sandbox-exec', '-f', str(profile)]
    if platform.system() == 'Linux' and shutil.which('bwrap'):
        command = ['bwrap', '--die-with-parent', '--unshare-pid', '--ro-bind', '/', '/',
                   '--dev', '/dev', '--proc', '/proc', '--bind', str(work), str(work)]
        for path in denied:
            if path.exists(): command += ['--tmpfs', str(path.resolve())]
        return command + ['--ro-bind', str(inputs), str(inputs)]
    raise RuntimeError('需要 macOS sandbox-exec 或 Linux bwrap')


def runtime_environment(work, config):
    home = work / 'home'
    home.mkdir()
    native = home / ('.pi/agent' if config.get('backend', 'pi') == 'pi' else '.codex')
    native.mkdir(parents=True)
    if config.get('svc', False):
        # Corpus is optional core guidance, independent of the workflow engine.
        runtime = work / 'runtime'
        shutil.copytree(ROOT / '.venv', runtime, symlinks=True)
        svc = runtime / 'bin/svc'
        interpreter = (ROOT / '.venv/bin/python').resolve()
        svc.write_text('#!' + str(interpreter) + '\nimport sys\nsys.path.insert(0, ' + repr(str(next((runtime/'lib').glob('python*/site-packages')))) + ')\nfrom svc_cli.cli import main\nsys.exit(main())\n')
        svc.chmod(0o755)
        guidance=ROOT/'variants'/config.get('variant','')/'AGENTS.md'
        shutil.copy2(guidance if guidance.is_file() else ROOT/'harness/AGENTS.md', native/'AGENTS.md')
    env = {key: value for key, value in os.environ.items()
           if key in ('PATH','LANG','LC_ALL','SSL_CERT_FILE','SSL_CERT_DIR','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY')}
    (work/'tmp').mkdir()
    env.update(TMPDIR=str(work/'tmp'), HOME=str(home), XDG_CONFIG_HOME=str(home/'.config'),
               PI_CODING_AGENT_DIR=str(native), CODEX_HOME=str(native),
               PI_TELEMETRY='0', PI_OFFLINE='1', FACTORY26_API_KEY=api_key())
    if config.get('svc', False):
        env['PATH'] = str(runtime/'bin') + os.pathsep + env.get('PATH','/usr/bin:/bin')
    return native, env


@contextmanager
def responses_adapter(config, output):
    if config.get('backend','pi') != 'codex':
        yield config['base_url']
        return
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0))
        port=listener.getsockname()[1]
    adapter_config = output/'adapter.json'
    save(adapter_config, {'model_list':[{'model_name':config['model'], 'litellm_params':{
        'model':'openai/'+config['model'], 'api_base':config['base_url'],
        'api_key':'os.environ/FACTORY26_API_KEY', 'use_chat_completions_api':True},
        'model_info':{'mode':'chat'}}], 'litellm_settings':{'telemetry':False}})
    executable=ROOT/'.adapter/bin/litellm'
    if not executable.exists(): raise RuntimeError('请先为 Codex 配置运行 bootstrap 安装适配器')
    with (output/'adapter.log').open('w') as log:
        proc=subprocess.Popen([str(executable),'--config',str(adapter_config),'--host','127.0.0.1','--port',str(port)],
             env=dict(os.environ,FACTORY26_API_KEY=api_key()),stdout=log,stderr=log,start_new_session=True)
        try:
            while True:
                if proc.poll() is not None: raise RuntimeError('Responses adapter exited; see adapter.log')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health/liveliness',timeout=2) as response:
                        if response.status==200: break
                except OSError: pass
                time.sleep(.2)
            yield f'http://127.0.0.1:{port}/v1'
        finally: stop(proc)


def braid_request(config, work, app, native, prompt, state):
    backend=config['backend']
    wrapper=work/'pi-clean'
    if backend == 'pi':
        context_flag='' if config.get('svc') else ' --no-context-files'
        wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(shutil.which('pi'))+
                           ' --no-extensions --no-skills --no-prompt-templates --no-themes'+context_flag+' "$@"\n')
        wrapper.chmod(0o755)
    profile={'id':backend, 'display_name':backend, 'tags':[], 'adapter_type':backend,
             'adapter_version':'local', 'provider':'factory26', 'model':config['model'],
             'reasoning':config['thinking'], 'user_instructions':'', 'workspace':str(app),
             'github_actor_node_id':None,'status_surfaces':[],
             'github_context_soft_ratio':0.8,'github_context_hard_bytes':1000000}
    request={'profile':profile,'prompt':prompt,'state':str(state),'codex':None,'pi':None}
    if backend == 'pi':
        request['pi']={'executable':str(wrapper),'provider':'deepseek','model':config['model'],
                       'thinking':config['thinking'],'home':str(native),'api_key_environment':'FACTORY26_API_KEY'}
    else:
        request['codex']={'executable':shutil.which('codex'),'home':str(native),
                         'version':capture('codex','--version'),'stable_schema_sha256':'','experimental_schema_sha256':''}
    return request


def generate(config):
    backend = config.get('backend', 'pi')
    workflow = config.get('workflow', 'single')
    if backend not in ('pi', 'codex') or workflow not in ('single', 'braid'):
        raise ValueError('unknown backend/workflow')
    if capture('git', 'rev-parse', 'HEAD', cwd=BENCH) != config['benchmark_revision'] or capture('git', 'status', '--porcelain', cwd=BENCH):
        raise RuntimeError('benchmark 必须为固定干净版本')
    requirements = BENCH / 'arc-bench/webapp' / config['task'] / 'requirements'
    if not requirements.is_dir(): raise ValueError('任务需求包不存在')
    run = ROOT / 'runs' / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    save(run/'config.json', config)
    save(run/'input-hashes.json', hashes(requirements))
    save(run/'runner-hashes.json', hashes(ROOT/'scripts'))
    save(run/'harness-hashes.json', hashes(ROOT/'harness'))
    shutil.copytree(ROOT/'scripts', run/'runner-source', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'harness', run/'harness-source')
    variant=ROOT/'variants'/config.get('variant','')
    if config.get('variant') and variant.is_dir():
        shutil.copytree(variant,run/'variant-source')
    metadata = {'variant':config.get('variant'), 'status':'generating', 'started_at':time.time(), 'task':config['task'],
                'backend':backend, 'workflow':workflow, 'mode':'competition-gateway-local',
                'submission_eligible':False, 'benchmark_revision':config['benchmark_revision'],
                'versions':{backend:capture(backend,'--version'), 'node':capture('node','--version'),
                            'platform':platform.platform()}, 'estimated_cost':None}
    if config.get('svc'):
        record=sources.archive('svc',run/'sources')
        metadata['svc_revision']=record['source']['revision']
        save(run/'corpus-hashes.json', hashes(sources.checkout('svc')/'corpus'))
    if workflow=='braid':
        record=sources.archive('braid',run/'sources')
        metadata['braid_revision']=record['source']['revision']
        metadata['braid_binary_sha256']=record['artifacts']['braid']
        metadata['workflow_implementation']='braid-local-v1'
    if backend=='codex': metadata['responses_adapter']='litellm==1.102.0'
    phase(run/'run.json',metadata,'setup')
    print(f'[生成] {run}', flush=True)
    begin = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='factory26-') as temp, responses_adapter(config, run) as responses_url:
            work = Path(temp).resolve()
            app, inputs = work/'application', work/'requirements'
            app.mkdir(); shutil.copytree(requirements, inputs)
            native, env = runtime_environment(work, config)
            prefix = isolation_prefix(work, inputs)
            prompt = f'''请根据 {inputs} 中完整需求包独立实现 Web 应用，在当前目录 {app} 工作。
    阅读 requirements.md、requirements.yaml 和参考图片；格式错误或图片缺失时使用可读需求语义并记录问题。覆盖全部需求、场景和明确指定的初始数据，保留界面文字，使用可访问控件。
    交付 package.json：npm install 安装依赖；如需构建提供 npm run build；npm start 接受 PORT 并在 127.0.0.1 提供服务，GET /api/health 返回 200。
    可以编写运行自己的检查，完成后停止服务。不得创建 Git 提交，不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。只依据需求生成，自检后中文说明结果并结束。'''
            (run/'prompt.txt').write_text(prompt)
            if backend == 'pi':
                save(native/'models.json', {'providers':{'deepseek':{'baseUrl':config['base_url'], 'apiKey':'$FACTORY26_API_KEY'}}})
            else:
                from core import codex_config
                codex_config(native, responses_url, config['model'])
            if (native/'AGENTS.md').exists(): shutil.copy2(native/'AGENTS.md',run/'user-AGENTS.md')
            state = work/'braid-state'
            phase(run/'run.json',metadata,'preflight',runtime={'work':str(work),'native':str(native),'braid_state':str(state)})
            try:
                blocked = subprocess.run(prefix+['cat',str(BENCH/'package.json')],capture_output=True)
                readable = subprocess.run(prefix+['cat',str(inputs/'requirements.md')],capture_output=True)
                if blocked.returncode == 0 or readable.returncode != 0: raise RuntimeError('文件隔离检查失败')
                if config.get('svc'):
                    lookup = subprocess.run(prefix+['svc','lookup','--path','index.md'],cwd=app,env=env,capture_output=True,text=True)
                    if lookup.returncode: raise RuntimeError('沙箱内 svc 不可用: '+lookup.stderr)
                save(run/'isolation-check.json', {'evaluator_read_denied':True,'requirements_readable':True,'network_airgap':False})
                if workflow == 'braid':
                    braid = work/'braid'
                    shutil.copy2(sources.binary(),braid)
                    request=braid_request(config,work,app,native,prompt,state)
                    save(work/'braid-request.json',request)
                    phase(run/'run.json',metadata,'braid','braid.log')
                    code = logged(prefix+[str(braid),'local',str(work/'braid-request.json')],app,env,run/'braid.log', metadata.setdefault('cleanup_errors',[]))
                    metadata['process_exit_code']=code
                    if code: raise RuntimeError('braid local 执行失败；参阅 braid.log')
                    sessions = list((app/'.braid/pi-sessions').glob('*.jsonl')) if backend=='pi' else list(native.glob('sessions/**/*.jsonl'))
                elif backend == 'pi':
                    session = native/'session.jsonl'
                    command = prefix+['pi','--provider','deepseek','--model',config['model'],'--thinking',config['thinking'],
                                      '--mode','json','--print','--no-extensions','--no-skills','--no-prompt-templates','--no-themes',
                                      '--session',str(session)]
                    if not config.get('svc'): command.append('--no-context-files')
                    phase(run/'run.json',metadata,'agent','pi-events.jsonl')
                    code = logged(command+[prompt],app,env,run/'pi-events.jsonl', metadata.setdefault('cleanup_errors',[]))
                    metadata['process_exit_code']=code
                    if code: raise RuntimeError('Pi 退出失败')
                    sessions = [session]
                else:
                    from core import codex_turn
                    phase(run/'run.json',metadata,'agent','codex-events.jsonl')
                    metadata['usage'] = codex_turn(prefix+['codex'],app,env,prompt,run,config['model'],config['thinking'])
                    sessions = list(native.glob('sessions/**/*.jsonl'))
                if backend == 'pi':
                    if not sessions: raise RuntimeError('没有 Pi 原生会话')
                    usages = [pi_usage(s) for s in sessions]
                    metadata['usage'] = {'sessions':len(usages), 'assistant_responses':sum(u['assistant_responses'] for u in usages),
                        'summary_events_without_usage':sum(u['summary_events_without_usage'] for u in usages),
                        'tokens':{key:sum(u['tokens'][key] for u in usages) if all(u['tokens'][key] is not None for u in usages) else None for key in usages[0]['tokens']},'estimated_cost':None}
                else:
                    metadata['usage']=codex_usage(sessions)
                metadata['status']='generated'
                phase(run/'run.json',metadata,'cleanup')
            except BaseException as exc:
                metadata.update(status='generation_failed', error=str(exc), failed_phase=metadata.get('phase'),
                                failed_phase_log=metadata.get('phase_log')); raise
            finally:
                metadata['cleanup_pids']=cleanup_workspace(work)
                metadata.update(generation_seconds=time.monotonic()-begin,generation_finished_at=time.time())
                shutil.copytree(app,run/'application',ignore=shutil.ignore_patterns('node_modules','.git','__pycache__','.braid'))
                shutil.copytree(inputs,run/'input')
                native_output = run/'native';native_output.mkdir()
                native_sessions = list(native.glob('sessions/**/*.jsonl')) if backend=='codex' else ([native/'session.jsonl'] if (native/'session.jsonl').exists() else []) + list((app/'.braid/pi-sessions').glob('*.jsonl'))
                for i, session in enumerate(sorted(native_sessions)):
                    shutil.copy2(session,native_output/f'{i:03}-{session.name}')
                if state.exists(): shutil.copytree(state,run/'braid-state')
                save(run/'application-hashes.json',hashes(run/'application'))
                metadata.pop('runtime',None)
                phase(run/'run.json',metadata,'frozen' if metadata['status']=='generated' else 'failed')
    except BaseException as exc:
        metadata.update(status='generation_failed',error=str(exc),generation_seconds=time.monotonic()-begin,
                        generation_finished_at=time.time())
        metadata.setdefault('failed_phase',metadata.get('phase'))
        phase(run/'run.json',metadata,'failed',metadata.get('failed_phase_log') or metadata.get('phase_log'))
        raise
    print(f'[已冻结] {run}',flush=True)
    return run


def logged(command, cwd, env, log, cleanup_errors=None):
    with log.open("w") as output:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return proc.wait()
        finally:
            try: stop(proc)
            except PermissionError as exc:
                # Generation has an outer, verified workspace cleanup before freezing.
                if cleanup_errors is None or proc.returncode is None: raise
                cleanup_errors.append({'pid':proc.pid,'exit_code':proc.returncode,'error':str(exc)})


def score(report):
    stats = report["stats"]
    passed = stats["expected"]
    failed = stats["unexpected"]
    flaky = stats["flaky"]
    skipped = stats["skipped"]
    total = passed + failed + flaky + skipped
    return {"passed": passed, "failed": failed, "flaky": flaky, "skipped": skipped,
            "total": total, "pass_rate": passed / total if total else None,
            "errors": report.get("errors", []), "duration_ms": stats["duration"]}


def validate_snapshot(run):
    config = json.loads((run / "config.json").read_text())
    metadata = json.loads((run / "run.json").read_text())
    if metadata["status"] != "generated":
        raise RuntimeError("只评测已完成并冻结的生成结果")
    if hashes(run / "application") != json.loads((run / "application-hashes.json").read_text()):
        raise RuntimeError("应用快照已被修改；新实验需创建新 run")
    return config


def evaluate(run):
    config = validate_snapshot(run)
    if capture("git", "rev-parse", "HEAD", cwd=BENCH) != config["benchmark_revision"] or capture("git", "status", "--porcelain", cwd=BENCH):
        raise RuntimeError("评测器必须是固定且未经修改的版本")
    output = run / "evaluation" / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    output.mkdir(parents=True)
    shutil.copy2(Path(__file__), output / "runner-evaluation.py")
    result = {"status": "starting", "started_at": time.time(), "retries": 0, "workers": 1,
              "platform": platform.platform(), "node_version": capture("node", "--version"),
              "test_timeout_ms": 60000, "expect_timeout_ms": 10000,
              "ci": False, "source_application_hashes": "../../application-hashes.json"}
    begin = time.monotonic()
    phase(output/'summary.json',result,'setup')
    print(f"[评测] {output}", flush=True)
    env = dict(os.environ)
    env.pop("CI", None)
    # Benchmark wrapper supports ROOT variables that otherwise override per-run output paths.
    for key in list(env):
        if key.startswith(("PLAYWRIGHT_", "ARC_")) or key == "TARGET_URL":
            env.pop(key)
    try:
        with tempfile.TemporaryDirectory(prefix="factory26-eval-") as temp:
            app = Path(temp) / "application"
            shutil.copytree(run / "application", app)
            package = json.loads((app / "package.json").read_text())
            install = ["npm", "ci"] if (app / "package-lock.json").exists() else ["npm", "install"]
            phase(output/'summary.json',result,'install','install.log')
            if logged(install, app, env, output / "install.log") != 0:
                raise RuntimeError("应用依赖安装失败")
            if "build" in package.get("scripts", {}):
                phase(output/'summary.json',result,'build','build.log')
                if logged(["npm", "run", "build"], app, env, output / "build.log") != 0:
                    raise RuntimeError("应用构建失败")
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            url = f"http://127.0.0.1:{port}"
            result["target_url"] = url
            env["PORT"] = str(port)
            phase(output/'summary.json',result,'health','application.log')
            with (output / "application.log").open("w") as log:
                proc = subprocess.Popen(["npm", "start"], cwd=app, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    while True:
                        if proc.poll() is not None:
                            raise RuntimeError("应用在健康检查前退出")
                        try:
                            with urllib.request.urlopen(url + "/api/health", timeout=2) as response:
                                if response.status == 200:
                                    break
                        except OSError:
                            pass
                        time.sleep(0.5)
                    env.update(PLAYWRIGHT_JSON_OUTPUT_FILE=str(output / "results.json"),
                               PLAYWRIGHT_REPORT_DIR=str(output / "html"),
                               # --reporter replaces the HTML options in playwright.config.ts.
                               PLAYWRIGHT_HTML_OUTPUT_DIR=str(output / "html"), PLAYWRIGHT_HTML_OPEN="never",
                               PLAYWRIGHT_OUTPUT_DIR=str(output / "test-results"))
                    command = ["npm", "run", "test", "--", "--app", config["task"],
                               "--target-url", url, "--timeout", "60000", "--expect-timeout", "10000",
                               "--retries=0", "--reporter=list,json,html"]
                    save(output / "command.json", command)
                    phase(output/'summary.json',result,'tests','test.log')
                    result["exit_code"] = logged(command, BENCH, env, output / "test.log")
                    if not (output / "results.json").exists():
                        raise RuntimeError("评测未生成 JSON 报告；参阅 test.log")
                    result.update(score(json.loads((output / "results.json").read_text())))
                    if not result["total"] or result["errors"] or result["exit_code"] not in (0, 1):
                        raise RuntimeError("评测中断、没有测试结果或出现全局错误，不能作为完整分数")
                    result["status"] = "completed"
                finally:
                    stop(proc)
    except BaseException as exc:
        result.update(status="interrupted" if isinstance(exc,KeyboardInterrupt) else "evaluation_error",
                      error=str(exc) or type(exc).__name__, failed_phase=result.get("phase"))
        raise
    finally:
        result.update(wall_seconds=time.monotonic() - begin, finished_at=time.time())
        phase(output/'summary.json',result,'completed' if result['status']=='completed' else 'failed',result.get('phase_log'))
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return output


def remote_evaluation_snapshot(host, remote_run):
    code = "from pathlib import Path; import json; p=Path("+repr(remote_run)+")/'evaluation'; print(json.dumps({x.parent.name:json.loads(x.read_text()) for x in p.glob('*/summary.json')}))"
    return json.loads(capture('ssh',host,'python3 -c '+shlex.quote(code)))


def evaluate_remote(run, host):
    """Transfer a frozen application; the host keeps its installed evaluator."""
    config=validate_snapshot(run)
    remote={'host':host}
    phase(run/'remote-evaluation.json',remote,'connect')
    try:
        remote_home=capture('ssh',host,'pwd')
        remote_root=remote_home+'/Development/factory26'
        remote_run=remote_root+'/runs/'+run.name
        remote['remote_run']=remote_run
        phase(run/'remote-evaluation.json',remote,'transfer')
        probe=subprocess.run(['ssh',host,'test -d '+shlex.quote(remote_run)],capture_output=True)
        if probe.returncode:
            command='mkdir -p '+shlex.quote(remote_run)+' && tar -xf - -C '+shlex.quote(remote_run)
            transfer=subprocess.Popen(['ssh',host,command],stdin=subprocess.PIPE)
            try:
                with tarfile.open(fileobj=transfer.stdin,mode='w|') as archive:
                    for name in ('application','application-hashes.json','config.json','run.json'):
                        archive.add(run/name,arcname=name)
            finally: transfer.stdin.close()
            if transfer.wait(): raise RuntimeError('remote application transfer failed')
        remote_hashes=json.loads(capture('ssh',host,'cat '+shlex.quote(remote_run+'/application-hashes.json')))
        if remote_hashes!=json.loads((run/'application-hashes.json').read_text()):
            raise RuntimeError('remote run identity has different application hashes')
        remote_config=json.loads(capture('ssh',host,'cat '+shlex.quote(remote_run+'/config.json')))
        if remote_config!=config: raise RuntimeError('remote run configuration differs from frozen local run')
        command='cd '+shlex.quote(remote_root)+' && python3 scripts/factory.py eval --run '+shlex.quote(remote_run)
        previous=set(remote_evaluation_snapshot(host,remote_run))
        phase(run/'remote-evaluation.json',remote,'running_remote')
        result=subprocess.Popen(['ssh',host,command])
        while True:
            try:
                result.wait(timeout=15)
                break
            except subprocess.TimeoutExpired:
                try:
                    observations=remote_evaluation_snapshot(host,remote_run)
                    current=sorted(set(observations)-previous)
                    if current:
                        attempt=current[-1]
                        remote.update(attempt=attempt,summary=observations[attempt],observation_error=None)
                    remote['observed_at']=time.time()
                except (OSError,subprocess.CalledProcessError,ValueError) as exc:
                    remote['observation_error']=str(exc)
                remote['updated_at']=time.time()
                save(run/'remote-evaluation.json',remote)
        phase(run/'remote-evaluation.json',remote,'download',exit_code=result.returncode)
        with tempfile.TemporaryDirectory(prefix='factory26-results-') as temp:
            download=subprocess.Popen(['ssh',host,'tar -cf - -C '+shlex.quote(remote_run)+' evaluation'],stdout=subprocess.PIPE)
            try:
                with tarfile.open(fileobj=download.stdout,mode='r|') as archive:
                    archive.extractall(temp,filter='data')
            finally: download.stdout.close()
            if download.wait(): raise RuntimeError('remote evidence download failed')
            output=run/'evaluation';output.mkdir(exist_ok=True)
            for folder in (Path(temp)/'evaluation').iterdir():
                if not (output/folder.name).exists(): shutil.copytree(folder,output/folder.name)
        attempts=sorted(folder for folder in output.iterdir() if folder.is_dir() and folder.name not in previous)
        if attempts:
            latest=attempts[-1]
            summary=json.loads((latest/'summary.json').read_text())
            remote.update(attempt=latest.name,summary=summary,observed_at=time.time(),observation_error=None)
        if result.returncode:
            remote['failed_phase']='remote_'+(remote.get('summary',{}).get('failed_phase') or 'execution')
            raise RuntimeError('remote evaluation failed; downloaded evidence retained')
        phase(run/'remote-evaluation.json',remote,'completed')
    except BaseException as exc:
        remote.update(error=str(exc) or type(exc).__name__)
        remote.setdefault('failed_phase',remote.get('phase'))
        phase(run/'remote-evaluation.json',remote,'failed')
        raise
    return run/'evaluation'


def analyze(run, svc_source=None):
    svc = ['pdm','run','-p',str(svc_source),'svc'] if svc_source else [str(ROOT/'.venv/bin/svc')]
    provenance={'command':svc,'version':capture(*svc,'--version')}
    if svc_source:
        provenance.update(source=str(svc_source), revision=capture('git','rev-parse','HEAD',cwd=svc_source),
                          source_hashes=hashes(svc_source/'cli/src'))
    else:
        package=Path(capture(str(ROOT/'.venv/bin/python'),'-c',
                            'import svc_cli; print(next(iter(svc_cli.__path__)))'))
        provenance['source_hashes']=hashes(package)
    requests=[{'version':3,'intent':'overview'},{'version':3,'intent':'profile','breakdown':'model'}]
    provenance['requests']=requests
    fingerprint=hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest()[:16]
    metadata=json.loads((run/'run.json').read_text())
    sources=sorted((run/'native').glob('*.jsonl'))
    if not sources: sources=[run/'pi-session.jsonl']
    output=run/'analysis'; output.mkdir(exist_ok=True)
    for index, source in enumerate(sources):
        # Immutable analysis generations: changing an exporter must actually re-export.
        folder=output/f'{index:03}-{fingerprint}'
        if folder.exists():
            print(f'[缓存] {folder}',flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix='.analysis-',dir=output) as temp:
            staging=Path(temp)
            evidence=staging/'evidence-v4.zip'
            result=capture(*svc,'telemetry','agent-thread','export','--provider',metadata['backend'],
                           '--source',str(source),'--output',str(evidence),'--json')
            (staging/'export.json').write_text(result+'\n')
            for request in requests:
                response=subprocess.run([*svc,'analysis','query','--input',str(evidence),'--request','-'],
                                        input=json.dumps(request),capture_output=True,text=True,check=True)
                save(staging/f"{request['intent']}.json",json.loads(response.stdout))
            save(staging/'provenance.json',dict(provenance,created_at=time.time(),source_session=source.name,
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
            staging.rename(folder)
    print(f'[svc] {output}，{len(sources)} 个原生会话，来源 {fingerprint}',flush=True)


def bootstrap(config):
    if config.get('backend')=='codex':
        if not (ROOT/'.adapter/bin/python').exists():
            subprocess.run(['uv','venv',str(ROOT/'.adapter')],check=True)
        subprocess.run(['uv','pip','install','--python',str(ROOT/'.adapter/bin/python'),'litellm[proxy]==1.102.0'],check=True)
    sources.build('svc')
    if config.get('workflow')=='braid':
        sources.build('braid')
    if not BENCH.exists():
        BENCH.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", "--filter=blob:none", config["benchmark_url"], str(BENCH)], check=True)
        subprocess.run(["git", "checkout", "--detach", config["benchmark_revision"]], cwd=BENCH, check=True)
    if capture("git", "rev-parse", "HEAD", cwd=BENCH) != config["benchmark_revision"]:
        raise RuntimeError("已有 benchmark 版本不匹配；为保护本地状态，未自动切换")
    if capture("git", "status", "--porcelain", cwd=BENCH):
        raise RuntimeError("benchmark 有本地改动，拒绝覆盖依赖或运行检查")
    lock_hash = hashlib.sha256((BENCH/'package-lock.json').read_bytes()).hexdigest()
    stamp = BENCH/'node_modules/.factory26-lock'
    if not stamp.exists() or stamp.read_text() != lock_hash or not (BENCH/'node_modules/@playwright/test').is_dir():
        subprocess.run(['npm','ci'],cwd=BENCH,check=True)
        stamp.write_text(lock_hash)
    else:
        print('[缓存] ARC-bench node_modules',flush=True)
    browser = capture('node','-e',"console.log(require('playwright').chromium.executablePath())",cwd=BENCH)
    if not Path(browser).exists():
        subprocess.run(['npx','playwright','install','chromium'],cwd=BENCH,check=True)
    else:
        print('[缓存] Playwright Chromium',flush=True)
    subprocess.run(["npm", "run", "test:audit"], cwd=BENCH, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bootstrap", "generate", "eval", "analyze", "run", "list", "show"])
    parser.add_argument("run_id", nargs="?", help="show 的 run ID")
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument("--config", type=Path, help="显式配置文件，兼容历史入口")
    selection.add_argument("--variant", help="variants/<id>/config.json；list 时作为过滤器")
    parser.add_argument("--task", help="list 按任务过滤")
    parser.add_argument("--json", action="store_true", help="输出可机器读取的摘要")
    parser.add_argument("--eval", dest="evaluation", help="show 指定评测尝试")
    parser.add_argument("--svc-source", type=Path, help="使用本地 SVC 工作树的 PDM 环境做 analysis；运行时 Corpus 不变")
    parser.add_argument("--case", help="show 指定失败用例，如 REQ-2.2")
    parser.add_argument("--eval-host", help="SSH host with bootstrapped ~/Development/factory26 evaluator")
    parser.add_argument("--run", type=Path, help="eval/analyze/show 的已有 run 目录")
    args = parser.parse_args()
    if args.command in ('list','show'):
        from inspect_runs import list_runs, show_run, render_list, render_show
        if args.command=='list':
            result=list_runs(ROOT,variant=args.variant,task=args.task)
            output=render_list(result)
        else:
            selected=args.run or (ROOT/'runs'/args.run_id if args.run_id else None)
            if selected is None: parser.error('show 需要 run ID 或 --run')
            result=show_run(selected.resolve(),evaluation=args.evaluation,case=args.case)
            output=render_show(result)
        print(json.dumps(result,ensure_ascii=False,indent=2) if args.json else output)
        return
    if args.command in ('eval','analyze'):
        if args.run is None: parser.error('eval/analyze 需要 --run')
        if args.command=='eval' and args.eval_host: evaluate_remote(args.run.resolve(),args.eval_host)
        elif args.command=='analyze': analyze(args.run.resolve(),args.svc_source.resolve() if args.svc_source else None)
        else: evaluate(args.run.resolve())
        return
    variant=args.variant or 'pi-baseline'
    if Path(variant).name!=variant or variant in ('.','..'): parser.error('variant 必须为目录名称')
    source=(args.config or ROOT/'variants'/variant/'config.json').resolve()
    config=json.loads(source.read_text())
    if source.parent.parent==ROOT/'variants': config['variant']=source.parent.name
    if args.command=='bootstrap':
        bootstrap(config)
    else:
        run=generate(config)
        if args.command=='run':
            try:
                if args.eval_host: evaluate_remote(run,args.eval_host)
                else: evaluate(run)
            finally: analyze(run,args.svc_source.resolve() if args.svc_source else None)


if __name__ == "__main__":
    main()
