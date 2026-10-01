"""Freeze a hosted Braid workspace for self-funded recovery; generation requires explicit opt-in."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from package_agent import is_metadata_path, require_private_artifact

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    path.chmod(0o600)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def get_workspace(run_id, evidence):
    """Keep the response body even when the official read-only download fails."""
    sys.path.insert(0, str(ROOT))
    from lab.arc_bench.playground import API, Client, run_path
    endpoint = run_path(run_id) + "/workspace/template-bundle"
    target = evidence / "workspace.zip"
    receipt = {"method": "GET", "url": API + endpoint, "run_id": run_id,
               "started_at": datetime.now(timezone.utc).isoformat()}
    result = subprocess.run([
        "curl", "-q", "--silent", "--show-error", "--proto", "=https",
        "--connect-timeout", "30", "--max-time", "600", "--request", "GET",
        "--cookie", str(Client().cookie), "--output", str(target),
        "--write-out", "%{http_code}", API + endpoint,
    ], capture_output=True, text=True)
    receipt.update(finished_at=datetime.now(timezone.utc).isoformat(),
                   http_status=result.stdout.strip(), curl_exit_code=result.returncode,
                   transport_error=result.stderr.strip())
    if target.exists():
        target.chmod(0o600)
        receipt.update(bytes=target.stat().st_size, sha256=digest(target), body=str(target))
    save(evidence / "download.json", receipt)
    if result.returncode or result.stdout.strip() != "200":
        raise RuntimeError(f"workspace GET HTTP {receipt['http_status']}; curl {result.returncode}; "
                           f"raw response and receipt retained in {evidence}")
    return target


def validate_archive(path, index_path, *, workspace=False, manifest=None):
    """Check every member's CRC and hash without extracting or executing it."""
    rows = []
    with ZipFile(path) as archive:
        seen = set()
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            if (name.is_absolute() or ".." in name.parts or "\\" in item.filename
                    or not name.parts or (workspace and name.parts[0] != "template")
                    or name.as_posix() in seen):
                raise ValueError(f"unsafe or duplicate ZIP path: {item.filename}")
            seen.add(name.as_posix())
            mode = item.external_attr >> 16
            if not workspace and stat.S_ISLNK(mode):
                raise ValueError(f"package contains symlink: {item.filename}")
            if item.is_dir():
                continue
            with archive.open(item) as stream:
                sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
            if manifest is not None and not is_metadata_path(item.filename) and item.filename != "package-manifest.json":
                record = manifest["files"].get(item.filename)
                if not record or record["sha256"] != sha256:
                    raise ValueError(f"package manifest hash mismatch: {item.filename}")
            rows.append({"path": item.filename, "bytes": item.file_size,
                         "crc32": f"{item.CRC:08x}", "mode": oct(mode), "sha256": sha256})
        if manifest is not None:
            actual = {row["path"] for row in rows if row["path"] != "package-manifest.json"
                      and not is_metadata_path(row["path"])}
            if actual != {name for name in manifest["files"] if not is_metadata_path(name)}:
                raise ValueError("package manifest member set differs from ZIP")
    save(index_path, rows)
    return rows


def journal_inputs(folder, task, run_id, evidence):
    inputs_path, state_path = folder / "inputs.json", folder / "state.json"
    inputs, state = json.loads(inputs_path.read_text()), json.loads(state_path.read_text())
    if inputs.get("venue") != "hosted" or state.get("venue") != "hosted":
        raise ValueError("recovery journal must describe a hosted run")
    tasks = state["tasks"]
    if task is None:
        if len(tasks) != 1:
            raise ValueError("journal has multiple tasks; specify --task")
        task = next(iter(tasks))
    selected = tasks[task]
    if task not in inputs["tasks"] or not selected.get("run_id"):
        raise ValueError("journal has no frozen input and run for selected task")
    if run_id is not None and selected["run_id"] != run_id:
        raise ValueError("--source-run-id differs from journal")
    if selected.get("remote_status") not in {"PASSED", "FAILED", "CANCELLED"} or state.get("pending"):
        raise ValueError("journal does not confirm a stopped source run")
    if not inputs.get("package_sha256") or inputs["package_sha256"] != state.get("package_sha256"):
        raise ValueError("journal package SHA256 differs between inputs and state")
    receipt = {"journal": str(folder), "task": task, "run_id": selected["run_id"],
               "submission_id": state.get("submission_id"),
               "package_sha256": inputs["package_sha256"],
               "terminal_status": selected["remote_status"], "observed_at": selected.get("observed_at"),
               "status_source": "saved journal, not a fresh API observation",
               "inputs_sha256": digest(inputs_path), "state_sha256": digest(state_path)}
    save(evidence / "journal.json", receipt)
    return inputs, receipt


def main():
    # Frozen runtime material can contain tool credentials, including while writing.
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, help="Hosted Competition journal; discovers frozen package and run")
    parser.add_argument("--task", help="Required only when the journal contains multiple tasks")
    parser.add_argument("--source-run-id")
    parser.add_argument("--workspace", type=Path, help="Reuse an original ZIP; otherwise download the official bundle")
    parser.add_argument("--workspace-sha256", help="Expected SHA256 of a reused original ZIP")
    parser.add_argument("--base-package", type=Path)
    parser.add_argument("--braid", type=Path, help="Explicit binary override; default is exact binary from frozen package")
    parser.add_argument("--braid-source", type=Path, help="Optional source snapshot for reproducing a binary override")
    parser.add_argument("--braid-source-identity", type=Path,
                        help="Optional source files/tree receipt; verifies braid/ members in --braid-source")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, help="New directory for original ZIP, indices and receipts")
    parser.add_argument("--continue-generation", action="store_true",
                        help="Resume open work items with models; source execution must already be stopped")
    parser.add_argument("--replace-braid-deepseek-with-glm", action="store_true",
                        help="Explicit I13 recipe migration: retain historical DeepSeek profile identity, execute GLM")
    parser.add_argument("--with-official-signal-evidence", action="store_true",
                        help="Overlay current collector/support/archive modules; requires explicit combined Braid binary")
    parser.add_argument("--override-native-transport", action="store_true",
                        help="Explicitly bind retained native factory26 transports to this run's model URLs and key variables")
    parser.add_argument("--refresh-native-materials", action="store_true",
                        help="Refresh owned native materials; I13 uses the complete frozen I13-2 base package")
    args = parser.parse_args()
    if args.refresh_native_materials and not args.continue_generation:
        parser.error("--refresh-native-materials requires --continue-generation")
    if args.replace_braid_deepseek_with_glm and (not args.continue_generation or args.refresh_native_materials):
        parser.error("--replace-braid-deepseek-with-glm requires --continue-generation and unchanged native materials")
    if args.with_official_signal_evidence and not args.braid:
        parser.error("--with-official-signal-evidence requires --braid with the combined signal/catalog implementation")
    if args.override_native_transport and (not args.continue_generation or args.refresh_native_materials):
        parser.error("--override-native-transport requires --continue-generation and unchanged native materials")
    if args.braid_source_identity and (not args.braid or not args.braid_source):
        parser.error("--braid-source-identity requires both --braid and --braid-source")
    if not args.journal and (not args.source_run_id or not args.base_package):
        parser.error("provide --journal or both --source-run-id and --base-package")
    if args.task and not args.journal:
        parser.error("--task requires --journal")
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    evidence = (args.evidence_dir or output.parent / (output.stem + "-evidence")).resolve()
    require_private_artifact(output)
    require_private_artifact(evidence)
    evidence.mkdir(parents=True, mode=0o700, exist_ok=False)
    inputs = binding = None
    if args.journal:
        journal = args.journal.resolve(strict=True)
        inputs, binding = journal_inputs(journal, args.task, args.source_run_id, evidence)
        args.source_run_id = binding["run_id"]
        if args.base_package is None:
            args.base_package = journal / inputs["package"]
    base = args.base_package.resolve(strict=True)
    base_sha256 = digest(base)
    if inputs and base_sha256 != inputs["package_sha256"]:
        raise ValueError("base package SHA256 differs from frozen journal")
    with ZipFile(base) as archive:
        frozen_manifest = json.loads(archive.read("package-manifest.json"))
    if inputs and frozen_manifest != inputs["package_manifest"]:
        raise ValueError("base package manifest differs from frozen journal")
    if args.replace_braid_deepseek_with_glm and frozen_manifest.get("capabilities", {}).get("variant") not in {
            "pi-braid-i13", "pi-braid-i13-glm-root"}:
        raise ValueError("DeepSeek Braid migration supports only the two I13 variants")
    validate_archive(base, evidence / "base-index.json", manifest=frozen_manifest)
    if args.workspace:
        original_workspace = args.workspace.resolve(strict=True)
        workspace = evidence / "workspace.zip"
        with original_workspace.open("rb") as incoming, workspace.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        workspace.chmod(0o600)
        save(evidence / "workspace-origin.json", {"mode": "reused original", "path": str(original_workspace),
             "sha256": digest(original_workspace), "run_binding": "selected source run; not embedded official identity",
             "preserved_at": datetime.now(timezone.utc).isoformat()})
    else:
        workspace = get_workspace(args.source_run_id, evidence)
    workspace_sha256 = digest(workspace)
    if args.workspace_sha256 and workspace_sha256 != args.workspace_sha256:
        raise ValueError("workspace SHA256 differs from expected original")
    validate_archive(workspace, evidence / "workspace-index.json", workspace=True)
    if args.braid:
        braid = args.braid.resolve(strict=True)
    else:
        braid = evidence / "braid"
        with ZipFile(base) as archive, archive.open("runtime/bin/braid") as incoming, braid.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        braid.chmod(0o600)
    braid_source = args.braid_source.resolve(strict=True) if args.braid_source else None
    source_identity = None
    if args.braid_source_identity:
        source_identity_path = args.braid_source_identity.resolve(strict=True)
        source_identity = json.loads(source_identity_path.read_text())
        actual_sources = {}
        with tarfile.open(braid_source) as archive:
            for item in archive.getmembers():
                path = PurePosixPath(item.name)
                if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "braid":
                    raise ValueError(f"unexpected Braid source snapshot path: {item.name}")
                if item.isdir():
                    continue
                name = path.relative_to("braid").as_posix()
                if not item.isfile() or name in actual_sources:
                    raise ValueError(f"unexpected or duplicate Braid source member: {item.name}")
                with archive.extractfile(item) as stream:
                    actual_sources[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        aggregate = hashlib.sha256(json.dumps(actual_sources, sort_keys=True).encode()).hexdigest()
        if (source_identity.get("algorithm") != "sha256-json-sorted-files"
                or source_identity.get("files") != actual_sources or source_identity.get("source_sha256") != aggregate):
            raise ValueError("Braid source identity differs from actual snapshot members")
    with ZipFile(workspace) as archive:
        candidates = [p for p in archive.namelist() if p.startswith("template/.factory26/")
                      and len(Path(p).parts) == 5 and p.endswith("/braid-state/request.json")]
        if len(candidates) != 1:
            raise ValueError(f"expected one retained Braid run, found {len(candidates)}")
        braid_run = candidates[0].split("/")[2]
        request = json.loads(archive.read(candidates[0]))
        if request.get("run_id") != braid_run:
            raise ValueError("retained Braid run identity differs from its path")
        live_request = json.loads(archive.read(f"template/.factory26/{braid_run}/braid-request.json"))
        if (live_request.get("run_id") != braid_run
                or live_request.get("state") != f"/workspace/template/.factory26/{braid_run}/braid-state"):
            raise ValueError("retained launcher request does not match the official workspace layout")
        for name in ("braid-state/braid.sqlite3", "materials.json"):
            archive.getinfo(f"template/.factory26/{braid_run}/{name}")
        materials = json.loads(archive.read(f"template/.factory26/{braid_run}/materials.json"))
        material_mismatches = []
        for section in ("agents", "skills"):
            for name, sha256 in materials.get(section, {}).items():
                if frozen_manifest["files"].get(f"{section}/{name}", {}).get("sha256") != sha256:
                    material_mismatches.append(f"{section}/{name}")
        if material_mismatches and not args.refresh_native_materials:
            raise ValueError(f"workspace material differs from frozen package: {material_mismatches}")
        requirements_sha256 = hashlib.sha256(archive.read("template/requirements/requirements.yaml")).hexdigest()
    source = {"source_run_id": args.source_run_id, "braid_run_id": braid_run,
              "workspace_sha256": workspace_sha256, "base_package_sha256": base_sha256,
              "braid_sha256": digest(braid), "braid_source_sha256": digest(braid_source) if braid_source else None,
              "braid_binary_source": "explicit override" if args.braid else "frozen package runtime/bin/braid",
              "braid_source_role": "auxiliary snapshot for caller-supplied binary" if args.braid
                                   else "auxiliary snapshot; executing frozen binary",
              "frozen_braid_source": frozen_manifest.get("sources", {}).get("braid"),
              "requirements_sha256": requirements_sha256,
              "source_stop_confirmation": "saved terminal journal" if binding else "caller-confirmed; not independently verified",
              "workspace_material_differences": material_mismatches,
              "mode": "workspace-resume" if args.continue_generation else "completed-workspace-recovery",
              "replace_braid_deepseek_with_glm": args.replace_braid_deepseek_with_glm,
              "with_official_signal_evidence": args.with_official_signal_evidence,
              "override_native_transport": args.override_native_transport,
              "refresh_native_materials": args.refresh_native_materials}
    if binding:
        source["journal_binding"] = binding
    main_file = ROOT / "submission/recover_completed.py"
    replacements = {"main.py": main_file, "runtime/bin/braid": braid,
                    "recovery-workspace.zip": workspace}
    if braid_source:
        replacements["recovery-braid-source.tar.gz"] = braid_source
    if source_identity:
        replacements["recovery-braid-source-identity.json"] = source_identity_path
        source["braid_compiled_source_sha256"] = source_identity["source_sha256"]
        source["braid_source_identity_sha256"] = digest(source_identity_path)
    if args.with_official_signal_evidence:
        signal_files = {"support/agent_support.py": ROOT / "scripts/agent_support.py",
                        "support/core.py": ROOT / "scripts/core.py", "support/otlp.py": ROOT / "lab/otlp.py"}
        if not set(signal_files) <= set(frozen_manifest["files"]):
            raise ValueError("frozen package lacks expected signal-evidence support modules")
        replacements.update(signal_files)
        source["signal_evidence_files_sha256"] = {name: digest(path) for name, path in signal_files.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        stream = output.open("xb")
        created = True
        with stream, ZipFile(base) as original, ZipFile(stream, "w", allowZip64=True) as target:
            manifest = json.loads(original.read("package-manifest.json"))
            manifest["files"] = {name: record for name, record in manifest["files"].items()
                                 if not is_metadata_path(name)}
            if args.refresh_native_materials:
                variant = manifest.get("capabilities", {}).get("variant")
                i13_refresh = variant in {"pi-braid-i13", "pi-braid-i13-glm-root"}
                if not i13_refresh and variant not in {"pi-braid", "pi-braid-flash-team", "pi-braid-i11"}:
                    raise ValueError(f"unsupported Braid variant for native refresh: {variant}")
                instructions = sorted(name for name in manifest["files"]
                                      if len(Path(name).parts) == 3 and Path(name).parts[0] == "agents"
                                      and Path(name).name == "instructions.md")
                observer = "extensions/factory-subagent-observer.ts"
                if ("support/otlp.py" not in manifest["files"] or observer not in manifest["files"]
                        or not instructions):
                    raise ValueError("base package is missing collector, observer, or variant instructions")
                if i13_refresh:
                    # I13-2 replaces the complete frozen runtime, roles and independent
                    # skills. Do not quietly mix current checkout files into that base.
                    required = {"runtime/native-managed.mjs", "support/runtime_resources.py"}
                    if not required <= set(manifest["files"]):
                        raise ValueError("I13 native refresh requires a complete I13-2 base package")
                    runtime_source = json.loads(original.read("runtime/runtime-source.json"))
                    patches = {"pi-coding-agent-0.85.1-i13-2-managed.patch",
                               "pi-background-bash-1.0.5-i13-2-managed.patch",
                               "pi-subagents-0.56.0-i13-2-managed.patch"}
                    if not patches <= set(runtime_source.get("native_patch_sha256", {})):
                        raise ValueError("I13 native refresh runtime lacks managed process patches")
                    refreshed = sorted(name for name in manifest["files"] if
                                       name.startswith(("agents/", "skills/", "extensions/"))
                                       or name in required or name == "run.py")
                    source.update(native_materials_source="frozen base package",
                                  resource_admission="i13-2-v1")
                else:
                    refreshed = ["support/otlp.py", observer, *instructions]
                    replacements["support/otlp.py"] = (ROOT / "lab/otlp.py").resolve(strict=True)
                    replacements[observer] = (ROOT / "variants" / variant / observer).resolve(strict=True)
                    replacements.update({name: (ROOT / "variants" / variant / name).resolve(strict=True)
                                         for name in instructions})
            skipped = set(replacements) | {"recovery-source.json", "package-manifest.json", "recovery-braid-source.tar.gz",
                                           "recovery-braid-source-identity.json"}
            manifest["files"].pop("recovery-braid-source.tar.gz", None)
            manifest["files"].pop("recovery-braid-source-identity.json", None)
            for item in original.infolist():
                if item.filename in skipped or is_metadata_path(item.filename):
                    continue
                with original.open(item) as incoming, target.open(item, "w") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            for name, path in replacements.items():
                target.write(path, name, compress_type=ZIP_STORED if name.endswith(".zip") else ZIP_DEFLATED)
                manifest["files"][name] = {"sha256": digest(path),
                                           "executable": name == "runtime/bin/braid"}
            if args.refresh_native_materials:
                source["refreshed_files_sha256"] = {name: manifest["files"][name]["sha256"]
                                                    for name in refreshed}
            encoded = (json.dumps(source, ensure_ascii=False, indent=2) + "\n").encode()
            target.writestr("recovery-source.json", encoded, compress_type=ZIP_DEFLATED)
            manifest["files"]["recovery-source.json"] = {"sha256": hashlib.sha256(encoded).hexdigest(),
                                                          "executable": False}
            if args.braid:
                # The original revision/tree hash describes the frozen binary, not this override.
                manifest["sources"]["braid"] = {"binary_source": "caller-supplied override"}
            manifest["sources"]["braid"]["binary_sha256"] = source["braid_sha256"]
            if braid_source:
                manifest["sources"]["braid"]["source_snapshot_sha256"] = source["braid_source_sha256"]
            if source_identity:
                manifest["sources"]["braid"].update(source_sha256=source_identity["source_sha256"],
                                                     source_identity="recovery-braid-source-identity.json")
            target.writestr("package-manifest.json", json.dumps(manifest, ensure_ascii=False),
                            compress_type=ZIP_DEFLATED)
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise
    output.chmod(0o600)
    validate_archive(output, evidence / "recovery-index.json", manifest=manifest)
    receipt = {"package": str(output), "sha256": digest(output), "evidence": str(evidence), **source}
    save(evidence / "receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
