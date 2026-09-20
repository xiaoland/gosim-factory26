#!/usr/bin/env python3
"""Real-provider integration check; exercises memory replacement, not ARC-bench scoring."""
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
from core import codex_config


PROMPT = '''这是一个小型本地编排接入检查，不是产品生成或 benchmark。无人类中途介入，不要创建 Git 提交。
最终交付 calc.py 的 add(a,b) 函数，正确返回两个数的和；运行你自己的 Python 断言验证正数、负数和零。
请严格走四个正常结束的会话，使用 Braid 提供的控制协议：
1. 首次设计：生成一个随机 UUID，在当前设计正文中写 RETIRED_CANDIDATE=<uuid>，故意暂写减法作为待纠正候选；交给 implement，不写应用。
2. 首次实现：先建立 calc.py（暂时是减法）以验证工作区保留；发现与最终需求矛盾后，覆盖当前设计为加法，完全删除旧候选 UUID。implementation.md 记录已有文件及待修正函数，然后交回 design，不能在此会话完成。
3. 第二次设计：只依据当前正文与需求审查更正；在 design.md 记录 DESIGN_REVIEWED，确认加法与验收断言，然后交给 implement。
4. 第二次实现：确认已有 calc.py，修改为正确加法，运行断言，在 implementation.md 记录实际验证结果，然后 complete。
不要把每阶段输出或旧候选追加回当前记忆。此检查为小任务；保持说明简短。
'''


def check(backend, svc):
    config=json.loads((factory.ROOT/f'variants/{backend}-svc-braid/config.json').read_text())
    config['svc']=svc
    output=factory.ROOT/'runs/integration'/f"{time.strftime('%Y%m%d-%H%M%S')}-{backend}-{'svc' if svc else 'plain'}-{uuid.uuid4().hex[:6]}"
    output.mkdir(parents=True)
    record={'backend':backend,'svc':svc,'status':'running','started_at':time.time(),
            'model':config['model'],'kind':'braid-memory-integration',
            'core_version':factory.capture(backend,'--version')}
    factory.save(output/'check.json',record)
    factory.save(output/'config.json',config)
    sources.archive('braid',output/'sources')
    if svc: sources.archive('svc',output/'sources')
    print(f'[接入检查] {output}',flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix='factory26-check-') as temporary, factory.responses_adapter(config,output) as url:
            work=Path(temporary).resolve(); app=work/'application'; app.mkdir()
            inputs=work/'input'; inputs.mkdir()
            native,env=factory.runtime_environment(work,config)
            if backend=='pi':
                factory.save(native/'models.json',{'providers':{'deepseek':{'baseUrl':config['base_url'],'apiKey':'$FACTORY26_API_KEY'}}})
            else:
                codex_config(native,url,config['model'])
            state=work/'braid-state'
            executable=work/'braid'; shutil.copy2(sources.binary(),executable)
            factory.save(work/'request.json',factory.braid_request(config,work,app,native,PROMPT,state))
            prefix=factory.isolation_prefix(work,inputs)
            try:
                record['process_exit_code']=factory.logged(
                    prefix+[str(executable),'local',str(work/'request.json')],
                    app,env,output/'braid.log',record.setdefault('cleanup_errors',[]))
                if record['process_exit_code']:
                    raise RuntimeError('braid local failed; see braid.log')
                # Execute the generated module rather than accepting its claimed verification.
                subprocess.run(prefix+['python3','-c',
                    'from calc import add; assert add(2,3)==5; assert add(-4,1)==-3; assert add(0,0)==0'],
                    cwd=app,env=env,check=True)
            finally:
                record['cleanup_pids']=factory.cleanup_workspace(work)
                if state.exists(): shutil.copytree(state,output/'braid-state')
                shutil.copytree(app,output/'application',ignore=shutil.ignore_patterns('__pycache__'))
                shutil.copytree(native,output/'native')
        turns=sorted(path for path in (output/'braid-state').iterdir() if path.is_dir())
        sessions=[json.loads((turn/'session.json').read_text()) for turn in turns]
        if [entry['stage'] for entry in sessions] != ['design','implement','design','implement']:
            raise RuntimeError('expected design -> implement -> design -> implement')
        if len({entry['id'] for entry in sessions}) != 4:
            raise RuntimeError('physical sessions were reused')
        marker=re.search(r'RETIRED_CANDIDATE=([\w-]+)',(turns[0]/'design.md').read_text())
        if not marker: raise RuntimeError('first design omitted the obsolete memory marker')
        if marker[1] not in (turns[1]/'context.md').read_text() or marker[1] in (turns[2]/'context.md').read_text():
            raise RuntimeError('current context did not replace obsolete design')
        if 'DESIGN_REVIEWED' not in (turns[3]/'context.md').read_text():
            raise RuntimeError('reviewed design was not handed back to implementation')
        native=list((output/'application/.braid/pi-sessions').glob('*.jsonl')) if backend=='pi' else list((output/'native/sessions').rglob('*.jsonl'))
        for turn,entry in zip(turns,sessions):
            matches=[path for path in native if path.name==Path(entry['id']).name or path.name.endswith('-'+entry['id']+'.jsonl')]
            if len(matches)!=1: raise RuntimeError('cannot identify the actual native session')
            messages=[]
            for line in matches[0].open():
                frame=json.loads(line)
                message=frame.get('message',{}) if backend=='pi' else frame.get('payload',{})
                if message.get('role')=='user':
                    messages += [part.get('text','') for part in message.get('content',[]) if isinstance(part,dict)]
            if not any((turn/'context.md').read_text() in text for text in messages):
                raise RuntimeError('archived context missing from actual provider input')
        record.update(status='passed',physical_sessions=4,workitems=sorted({entry['workitem'] for entry in sessions}),
                      memory_replacement_verified=True,native_context_verified=True,application_check_passed=True)
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
