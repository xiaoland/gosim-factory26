#!/usr/bin/env python3
"""Codex app-server / Pi、SVC / braid 与官方 ARC-bench 的单任务实验入口。"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import shlex
import signal
import socket
import subprocess
import tempfile
import tarfile
import time
import urllib.error
import urllib.request
import uuid
import sources

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "third_party/arc-bench"


def load_config(path=None, backend=None, variant=None, task=None):
    """新运行解析选定配方；历史归档和显式单核心检查保留原入口。"""
    if path is None:
        from profiles import configuration, DEFAULT_VARIANT
        selected = variant or DEFAULT_VARIANT
        result = configuration(selected, task or "keep", ROOT)
        if backend is not None and backend != result["backend"]:
            raise ValueError("backend 与 variant 核心不一致；请显式选择 variant")
        return result
    active = (ROOT / 'variants/factory/config.json').resolve()
    source = Path(path).resolve() if path is not None else active
    config = json.loads(source.read_text())
    if not isinstance(config, dict):
        raise ValueError('配置必须是 JSON 对象')
    config['variant'] = 'factory' if source == active else 'custom'
    config['backend'] = backend if backend is not None else config.get('backend', 'pi')
    if config['backend'] not in ('pi', 'codex'):
        raise ValueError('backend 必须是 pi 或 codex')
    if source == active and (config.get('workflow') != 'braid' or config.get('svc') is not True):
        raise ValueError('factory 配置必须启用 Braid 与 SVC；消融使用显式 --config')
    return config


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


def copy_application(source, output):
    root=source.resolve()
    omitted={'node_modules','.git','__pycache__','.braid'}
    def ignore(folder, names):
        for name in set(names)-omitted:
            path=Path(folder)/name
            if path.is_symlink() and not path.resolve().is_relative_to(root):
                raise RuntimeError(f'应用链接指向工作区外: {path.relative_to(source)}')
        return omitted.intersection(names)
    shutil.copytree(source,output,ignore=ignore)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def evaluation_id(value=None):
    value = value or (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value):
        raise ValueError('evaluation ID 必须是单个目录名称')
    return value


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


def api_key():
    path = Path.home() / ".config/factory26/llm.env"
    for line in path.read_text().splitlines():
        if line.startswith("FACTORY26_API_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise RuntimeError(f"请先在 {path} 填写 FACTORY26_API_KEY")


def pi_usage(session, require_completed=True):
    entries = [json.loads(line) for line in session.read_text().splitlines()]
    messages = [entry.get("message", {}) for entry in entries]
    assistants = [m for m in messages if m.get("role") == "assistant"]
    usages = [m["usage"] for m in assistants if isinstance(m.get("usage"), dict)]
    summaries = [entry for entry in entries if entry.get("type") in ("compaction", "branch_summary")]
    usages += [entry["usage"] for entry in summaries if isinstance(entry.get("usage"), dict)]
    if require_completed and (not assistants or assistants[-1].get("stopReason") != "stop"):
        last = assistants[-1] if assistants else {}
        raise RuntimeError(f"Pi 未正常完成：{last.get('errorMessage') or last.get('stopReason') or '无 assistant 终态'}")
    totals = {key: sum(u[key] for u in usages) if usages and all(key in u for u in usages) else None
              for key in ("input", "output", "cacheRead", "cacheWrite", "reasoning", "totalTokens")}
    return {"assistant_responses": len(assistants), "tokens": totals, "estimated_cost": None,
            "last_stop_reason": assistants[-1].get('stopReason') if assistants else None,
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


def runtime_environment(work, config):
    if config.get('runtime') == 'submission':
        from submission import environment
        return environment(work, config)
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
        shutil.copy2(ROOT/'harness/AGENTS.md', native/'AGENTS.md')
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
def generation_workspace(output, retain_failure=False):
    work=Path(tempfile.mkdtemp(prefix='factory26-', dir='/tmp')).resolve()
    try:
        yield work
    except BaseException:
        if retain_failure:
            # Linked worktrees require their common Git directory for recovery.
            save(output/'recovery-workspace.json',{'path':str(work),
                 'request':str(work/'braid-request.json'),
                 'note':'生成失败的原始工作区已保留；未冻结交付，不可直接评测。'})
        else:
            shutil.rmtree(work)
        raise
    else:
        shutil.rmtree(work)


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
        'model_info':{'mode':'chat'}}], 'litellm_settings':{'telemetry':False,
            'callbacks':['responses_compat.proxy_handler_instance']}})
    packaged = config.get('runtime') == 'submission'
    executable=ROOT/('runtime/bin/litellm' if packaged else '.adapter/bin/litellm')
    if packaged:
        from submission import adapter_environment
        adapter_env = adapter_environment(config, output)
    else:
        adapter_env = dict(os.environ, FACTORY26_API_KEY=api_key())
    adapter_env['PYTHONPATH'] = os.pathsep.join(filter(None,[str(ROOT/'scripts'),adapter_env.get('PYTHONPATH')]))
    if not executable.exists(): raise RuntimeError('请先为 Codex 配置运行 bootstrap 安装适配器')
    with (output/'adapter.log').open('w') as log:
        proc=subprocess.Popen([str(executable),'--config',str(adapter_config),'--host','127.0.0.1','--port',str(port)],
             env=adapter_env,stdout=log,stderr=log,start_new_session=True)
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


def braid_request(config, work, app, native, prompt, state, run_id=None, responses_url=None):
    backend=config['backend']
    if 'effective' in config:
        from native_profiles import materialize, executable as native_executable
        profiles, bindings = materialize(config['effective'], work, responses_url or config['base_url'],
                                         run_id or work.name, config.get('visual_base_url'))
        request = dict(profiles=profiles, defaults=config['effective']['defaults'], bindings=bindings,
                       prompt=prompt, state=str(state), run_id=run_id or work.name,
                       delivery_ref='refs/heads/braid-delivery', codex=None, pi=None)
        if backend == 'pi':
            request['pi'] = dict(executable=native_executable('pi'), home=str(native), api_key_environment='FACTORY26_API_KEY')
        else:
            command=native_executable('codex')
            request['codex'] = dict(executable=command, home=str(native), version=capture(command,'--version'), stable_schema_sha256='', experimental_schema_sha256='')
        return request
    executable = str(ROOT/'runtime/bin'/backend) if config.get('runtime') == 'submission' else shutil.which(backend)
    wrapper=work/'pi-clean'
    if backend == 'pi':
        context_flag='' if config.get('svc') else ' --no-context-files'
        wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(executable)+
                           ' --no-extensions --no-skills --no-prompt-templates --no-themes'+context_flag+' "$@"\n')
        wrapper.chmod(0o755)
    descriptions = {'pi':'适合通用需求理解、实现与整合；可处理完整工作项。',
                    'codex':'适合通用需求理解、实现与整合；可处理完整工作项。'}
    profile={'id':backend, 'display_name':backend, 'assignee_login':backend,
             'assignee_description':descriptions[backend], 'tags':[], 'adapter_type':backend,
             'adapter_version':'local', 'provider':'deepseek' if backend=='pi' else 'factory26', 'model':config['model'],
             'reasoning':config['thinking'], 'user_instructions':'', 'workspace':str(app),
             'context_soft_ratio':0.8,'context_hard_bytes':1000000}
    request={'profiles':[profile], 'defaults':{'issue':backend,'pr':backend},
             'bindings':{backend:{'adapter_type':backend,'executable':str(wrapper) if backend=='pi' else executable,
                                  'api_key_environment':'FACTORY26_API_KEY','native_template':str(native)}},
             'prompt':prompt,'state':str(state),'codex':None,'pi':None,
             'run_id':run_id or work.name, 'delivery_ref':'refs/heads/braid-delivery'}
    if backend == 'pi':
        request['pi']={'executable':str(wrapper),'home':str(native),'api_key_environment':'FACTORY26_API_KEY'}
    else:
        request['codex']={'executable':executable,'home':str(native),
                         'version':capture(executable,'--version'),'stable_schema_sha256':'','experimental_schema_sha256':''}
    return request


def new_run():
    run = ROOT / 'runs' / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    return run


def application_contract(config):
    if config.get('deployment') == 'arcbench':
        return ('交付 frontend/package.json 和 backend/package.json。平台先在 frontend 执行 npm install、npm run build，'
                '再在 backend 执行 npm install、HOST=0.0.0.0 PORT=3000 npm run start。'
                '目标应用兼容 Node.js 20.19.3；后端必须通过 HOST/PORT 提供构建后的前端与 API，首页可访问；启动须在 120 秒内完成。'
                '禁止依赖根 npm start 或 deploy.sh；不要交付 requirements、.arc、.git、.factory26 等平台保留目录。')
    return '交付 package.json：npm install 安装依赖；如需构建提供 npm run build；npm start 接受 PORT 并在 127.0.0.1 提供服务，GET /api/health 返回 200。'


def generate(config, run=None, requirements=None):
    backend = config.get('backend', 'pi')
    workflow = config.get('workflow', 'single')
    if backend not in ('pi', 'codex') or workflow not in ('single', 'braid'):
        raise ValueError('unknown backend/workflow')
    packaged = config.get('runtime') == 'submission'
    if packaged:
        if requirements is None or run is None:
            raise ValueError('参赛模式必须显式提供需求与证据目录')
        package = json.loads((ROOT/'package-manifest.json').read_text())
    else:
        if requirements is not None:
            raise ValueError('外部需求入口仅用于参赛包')
        if capture('git', 'rev-parse', 'HEAD', cwd=BENCH) != config['benchmark_revision'] or capture('git', 'status', '--porcelain', cwd=BENCH):
            raise RuntimeError('benchmark 必须为固定干净版本')
        requirements = BENCH / 'arc-bench/webapp' / config['task'] / 'requirements'
    if not requirements.is_dir(): raise ValueError('任务需求包不存在')
    run = new_run() if run is None else run
    save(run/'config.json', config)
    if 'effective' in config: save(run/'effective-config.json', config['effective'])
    save(run/'input-hashes.json', hashes(requirements))
    save(run/'runner-hashes.json', hashes(ROOT/'scripts'))
    save(run/'harness-hashes.json', hashes(ROOT/'harness'))
    shutil.copytree(ROOT/'scripts', run/'runner-source', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'harness', run/'harness-source')
    variant=ROOT/'variants'/config.get('variant','')
    if config.get('variant') and variant.is_dir():
        shutil.copytree(variant,run/'variant-source')
    metadata = {'variant':config.get('variant'), 'status':'generating', 'started_at':time.time(), 'task':config['task'],
                'backend':backend, 'workflow':workflow, 'mode':'platform-package' if packaged else 'competition-gateway-local',
                'deployment':config.get('deployment','legacy'),
                'submission_eligible':False, 'benchmark_revision':config['benchmark_revision'],
                'versions':{backend:capture(str(ROOT/'runtime/bin'/backend) if packaged else __import__('native_profiles').executable(backend) if 'effective' in config else backend,'--version'),
                            'node':capture(str(ROOT/'runtime/bin/node') if packaged else 'node','--version'),
                            'platform':platform.platform()}, 'estimated_cost':None}
    if packaged:
        save(run/'runtime-provenance.json', package)
        metadata.update(svc_revision=package['sources']['svc']['revision'],
                        braid_revision=package['sources']['braid']['revision'],
                        braid_binary_sha256=package['files']['runtime/bin/braid']['sha256'],
                        workflow_implementation='braid-local-objects-v1')
    if config.get('svc') and not packaged:
        record=sources.archive('svc',run/'sources')
        metadata['svc_revision']=record['source']['revision']
        save(run/'corpus-hashes.json', hashes(sources.checkout('svc')/'corpus'))
    if workflow=='braid' and not packaged:
        record=sources.archive('braid',run/'sources')
        metadata['braid_revision']=record['source']['revision']
        metadata['braid_binary_sha256']=record['artifacts']['braid']
        metadata['workflow_implementation']='braid-local-objects-v1'
    if backend=='codex': metadata['responses_adapter']='litellm==1.102.0'
    phase(run/'run.json',metadata,'setup')
    print(f'[生成] {run}', flush=True)
    begin = time.monotonic()
    try:
        with generation_workspace(run,workflow=='braid') as work, responses_adapter(config, run) as responses_url:
            app = work/'application'
            inputs = run/'input' if packaged else work/'requirements'
            app.mkdir(); shutil.copytree(requirements, inputs)
            native, env = runtime_environment(work, config)
            workspace_instruction = '使用当前工作项分配的 Git worktree。' if workflow=='braid' else f'在 {app} 工作。'
            prompt = f'''请根据 {inputs} 中完整需求包独立实现 Web 应用。{workspace_instruction}
    阅读 requirements.md、requirements.yaml 和参考图片；格式错误或图片缺失时使用可读需求语义并记录问题。覆盖全部需求、场景和明确指定的初始数据，保留界面文字，使用可访问控件。
    {application_contract(config)}
    本任务授权在本次临时工作区内设计、实现、安装依赖、自检及本地 Git commit/merge。无人类中途介入；依据需求处理常规歧义，记录重要假设；遇到真实阻塞则报告，不等待用户。禁止 push、发布和修改外部系统或开发源码仓库。
    可以编写运行自己的检查，完成后停止服务。不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。只依据需求生成，自检后中文说明结果并结束。'''
            (run/'prompt.txt').write_text(prompt)
            if backend == 'pi':
                provider = {'baseUrl':config['base_url'], 'apiKey':'$FACTORY26_API_KEY'}
                if packaged:
                    provider.update(api='openai-completions', models=[{'id':config['model'], 'reasoning':True,
                                    'input':['text','image'] if config['image_input'] else ['text']}])
                save(native/'models.json', {'providers':{'deepseek':provider}})
            else:
                from core import codex_config
                codex_config(native, responses_url, config['model'])
            if (native/'AGENTS.md').exists(): shutil.copy2(native/'AGENTS.md',run/'user-AGENTS.md')
            state = run/'braid-state'
            session_entries = []
            delivery = None
            metadata['runtime']={'work':str(work),'native':str(native),'braid_state':str(state)}
            try:
                if workflow == 'braid':
                    from braid_runtime import initialize_repository, load_delivery
                    initialize_repository(app)
                    (work/'bin').mkdir(exist_ok=True)
                    braid = work/'bin/braid'
                    shutil.copy2(ROOT/'runtime/bin/braid' if packaged else sources.binary(),braid)
                    if hashlib.sha256(braid.read_bytes()).hexdigest() != metadata['braid_binary_sha256']:
                        raise RuntimeError('Braid 运行制品与已归档构建不一致')
                    env['PATH'] = str(braid.parent) + os.pathsep + env['PATH']
                    request=braid_request(config,work,app,native,prompt,state,run.name,responses_url)
                    save(work/'braid-request.json',request)
                    phase(run/'run.json',metadata,'braid','braid.log')
                    code = logged([str(braid),'local',str(work/'braid-request.json')],app,env,run/'braid.log', metadata.setdefault('cleanup_errors',[]))
                    metadata['process_exit_code']=code
                    if code: raise RuntimeError('braid local 执行失败；参阅 braid.log')
                    delivery=load_delivery(state,app,work,request)
                    metadata['delivery'] = delivery
                elif backend == 'pi':
                    session = native/'session.jsonl'
                    command = ['pi','--provider','deepseek','--model',config['model'],'--thinking',config['thinking'],
                                      '--mode','json','--print','--no-extensions','--no-skills','--no-prompt-templates','--no-themes',
                                      '--session',str(session)]
                    if not config.get('svc'): command.append('--no-context-files')
                    phase(run/'run.json',metadata,'agent','pi-events.jsonl')
                    code = logged(command+[prompt],app,env,run/'pi-events.jsonl', metadata.setdefault('cleanup_errors',[]))
                    metadata['process_exit_code']=code
                    if code: raise RuntimeError('Pi 退出失败')
                    session_entries = [{'provider':'pi','session_id':str(session),'native_session_path':str(session),
                                        'worktree':str(app),'turns':[{'status':'failed'}]}]
                    # Pi print mode can exit 0 after exhausting stream retries.
                    pi_usage(session)
                    session_entries[0]['turns'][0]['status']='completed'
                else:
                    from core import codex_turn
                    phase(run/'run.json',metadata,'agent','codex-events.jsonl')
                    terminal = codex_turn(['codex'],app,env,prompt,run,config['model'],config['thinking'])
                    session_entries = [{'provider':'codex','session_id':terminal['thread_id'],
                                        'worktree':str(app),'turns':[{'status':'completed'}]}]
                metadata['status']='generated'
                phase(run/'run.json',metadata,'cleanup')
            except BaseException as exc:
                metadata.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'generation_failed',
                                error=str(exc) or type(exc).__name__, failed_phase=metadata.get('phase'),
                                failed_phase_log=metadata.get('phase_log')); raise
            finally:
                metadata['cleanup_pids']=cleanup_workspace(work)
                metadata.update(generation_seconds=time.monotonic()-begin,generation_finished_at=time.time())
                if delivery is not None:
                    from braid_runtime import export_delivery
                    export_delivery(app,delivery['delivery_commit'],run/'application')
                else:
                    copy_application(app,run/'application')
                if inputs != run/'input':
                    shutil.copytree(inputs,run/'input')
                if workflow == 'braid' and state.exists():
                    from braid_runtime import archive_state
                    session_entries = archive_state(state,run)
                elif not session_entries:
                    # A failed native turn still has useful evidence, identified by its own header.
                    paths = native.glob('sessions/**/*.jsonl') if backend=='codex' else native.glob('session.jsonl')
                    for source in sorted(paths):
                        try:
                            with source.open() as stream: header=json.loads(stream.readline())
                            identity=header.get('payload',{}).get('id') if backend=='codex' else str(source)
                        except Exception:
                            identity=str(source)
                        session_entries.append({'provider':backend,'session_id':identity,
                                                'native_session_path':str(source),'turns':[]})
                from core import archive_sessions
                archived = archive_sessions(run,native,work,session_entries)
                if metadata['status']=='generated' and config.get('deployment') == 'arcbench':
                    from submission import validate_application
                    validate_application(run/'application')
                save(run/'application-hashes.json',hashes(run/'application'))
                metadata['application_sha256']=digest(hashes(run/'application'))
                metadata.pop('runtime',None)
                complete=[entry for entry in archived if entry.get('native') and not entry.get('archive_error')]
                diagnostic_status=json.loads((run/'native/manifest.json').read_text())['diagnostic_status']
                metadata['native_diagnostics']={'status':diagnostic_status,
                    'archived_sessions':len(complete),'reported_sessions':len(archived)}
                if complete:
                    if backend == 'pi':
                        usages=[]
                        for entry in complete:
                            try:
                                usages.append(pi_usage(run/entry['native'],require_completed=workflow!='braid'
                                                       and metadata['status']=='generated'))
                            except Exception:
                                pass
                        if not usages:
                            metadata['usage']={'coverage':'unknown','sessions':0,'estimated_cost':None}
                        else:
                            coverage='complete' if diagnostic_status=='complete' and len(usages)==len(complete) else 'partial'
                            metadata['usage'] = {'coverage':coverage,'sessions':len(usages),'assistant_responses':sum(u['assistant_responses'] for u in usages),
                                'summary_events_without_usage':sum(u['summary_events_without_usage'] for u in usages),
                                'tokens':{key:sum(u['tokens'][key] for u in usages) if all(u['tokens'][key] is not None for u in usages)
                                          else None for key in usages[0]['tokens']},'estimated_cost':None}
                    else:
                        try:
                            metadata['usage']={'coverage':diagnostic_status,
                                'aggregation':'separate-root-and-children; inclusive-parent-accounting-unverified',
                                'braid_sessions':codex_usage([run/e['native'] for e in complete if not e.get('parent_native_session_id')]),
                                'native_children':codex_usage([run/e['native'] for e in complete if e.get('parent_native_session_id')]),
                                'estimated_cost':None}
                        except Exception:
                            metadata['usage']={'coverage':'unknown','estimated_cost':None}
                else:
                    metadata['usage']={'coverage':'unknown','sessions':0,'estimated_cost':None}
                phase(run/'run.json',metadata,'frozen' if metadata['status']=='generated' else
                      'interrupted' if metadata['status']=='interrupted' else 'failed')
    except BaseException as exc:
        metadata.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'generation_failed',
                        error=str(exc) or type(exc).__name__,generation_seconds=time.monotonic()-begin,
                        generation_finished_at=time.time())
        metadata.setdefault('failed_phase',metadata.get('phase'))
        phase(run/'run.json',metadata,'interrupted' if metadata['status']=='interrupted' else 'failed',
              metadata.get('failed_phase_log') or metadata.get('phase_log'))
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


def report_cases(report):
    """Keep discovery and results on the same official test identities."""
    cases = {}
    def visit(suite):
        for spec in suite.get('specs', []):
            for test in spec.get('tests', []):
                key = (spec['id'], test['projectId'])
                if key in cases:
                    raise RuntimeError('评测报告包含重复测试身份')
                cases[key] = test
        for child in suite.get('suites', []):
            visit(child)
    visit(report)
    return cases


def verify_case_completion(listed, report):
    expected, actual = report_cases(listed), report_cases(report)
    if not expected or expected.keys() != actual.keys():
        raise RuntimeError('实际评测用例与官方发现清单不一致')
    if any(not test.get('results') or test['results'][-1].get('status')
           not in ('passed', 'failed', 'timedOut') for test in actual.values()):
        raise RuntimeError('评测存在跳过或未完成用例')
    return len(expected)


def evaluate(run, attempt=None):
    config = validate_snapshot(run)
    if capture("git", "rev-parse", "HEAD", cwd=BENCH) != config["benchmark_revision"] or capture("git", "status", "--porcelain", cwd=BENCH):
        raise RuntimeError("评测器必须是固定且未经修改的版本")
    attempt = evaluation_id(attempt)
    output = run / 'evaluation' / attempt
    output.mkdir(parents=True)
    shutil.copy2(Path(__file__), output / "runner-evaluation.py")
    arcbench = config.get("deployment") == "arcbench"
    result = {"status": "starting", "started_at": time.time(), "retries": 0, "workers": 1,
              "deployment": "arcbench" if arcbench else "legacy",
              "platform": platform.platform(), "node_version": capture("node", "--version"),
              "test_timeout_ms": 10000 if arcbench else 60000, "expect_timeout_ms": 10000,
              "ci": False, "source_application_hashes": "../../application-hashes.json",
              "evaluation_id": attempt, "run_id": run.name,
              "benchmark_revision": config['benchmark_revision'],
              "application_sha256": digest(hashes(run/'application'))}
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
            result['evaluated_source_sha256'] = digest(hashes(app))
            if result['evaluated_source_sha256'] != result['application_sha256']:
                raise RuntimeError('评测副本与冻结应用不一致')
            if arcbench:
                from submission import validate_application
                validate_application(app)
            for directory in (('frontend', 'backend') if arcbench else ('',)):
                target = app/directory
                package = json.loads((target/'package.json').read_text())
                install = (['npm','install','--include=optional','--no-audit','--no-fund'] if arcbench else
                           ['npm','ci'] if (target/'package-lock.json').exists() else ['npm','install'])
                label = directory+'-' if directory else ''
                phase(output/'summary.json',result,'install',label+'install.log')
                if logged(install, target, env, output/(label+'install.log')) != 0:
                    raise RuntimeError('应用依赖安装失败')
                if (arcbench and directory == 'frontend') or (not arcbench and 'build' in package.get('scripts', {})):
                    phase(output/'summary.json',result,'build',label+'build.log')
                    if logged(['npm','run','build'], target, env, output/(label+'build.log')) != 0:
                        raise RuntimeError('应用构建失败')
            prepared_hashes=hashes(app)
            save(output/'prepared-application-hashes.json',prepared_hashes)
            result['prepared_application_sha256']=digest(prepared_hashes)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            url = f"http://127.0.0.1:{port}"
            result["target_url"] = url
            env["PORT"] = str(port)
            if arcbench: env["HOST"] = "0.0.0.0"
            phase(output/'summary.json',result,'health','application.log')
            with (output / "application.log").open("w") as log:
                proc = subprocess.Popen(["npm", "run", "start"], cwd=app/"backend" if arcbench else app, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    deadline = time.monotonic() + 120 if arcbench else None
                    while True:
                        if deadline is not None and time.monotonic() >= deadline:
                            raise RuntimeError("应用启动超过 120 秒")
                        if proc.poll() is not None:
                            raise RuntimeError("应用在健康检查前退出")
                        try:
                            with urllib.request.urlopen(url + ("/" if arcbench else "/api/health"), timeout=2) as response:
                                healthy = response.status < 500 if arcbench else response.status == 200
                                if healthy:
                                    break
                        except urllib.error.HTTPError as exc:
                            if arcbench and exc.code < 500:
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
                               "--target-url", url, "--timeout", str(result["test_timeout_ms"]), "--expect-timeout", "10000",
                               "--retries=0", "--reporter=list,json,html"]
                    save(output / "command.json", command)
                    phase(output/'summary.json',result,'discovery','discovery.log')
                    discovery_env = dict(env, PLAYWRIGHT_JSON_OUTPUT_FILE=str(output/'listed.json'))
                    discovery = ['npm', 'run', 'test', '--', '--app', config['task'],
                                 '--', '--list', '--reporter=json']
                    if logged(discovery, BENCH, discovery_env, output/'discovery.log') != 0:
                        raise RuntimeError('官方用例发现失败')
                    listed = json.loads((output/'listed.json').read_text())
                    if listed.get('errors'):
                        raise RuntimeError('官方用例发现报告包含错误')
                    phase(output/'summary.json',result,'tests','test.log')
                    result["exit_code"] = logged(command, BENCH, env, output / "test.log")
                    if not (output / "results.json").exists():
                        raise RuntimeError("评测未生成 JSON 报告；参阅 test.log")
                    report = json.loads((output / 'results.json').read_text())
                    result.update(score(report))
                    if not result["total"] or result["errors"] or result["exit_code"] not in (0, 1):
                        raise RuntimeError("评测中断、没有测试结果或出现全局错误，不能作为完整分数")
                    result['verified_cases'] = verify_case_completion(listed, report)
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


def remote_evaluation_snapshot(host, remote_run, attempt):
    code = "from pathlib import Path; import json; p=Path("+repr(remote_run)+")/'evaluation'/"+repr(attempt)+"/'summary.json'; print(p.read_text() if p.exists() else 'null')"
    return json.loads(capture('ssh',host,'python3 -c '+shlex.quote(code)))


def wait_for_remote(process, observe):
    """Process completion is immediate; remote status sampling is at most every 3 minutes."""
    while True:
        try:
            return process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            observe()


def check_evaluation_identity(summary, run, config, attempt):
    expected = {'evaluation_id': attempt, 'run_id': run.name,
                'benchmark_revision': config['benchmark_revision'],
                'application_sha256': digest(json.loads((run/'application-hashes.json').read_text()))}
    if any(summary.get(key) != value for key, value in expected.items()):
        raise RuntimeError('评测身份与请求或冻结应用不一致')


def evaluate_remote(run, host, attempt=None):
    """Transfer a frozen application; the host keeps its installed evaluator."""
    config=validate_snapshot(run)
    attempt = evaluation_id(attempt)
    record = run/'remote-evaluations'/f'{attempt}.json'
    record.parent.mkdir(exist_ok=True)
    if record.exists():
        raise FileExistsError(f'评测 ID 已使用: {attempt}')
    remote={'host':host, 'attempt':attempt}
    def publish(name=None, **fields):
        if name:
            phase(record, remote, name, **fields)
        else:
            remote.update(updated_at=time.time(), **fields)
            save(record, remote)
        # Convenience pointer for old readers; this attempt's record is authoritative.
        save(run/'remote-evaluation.json', remote)
    publish('connect')
    try:
        remote_home=capture('ssh',host,'pwd')
        remote_root=remote_home+'/Development/factory26'
        remote_run=remote_root+'/runs/'+run.name
        remote['remote_run']=remote_run
        publish('transfer')
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
        command='cd '+shlex.quote(remote_root)+' && python3 scripts/factory.py eval --run '+shlex.quote(remote_run)+' --evaluation-id '+shlex.quote(attempt)
        publish('running_remote')
        result=subprocess.Popen(['ssh',host,command])
        def observe():
            try:
                summary=remote_evaluation_snapshot(host,remote_run,attempt)
                if summary is not None:
                    check_evaluation_identity(summary,run,config,attempt)
                    remote.update(summary=summary,observation_error=None)
                remote['observed_at']=time.time()
            except (OSError,subprocess.CalledProcessError,ValueError) as exc:
                remote['observation_error']=str(exc)
            publish()
        wait_for_remote(result,observe)
        publish('download',exit_code=result.returncode)
        with tempfile.TemporaryDirectory(prefix='factory26-results-') as temp:
            download=subprocess.Popen(['ssh',host,'tar -cf - -C '+shlex.quote(remote_run)+' '+shlex.quote('evaluation/'+attempt)],stdout=subprocess.PIPE)
            try:
                with tarfile.open(fileobj=download.stdout,mode='r|') as archive:
                    archive.extractall(temp,filter='data')
            finally: download.stdout.close()
            if download.wait(): raise RuntimeError('remote evidence download failed')
            downloaded=Path(temp)/'evaluation'/attempt
            summary=json.loads((downloaded/'summary.json').read_text())
            check_evaluation_identity(summary,run,config,attempt)
            output=run/'evaluation'/attempt
            output.parent.mkdir(exist_ok=True)
            shutil.copytree(downloaded,output)
        remote.update(summary=summary,observed_at=time.time(),observation_error=None)
        if result.returncode:
            remote['failed_phase']='remote_'+(remote.get('summary',{}).get('failed_phase') or 'execution')
            raise RuntimeError('remote evaluation failed; downloaded evidence retained')
        if summary.get('status') != 'completed':
            raise RuntimeError('远程进程结束但评测没有完整终态')
        publish('completed')
    except BaseException as exc:
        remote.update(error=str(exc) or type(exc).__name__)
        remote.setdefault('failed_phase',remote.get('phase'))
        publish('failed')
        raise
    return output


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
    metadata=json.loads((run/'run.json').read_text())
    manifest = run/'native/manifest.json'
    if manifest.exists():
        entries = json.loads(manifest.read_text())['sessions']
        if any(entry.get('archive_error') or not entry.get('native') for entry in entries):
            raise RuntimeError('原生清单包含缺失证据；不能关联 analysis')
    else:
        paths=sorted((run/'native').glob('*.jsonl'))
        if not paths and (run/'pi-session.jsonl').exists(): paths=[run/'pi-session.jsonl']
        entries = [{'native':str(path.relative_to(run)), 'provider':metadata['backend']} for path in paths]
    if not entries:
        raise RuntimeError('没有可分析的原生会话')
    output=run/'analysis'; output.mkdir(exist_ok=True)
    for index, entry in enumerate(entries):
        source = (run/entry['native']).resolve(strict=True)
        if not source.is_relative_to(run.resolve()):
            raise RuntimeError('原生清单指向 run 以外的路径')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if entry.get('sha256') is not None and source_hash != entry['sha256']:
            raise RuntimeError('原生清单内容哈希不一致')
        inputs = dict(provenance, source_session=source.name, source_sha256=source_hash,
                      provider=entry['provider'],
                      session_identity={k:entry.get(k) for k in ('native_id','profile_id','effective_profile_digest','parent_native_session_id','native_role','work_item_kind','work_item_id','assignment_generation')})
        fingerprint = digest(inputs)[:20]
        # Both the exporter and exact native bytes determine a reusable analysis.
        folder=output/f'{index:03}-{fingerprint}'
        if folder.exists():
            cached = json.loads((folder/'provenance.json').read_text())
            if any(cached.get(key) != value for key, value in inputs.items()):
                raise RuntimeError(f'analysis 缓存来源不匹配: {folder}')
            if any(not (folder/name).is_file() or hashlib.sha256((folder/name).read_bytes()).hexdigest() != sha
                   for name, sha in cached['artifacts'].items()):
                raise RuntimeError(f'analysis 缓存内容已改变: {folder}')
            print(f'[缓存] {folder}',flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix='.analysis-',dir=output) as temp:
            staging=Path(temp)
            evidence=staging/'evidence-v4.zip'
            result=capture(*svc,'telemetry','agent-thread','export','--provider',entry['provider'],
                           '--source',str(source),'--output',str(evidence),'--json')
            (staging/'export.json').write_text(result+'\n')
            for request in requests:
                response=subprocess.run([*svc,'analysis','query','--input',str(evidence),'--request','-'],
                                        input=json.dumps(request),capture_output=True,text=True,check=True)
                save(staging/f"{request['intent']}.json",json.loads(response.stdout))
            if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
                raise RuntimeError('原生会话在 analysis 导出期间改变')
            save(staging/'provenance.json',dict(inputs,created_at=time.time(),artifacts=hashes(staging)))
            staging.rename(folder)
    print(f'[svc] {output}，{len(entries)} 个原生会话',flush=True)


def run_experiment(config, eval_host=None, svc_source=None):
    """Run one experiment and publish its terminal result after evidence collection.

    A generation error must not bypass analysis. Analysis errors are secondary:
    they cannot replace a generation/evaluation error or invalidate a real score.
    """
    from run_feedback import monitor
    run = new_run()
    save(run/'config.json', config)
    outcome = {'schema_version':1, 'run_id':run.name, 'variant':config.get('variant'),
               'backend':config.get('backend','pi'),
               'task':config['task'], 'status':'running', 'stage':'generation',
               'started_at':time.time(), 'finished_at':None, 'error':None,
               'analysis':{'status':'pending'}, 'evaluation_id':None}
    save(run/'outcome.json', outcome)
    print(f'[实验] {run}', flush=True)
    original = None
    terminal = 'completed'
    with monitor(run):
        try:
            generate(config, run=run)
            outcome['stage']='evaluation'
            outcome['evaluation_id']=evaluation_id()
            save(run/'outcome.json', outcome)
            if eval_host:
                evaluate_remote(run,eval_host,outcome['evaluation_id'])
            else:
                evaluate(run,outcome['evaluation_id'])
        except BaseException as exc:
            original = exc
            terminal = 'interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed'
            outcome.update(failed_stage=outcome['stage'],
                           error={'type':type(exc).__name__, 'message':str(exc) or type(exc).__name__})
        finally:
            outcome['stage']='analysis'
            save(run/'outcome.json', outcome)
            if (run/'native/manifest.json').is_file():
                try:
                    analyze(run,svc_source)
                    outcome['analysis']={'status':'completed'}
                except BaseException as exc:
                    outcome['analysis']={'status':'interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',
                        'error':{'type':type(exc).__name__, 'message':str(exc) or type(exc).__name__}}
                    if isinstance(exc,KeyboardInterrupt) and original is None:
                        original, terminal = exc, 'interrupted'
                        outcome.update(failed_stage='analysis',error=outcome['analysis']['error'])
            else:
                outcome['analysis']={'status':'unavailable', 'reason':'没有可关联的原生会话清单'}
            outcome.update(status=terminal,finished_at=time.time())
            save(run/'outcome.json', outcome)
    if original is not None:
        raise original
    return run


def bootstrap(config):
    if 'effective' in config:
        from native_profiles import bootstrap as bootstrap_native
        bootstrap_native()
    if config.get('backend')=='codex':
        if not (ROOT/'.adapter/bin/python').exists():
            subprocess.run(['uv','venv',str(ROOT/'.adapter')],check=True)
        subprocess.run(['uv','pip','install','--python',str(ROOT/'.adapter/bin/python'),'litellm[proxy]==1.102.0'],check=True)
    if config.get('svc'):
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
    parser.add_argument("command", choices=["bootstrap", "generate", "eval", "analyze", "run", "list", "show", "batch"])
    parser.add_argument("run_id", nargs="?", help="show 的 run ID")
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument("--config", type=Path, help="显式自定义单核心配置；默认 pi-team-mixed variant")
    selection.add_argument("--variant", help="生成 variant，或 list 的历史 variant 过滤器")
    parser.add_argument("--backend", choices=('pi', 'codex'), help="生成核心；默认取配置（pi）；list 时过滤 backend")
    parser.add_argument("--task", help="选择 ARC-Bench-Lite 任务，或 list 按任务过滤")
    parser.add_argument("--json", action="store_true", help="输出可机器读取的摘要")
    parser.add_argument("--eval", dest="evaluation", help="show 指定评测尝试")
    parser.add_argument("--evaluation-id", help="eval 的明确执行 ID；已存在时拒绝覆盖")
    parser.add_argument("--svc-source", type=Path, help="使用本地 SVC 工作树的 PDM 环境做 analysis；运行时 Corpus 不变")
    parser.add_argument("--profile", help="show 按 Braid profile 选择原生证据")
    parser.add_argument("--session", help="show 按原生 session ID 选择证据")
    parser.add_argument("--case", help="show 指定失败用例，如 REQ-2.2")
    parser.add_argument("--eval-host", help="SSH host with bootstrapped ~/Development/factory26 evaluator")
    parser.add_argument("--run", type=Path, help="eval/analyze/show 的已有 run 目录")
    parser.add_argument("--batch-manifest", type=Path, default=ROOT/"experiments/multi-agent-lite.json")
    args = parser.parse_args()
    if args.command == "batch":
        if args.config or args.variant or args.backend or args.task or args.eval_host:
            parser.error("batch 从固定 manifest 读取配置，不接受单项覆盖")
        from batch import execute
        directory = args.run or ROOT/"runs"/("batch-"+evaluation_id())
        result = execute(args.batch_manifest, directory)
        print(json.dumps({"batch":str(directory), "status":result["status"]}, ensure_ascii=False))
        return
    if args.command in ('show','eval','analyze') and (args.config or args.variant or args.backend):
        parser.error('已有 run 使用归档配置，不接受 --config、--variant 或 --backend 覆盖')
    if args.command in ('list','show'):
        from inspect_runs import list_runs, show_run, render_list, render_show
        if args.command=='list':
            if args.config: parser.error('list 不接受 --config')
            result=list_runs(ROOT,variant=args.variant,task=args.task,backend=args.backend)
            output=render_list(result)
        else:
            selected=args.run or (ROOT/'runs'/args.run_id if args.run_id else None)
            if selected is None: parser.error('show 需要 run ID 或 --run')
            result=show_run(selected.resolve(),evaluation=args.evaluation,case=args.case,profile=args.profile,session=args.session)
            output=render_show(result)
        print(json.dumps(result,ensure_ascii=False,indent=2) if args.json else output)
        return
    if args.command in ('eval','analyze'):
        if args.run is None: parser.error('eval/analyze 需要 --run')
        if args.command=='eval' and args.eval_host: evaluate_remote(args.run.resolve(),args.eval_host,args.evaluation_id)
        elif args.command=='analyze': analyze(args.run.resolve(),args.svc_source.resolve() if args.svc_source else None)
        else: evaluate(args.run.resolve(),args.evaluation_id)
        return
    try:
        config=load_config(args.config,args.backend,args.variant,args.task)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.command=='bootstrap':
        bootstrap(config)
    elif args.command=='run':
        run_experiment(config,args.eval_host,args.svc_source.resolve() if args.svc_source else None)
    else:
        generate(config)


if __name__ == "__main__":
    main()
