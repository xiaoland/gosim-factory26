"""此 variant 明确选择打包材料；运行行为由同目录源码持有。"""
import argparse
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'scripts'))
from package_agent import assemble
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',type=Path,required=True)
p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--skills',type=Path,required=True)
a=p.parse_args()
assemble(HERE,a.stage,a.runtime,a.skills,
         skills=('svc-sub-agents','svc-task-packet','svc-documentation',
                 'svc-verification','hyperformula','handsontable','better-auth-best-practices',
                 'organization-best-practices','fixing-accessibility','ponytail','impeccable',
                 'agent-browser'))
subprocess.run([sys.executable, '-m', 'lab.arc_bench', 'runtime', 'export',
                '--output', str((a.stage/'arc-runtime.pyz').resolve())],
               cwd=HERE.parents[1], stdout=subprocess.DEVNULL, check=True)
