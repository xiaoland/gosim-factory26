"""Verify immutable host assets consumed by frozen experiments."""

import hashlib
import json
import os
from pathlib import Path
import stat

from .records import read_json


def asset_inventory(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"asset root must be a real directory: {root}")
    entries = []
    allocated = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if relative.as_posix() == "asset.json" or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        info = path.lstat()
        key = (info.st_dev, info.st_ino)
        allocated[key] = max(allocated.get(key, 0), info.st_blocks * 512)
        mode = info.st_mode
        if stat.S_ISLNK(mode):
            entries.append({"path": relative.as_posix(), "type": "link", "target": os.readlink(path)})
        elif stat.S_ISREG(mode):
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            entries.append({"path": relative.as_posix(), "type": "file", "sha256": digest,
                            "executable": bool(mode & 0o111)})
        elif stat.S_ISDIR(mode):
            entries.append({"path": relative.as_posix(), "type": "directory"})
        else:
            raise ValueError(f"asset contains unsupported entry: {path}")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"algorithm": "tree-sha256-v1", "sha256": hashlib.sha256(encoded).hexdigest(),
            "bytes": sum(allocated.values()), "entries": len(entries)}


def host_runtime(receipt_path):
    receipt_path = Path(receipt_path).expanduser().absolute()
    receipt = read_json(receipt_path)
    if receipt.get("schema_version") != 1 or receipt.get("record_type") != "factory26.host-runtime":
        raise ValueError(f"invalid host runtime receipt: {receipt_path}")
    root = Path(receipt.get("root", "")).expanduser().absolute()
    launcher = Path(receipt.get("launcher", "")).expanduser().absolute()
    if receipt_path != root / "asset.json" or not launcher.is_relative_to(root):
        raise ValueError(f"host runtime receipt paths disagree: {receipt_path}")
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise ValueError(f"host runtime launcher is unavailable: {launcher}")
    base_python = Path(receipt.get("base_python", "")).expanduser().absolute()
    if not base_python.is_file() or not os.access(base_python, os.X_OK):
        raise ValueError(f"host runtime base Python is unavailable: {base_python}")
    actual = asset_inventory(root)
    if actual != receipt.get("identity"):
        raise ValueError(f"host runtime identity mismatch: {root}")
    return {**receipt, "receipt": str(receipt_path), "root": str(root), "launcher": str(launcher)}


def frozen_host_runtime(declaration):
    if not isinstance(declaration, dict) or declaration.get("kind") != "host-lab-runtime":
        raise ValueError("schema v3 requires a host-lab-runtime controller declaration")
    runtime = host_runtime(declaration.get("receipt", ""))
    for field in ("location", "launcher", "identity"):
        actual = runtime["root" if field == "location" else field]
        if declaration.get(field) != actual:
            raise ValueError(f"frozen host runtime {field} disagrees with its receipt")
    return runtime
