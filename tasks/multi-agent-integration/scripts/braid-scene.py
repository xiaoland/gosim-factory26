#!/usr/bin/env python3
"""Joint acceptance: live native-tree reset, then two Braid work-item deliveries.

Uses synthetic requirements only. The host changes context after observing an
actual native child writer; model output is not the stop oracle.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
import factory
import profiles
import sources
from braid_runtime import initialize_repository, load_delivery, export_delivery, archive_state
from core import archive_sessions


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def run(backend):
    config = profiles.configuration('pi-team' if backend == 'pi' else 'codex-generalist')
    output = ROOT/'runs/integration'/f'{time.strftime("%Y%m%d-%H%M%S")}-{backend}-braid-{uuid.uuid4().hex[:6]}'
    output.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix='f26-braid-', dir='/tmp')).resolve()
    app = work/'application'; app.mkdir()
    inputs = work/'input'; inputs.mkdir()
    record = dict(kind='multi-agent-joint-braid-stage', backend=backend, status='running',
                  started_at=time.time(), workspace=str(work), resets=[])
    factory.save(output/'check.json', record)
    factory.save(output/'effective-config.json', config['effective'])
    sources.archive('braid',output/'sources'); sources.archive('svc',output/'sources')
    spec = importlib.util.spec_from_file_location('native_scene',Path(__file__).with_name('native-scene.py'))
    native_scene = importlib.util.module_from_spec(spec); spec.loader.exec_module(native_scene)
    native_scene.fixture_png(inputs/'image.png')
    writer = inputs/'writer.py'
    writer.write_text('''import json, os, sys, time
from pathlib import Path
target=Path(sys.argv[1]); identity=os.environ.get('PI_SESSION_ID') or os.environ.get('CODEX_THREAD_ID')
assert identity, 'native child identity is required'
while True:
    with target.open('a') as stream:
        stream.write(json.dumps({'native_session_id':identity,'pid':os.getpid(),'time':time.time()})+'\\n')
    time.sleep(.2)
''')
    initialize_repository(app)
    native,env = factory.runtime_environment(work,config)
    state = work/'braid-state'
    (work/'bin').mkdir()
    executable = work/'bin/braid'; shutil.copy2(sources.binary(),executable)
    env['PATH']=str(executable.parent)+os.pathsep+env['PATH']
    # Host CLI must not borrow the runtime's writer identity.
    def cli(*args, check=True):
        return subprocess.run([str(executable),'--state',str(state),'--external',*args],
                              cwd=app,env=env,text=True,capture_output=True,check=check)
    def snapshots():
        rows = read_json(state/'sessions.json',[])
        assert [row.get('context_path') for row in rows] == sorted(row.get('context_path') for row in rows), 'sessions.json is not sorted by context path'
        return rows
    def await_condition(predicate, process):
        while not predicate():
            if process.poll() is not None:
                raise RuntimeError(f'Braid exited before expected observation: {process.returncode}; see braid.log')
            time.sleep(.5)
    def await_native_quiet(path, process):
        """The fixture writes every .2s; one quiet second is a stop oracle."""
        deadline = time.time()+10
        last = (path.stat().st_size, path.stat().st_mtime_ns)
        quiet_since = time.time()
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f'Braid exited before native child stopped: {process.returncode}; see braid.log')
            time.sleep(.2)
            current = (path.stat().st_size, path.stat().st_mtime_ns)
            if current != last:
                last, quiet_since = current, time.time()
            elif time.time()-quiet_since >= 1:
                return
        raise RuntimeError('native child heartbeat did not become quiet before replacement')
    def root_entries():
        return [entry for entry in snapshots() if str(entry.get('work_item_id'))=='1' and entry.get('work_item_kind')=='issue']
    phases = ['foreground','background'] if backend=='pi' else ['foreground']
    def reset_prompt(mode):
        task = f'只运行 python3 {writer} {work}/{mode}.jsonl，保持前台；不要另行后台化，不要设置短 timeout。宿主会停止本子代理。不要调用 Braid。'
        if backend=='pi':
            launch = ('调用 subagent，async:'+str(mode=='background').lower()+', context:"fresh", workflowScript:'+json.dumps('return runs.run("writer", { agent: "executor", task: '+json.dumps(task,ensure_ascii=False)+' });',ensure_ascii=False))
        else:
            launch = '用 spawn_agent(agent_type="executor") 创建原生子代理，任务为 '+task+'；用 wait 等待。'
        return f'''这是受控生命周期检查，不是应用需求。先在当前工作树写入 retained.txt，内容必须为 retained-dirty；已有则核对，不要提交。
{launch}
主会话不可运行 writer.py，不要创建 Issue/PR 或关闭 Issue。子代理启动后不要重复派发；在 {work}/{mode}.jsonl 至少有两行前持续等待并检查，不要结束本次响应。宿主观察到真实写入后会修改当前 description 并重建上下文。'''
    profile_ids = list(config['effective']['profiles'])
    ui = 'team-ui' if backend=='pi' else profile_ids[0]
    impl = 'team-app' if backend=='pi' else profile_ids[0]
    final_prompt = f'''这是受控 Braid multi-agent 交付场景。先核对当前工作树 retained.txt 的内容是 retained-dirty；删除此临时检查文件，不要提交它。
创建两个子 Issue（parent=1），分别明确 assignee：
A. {ui}：交付 colors.py 的 bands() 返回图像 {inputs}/image.png 从上到下的英文颜色名称列表。必须用原生图像工具观察图片，不可解码像素。通过工具编写代码，自己选择并读取已配置的一个相关技能，设计验收并用 PR 实现、提交和合入，PR 也明确指派 {ui}。
B. {impl}：交付 calc.py 的 add(a,b)，包括负数和零。自己选择并读取已配置的一个相关技能，设计验收并用 PR 实现、提交和合入，PR 明确指派 {impl}。
两项互不修改对方文件，可独立推进；不要亲自代替它们实现。各子 Issue 用评论向根 Issue 报告产物与证据，完成后 close --reason completed。你通过评论讨论、核对各 PR 已合入，最后验证交付分支的 bands()==['red','green','blue']、add(2,3)==5、add(-4,1)==-3，再关闭根 Issue completed。
这是临时仓库，允许本地 commit/merge，禁止 push。所有 shell 需要走当前输入给定的 Braid writer 身份。无中途人类介入，不用官方 benchmark，不安装依赖，不开发 Web 应用。'''
    proc=None
    try:
        with factory.responses_adapter(config,output) as responses_url:
            request=factory.braid_request(config,work,app,native,reset_prompt(phases[0]),state,output.name,responses_url)
            factory.save(work/'request.json',request)
            factory.save(output/'request.json',request)
            with (output/'braid.log').open('w') as log:
                proc=subprocess.Popen(factory.isolation_prefix(work,inputs)+[str(executable),'local',str(work/'request.json')],
                    cwd=app,env=env,stdout=log,stderr=log,start_new_session=True)
                for index,mode in enumerate(phases):
                    heartbeat=work/f'{mode}.jsonl'
                    await_condition(lambda: heartbeat.exists() and len(heartbeat.read_text().splitlines())>=2,proc)
                    roots=root_entries()
                    old=next(e for e in roots if e['status'] in ('running','idle'))
                    assert old.get('profile_id') and old.get('effective_profile_digest'), 'root session lacks profile material identity'
                    assert old.get('native_session_id') and old.get('parent_native_session_id') is None, 'invalid root native identity fields'
                    assert old.get('native_home') and old.get('native_session_path'), 'root session lacks native paths'
                    assert old.get('work_item_kind') == 'issue' and str(old.get('work_item_id')) == '1'
                    previous_ids={e['session_id'] for e in roots}
                    old_id=old['session_id']; old_worktree=old['worktree']
                    child_id=json.loads(heartbeat.read_text().splitlines()[0])['native_session_id']
                    assert child_id != old.get('native_session_id',old_id), 'parent ran the child writer'
                    replacement=reset_prompt(phases[index+1]) if index+1<len(phases) else final_prompt
                    assert (Path(old_worktree)/'retained.txt').read_text().strip()=='retained-dirty'
                    cli('issue','edit','1','--body',replacement)
                    stale=subprocess.run([str(executable),'--state',str(state),'--writer-turn',old['turns'][-1]['braid_turn_id'],
                        'issue','comment','1','--body','stale writer must not mutate'],cwd=app,env=env,text=True,capture_output=True)
                    assert stale.returncode and 'stale, fenced, or no longer running' in stale.stderr, 'old writer was accepted'
                    await_native_quiet(heartbeat,proc)
                    await_condition(lambda: any(e['session_id'] not in previous_ids for e in root_entries()),proc)
                    replacement_entry=next(e for e in root_entries() if e['session_id'] not in previous_ids)
                    assert replacement_entry['worktree']==old_worktree, 'replacement discarded the original worktree'
                    # A new native root may not coexist with the old child writer.
                    size=heartbeat.stat().st_size; time.sleep(2)
                    assert heartbeat.stat().st_size==size, 'old native child continues writing after replacement'
                    reset=dict(mode=mode,old_session_id=old_id,new_session_id=replacement_entry['session_id'],
                               child_native_session_id=child_id,worktree=old_worktree,writer_stopped=True,old_writer_rejected=True)
                    if backend=='pi':
                        receipt=read_json(Path(old['native_home'])/'.factory/subagent-stop.json')
                        assert receipt and receipt['state']=='stopped', 'missing successful native-tree receipt'
                        child=next((c for c in receipt['children'] if c.get('child_session_id')==child_id and c.get('mode')==mode),None)
                        assert child, 'stop receipt omits active child'
                        proof=child.get('proof',{})
                        if mode=='foreground':
                            assert child.get('mode')=='foreground' and proof.get('parent_process_group_terminal') is True, 'foreground process-group proof is invalid'
                        else:
                            assert child.get('mode')=='background' and all(proof.get(key) is True for key in ('control_requested','parent_process_group_terminal')), 'background process-tree proof is invalid'
                        receipt_mtime=Path(old['native_home'],'.factory/subagent-stop.json').stat().st_mtime_ns
                        replacement_file=next(path for path in state.glob('physical/*/session.json') if read_json(path).get('session_id') == replacement_entry['session_id'])
                        assert receipt_mtime <= replacement_file.stat().st_mtime_ns, 'replacement root appeared before native stop receipt'
                        reset['receipt']=receipt
                    record['resets'].append(reset); factory.save(output/'check.json',record)
                proc.wait()
                if proc.returncode: raise RuntimeError(f'Braid exit {proc.returncode}; see braid.log')
                delivery=load_delivery(state,app,work,request)
                export_delivery(app,delivery['delivery_commit'],output/'application')
                subprocess.run([sys.executable,'-c',"from calc import add; from colors import bands; assert add(2,3)==5; assert add(-4,1)==-3; assert bands()==['red','green','blue']"],cwd=output/'application',check=True)
                entries=snapshots()
                children=[e for e in entries if e.get('work_item_kind')=='issue' and str(e.get('work_item_id'))!='1']
                assert len({e['work_item_id'] for e in children})>=2, 'two distinct Braid Issues were not executed'
                assert {ui,impl}.issubset({e.get('profile_id') for e in children}), 'requested profiles did not run'
                prs=[e for e in entries if e.get('work_item_kind')=='pr']
                assert len({e['work_item_id'] for e in prs})>=2, 'two distinct PRs were not executed'
                assert {ui,impl}.issubset({e.get('profile_id') for e in prs}), 'requested PR profiles did not run'
                record.update(status='passed',delivery=delivery,child_issues=sorted({e['work_item_id'] for e in children}))
    except BaseException as error:
        record.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        if proc: factory.stop(proc)
        record['cleanup_pids']=factory.cleanup_workspace(work)
        entries=archive_state(state,output) if state.exists() else []
        archived=archive_sessions(output,native,work,entries)
        if record['status']=='passed' and (not archived or any(e.get('archive_error') or e.get('evidence_error') for e in archived)):
            record.update(status='failed',error='Native evidence incomplete')
        for mode in phases:
            if (work/f'{mode}.jsonl').exists(): shutil.copy2(work/f'{mode}.jsonl',output/f'{mode}.jsonl')
        record['finished_at']=time.time(); factory.save(output/'check.json',record)
        print(json.dumps(record,ensure_ascii=False),flush=True)
        if record['status']=='passed': shutil.rmtree(work)
    if record['status']!='passed': raise RuntimeError(record['error'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=('pi','codex'),required=True)
    run(parser.parse_args().backend)
