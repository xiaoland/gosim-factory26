"""此 variant 明确选择打包材料；运行行为由同目录源码持有。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import zipfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tooling/scripts'))
from package_agent import (assemble, write_tool_credentials, write_provider_credentials,
                           write_gateway_routes)
from agent_support import copy_skill
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',type=Path,required=True)
p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--skills',type=Path,required=True)
p.add_argument('--tool-env',type=Path,help='两服务凭据的显式 dotenv 输入')
p.add_argument('--provider-env',type=Path,help='显式选定模型供应商环境 JSON；写入私有 artifact')
p.add_argument('--application-seed',type=Path,
               help='可选冻结 seed 目录或 ZIP；必须含 application-manifest.json 与 application/')
p.add_argument('--gateway-routes',type=Path,
               help='公开 alias 到有序 deployment list 的冻结 JSON')
a=p.parse_args()
assemble(HERE,a.stage,a.runtime,a.skills,
         skills=('svc-sub-agents','svc-task-packet','svc-documentation',
                 'svc-verification','hyperformula','handsontable','better-auth-best-practices',
                 'organization-best-practices','fixing-accessibility','ponytail','impeccable',
                 'agent-browser','braid-collaboration','arc-bench'))

# The provider owner may replace this with its explicitly selected catalog during
# material production; the run only accepts this package-bound copy.
# assemble provides common I14 support; this run deliberately omits the model gateway.
for relative in ('model-gateway.json', 'support/model-gateway.json',
                 'support/hackathon_gateway.py', 'support/hackathon_gateway_compat.py',
                 'support/responses_compat.py'):
    (a.stage/relative).unlink(missing_ok=True)

if a.application_seed is not None:
    source = a.application_seed.resolve(strict=True)
    staging = Path(tempfile.mkdtemp(prefix='reviewer-seed-', dir=a.stage.parent))
    try:
        if source.is_file():
            with zipfile.ZipFile(source) as archive:
                names = archive.namelist()
                if any(name.startswith('/') or '..' in Path(name).parts for name in names):
                    raise ValueError('应用 seed ZIP 含越界路径')
                archive.extractall(staging)
            candidates = [staging, *[path for path in staging.iterdir() if path.is_dir()]]
            source = next((path for path in candidates
                           if (path/'application-manifest.json').is_file() and (path/'application').is_dir()), None)
            if source is None:
                raise ValueError('应用 seed ZIP 根部缺少 application-manifest.json/application')
        if not source.is_dir() or not (source/'application-manifest.json').is_file() or not (source/'application').is_dir():
            raise ValueError('应用 seed 必须是含 application-manifest.json/application 的目录或 ZIP')
        manifest = json.loads((source/'application-manifest.json').read_text())
        if manifest.get('kind') != 'factory26.harness.application' or manifest.get('schema_version') != 2:
            raise ValueError('应用 seed 必须是 application manifest v2')
        if manifest.get('status') != 'published':
            raise ValueError('应用 seed 必须是 published')
        shutil.copytree(source, a.stage/'seed')
    finally:
        shutil.rmtree(staging, ignore_errors=True)
copy_skill(a.runtime/'node_modules/@upstash/context7-pi/skills/context7-docs',
           a.stage/'skills/context7-docs')
if a.tool_env is not None:
    write_tool_credentials(a.tool_env, a.stage)
if a.provider_env is not None:
    write_provider_credentials(a.provider_env, a.stage, a.gateway_routes)
if a.gateway_routes is not None:
    raise ValueError('直连 variant 不接受 gateway routes')
subprocess.run([sys.executable, '-m', 'lab.arc_bench', 'runtime', 'export',
                '--output', str((a.stage/'arc-runtime.pyz').resolve())],
               cwd=HERE.parents[1], stdout=subprocess.DEVNULL, check=True)
