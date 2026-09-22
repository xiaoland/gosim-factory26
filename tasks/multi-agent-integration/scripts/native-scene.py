#!/usr/bin/env python3
"""Joint acceptance, native-capability stage. No benchmark inputs or evaluator."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from threading import Thread
import time
import uuid
import zlib

_bootstrap = argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--package', type=Path)
_bootstrap.add_argument('--output', type=Path)
_bootstrap_args, _ = _bootstrap.parse_known_args()
PACKAGE = _bootstrap_args.package or (Path(os.environ['FACTORY26_QUALIFICATION_PACKAGE'])
                                      if os.environ.get('FACTORY26_QUALIFICATION_PACKAGE') else None)
if PACKAGE:
    ROOT = PACKAGE.resolve()
else:
    try:
        ROOT = Path(__file__).resolve().parents[3]
    except IndexError as error:
        raise RuntimeError('浅路径运行必须传 --package 或 FACTORY26_QUALIFICATION_PACKAGE') from error
sys.path.insert(0, str(ROOT/'scripts'))
import factory
import native_profiles
import profiles
import submission
from core import archive_sessions, codex_turn


def fixture_png(path):
    def chunk(kind, data):
        return struct.pack('!I', len(data))+kind+data+struct.pack('!I', zlib.crc32(kind+data))
    rows = b''.join(b'\0'+bytes(color)*96 for color in [(255, 0, 0)]*32+[(0, 255, 0)]*32+[(0, 0, 255)]*32)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('!2I5B',96,96,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))


def pi_entry(native, profile):
    manifest = native/'.factory/session-tree.json'
    tree = json.loads(manifest.read_text()) if manifest.exists() else {}
    return dict(provider='pi',session_id=tree.get('parent_native_session_id'),
                native_session_path=tree.get('parent_session_file'),native_home=str(native),
                native_teardown_configured=True,profile_id=profile,parent_native_session_id=None)


def codex_entry_from_events(output, native, profile):
    """Recover the started Codex root from the transport event, even on a failed turn."""
    thread_id = None
    session_path = None
    events = output/'codex-events.jsonl'
    if events.exists():
        for line in events.read_text().splitlines():
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            result_thread = (frame.get('result') or {}).get('thread') if isinstance(frame.get('result'), dict) else None
            param_thread = (frame.get('params') or {}).get('thread') if isinstance(frame.get('params'), dict) else None
            thread = result_thread or param_thread
            if isinstance(thread, dict):
                thread_id = thread.get('id') or thread_id
                session_path = thread.get('path') or session_path
            if thread_id and session_path:
                break
    return dict(provider='codex', session_id=thread_id, native_session_path=session_path,
                native_home=str(native), profile_id=profile,
                parent_native_session_id=None)


def configuration(backend):
    if PACKAGE:
        manifest = submission.verify_package(ROOT)
        config = submission.platform_config(ROOT, manifest)
        if config['backend'] != backend:
            raise ValueError(f'资格包 backend 是 {config["backend"]}，不是 {backend}')
        return config
    variant = 'pi-team-mixed' if backend == 'pi' else 'codex-generalist'
    return profiles.configuration(variant)


def run(backend, selected_output=None):
    config = configuration(backend)
    selected_output = selected_output or (Path(os.environ['FACTORY26_QUALIFICATION_OUTPUT'])
                                          if os.environ.get('FACTORY26_QUALIFICATION_OUTPUT') else None)
    if selected_output:
        output = selected_output.resolve()
    elif PACKAGE:
        raise ValueError('包模式必须传 --output 或 FACTORY26_QUALIFICATION_OUTPUT')
    else:
        output = ROOT/'runs/integration'/f'{time.strftime("%Y%m%d-%H%M%S")}-{backend}-native-{uuid.uuid4().hex[:6]}'
    output.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix='f26-scene-', dir='/tmp')).resolve()
    external_inputs = Path(tempfile.mkdtemp(prefix='f26-scene-input-', dir='/tmp')).resolve() if PACKAGE else None
    record = dict(kind='multi-agent-joint-native-stage', backend=backend, status='running',
                  started_at=time.time(), workspace=str(work), effective_digest=config['effective']['effective_digest'])
    factory.save(output/'check.json',record)
    factory.save(output/'effective-config.json',config['effective'])
    print(output,flush=True)
    app = work/'application'; app.mkdir()
    inputs = external_inputs or work/'input'
    if not external_inputs: inputs.mkdir()
    fixture_png(inputs/'image.png')
    (inputs/'index.html').write_text('<!doctype html><title>Isolation probe</title><label>Value<input id="value"></label><button onclick="localStorage.setItem(\'probe\',document.querySelector(\'input\').value);document.cookie=\'probe=\'+document.querySelector(\'input\').value">Save</button>')
    handler = partial(SimpleHTTPRequestHandler,directory=str(inputs))
    server = ThreadingHTTPServer(('127.0.0.1',0),handler)
    Thread(target=server.serve_forever,daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    native,env = factory.runtime_environment(work,config)
    env['PATH'] = str(work/'bin')+os.pathsep+env['PATH']
    parent = config['effective']['defaults']['issue']
    entries = []
    try:
        with factory.responses_adapter(config,output) as responses_url:
            _,bindings = native_profiles.materialize(config['effective'],work,responses_url or config['base_url'],output.name)
            binding = bindings[parent]
            native = work/'native'; shutil.copytree(binding['native_template'],native)
            env.update(PI_CODING_AGENT_DIR=str(native),CODEX_HOME=str(native))
            browser_tasks = []
            for token in ('alpha','beta'):
                browser_tasks.append(f'''你是原生 browser-operator，读取 agent-browser 技能。用 agent-browser 打开 {url}。
先用 eval 读取 localStorage.getItem('probe')，必须为 null；fill #value 为 {token}，click button，reload。
用 eval 读取 storage 和 cookie，确认均为 {token}，screenshot {app}/{token}.png。
不要覆盖 --session。将观察写入 {app}/{token}.json，格式 {{"initial":null,"stored":"{token}","cookie":"probe={token}","native_session_id":"实际 PI_SESSION_ID 或 CODEX_THREAD_ID"}}，关闭当前浏览器。
仅操作这份受控页面和自己的证据文件。''')
            delegation = ('Pi 子代理调用统一传 async:false、context:fresh。workflowScript 单项用 return runs.run("key", {agent:"角色", task:"任务"})；'
                          '并行用 return await runs.all([{key:"alpha",agent:"browser-operator",task:"任务A"},'
                          '{key:"beta",agent:"browser-operator",task:"任务B"}])。runs.all 接受带 key 的描述对象，不接受 runs.run 的 Promise；'
                          '结果为有序数组，用索引读取。两个 browser-operator 必须使用上述并行调用。'
                          if backend=='pi' else '用原生 spawn_agent 启动两个 browser-operator，等待并收取各自结果。')
            prompt = f'''这是 multi-agent 联合验收的原生能力阶段，不是产品开发。不要创建 Issue/PR、不要创建 Git repo、不要调用外部服务。
{delegation}
1. 委派 vision 子代理，用其原生图像读取工具观察 {inputs}/image.png；vision 只返回从上到下三条色带的英文名称，不写文件，不可通过解码像素替代图像输入。父会话收到观察结果后用自己的工具写入 {app}/image.json JSON 数组。
2. 委派 executor 实现 {app}/calc.py 的 add(a,b)，自行运行 add(2,3)==5 和 add(-4,1)==-3 的断言。executor 阅读自己配置的技能，独立完成局部反馈并返回证据。
3. 两个 browser-operator 并行执行，任务分别为：{json.dumps(browser_tasks,ensure_ascii=False)}
不要让主会话执行浏览器步骤。收齐产物后检查并结束；遇到协议/能力错误请直接报告，不安装或更换核心、扩展或模型。'''
            (output/'prompt.txt').write_text(prompt)
            prefix = submission.isolation_prefix(work,inputs) if PACKAGE else factory.isolation_prefix(work,inputs)
            if backend=='pi':
                session = native/'parent.jsonl'
                command = prefix+[binding['executable'],'--provider','factory26','--model',config['model'],
                    '--thinking',config['thinking'],'--mode','json','--print','--session',str(session),prompt]
                code = factory.logged(command,app,env,output/'pi-events.jsonl')
                entries = [pi_entry(native,parent)]
                if code: raise RuntimeError(f'Pi process exit {code}')
                factory.pi_usage(Path(entries[0]['native_session_path']))
            else:
                terminal = codex_turn(prefix+[binding['executable']],app,env,prompt,output,config['model'],config['thinking'])
                entries = [dict(provider='codex',session_id=terminal['thread_id'],native_home=str(native),profile_id=parent,parent_native_session_id=None)]
            assert json.loads((app/'image.json').read_text()) == ['red','green','blue'], 'image answer differs'
            subprocess.run([sys.executable,'-c','from calc import add; assert add(2,3)==5; assert add(-4,1)==-3'],cwd=app,check=True)
            states = [json.loads((app/f'{token}.json').read_text()) for token in ('alpha','beta')]
            for token,state in zip(('alpha','beta'),states):
                assert state['initial'] is None and state['stored']==token and state['cookie']==f'probe={token}'
            assert states[0]['native_session_id'] != states[1]['native_session_id'], 'browser operators share identity'
            record.update(status='passed',image=True,executor=True,browser_isolation=True)
    except BaseException as exc:
        record.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        server.shutdown(); server.server_close()
        record['cleanup_pids']=factory.cleanup_workspace(work)
        if not entries:
            entries = [pi_entry(native,parent)] if backend == 'pi' else [codex_entry_from_events(output,native,parent)]
        archived=archive_sessions(output,native,work,entries)
        if record['status']=='passed' and (len(archived)<4 or any(e.get('archive_error') for e in archived)):
            record.update(status='failed',error='Native parent/children evidence incomplete')
        shutil.copytree(app,output/'artifacts')
        record['finished_at']=time.time(); factory.save(output/'check.json',record)
        if external_inputs: shutil.rmtree(external_inputs)
        # Preserve failed workspaces and original paths for diagnosis.
        if record['status']=='passed': shutil.rmtree(work)
        print(json.dumps(record,ensure_ascii=False),flush=True)
    if record['status']!='passed': raise RuntimeError(record['error'])
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=('pi','codex'),required=True)
    parser.add_argument('--package',type=Path,help='已解包且冻结的 Linux x86_64 资格包根目录')
    parser.add_argument('--output',type=Path,help='本次资格证据目录；包模式必填')
    args=parser.parse_args()
    run(args.backend,args.output)
