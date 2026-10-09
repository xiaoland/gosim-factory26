"""I15's Lab native observation uses the shared Pi/Braid reader."""
import argparse
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--run", required=True)
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
for source in (Path(args.run) / "source", repository):
    if (source / "tooling/scripts/native_observation.py").is_file():
        sys.path.insert(0, str(source))
        break
from tooling.scripts.native_observation import observe

json.dump(observe(args.run, provider="pi-braid", braid=True), sys.stdout, ensure_ascii=False)
