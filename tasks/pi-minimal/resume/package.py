"""Freeze one authorized local continuation; does not start models."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
p=argparse.ArgumentParser()
p.add_argument('--base',type=Path,required=True)
p.add_argument('--workspace',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
source={'source_run_id':'pi-minimal--hackathon--github-59aaf58e7462bc',
        'mode':'local-pi-session-resume','base_sha256':digest(a.base),'workspace_sha256':digest(a.workspace),
        'excluded':'node_modules, dependency/browser caches, runner-owned .arc files except pi-minimal; no application code omitted'}
with ZipFile(a.base) as old, ZipFile(a.output,'x',compression=ZIP_DEFLATED) as new:
    manifest=json.loads(old.read('package-manifest.json'))
    for info in old.infolist():
        if info.filename in ('main.py','package-manifest.json','instructions.md'):continue
        new.writestr(info,old.read(info))
    updates={'main.py':Path(__file__).with_name('entry.py').read_bytes(),'pi_main.py':old.read('main.py'),
             'resume-source.json':(json.dumps(source,indent=2)+'\n').encode(),
             'instructions.md':old.read('instructions.md')+'\n本次从保留的应用代码与当前Pi会话接续，先核对已有成果与未完成工作，不重新实现。上述工作指令和能力配置已更新，以当前指令为准。依赖目录未搬运；使用app-env在目标Node20下重新安装，再继续验证。\n'.encode()}
    for name,data in updates.items():
        new.writestr(name,data)
        manifest['files'][name]={'sha256':hashlib.sha256(data).hexdigest(),'executable':False}
    new.write(a.workspace,'retained-workspace.zip',compress_type=ZIP_STORED)
    manifest['files']['retained-workspace.zip']={'sha256':source['workspace_sha256'],'executable':False}
    new.writestr('package-manifest.json',json.dumps(manifest))
print(json.dumps({'package':str(a.output),'sha256':digest(a.output),**source}))
