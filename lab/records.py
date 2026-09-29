"""Small, format-neutral helpers for durable experiment records."""

import hashlib
import json
import os
from pathlib import Path
import secrets
import stat


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(5)}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    return json.loads(Path(path).read_text())


def merge_labels(*groups):
    """Merge opaque string labels without changing an already declared value."""
    result = {}
    for labels in groups:
        if not isinstance(labels, dict) or any(not isinstance(key, str) or not key or
                not isinstance(value, str) for key, value in labels.items()):
            raise ValueError("labels must be an object of string keys and values")
        for key, value in labels.items():
            if key in result and result[key] != value:
                raise ValueError(f"conflicting label {key!r}: {result[key]!r} != {value!r}")
            result[key] = value
    return result


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(root):
    """Versioned content identity for a frozen file or directory."""
    root = Path(root)
    if root.is_file() and not root.is_symlink():
        return {"algorithm": "file-bytes-sha256-v1", "sha256": file_hash(root), "kind": "file"}
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"input must be a regular file or directory: {root}")
    files = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()):
                raise ValueError(f"link points outside snapshot: {relative}")
            files.append({"path": relative, "type": "link", "target": target})
        elif stat.S_ISREG(mode):
            files.append({"path": relative, "type": "file", "sha256": file_hash(path),
                          "executable": bool(mode & 0o111)})
        elif stat.S_ISDIR(mode):
            files.append({"path": relative, "type": "directory"})
        else:
            raise ValueError(f"non-file input: {relative}")
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"algorithm": "tree-sha256-v1", "sha256": hashlib.sha256(encoded).hexdigest(),
            "kind": "directory", "entries": files}


def experiment_paths(path):
    path = Path(path).expanduser().resolve()
    if (path / "manifest.json").is_file():
        manifest = read_json(path / "manifest.json")
        if manifest.get("runs_root"):
            return path, (path / manifest["runs_root"]).resolve()
    raise ValueError(f"not an experiment root: {path}")
