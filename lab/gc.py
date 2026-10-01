"""Build a read-only, failure-closed storage reclamation plan."""

import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import time

from .assets import host_runtime


PIN_PURPOSES = {"execution", "cleanup", "recovery", "execution_cleanup"}
DEPENDENCY_PURPOSES = PIN_PURPOSES | {"provenance"}
RECORD_NAMES = {"active.json", "archive.json", "manifest.json", "recovery-workspace.json", "run.json"}


def _raise(error):
    raise error


def _read(path, errors):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError("record is not an object")
        return value
    except (OSError, ValueError) as exc:
        errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return None


def _records(roots, errors):
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            errors.append({"path": str(root), "error": "scan root is missing, not a directory, or a symlink"})
            continue
        def failed(exc):
            errors.append({"path": exc.filename or str(root), "error": f"{type(exc).__name__}: {exc}"})
        for directory, names, files in os.walk(root, followlinks=False, onerror=failed):
            names[:] = sorted(name for name in names if name not in {".git", "node_modules"})
            for name in sorted(RECORD_NAMES.intersection(files)):
                yield Path(directory) / name


def _file_identity(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"algorithm": "file-bytes-sha256-v1", "sha256": digest,
            "bytes": path.stat().st_size, "kind": "file"}


def _tree_identity(root):
    entries = []
    total = 0
    for directory, names, files in os.walk(root, followlinks=False, onerror=_raise):
        names.sort(); files.sort()
        folder = Path(directory)
        for name in names[:]:
            path = folder / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                entries.append({"path": relative, "type": "link", "target": os.readlink(path)})
                names.remove(name)
            else:
                entries.append({"path": relative, "type": "directory"})
        for name in files:
            path = folder / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                entries.append({"path": relative, "type": "link", "target": os.readlink(path)})
            elif stat.S_ISREG(mode):
                identity = _file_identity(path)
                total += identity["bytes"]
                entries.append({"path": relative, "type": "file", "sha256": identity["sha256"],
                                "executable": bool(mode & 0o111)})
            else:
                raise ValueError(f"unsupported archive object entry: {path}")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"algorithm": "tree-sha256-v1", "sha256": hashlib.sha256(encoded).hexdigest(),
            "bytes": total, "entries": len(entries), "kind": "directory"}


def _allocated(root):
    inodes = {}
    for directory, names, files in os.walk(root, followlinks=False, onerror=_raise):
        folder = Path(directory)
        for path in [folder, *(folder / name for name in names + files)]:
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            key = (info.st_dev, info.st_ino)
            inodes[key] = max(inodes.get(key, 0), info.st_blocks * 512)
    return {"allocated_bytes": sum(inodes.values()), "inodes": len(inodes)}


def _path(value, source):
    path = Path(value).expanduser()
    return path.absolute() if path.is_absolute() else (source.parent / path).absolute()


def _overlap(left, right):
    try:
        left = left.resolve(strict=False)
        right = right.resolve(strict=False)
    except (OSError, RuntimeError):
        return True
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _dependency(item, source, references, errors):
    if (not isinstance(item, dict) or not isinstance(item.get("location"), str) or
            item.get("purpose") not in DEPENDENCY_PURPOSES or
            not isinstance(item.get("kind"), str)):
        errors.append({"path": str(source), "error": "invalid or unknown dependency reference"})
        return
    location = _path(item["location"], source)
    try:
        canonical = location.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        errors.append({"path": str(source),
                       "error": f"dependency path cannot be resolved: {type(exc).__name__}: {exc}"})
        canonical = location
    references.append({"path": str(location), "canonical_path": str(canonical),
                       "source": str(source), "purpose": item["purpose"], "kind": item["kind"],
                       "pins": item["purpose"] in PIN_PURPOSES})


def _rows(value, source, field, errors):
    if isinstance(value, list):
        return value
    errors.append({"path": str(source), "error": f"{field} is not a list"})
    return []


def _console_references(record, path, references, errors):
    """Recoverable Console configuration pins dependencies even when HTTP has stopped."""
    if record.get("schema_version") != 1 or record.get("state") != "registered":
        errors.append({"path": str(path), "error": "unknown Console service schema or registration state"})
    if record.get("host") != socket.gethostname():
        errors.append({"path": str(path), "error": "Console service belongs to another host; paths cannot be mapped"})
    def pin(location, kind):
        if not isinstance(location, str) or not Path(location).is_absolute():
            errors.append({"path": str(path), "error": f"Console {kind} needs an absolute host path"})
            return
        _dependency({"location": location, "kind": kind, "purpose": "execution_cleanup"}, path, references, errors)
    pin(str(path.parent.absolute()), "console-service")
    interpreter = record.get("interpreter")
    if not isinstance(interpreter, dict):
        errors.append({"path": str(path), "error": "Console interpreter identity is missing"})
    else:
        for key in ("executable", "prefix", "base_prefix"):
            pin(interpreter.get(key), "console-python-" + key)
    for run in _rows(record.get("runs"), path, "Console runs", errors):
        if not isinstance(run, dict):
            errors.append({"path": str(path), "error": "Console run is not an object"})
            continue
        if run.get("run_record"):
            pin(run["run_record"], "console-run-record")
        if run.get("mode") == "archive":
            if run.get("writable") is not False or run.get("docker") or run.get("cli_command"):
                errors.append({"path": str(path), "error": "Console archive has writable or container configuration"})
            pin(run.get("archive"), "console-archive")
        elif run.get("mode") == "live":
            for key in ("binary", "state", "workspace"):
                pin(run.get(key), "console-live-" + key)
            docker = run.get("docker")
            if docker is not None:
                if not isinstance(docker, dict) or not docker.get("context"):
                    errors.append({"path": str(path), "error": "Console Docker execution namespace is unknown"})
                    continue
                for mount in _rows(docker.get("mounts"), path, "Console host mounts", errors):
                    pin(mount.get("source") if isinstance(mount, dict) else None, "console-access-mount")
        else:
            errors.append({"path": str(path), "error": "Console run has unknown mode"})


def _archive_candidate(path, receipt, references, protections, complete):
    producer = path.parent.absolute()
    reclaim = receipt.get("reclaim_state") or {}
    if not isinstance(reclaim, dict):
        return {"receipt": str(path), "status": "blocked", "target": None,
                "reasons": ["archive reclaim_state is not an object"],
                "reclaim_authorized": False}
    target_name = reclaim.get("target")
    if reclaim.get("status") != "eligible" or not isinstance(target_name, str):
        return None
    relative = Path(target_name)
    reasons = []
    if relative.is_absolute() or not relative.parts or any(part in (".", "..") for part in relative.parts):
        return {"receipt": str(path), "status": "blocked", "target": target_name,
                "reasons": ["reclaim target is not a safe producer-relative path"],
                "reclaim_authorized": False}
    target = (producer / relative).absolute()
    if receipt.get("schema_version") != 1 or receipt.get("archive_level") != "decision":
        reasons.append("unsupported archive schema or level")
    if receipt.get("run_id") != producer.name:
        reasons.append("archive run_id does not match its producer directory")
    if target_name != "work":
        reasons.append("archive schema v1 only authorizes the work target")
    if reclaim.get("reasons"):
        reasons.append("eligible reclaim receipt unexpectedly contains blocking reasons")
    expected_archive_id = receipt.get("archive_id")
    content = {key: value for key, value in receipt.items() if key != "archive_id"}
    actual_archive_id = hashlib.sha256(json.dumps(
        content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if expected_archive_id != actual_archive_id:
        reasons.append("archive receipt identity mismatch")
    recovery = receipt.get("recovery_capability")
    if not isinstance(recovery, dict) or recovery.get("status") != "none":
        reasons.append("archive keeps or has an invalid recovery commitment")
    coverage = receipt.get("diagnostic_coverage")
    preservation = coverage.get("preservation") if isinstance(coverage, dict) else None
    if not isinstance(preservation, dict) or preservation.get("status") != "complete":
        reasons.append("archive raw preservation is incomplete or unverified")
    execution = receipt.get("execution_result")
    if not isinstance(execution, dict) or execution.get("status") != "generated":
        reasons.append("archive execution result is not generated")
    if (producer / "recovery-workspace.json").exists():
        reasons.append("recovery-workspace.json still exists")
    if not complete:
        reasons.append("record scan was incomplete")
    objects = receipt.get("objects")
    if not isinstance(objects, list):
        reasons.append("archive objects is not a list")
        objects = []
    elif not objects:
        reasons.append("archive contains no preserved objects")
    present = [item.get("path") for item in objects
               if isinstance(item, dict) and isinstance(item.get("path"), str)]
    if len(present) != len(objects):
        reasons.append("archive object paths are invalid")
    if len(present) != len(set(present)):
        reasons.append("archive object paths are not unique")
    required = {"braid-state", "native", "native-config", "run.json"}
    delivery = receipt.get("delivery_result")
    if not isinstance(delivery, dict) or delivery.get("status") != "delivered":
        reasons.append("archive delivery result is not delivered")
    required.add("application")
    missing = sorted(required - set(present))
    if missing:
        reasons.append("archive is missing required objects: " + ", ".join(missing))
    for item in objects:
        if not isinstance(item, dict):
            reasons.append("archive object is not an object")
            continue
        try:
            relative_object = Path(item["path"])
            if (relative_object.is_absolute() or not relative_object.parts or
                    any(part in (".", "..") for part in relative_object.parts)):
                raise ValueError("unsafe object path")
            object_path = producer / relative_object
            if object_path.is_symlink() or not object_path.exists():
                raise ValueError("object missing or root is a symlink")
            actual = _tree_identity(object_path) if object_path.is_dir() else _file_identity(object_path)
            expected = {key: item.get(key) for key in actual}
            if actual != expected:
                raise ValueError("object identity mismatch")
        except (KeyError, OSError, TypeError, ValueError) as exc:
            reasons.append(f"archive object invalid: {item.get('path')}: {type(exc).__name__}: {exc}")
    blockers = [item for item in references if item["pins"] and _overlap(target, Path(item["path"]))]
    blockers.extend(item for item in protections if _overlap(target, Path(item["path"])))
    if blockers:
        reasons.append("target overlaps a pinned reference or protected path")
    result = {"receipt": str(path), "target": str(target), "reclaim_authorized": False,
              "references": blockers, "reasons": reasons}
    if not target.exists():
        result["status"] = "already_absent"
    elif target.is_symlink() or not target.is_dir():
        result.update(status="blocked", reasons=[*reasons, "target is not a real directory"])
    elif reasons:
        result["status"] = "blocked"
    else:
        try:
            usage = _allocated(target)
            result.update(status="candidate", identity=_tree_identity(target),
                          allocated_bytes_observed=usage["allocated_bytes"], inodes=usage["inodes"],
                          reclaimable_bytes=None)
        except (OSError, ValueError) as exc:
            result.update(status="blocked",
                          reasons=[f"{type(exc).__name__}: {exc}"])
    return result


def plan(roots, asset_roots=(), protected=()):
    roots = [Path(value).expanduser().absolute() for value in roots]
    errors = []
    references = []
    protections = []
    for value in protected:
        original = Path(value).expanduser().absolute()
        try:
            canonical = original.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            errors.append({"path": str(original), "error": f"{type(exc).__name__}: {exc}"})
            canonical = original
        protections.append({"path": str(original), "canonical_path": str(canonical),
                            "source": "--protect", "purpose": "explicit", "pins": True})
    archives = []
    for path in _records(roots, errors):
        record = _read(path, errors)
        if record is None:
            continue
        if path.name == "manifest.json" and record.get("record_type") == "factory26.exp-console-service":
            _console_references(record, path, references, errors)
        elif path.name == "manifest.json" and record.get("record_type") == "factory26.console-service":
            errors.append({"path": str(path), "error": "obsolete Console service format; retire or explicitly protect before planning cleanup"})
        elif path.name == "manifest.json" and record.get("record_type") == "lab.experiment":
            if record.get("schema_version") == 3 and not isinstance(record.get("controller_runtime"), dict):
                errors.append({"path": str(path), "error": "schema v3 controller_runtime is missing"})
            if record.get("controller_runtime") is not None:
                _dependency(record["controller_runtime"], path, references, errors)
            for job in _rows(record.get("jobs"), path, "jobs", errors):
                if not isinstance(job, dict):
                    errors.append({"path": str(path), "error": "job is not an object"})
                    continue
                for item in _rows(job.get("dependencies", []), path, "job dependencies", errors):
                    _dependency(item, path, references, errors)
        elif path.name == "run.json" and (record.get("record_type") == "lab.run" or
                                           record.get("variant") in {"pi-braid-i12", "pi-braid-i13"}):
            if record.get("controller_runtime") is not None:
                _dependency(record["controller_runtime"], path, references, errors)
            for item in _rows(record.get("dependencies", []), path, "run dependencies", errors):
                _dependency(item, path, references, errors)
            terminal = ((record.get("record_type") == "lab.run" and
                         record.get("phase") in {"cancelled", "finished"}) or
                        (record.get("variant") in {"pi-braid-i12", "pi-braid-i13"} and
                         record.get("phase") == "frozen" and record.get("status") == "generated"))
            budget = record.get("storage_budget")
            if budget is not None and not isinstance(budget, dict):
                errors.append({"path": str(path), "error": "storage_budget is not an object"})
                resources_confirmed = False
            else:
                resources_confirmed = not budget or budget.get("resource_state") != "unconfirmed"
            if not terminal or not resources_confirmed:
                protections.append({"path": str(path.parent.absolute()), "source": str(path),
                                    "purpose": "run-active-or-unconfirmed", "pins": True})
        elif path.name == "archive.json" and record.get("record_type") == "factory26.archive":
            archives.append((path, record))
            for item in _rows(record.get("dependencies", []), path, "archive dependencies", errors):
                _dependency(item, path, references, errors)
        elif path.name == "recovery-workspace.json" and isinstance(record.get("path"), str):
            protections.append({"path": str(_path(record["path"], path)), "source": str(path),
                                "purpose": "recovery", "pins": True})
        elif path.name == "active.json" and record.get("phase") != "finished":
            protections.append({"path": str(path.parent.absolute()), "source": str(path),
                                "purpose": "controller-active-or-unconfirmed", "pins": True})
    assets = []
    seen_assets = set()
    for value in asset_roots:
        root = Path(value).expanduser().absolute()
        receipts = ([root] if root.name == "asset.json" else
                    ([root / "asset.json"] if (root / "asset.json").is_file() else []) +
                    sorted(root.glob("*/asset.json")))
        if not receipts:
            errors.append({"path": str(root), "error": "no managed asset receipts found"})
        for receipt_path in receipts:
            if receipt_path in seen_assets:
                continue
            seen_assets.add(receipt_path)
            try:
                asset = host_runtime(receipt_path)
                consumers = [item for item in references if _overlap(Path(asset["root"]), Path(item["path"]))]
                protected_by = [item for item in protections
                                if _overlap(Path(asset["root"]), Path(item["path"]))]
                status = "referenced" if consumers or protected_by else "unreferenced_in_scope"
                assets.append({"receipt": str(receipt_path), "root": asset["root"],
                               "identity": asset["identity"], "status": status,
                               "references": consumers, "protections": protected_by,
                               "reclaim_authorized": False})
            except (OSError, ValueError) as exc:
                errors.append({"path": str(receipt_path),
                               "error": f"{type(exc).__name__}: {exc}"})
                assets.append({"receipt": str(receipt_path), "status": "unknown",
                               "error": f"{type(exc).__name__}: {exc}", "reclaim_authorized": False})
    complete = not errors
    candidates = [candidate for path, receipt in archives
                  if (candidate := _archive_candidate(path, receipt, references, protections, complete))]
    if errors:
        for asset in assets:
            if asset["status"] == "unreferenced_in_scope":
                asset["status"] = "unknown"
    return {"schema_version": 1, "record_type": "factory26.gc-plan", "created_at": time.time(),
            "host": socket.gethostname(), "read_only": True, "complete": not errors,
            "roots": [str(root) for root in roots], "protections": protections,
            "references": references, "candidates": candidates, "assets": assets,
            "errors": errors}
