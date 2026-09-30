"""此 variant 明确选择打包材料；运行行为由同目录源码持有。"""
import argparse
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'scripts'))
from package_agent import assemble, write_tool_credentials
from agent_support import copy_skill
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',type=Path,required=True)
p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--skills',type=Path,required=True)
p.add_argument('--tool-env',type=Path,help='两服务凭据的显式 dotenv 输入')
a=p.parse_args()
assemble(HERE,a.stage,a.runtime,a.skills,
         skills=('svc-sub-agents','svc-task-packet','svc-documentation',
                 'svc-verification','hyperformula','handsontable','better-auth-best-practices',
                 'organization-best-practices','fixing-accessibility','ponytail','impeccable',
                 'agent-browser'))
copy_skill(a.runtime/'node_modules/@upstash/context7-pi/skills/context7-docs',
           a.stage/'skills/context7-docs')
if a.tool_env is not None:
    write_tool_credentials(a.tool_env, a.stage)
subprocess.run([sys.executable, '-m', 'lab.arc_bench', 'runtime', 'export',
                '--output', str((a.stage/'arc-runtime.pyz').resolve())],
               cwd=HERE.parents[1], stdout=subprocess.DEVNULL, check=True)
