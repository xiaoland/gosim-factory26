#!/usr/bin/env python3
"""真实核心检查：CLI 改对象后自动重建上下文，并完成本地 PR 交付。"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

import factory
import sources
from braid_runtime import initialize_repository, load_delivery, export_delivery, archive_state
from core import archive_sessions, codex_config


def input_texts(path, backend):
    """Read only model inputs for the specific physical-session assertion."""
    texts=[]
    for line in path.read_text().splitlines():
        event=json.loads(line)
        message=event.get('message',{}) if backend=='pi' else event.get('payload',{})
        if message.get('role') not in ('user','developer','system'):
            continue
        content=message.get('content',[])
        if isinstance(content,str): texts.append(content)
        elif isinstance(content,list): texts.extend(part.get('text','') for part in content if isinstance(part,dict))
    return '\n'.join(texts)


def comment_text(context, identity):
    match=re.search(r'(?ms)^### Comment: [^\n]*#issuecomment-'+re.escape(str(identity))+
                    r' by [^\n]+\n(.*?)(?=^### Comment:|\Z)',context)
    if not match: raise RuntimeError(f'投影缺失 comment {identity} 身份')
    return match.group(1)


def preparation_script(executable, state, ready, markers, final_prompt):
    """Each replacement resumes from canonical objects; every edit runs in the native shell."""
    data={'executable':str(executable),'state':str(state),'ready':str(ready),'markers':markers,
          'final_prompt':final_prompt}
    return 'data = '+repr(data)+'\n'+'''
import json, os, sqlite3, subprocess, sys
from pathlib import Path
assert os.environ.get('BRAID_AGENT_RUNTIME') == '1', 'provider did not mark its child runtime'
state=Path(data['state']); ready=Path(data['ready'])
prefix=[data['executable'],'--state',str(state)]
body=ready.with_suffix('.body'); body.write_text(data['markers']['HIDDEN'])
def counts():
    with sqlite3.connect(state/'braid.sqlite3') as db:
        return [db.execute('SELECT count(*) FROM '+table).fetchone()[0]
                for table in ('local_items','local_comments','events')]
before=counts()
external=subprocess.run(prefix+['--external','issue','comment','1','--body-file',str(body),'--json'],capture_output=True,text=True)
assert external.returncode != 0, 'agent used the host external entry'
assert counts()==before, 'rejected external operation changed objects or events'
writer=prefix+['--writer-turn',sys.argv[1]]
if ready.exists():
    ids=json.loads(ready.read_text())
else:
    ids={'first_turn':sys.argv[1]}
    for name,marker in [('hide','HIDDEN'),('delete','DELETED')]:
        body.write_text(data['markers'][marker])
        result=subprocess.run(writer+['issue','comment','1','--body-file',str(body),'--json'],check=True,capture_output=True,text=True)
        ids[name]=json.loads(result.stdout)['id']
    subprocess.run(writer+['comment','reaction','add',str(ids['hide']),'eyes'],check=True,capture_output=True,text=True)
    with sqlite3.connect(state/'braid.sqlite3') as db:
        pending=db.execute("SELECT count(*) FROM events WHERE work_item_node_id='issue:1' AND lifecycle='pending' AND kind IN ('wake','invalidate')").fetchone()[0]
    assert pending==0, 'ordinary self messages created a wake or reset'
stale=subprocess.run(prefix+['--writer-turn','00000000-0000-0000-0000-000000000000','comment','edit',str(ids['hide']),'--body-file',str(body)],capture_output=True,text=True)
assert stale.returncode != 0, 'unknown writer was accepted'
ids['guard']={'runtime_marker':os.environ['BRAID_AGENT_RUNTIME'],'external_rejected':True,
              'external_error':external.stderr.strip(),'objects_and_events_unchanged':True,
              'current_writer_succeeded':True,'unknown_writer_rejected':True,
              'ordinary_self_messages_no_wake':True}
if ids['first_turn']!=sys.argv[1]:
    before=counts()
    old=subprocess.run(prefix+['--writer-turn',ids['first_turn'],'comment','edit',str(ids['hide']),'--body','must not apply'],capture_output=True,text=True)
    assert old.returncode!=0 and 'stale, fenced, or no longer running' in old.stderr, 'old session writer was not fenced'
    assert counts()==before, 'old writer changed durable objects'
    ids['stale_write_rejected']=True
temporary=ready.with_suffix('.tmp');temporary.write_text(json.dumps(ids));temporary.replace(ready)
with sqlite3.connect(state/'braid.sqlite3') as db:
    hidden=db.execute('SELECT lifecycle FROM local_comments WHERE comment_id=?',(ids['hide'],)).fetchone()[0]
    deleted=db.execute('SELECT lifecycle FROM local_comments WHERE comment_id=?',(ids['delete'],)).fetchone()[0]
if hidden!='hidden':
    action=['comment','hide',str(ids['hide']),'--reason','context replacement probe']
elif deleted!='deleted':
    action=['comment','delete',str(ids['delete'])]
else:
    body.write_text(data['final_prompt'])
    action=['issue','edit','1','--body-file',str(body)]
# The committed mutation may interrupt this shell before it receives stdout.
# All continuation facts are already durable; the next native session repeats the script.
subprocess.run(writer+action,check=True,capture_output=True,text=True)
'''


def check(backend, svc=False):
    config=factory.load_config(factory.ROOT/'variants/factory/config.json',backend=backend)
    config['variant']='braid-integration-probe'
    config['svc']=svc
    output=factory.ROOT/'runs/integration'/f"{time.strftime('%Y%m%d-%H%M%S')}-{backend}-{'svc' if svc else 'plain'}-{uuid.uuid4().hex[:6]}"
    output.mkdir(parents=True)
    record={'backend':backend,'svc':svc,'status':'running','started_at':time.time(),
            'model':config['model'],'kind':'braid-context-integration',
            'core_version':factory.capture(backend,'--version')}
    factory.save(output/'check.json',record)
    factory.save(output/'config.json',config)
    braid_source=sources.archive('braid',output/'sources')
    if svc: sources.archive('svc',output/'sources')
    markers={name:f'{name}_{uuid.uuid4().hex}' for name in ('OLD','NEW','HIDDEN','DELETED')}
    print(f'[接入检查] {output}',flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix='factory26-check-') as temporary, factory.responses_adapter(config,output) as url:
            work=Path(temporary).resolve(); app=work/'application'; app.mkdir()
            inputs=work/'input'; inputs.mkdir()
            native,env=factory.runtime_environment(work,config)
            if backend=='pi':
                factory.save(native/'models.json',{'providers':{'deepseek':{'baseUrl':config['base_url'],'apiKey':'$FACTORY26_API_KEY'}}})
            else: codex_config(native,url,config['model'])
            initialize_repository(app)
            state=work/'braid-state'; (work/'bin').mkdir()
            executable=work/'bin/braid'; shutil.copy2(sources.binary(),executable)
            if factory.hashlib.sha256(executable.read_bytes()).hexdigest() != braid_source['artifacts']['braid']:
                raise RuntimeError('Braid 运行制品与已归档构建不一致')
            env['PATH']=str(executable.parent)+factory.os.pathsep+env['PATH']
            ready=work/'ready.json'
            preparation=inputs/'prepare.py'
            final_prompt=f'''当前有效需求标记是 {markers['NEW']}。请通过本地 Issue/PR 流程实现 calc.py 的 add(a,b)，返回两个数的和。
无中途人类交互；根 Issue 维护设计并请求 PR，PR 实现、验收并提交，根 Issue 接受合并后完成。允许本次临时仓库内 commit/merge，禁止 push。
交付前运行 Python 断言：add(2,3)==5、add(-4,1)==-3、add(0,0)==0。不要创建 Web 应用或安装依赖。'''
            preparation.write_text(preparation_script(executable,state,ready,markers,final_prompt))
            shutil.copy2(preparation,output/'prepare.py')
            prompt=f'''这是一个真实核心的受控接入探针。当前需求正文中的旧标记是 {markers['OLD']}。
当前只准备上下文检查，不建立 PR、不关闭 Issue。请在原生 shell 运行 `python3 {preparation} 当前turn的UUID`，将最后一个参数替换为本轮输入给出的 writer-turn 身份。
这是宿主提供的有写入操作的检查脚本：验证 Agent 不能使用 external、验证 writer，创建 comment 后分别 hide、delete，再修改本 Issue description 为真正的交付要求。每次自编辑会替换当前物理会话；只要新会话的当前 description 仍是这段准备要求，就用新 writer 再执行同一脚本。脚本从持久对象判断进度，不要自行重写或一次执行其它修改。
不等待宿主或人类提供下一条消息，不自行 refresh。不要把旧标记复制进其他对象。'''
            request=factory.braid_request(config,work,app,native,prompt,state,output.name)
            factory.save(work/'request.json',request)
            prefix=factory.isolation_prefix(work,inputs)
            def cli(*args):
                return subprocess.check_output([str(executable),'--state',str(state),*args],
                                               cwd=app,env=env,text=True)
            with (output/'braid.log').open('w') as log:
                proc=subprocess.Popen(prefix+[str(executable),'local',str(work/'request.json')],cwd=app,
                                      env=env,stdout=log,stderr=log,start_new_session=True)
                try:
                    proc.wait()
                    if not ready.exists():
                        raise RuntimeError('探针未留下原生 CLI 准备证据，参阅 braid.log')
                    comments=json.loads(ready.read_text())
                    shutil.copy2(ready,output/'preparation.json')
                    record['agent_control_guard']=comments['guard']
                    sessions=json.loads((state/'sessions.json').read_text())
                    old=next(s for s in sessions if any(t['braid_turn_id']==comments['first_turn'] for t in s.get('turns',[])))
                    if not comments.get('stale_write_rejected'):
                        raise RuntimeError('缺少运行中旧 writer 被拒绝的原生 CLI 证据')
                    current=cli('context','issue','1')
                    if markers['HIDDEN'] in comment_text(current,comments['hide']) or markers['DELETED'] in comment_text(current,comments['delete']):
                        raise RuntimeError('hide/delete 后当前投影仍包含已移除正文')
                    if 'State: deleted' not in comment_text(current,comments['delete']):
                        raise RuntimeError('delete 没有保留墓碑')
                    record.update(old_session_id=old['session_id'],old_group_id=old['group_id'],
                                  old_worktree=old['worktree'],stale_write_rejected=True,
                                  self_edit_from_native_shell=True,comment_hide_delete_verified=True,
                                  ordinary_self_messages_no_wake_verified=True)
                    factory.save(output/'check.json',record)
                    record['process_exit_code']=proc.returncode
                    if proc.returncode: raise RuntimeError('Braid 未完成受控探针，参阅 braid.log')
                    delivery=load_delivery(state,app,work,request)
                    record['delivery']=delivery
                finally:
                    factory.stop(proc)
                    record['cleanup_pids']=factory.cleanup_workspace(work)
                    entries=archive_state(state,output) if state.exists() else []
                    archived=archive_sessions(output,native,work,entries)
                    if record.get('delivery'): export_delivery(app,record['delivery']['delivery_commit'],output/'application')
            if not archived or any(entry.get('archive_error') or entry.get('evidence_error') for entry in archived):
                raise RuntimeError('原生会话证据不完整')
            old_entry=next(entry for entry in archived if entry['session_id']==record['old_session_id'])
            if markers['OLD'] not in input_texts(output/old_entry['native'],backend):
                raise RuntimeError('没有在旧物理会话输入中观察到旧正文')
            new_entries=[entry for entry in archived if entry.get('group_id')==record['old_group_id']
                         and entry['session_id']!=record['old_session_id']]
            verified=[]
            for entry in new_entries:
                context=(output/entry['context_path']).read_text()
                if markers['NEW'] not in context: continue
                text=input_texts(output/entry['native'],backend)
                if context not in text or any(markers[key] in text for key in ('OLD','HIDDEN','DELETED')):
                    raise RuntimeError('新物理会话没有准确收到当前投影，或保留了已移除正文')
                if entry['worktree']!=record['old_worktree']: raise RuntimeError('重建丢失原逻辑工作树')
                verified.append(entry['session_id'])
            if not verified: raise RuntimeError('没有观察到相同 group 的真实上下文替换')
            subprocess.run(['python3','-c','from calc import add; assert add(2,3)==5; assert add(-4,1)==-3; assert add(0,0)==0'],
                           cwd=output/'application',check=True)
            record.update(status='passed',replacement_sessions=verified,physical_sessions=len(archived),
                          native_context_verified=True,application_check_passed=True)
    except BaseException as error:
        record.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        record['finished_at']=time.time()
        factory.save(output/'check.json',record)
    print(json.dumps(record,ensure_ascii=False),flush=True)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=['pi','codex'],required=True)
    parser.add_argument('--svc',action='store_true')
    args=parser.parse_args()
    check(args.backend,args.svc)
