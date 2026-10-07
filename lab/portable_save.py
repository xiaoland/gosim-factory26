"""Create a small, relocatable archive of one Lab run's data domain.

The archive is deliberately narrower than a run directory.  ``program``,
``inputs`` (including the installed SDK/runtime), ``snapshots`` and
``evaluations`` remain run-local evidence and are not part of a portable
application/workspace package.  Dependencies below ``data/workspace`` or
``data/harness`` are data, not inferred installation directories, so an
application's ``node_modules`` and business files are retained.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import time
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .arc_bench import execution
from .arc_bench.run_layout import manifest, paths, storage_path, write_json


_TERMINAL = {"completed", "failed", "stopped"}
_ROOTS = ("manifest.json", "data/workspace", "data/harness", "records")
_ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz"}
_SCHEMA_VERSION = 2


def _is_archive(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in _ARCHIVE_SUFFIXES)


def _included_root(path: Path, run: Path) -> bool:
    try:
        relative = path.resolve(strict=False).relative_to(run.resolve())
    except ValueError:
        return False
    return relative == Path("manifest.json") or any(
        relative == Path(root) or Path(root) in relative.parents for root in _ROOTS[1:]
    )


def _safe_link_target(path: Path, run: Path) -> str | None:
    """Return a link target only when extraction cannot reach excluded data."""
    target = os.readlink(path)
    resolved = (path.parent / target).resolve(strict=False) if not os.path.isabs(target) else Path(target).resolve(strict=False)
    if not _included_root(resolved, run):
        # Local Docker mounts expose the native home through this one stable
        # container path.  The target is still present in this run's scope;
        # make the portable link relative instead of carrying the container
        # absolute path into another host.
        relative = path.relative_to(run)
        parts = relative.parts
        if (len(parts) == 4 and parts[:2] == ("data", "harness") and
                parts[3] == "pi-home"):
            scope = parts[2]
            expected = f"/workspace/template/.factory26/data/harness/{scope}/home"
            if target == expected and (path.parent / "home").is_dir():
                return "home"
        return None
    return target


def _facility_path(relative: Path, source: Path | None = None) -> str | None:
    """Return the small, explicit set of installed harness paths to omit."""
    parts = relative.parts
    if parts[:2] == ("data", "harness") and len(parts) >= 4:
        tail = parts[3:]
        if tail[0] == "browser-cache":
            return "harness browser runtime cache"
        if len(tail) >= 2 and tail[:2] in (("home", ".npm"), ("home", ".cache"), ("home", ".local")):
            return "harness installed package/browser cache"
        if len(tail) >= 3 and tail[:2] == ("work", "cache") and tail[2] in {"browser", "npm"}:
            return "harness work package/browser cache"
        if len(tail) >= 4 and tail[:3] == ("work", "home", ".cache") and tail[3] in {"pnpm", "node", "node-gyp"}:
            return "harness work package cache"
        if len(tail) >= 5 and tail[:4] == ("work", "home", ".local", "share") and tail[4] == "pnpm":
            return "harness work package cache"
        if len(tail) >= 5 and tail[:4] == ("work", "home", ".local", "state") and tail[4] == "pnpm":
            return "harness work package cache"
    if parts[:2] == ("data", "workspace") and len(parts) >= 3:
        tail = parts[2:]
        # A business directory may legitimately be called ``runtime``.  Only
        # omit it when the immutable runtime producer marker proves it is the
        # installed native bundle, rather than relying on its name alone.
        if ((tail[0] == "runtime" or tail[:2] == (".factory26", "runtime"))
                and source is not None and source.is_dir()
                and (source / "runtime-source.json").is_file()):
            return "workspace installed runtime"
    return None


def _zip_path(archive: ZipFile, source: Path, name: str, run: Path,
              excluded: list[dict[str, str]]) -> bool:
    if source.is_symlink():
        target = _safe_link_target(source, run)
        if target is None:
            excluded.append({"path": name, "reason": "symlink-target-outside-portable-data"})
            return False
        info = ZipInfo(name)
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, target.encode())
        return True
    if source.is_dir():
        info = ZipInfo(name.rstrip("/") + "/")
        info.create_system = 3
        info.external_attr = (stat.S_IFDIR | 0o755) << 16
        archive.writestr(info, b"")
        return True
    if source.is_file():
        archive.write(source, name)
        return True
    excluded.append({"path": name, "reason": "unsupported-filesystem-entry"})
    return False


def _add_tree(archive: ZipFile, root: Path, prefix: str, run: Path,
              excluded: list[dict[str, str]]) -> tuple[int, int]:
    files = directories = 0
    if not root.exists() and not root.is_symlink():
        excluded.append({"path": prefix, "reason": "missing-source-root"})
        return files, directories
    if root.is_symlink() or root.is_file():
        return files + int(_zip_path(archive, root, prefix, run, excluded)), directories
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = sorted(dirnames)
        filenames[:] = sorted(filenames)
        relative = directory_path.relative_to(root)
        directory_name = prefix if not relative.parts else f"{prefix}/{relative.as_posix()}"
        if not _zip_path(archive, directory_path, directory_name, run, excluded):
            continue
        directories += 1
        for dirname in list(dirnames):
            child = directory_path / dirname
            reason = _facility_path(child.relative_to(run), child)
            if reason:
                excluded.append({"path": child.relative_to(run).as_posix(), "reason": reason})
                dirnames.remove(dirname)
                continue
            if child.is_symlink():
                child_name = f"{directory_name}/{dirname}"
                if _zip_path(archive, child, child_name, run, excluded):
                    files += 1
                dirnames.remove(dirname)
        for filename in filenames:
            child = directory_path / filename
            child_name = f"{directory_name}/{filename}"
            reason = _facility_path(child.relative_to(run), child)
            if reason:
                excluded.append({"path": child.relative_to(run).as_posix(), "reason": reason})
                continue
            if prefix == "records" and child.name == "portable-save.json":
                # The final receipt is written into the archive after the
                # complete walk, so it contains this invocation's exclusions.
                continue
            if prefix == "records" and _is_archive(child):
                excluded.append({"path": child_name, "reason": "raw-export-archive"})
                continue
            if _zip_path(archive, child, child_name, run, excluded):
                files += 1
    return files, directories


def _source_save(run: Path, lifecycle: str) -> tuple[dict[str, Any], bool]:
    """Reuse a confirmed terminal save, otherwise request a live snapshot."""
    receipt = paths(run)["records"] / "save.json"
    if lifecycle in _TERMINAL and receipt.is_file():
        try:
            value = json.loads(receipt.read_text(encoding="utf-8"))
            if value.get("saved") is True and not value.get("errors"):
                return value, True
        except (OSError, ValueError, TypeError):
            pass
    return execution.save(run, live=lifecycle not in _TERMINAL), False


def _reuse(run: Path, lifecycle: str, output: str | os.PathLike[str] | None) -> dict[str, Any] | None:
    if output is not None or lifecycle not in _TERMINAL:
        return None
    receipt_path = paths(run)["records"] / "portable-save.json"
    source_receipt = paths(run)["records"] / "save.json"
    try:
        value = json.loads(receipt_path.read_text(encoding="utf-8"))
        current = json.loads(source_receipt.read_text(encoding="utf-8"))
        package = Path(value["package"]).expanduser().resolve(strict=True)
        if (value.get("schema_version") != _SCHEMA_VERSION or
                value.get("lifecycle") != lifecycle or
                value.get("source_as_of") != current.get("as_of") or
                value.get("source_saved") is not True or value.get("errors") or
                package.stat().st_size <= 0):
            return None
        storage_path(package)
        return value
    except (KeyError, OSError, ValueError, TypeError):
        return None


def create(run: str | os.PathLike[str], output: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Save and package a run without changing its lifecycle."""
    run = Path(run).expanduser().resolve(strict=True)
    paths(run)["root"].joinpath("manifest.json").resolve(strict=True)
    state = manifest(run)
    status_path = paths(run)["status"]
    status = {}
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            status = {}
    lifecycle = status.get("lifecycle", "unknown")
    reused = _reuse(run, lifecycle, output)
    if reused is not None:
        return reused
    source_save, reused = _source_save(run, lifecycle)
    destination = (Path(output).expanduser().resolve() if output else
                   paths(run)["snapshots"] / f"portable-{time.time_ns()}.zip")
    if destination.suffix.lower() != ".zip":
        raise ValueError("portable save output must be a .zip file")
    if any(destination == run / root or (run / root) in destination.parents
           for root in _ROOTS):
        raise ValueError("portable save output must not be inside a packaged data root")
    storage_path(destination)
    if destination.exists():
        raise FileExistsError(f"portable save output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    excluded: list[dict[str, str]] = [
        {"path": "program", "reason": "installed-agent-program-is-run-local"},
        {"path": "inputs", "reason": "SDK/runtime/development-environment-is-run-local"},
        {"path": "snapshots", "reason": "raw-platform-and-export-evidence-is-run-local"},
        {"path": "evaluations", "reason": "evaluation-output-is-run-local"},
    ]
    source_as_of = source_save.get("as_of") if isinstance(source_save, dict) else None
    started_at = time.time()
    result = {
        "schema_version": _SCHEMA_VERSION,
        "saved": True,
        "package": str(destination),
        "source_run": str(run),
        "run_id": state.get("run_id", run.name),
        "lifecycle": lifecycle,
        "consistent": lifecycle == "completed" and bool(source_save.get("saved"))
            and not bool(source_save.get("errors")) if isinstance(source_save, dict) else False,
        "source_saved": bool(source_save.get("saved")) if isinstance(source_save, dict) else False,
        "source_as_of": source_as_of,
        "source_save": source_save,
        "gaps": source_save.get("gaps", []) if isinstance(source_save, dict) else [],
        "errors": source_save.get("errors", []) if isinstance(source_save, dict) else [],
        "reused_terminal_save": reused,
        "layout": list(_ROOTS),
        "excluded": excluded,
        "package_started_at": started_at,
    }
    counts = {"files": 0, "directories": 0}
    with ZipFile(destination, "x", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for root_name in _ROOTS:
            source = run / root_name
            if root_name == "manifest.json":
                counts["files"] += int(_zip_path(archive, source, root_name, run, excluded))
                continue
            files, directories = _add_tree(archive, source, root_name, run, excluded)
            counts["files"] += files
            counts["directories"] += directories
        gaps = list(result["gaps"])
        gaps.extend(f"{item['path']}: {item['reason']}" for item in excluded
                    if item["reason"] in {"missing-source-root", "unsupported-filesystem-entry",
                                           "symlink-target-outside-portable-data"})
        result["gaps"] = gaps
        counts["files"] += 1  # records/portable-save.json, added below
        result.update({"members": counts, "packaged_at": time.time(),
                       "as_of": time.time()})
        receipt_bytes = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        archive.writestr("records/portable-save.json", receipt_bytes)
    result["package_bytes"] = destination.stat().st_size
    write_json(paths(run)["records"] / "portable-save.json", result)
    return result
