"""Record the frozen application identity without modifying the application."""

import argparse
import hashlib
import json
from pathlib import Path


EXCLUDED = {".arc", ".factory26", ".git", "requirements", "node_modules", ".cache", "dist", "build"}


def source_hash(root):
    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if set(relative.parts) & EXCLUDED or relative.name in {".env", ".env.local", ".env.production"}:
            continue
        if relative.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.as_posix().encode() + b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    witness = output / ".arc/frozen-source.json"
    witness.parent.mkdir(parents=True, exist_ok=True)
    witness.write_text(json.dumps({"sha256": source_hash(output)}) + "\n")


if __name__ == "__main__":
    main()
