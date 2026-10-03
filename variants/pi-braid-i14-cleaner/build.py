"""Declare this variant's materials; use the common definition/delivery producer."""
import argparse
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from scripts.package_agent import package
SKILLS=('svc-sub-agents', 'svc-task-packet', 'svc-documentation', 'svc-verification', 'hyperformula', 'handsontable', 'better-auth-best-practices', 'organization-best-practices', 'fixing-accessibility', 'ponytail', 'impeccable', 'agent-browser', 'braid-collaboration', 'arc-bench')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--skills',type=Path,required=True)
    parser.add_argument('--tool-env',type=Path)
    parser.add_argument('--e2e-runtime',type=Path)
    parser.add_argument('--otlp-dependencies',type=Path)
    parser.add_argument('--cache-root',type=Path)
    args=parser.parse_args()
    package(HERE.name,None,runtime=args.runtime,stage=args.stage,skill_source=args.skills,
            tool_env=args.tool_env,e2e_runtime=args.e2e_runtime,cache_root=args.cache_root,
            otlp_dependencies=args.otlp_dependencies)

if __name__=='__main__':
    main()
