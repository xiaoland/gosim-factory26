"""Native observer for the I14 Pi+Braid DX program."""
import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
for candidate in (root / "tooling/scripts", Path(__file__).resolve().parent / "scripts"):
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break
from native_observation import observe

parser = argparse.ArgumentParser()
parser.add_argument("--run", required=True)
args = parser.parse_args()
json.dump(observe(args.run, provider="pi-braid", braid=True), sys.stdout, ensure_ascii=False)
