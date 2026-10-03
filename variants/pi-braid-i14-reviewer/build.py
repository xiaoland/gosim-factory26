"""Declare this variant's materials; use the common definition/delivery producer."""
import argparse
import json
from pathlib import Path
import sys
import shutil
import tempfile
import zipfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from scripts.package_agent import package

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--skills',type=Path,required=True)
    parser.add_argument('--tool-env',type=Path)
    parser.add_argument('--provider-env',type=Path)
    parser.add_argument('--gateway-routes',type=Path)
    parser.add_argument('--application-seed',type=Path)
    parser.add_argument('--e2e-runtime',type=Path)
    parser.add_argument('--otlp-dependencies',type=Path)
    parser.add_argument('--cache-root',type=Path)
    args=parser.parse_args()
    package(HERE.name,None,runtime=args.runtime,stage=args.stage,skill_source=args.skills,
            tool_env=args.tool_env,e2e_runtime=args.e2e_runtime,cache_root=args.cache_root,
            otlp_dependencies=args.otlp_dependencies,provider_env=args.provider_env,application_seed=args.application_seed,gateway_routes=args.gateway_routes)

if __name__=='__main__':
    main()
