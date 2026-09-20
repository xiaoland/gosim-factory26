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


def check(backend, svc=False):
    config=json.loads((factory.ROOT/f'variants/{backend}-svc-braid/config.json').read_text())
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
            # The host mutates the object through CLI; no human participates in the run.
            ready=work/'ready.json'
            prompt=f'''这是一个真实核心的受控接入探针。当前需求正文中的旧标记是 {markers['OLD']}。
本 turn 只准备上下文检查，不建立 PR、不关闭 Issue。请按当前 turn 的 CLI 前缀，在根 Issue 1 创建两个 comment，正文分别严格为 {markers['HIDDEN']} 和 {markers['DELETED']}。
把返回的两个 comment id 通过临时文件再 rename 原子写入 {ready}，JSON 格式为 {{"hide":第一个id,"delete":第二个id}}。
然后执行 shell 命令 sleep 3600 保持当前 turn 运行。测试驱动会通过 Braid CLI 修改需求，系统随后自动重建上下文；不要等待人类，不要自行调用刷新或模拟下一阶段。不要把旧标记复制进其他对象。'''
            request=factory.braid_request(config,work,app,native,prompt,state,output.name)
            factory.save(work/'request.json',request)
            prefix=factory.isolation_prefix(work,inputs)
            def cli(*args, turn=None, external=False, succeeds=True):
                command=[str(executable),'object','--state',str(state)]
                if turn: command+=['--writer-turn',turn]
                if external: command+=['--external']
                result=subprocess.run(command+list(args),cwd=app,env=env,capture_output=True,text=True)
                if succeeds and result.returncode:
                    raise RuntimeError('Braid CLI failed: '+result.stderr)
                if not succeeds and result.returncode==0:
                    raise RuntimeError('失效 turn 的写操作未被拒绝')
                return result.stdout
            with (output/'braid.log').open('w') as log:
                proc=subprocess.Popen(prefix+[str(executable),'local',str(work/'request.json')],cwd=app,
                                      env=env,stdout=log,stderr=log,start_new_session=True)
                try:
                    while not ready.exists():
                        if proc.poll() is not None: raise RuntimeError('探针准备前 Braid 已退出，参阅 braid.log')
                        time.sleep(.25)
                    comments=json.loads(ready.read_text())
                    while True:
                        sessions=json.loads((state/'sessions.json').read_text())
                        old=next((s for s in sessions if s.get('work_item_kind')=='issue' and s.get('work_item_id')=='1'
                                  and any(t.get('status') in ('starting','running') for t in s.get('turns',[]))),None)
                        if old: break
                        if proc.poll() is not None: raise RuntimeError('Braid 在建立活动会话前退出')
                        time.sleep(.25)
                    old_turn=next(t['braid_turn_id'] for t in old['turns'] if t['status'] in ('starting','running'))
                    # Same-writer mutations must not interrupt or manufacture a wake.
                    before=json.loads(cli('status'))
                    cli('comment','hide',str(comments['hide']),turn=old_turn)
                    hidden=comment_text(cli('context','issue','1'),comments['hide'])
                    if markers['HIDDEN'] in hidden: raise RuntimeError('hide 后当前投影仍包含正文')
                    cli('comment','unhide',str(comments['hide']),turn=old_turn)
                    if markers['HIDDEN'] not in comment_text(cli('context','issue','1'),comments['hide']):
                        raise RuntimeError('unhide 未恢复正文')
                    cli('comment','hide',str(comments['hide']),turn=old_turn)
                    cli('comment','delete',str(comments['delete']),turn=old_turn)
                    current=cli('context','issue','1')
                    if markers['HIDDEN'] in comment_text(current,comments['hide']) or markers['DELETED'] in comment_text(current,comments['delete']):
                        raise RuntimeError('hide/delete 后当前投影仍包含已移除正文')
                    if 'State: deleted' not in comment_text(current,comments['delete']):
                        raise RuntimeError('delete 没有保留墓碑')
                    after=json.loads(cli('status'))
                    if any(after.get(key) != 0 for key in ('pending_batches','pending_resets','pending_events')):
                        raise RuntimeError('自身写入产生了额外唤醒或失效')
                    if after.get('active_turns') != 1 or {s.get('session_id') for s in before['physical_sessions']} != {
                            s.get('session_id') for s in after['physical_sessions']}:
                        raise RuntimeError('自身写入打断或替换了当前物理会话')
                    final_prompt=f'''当前有效需求标记是 {markers['NEW']}。请通过本地 Issue/PR 流程实现 calc.py 的 add(a,b)，返回两个数的和。
无中途人类交互；根 Issue 维护设计并请求 PR，PR 实现、自检并提交，根 Issue 接受合并后完成。允许本次临时仓库内 commit/merge，禁止 push。
交付前运行 Python 断言：add(2,3)==5、add(-4,1)==-3、add(0,0)==0。不要创建 Web 应用或安装依赖。'''
                    body=work/'replacement.md';body.write_text(final_prompt)
                    cli('issue','edit','1','--body-file',str(body),external=True)
                    cli('issue','edit','1','--body-file',str(body),turn=old_turn,succeeds=False)
                    record.update(old_session_id=old['session_id'],old_group_id=old['group_id'],
                                  old_worktree=old['worktree'],stale_write_rejected=True,
                                  comment_hide_unhide_delete_verified=True,self_write_no_wake_verified=True)
                    factory.save(output/'check.json',record)
                    proc.wait()
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
