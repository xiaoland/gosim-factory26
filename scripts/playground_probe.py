#!/usr/bin/env python3
"""将官方 blank template 打包为无模型调用的 Playground 环境探针。"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

MAIN = '''import argparse
import json
import os
import platform
import shutil
from pathlib import Path

from arcbench_agent_runtime import AgentRuntime

parser = argparse.ArgumentParser()
parser.add_argument("requirement_path")
parser.add_argument("--output-dir", required=True)
parser.add_argument("--type", default="web")
args = parser.parse_args()
runtime = AgentRuntime.from_env()
print("FACTORY26_PROBE " + json.dumps({
    "python": platform.python_version(), "platform": platform.system(),
    "architecture": platform.machine(), "cpu_count": os.cpu_count(),
    "tools": {name: bool(shutil.which(name)) for name in
              ("node", "npm", "git", "codex", "pi", "uv", "cargo", "bwrap")},
    "requirements_present": (Path(args.requirement_path) / "requirements.yaml").is_file(),
    "model_calls": 0
}), flush=True)
shutil.copytree(Path(__file__).parent / "template", args.output_dir, dirs_exist_ok=True)
'''


def build(source, output):
    with ZipFile(source) as template, ZipFile(output, 'w', ZIP_DEFLATED) as probe:
        for name in template.namelist():
            if name.startswith(('template/', 'arcbench-agent-runtime/')):
                probe.writestr(name, template.read(name))
        probe.writestr('requirements.txt', './arcbench-agent-runtime\n')
        probe.writestr('main.py', MAIN)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.template, args.output)
    print(args.output)
