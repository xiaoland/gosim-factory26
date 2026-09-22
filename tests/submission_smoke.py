"""Linux 无模型验收：先检查真实工具，再用显式测试替身驱动 ZIP 入口。

在带 Git/npm 的 CPython 3.12 Linux 容器中执行：
python tests/submission_smoke.py /path/to/extracted-agent
修改仅限传入的测试副本；结束时恢复 Braid 和制品清单。
"""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request


FAKE_BRAID = r'''#!/usr/bin/env python3
import json, pathlib, subprocess, sys
if sys.argv[1:] == ['--version']:
    print('braid-test-double'); raise SystemExit(0)
request=json.loads(pathlib.Path(sys.argv[2]).read_text())
profile=next(p for p in request['profiles'] if p['id']==request['defaults']['issue']) if 'profiles' in request else request['profile']
inputs=pathlib.Path(request['prompt'].split('请根据 ',1)[1].split(' 中',1)[0])
if 'fixture-failure' in (inputs/'requirements.md').read_text(): raise SystemExit(9)
app=pathlib.Path(profile['workspace']); state=pathlib.Path(request['state']); state.mkdir()
for directory, scripts in [('frontend',{'build':'node build.js'}),('backend',{'start':'node server.js'})]:
    (app/directory).mkdir()
    (app/directory/'package.json').write_text(json.dumps({'name':directory,'version':'1.0.0','scripts':scripts}))
(app/'frontend/build.js').write_text("const fs=require('fs');fs.mkdirSync('dist',{recursive:true});fs.writeFileSync('dist/index.html','<h1>fixture</h1>');")
(app/'backend/server.js').write_text("const http=require('http'),fs=require('fs');http.createServer((q,s)=>s.end(fs.readFileSync('../frontend/dist/index.html'))).listen(process.env.PORT,process.env.HOST);")
subprocess.run(['git','add','.'],cwd=app,check=True)
subprocess.run(['git','commit','-qm','test fixture'],cwd=app,check=True)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip()
subprocess.run(['git','update-ref',request['delivery_ref'],commit],cwd=app,check=True)
provider=profile['adapter_type']
session=pathlib.Path(request[provider]['home'])/'session.jsonl'
identity='11111111-1111-1111-1111-111111111111'
entries=([{'id':identity},{'message':{'role':'assistant','stopReason':'stop','usage':{'input':0,'output':0,'totalTokens':0}}}] if provider=='pi' else
         [{'type':'session_meta','payload':{'id':identity}},{'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{'input_tokens':0,'output_tokens':0,'total_tokens':0}}}}])
session.write_text('\n'.join(json.dumps(entry) for entry in entries)+'\n')
(state/'objects.db').write_text('test-double')
(state/'sessions.json').write_text(json.dumps([{'provider':provider,'session_id':identity,'native_session_path':str(session),'turns':[{'status':'completed'}]}]))
(state/'result.json').write_text(json.dumps({'schema_version':1,'status':'completed','root_issue':{'kind':'issue','id':'1'},'run_id':request['run_id'],'delivery_ref':request['delivery_ref'],'delivery_commit':commit,'repository':str(app),'objects_database':str(state/'objects.db'),'sessions_manifest':str(state/'sessions.json')}))
'''


def main():
    package=Path(sys.argv[1]).resolve()
    sys.path.insert(0,str(package/'scripts'))
    import factory
    import submission
    manifest=submission.verify_package(package)
    backend=manifest['backend']
    with tempfile.TemporaryDirectory(prefix='factory26-smoke-') as temp:
        root=Path(temp); inputs=root/'requirements'; inputs.mkdir()
        (inputs/'requirements.yaml').write_text('title: contract fixture\n')
        (inputs/'requirements.md').write_text('仅用于无模型契约验收，不是参赛答案。')
        work=root/'work';work.mkdir(); evidence=root/'evidence';evidence.mkdir()
        frozen=json.loads((package/'variants/factory/config.json').read_text())
        env=dict(os.environ,OPENAI_API_KEY='test-placeholder',OPENAI_BASE_URL='http://127.0.0.1:9/v1',MODEL=frozen['model'])
        os.environ.update(OPENAI_API_KEY=env['OPENAI_API_KEY'],OPENAI_BASE_URL=env['OPENAI_BASE_URL'],MODEL=env['MODEL'])
        config=submission.platform_config(package,manifest)
        native, agent_env=submission.environment(work,config)
        prefix=submission.isolation_prefix(work,inputs)
        submission.preflight(prefix,work,inputs,evidence,agent_env)
        for command in (['node','--version'],['npm','--version'],[backend,'--version'],['braid','--version'],['git','--version'],['svc','lookup','--path','index.md']):
            result=subprocess.run(prefix+command,cwd=work,env=agent_env,capture_output=True,text=True,timeout=60)
            assert result.returncode==0,(command,result.stderr)
            print('真实工具通过：'+ ' '.join(command),flush=True)
        if backend=='pi':
            factory.save(native/'models.json',{'providers':{'deepseek':{'baseUrl':config['base_url'],'apiKey':'$FACTORY26_API_KEY',
                         'api':'openai-completions','models':[{'id':'fixture','input':['text'],'reasoning':True}]}}})
            listed=subprocess.run(prefix+['pi','--list-models','fixture'],cwd=work,env=agent_env,capture_output=True,text=True,timeout=60)
            assert listed.returncode==0 and 'fixture' in listed.stdout,listed.stderr
        braid=package/'runtime/bin/braid'; original=braid.read_bytes()
        manifest_path=package/'package-manifest.json'; original_manifest=manifest_path.read_bytes()
        try:
            braid.write_text(FAKE_BRAID)
            manifest['files']['runtime/bin/braid']['sha256']=hashlib.sha256(braid.read_bytes()).hexdigest()
            manifest['test_only']='无模型替身，禁止参赛'
            manifest_path.write_text(json.dumps(manifest))
            output=root/'output';output.mkdir();(output/'.arc').mkdir();(output/'.arc/sentinel').write_text('preserve')
            (output/'requirements').mkdir();(output/'requirements/sentinel').write_text('preserve')
            command=[sys.executable,str(package/'main.py'),str(inputs),'--type','web','--output-dir',str(output)]
            subprocess.run(command,env=env,check=True,timeout=120)
            assert (output/'.arc/sentinel').read_text()=='preserve'
            assert (output/'requirements/sentinel').read_text()=='preserve'
            run=next((output/'.factory26').iterdir())
            assert json.loads((run/'run.json').read_text())['status']=='generated'
            assert json.loads((run/'delivery.json').read_text())['status']=='delivered'
            assert (run/'native/manifest.json').is_file()
            with socket.socket() as listener:
                listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
            for folder in ('frontend','backend'):
                subprocess.run(['npm','install','--include=optional','--no-audit','--no-fund'],cwd=output/folder,check=True,timeout=60)
                if folder=='frontend': subprocess.run(['npm','run','build'],cwd=output/folder,check=True,timeout=60)
            server=subprocess.Popen(['npm','run','start'],cwd=output/'backend',env=dict(env,PORT=str(port),HOST='0.0.0.0'),start_new_session=True)
            try:
                deadline=time.monotonic()+30
                while True:
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}',timeout=2) as response:
                            assert response.read()==b'<h1>fixture</h1>';break
                    except OSError:
                        if time.monotonic()>deadline or server.poll() is not None: raise
                        time.sleep(.1)
            finally: factory.stop(server)
            nested=root/'nested'; (nested/'requirements').mkdir(parents=True)
            (nested/'requirements/requirements.yaml').write_text('title: nested fixture')
            nested_command=[sys.executable,str(package/'main.py'),str(nested/'requirements'),'--output-dir',str(nested)]
            subprocess.run(nested_command,env=env,check=True,timeout=120)
            assert (nested/'requirements/requirements.yaml').read_text()=='title: nested fixture'
            # A second delivery must report its own failure without overwriting the old app.
            duplicate=subprocess.run(command,env=env,capture_output=True,text=True,timeout=120)
            assert duplicate.returncode!=0
            delivery_states=[json.loads(p.read_text())['status'] for p in (output/'.factory26').glob('*/delivery.json')]
            assert sorted(delivery_states)==['delivered','failed'],delivery_states
            failed=root/'failed'
            (inputs/'requirements.md').write_text('fixture-failure')
            result=subprocess.run(command[:-1]+[str(failed)],env=env,capture_output=True,text=True,timeout=120)
            assert result.returncode!=0
            assert not (failed/'frontend').exists()
            failure=json.loads(next((failed/'.factory26').glob('*/run.json')).read_text())
            assert failure['status']=='generation_failed',failure
            print('入口、冻结交付、平台文件保留、标准部署及失败退出通过；模型调用为零。',flush=True)
        finally:
            braid.write_bytes(original)
            manifest_path.write_bytes(original_manifest)
    submission.verify_package(package)


if __name__=='__main__': main()
