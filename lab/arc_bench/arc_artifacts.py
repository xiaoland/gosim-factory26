"""ARC package identity and delivered-application snapshot contracts."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
from zipfile import ZipFile


EXCLUDED = {".arc", ".factory26", ".git", "requirements", "node_modules", ".cache"}
PRIVATE_FILES = {".env", ".env.local", ".env.production"}
ALGORITHM = "arc-application-tree-sha256-v1"


def package_variant(value):
    """Read the producer's identity; legacy declarations must agree when both exist."""
    current = value.get("capabilities", {}).get("variant")
    legacy = value.get("variant")
    if any(item is not None and (not isinstance(item, str) or not item) for item in (current, legacy)):
        raise ValueError("package variant must be a nonempty string")
    if current and legacy and current != legacy:
        raise ValueError(f"conflicting package variant: {current!r} != {legacy!r}")
    return current or legacy


def application_source(state, run, identity, provenance):
    """Reference the actual source run and its saved inputs, without reconstructing missing facts."""
    return {"run_id": state["run_id"], "run_path": str(Path(run).resolve()),
            "experiment_id": state.get("experiment_id"), "labels": state.get("labels", {}),
            "source_package": state.get("inputs", {}).get("agent"),
            "algorithm": identity.get("algorithm"), "sha256": identity.get("sha256"),
            "provenance": provenance,
            **({"source_application": state["source_application"]} if state.get("source_application") else {})}


def replay_source(case):
    """Describe a replay case using its own digest algorithm, including old manifests."""
    identity = case.get("application_manifest") or {
        "algorithm": "arc-replay-files-json-sha256-v1", "sha256": case.get("application_sha256")}
    return {**case.get("source_application", {}), "run_id": case["run_id"],
            "variant": case.get("variant"), "competition": case.get("competition"),
            "task": case.get("task"), "requirements_sha256": case["requirements_sha256"],
            "algorithm": identity.get("algorithm"), "sha256": identity.get("sha256"),
            "provenance": case.get("provenance", "producer-declared")}


def package_metadata(package):
    """Read declared package/source identity, independent of the ZIP name or experiment case."""
    with ZipFile(package) as archive:
        names = archive.namelist()
        value = json.loads(archive.read("package-manifest.json")) if "package-manifest.json" in names else {}
        replay = json.loads(archive.read("replay-manifest.json")) if "replay-manifest.json" in names else None
    if not isinstance(value, dict) or not isinstance(value.get("capabilities", {}), dict):
        raise ValueError("invalid package identity manifest")
    if replay is not None and (not isinstance(replay, dict) or replay.get("mode") != "artifact-replay"
                               or not isinstance(replay.get("cases"), list)):
        raise ValueError("invalid replay identity manifest")
    return {"variant": package_variant(value), "operation": "replay" if replay is not None else "generate",
            "source_applications": [replay_source(case) for case in replay["cases"]] if replay is not None else []}


def _included(path, root):
    relative = path.relative_to(root)
    return (not set(relative.parts) & EXCLUDED and relative.name not in PRIVATE_FILES
            and relative.suffix not in {".pyc", ".pyo"})


def manifest(root):
    root = Path(root).resolve(strict=True)
    entries = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if not _included(path, root):
            continue
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            if not (path.parent / target).resolve().is_relative_to(root):
                raise ValueError(f"application link escapes root: {relative}")
            entries.append({"path": relative, "type": "link", "target": target})
        elif stat.S_ISREG(mode):
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            entries.append({"path": relative, "type": "file", "sha256": digest,
                            "executable": bool(mode & 0o111)})
        elif not stat.S_ISDIR(mode):
            raise ValueError(f"unsupported application file: {relative}")
    content = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"algorithm": ALGORITHM, "sha256": hashlib.sha256(content).hexdigest(), "entries": entries}


def copy_snapshot(source, parent):
    source, parent = Path(source).resolve(strict=True), Path(parent)
    for part in ("frontend", "backend"):
        if not (source / part / "package.json").is_file():
            raise ValueError(f"missing {part}/package.json")
    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / "application.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    for entry in manifest(source)["entries"]:
        origin, target = source / entry["path"], staging / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry["type"] == "link":
            target.symlink_to(entry["target"])
        else:
            shutil.copy2(origin, target)
    receipt = manifest(staging)
    if (parent / "application").exists():
        raise ValueError("application was already published")
    staging.rename(parent / "application")
    temporary = parent / "receipt.json.partial"
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(parent / "receipt.json")
    return receipt


def verify(root, receipt):
    expected = receipt if isinstance(receipt, dict) else json.loads(Path(receipt).read_text())
    actual = manifest(root)
    if expected.get("algorithm") != ALGORITHM or expected.get("sha256") != actual["sha256"]:
        raise ValueError(f"frozen application changed: expected {expected.get('sha256')}, got {actual['sha256']}")
    return actual


def restore_modes(root, receipt):
    root = Path(root)
    for entry in receipt.get("entries", []):
        if entry.get("type") == "file":
            path = root / entry["path"]
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"invalid application entry: {entry['path']}")
            mode = path.stat().st_mode
            path.chmod((mode | 0o111) if entry["executable"] else (mode & ~0o111))
