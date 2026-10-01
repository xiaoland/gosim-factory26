"""此 variant 明确选择打包材料；运行行为由同目录源码持有。"""
import argparse
import json
import os
from pathlib import Path
import shutil
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
p.add_argument('--e2e-runtime',type=Path,default=os.environ.get('FACTORY26_E2E_RUNTIME'),
               help='tools/build-e2e.py 导出的冻结 Linux addon')
a=p.parse_args()
addon = (a.e2e_runtime or a.runtime/'e2e').resolve(strict=True)
if not (addon/'addon-source.json').is_file():
    raise ValueError('e2e addon 缺少构建来源；先运行 tools/build-e2e.py')
if json.loads((addon/'addon-source.json').read_text()).get('superseded_reason'):
    raise ValueError('不能打包已标记替换的 e2e addon')
assemble(HERE,a.stage,a.runtime,a.skills,
         skills=('svc-sub-agents','svc-task-packet','svc-documentation',
                 'svc-verification','hyperformula','handsontable','better-auth-best-practices',
                 'organization-best-practices','fixing-accessibility','ponytail','impeccable',
                 'agent-browser','e2e','braid-collaboration','arc-bench'))
if not (a.stage/'runtime/e2e').exists():
    shutil.copytree(addon, a.stage/'runtime/e2e', symlinks=True)
shutil.copy2(HERE/'tools/e2e-cli', a.stage/'runtime/bin/e2e')
(a.stage/'runtime/bin/e2e').chmod(0o755)
copy_skill(a.runtime/'node_modules/@upstash/context7-pi/skills/context7-docs',
           a.stage/'skills/context7-docs')
if a.tool_env is not None:
    write_tool_credentials(a.tool_env, a.stage)
subprocess.run([sys.executable, '-m', 'lab.arc_bench', 'runtime', 'export',
                '--output', str((a.stage/'arc-runtime.pyz').resolve())],
               cwd=HERE.parents[1], stdout=subprocess.DEVNULL, check=True)
