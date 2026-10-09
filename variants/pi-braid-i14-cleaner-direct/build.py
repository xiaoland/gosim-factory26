"""此 variant 明确选择打包材料；运行行为由同目录源码持有。"""
import argparse
import shutil
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tooling/scripts'))
from package_agent import (assemble, write_tool_credentials,
                           write_provider_credentials, write_gateway_routes)
from agent_support import copy_skill
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',type=Path,required=True)
p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--skills',type=Path,required=True)
p.add_argument('--tool-env',type=Path,help='两服务凭据的显式 dotenv 输入')
p.add_argument('--provider-env',type=Path,help='本轮激活链的私有模型供应商 JSON 环境')
p.add_argument('--gateway-routes',type=Path,help='公开 alias 到有序 deployment list 的冻结 JSON')
a=p.parse_args()
assemble(HERE,a.stage,a.runtime,a.skills,
         skills=('svc-sub-agents','svc-task-packet','svc-documentation',
                 'svc-verification','hyperformula','handsontable','better-auth-best-practices',
                 'organization-best-practices','fixing-accessibility','ponytail','impeccable',
                 'agent-browser','braid-collaboration','arc-bench'))
copy_skill(a.runtime/'node_modules/@upstash/context7-pi/skills/context7-docs',
           a.stage/'skills/context7-docs')
# This isolated variant ships direct routes instead of a resident model gateway.
for relative in ('model-gateway.json', 'support/model-gateway.json',
                 'support/hackathon_gateway.py', 'support/hackathon_gateway_compat.py',
                 'support/responses_compat.py'):
    (a.stage/relative).unlink(missing_ok=True)

if a.tool_env is not None:
    write_tool_credentials(a.tool_env, a.stage)
if a.gateway_routes is not None:
    raise ValueError('直连 variant 不接受 gateway routes')
if a.provider_env is not None:
    write_provider_credentials(a.provider_env, a.stage, a.gateway_routes)
subprocess.run([sys.executable, '-m', 'lab.arc_bench', 'runtime', 'export',
                '--output', str((a.stage/'arc-runtime.pyz').resolve())],
               cwd=HERE.parents[1], stdout=subprocess.DEVNULL, check=True)
