"""ARC adapter operations."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipapp

def export_runtime(argv):
    parser = argparse.ArgumentParser(prog="python -m lab.arc_bench runtime export")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"output already exists: {output}")
    source = Path(__file__).with_name("agent_runtime")
    if not (source / "SOURCE.json").is_file():
        raise ValueError("official SDK source record is missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / output.name
        zipapp.create_archive(source, staged, interpreter="/usr/bin/env python3", compressed=True,
                              filter=lambda path: "__pycache__" not in path.parts and
                              path.suffix in {".py", ".md", ".json", ".toml"})
        staged.replace(output)
    with output.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    print(json.dumps({"runtime": str(output), "sha256": sha256,
                      "sdk": json.loads((source / "SOURCE.json").read_text())["version"]}, ensure_ascii=False))
    return 0


def main():
    if sys.argv[1:3] == ["runtime", "export"]:
        return export_runtime(sys.argv[3:])
    if sys.argv[1:2] == ["traceability"]:
        from .traceability import main as traceability
        return traceability(sys.argv[2:])
    raise SystemExit("usage: python -m lab.arc_bench {runtime export|traceability} ...")


if __name__ == "__main__":
    sys.exit(main())
