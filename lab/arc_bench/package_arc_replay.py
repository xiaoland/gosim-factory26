"""Package published applications or provisional Git snapshots for ARC replay."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

from .arc_artifacts import application_source, manifest as application_manifest, verify as verify_application


def package(runs, output, *, git_repo=None, ref=None):
    if (git_repo is None) != (ref is None):
        raise ValueError("--git-repo and --ref must be supplied together")
    if git_repo is None:
        return _package(runs, output)
    if len(runs) != 1:
        raise ValueError("A Git snapshot requires exactly one source --run")
    repository = Path(git_repo).resolve(strict=True)
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        text=True).strip()
    with TemporaryDirectory(prefix="arc-replay-") as directory:
        archive_path = Path(directory) / "application.tar"
        application = Path(directory) / "application"
        subprocess.run(["git", "-C", str(repository), "archive", "--format=tar",
                        "--output", str(archive_path), commit], check=True)
        with tarfile.open(archive_path) as archive:
            archive.extractall(application, filter="data")
        source = {"provisional": True,
                  "git": {"repository": str(repository), "ref": ref, "commit": commit}}
        return _package(runs, output, application=application, snapshot_source=source)


def _package(runs, output, *, application=None, snapshot_source=None):
    cases, files = [], {}
    for run in runs:
        state = json.loads((run / "run.json").read_text())
        published = None if snapshot_source else next((path for path in (run / "workspace/official-generation/.lab-artifacts/application",
                                            run / "workspace/official/.lab-artifacts/application")
                          if path.is_dir() and (path.parent / "receipt.json").is_file()), None)
        selected = (application if snapshot_source else published or next((path for path in (run / "workspace/official-generation/template",
                                                             run / "workspace/official/template") if path.is_dir()),
                                         run / "workspace/official-generation/template")).resolve(strict=True)
        for part in ("frontend", "backend"):
            if not (selected / part / "package.json").is_file():
                identity = f" at Git commit {snapshot_source['git']['commit']}" if snapshot_source else ""
                raise ValueError(f"Missing {part}/package.json{identity}: {selected}")
        requirement = run / "inputs/requirements/requirements.yaml"
        requirement_hash = hashlib.sha256(requirement.read_bytes()).hexdigest()
        if any(case["requirements_sha256"] == requirement_hash for case in cases):
            raise ValueError("A replay package must contain only one application per requirement")
        receipt = published.parent / "receipt.json" if published else None
        app_manifest = verify_application(selected, receipt) if receipt and receipt.is_file() else application_manifest(selected)
        hashes = {}
        for item in app_manifest["entries"]:
            if item["type"] != "file":
                raise ValueError(f"replay ZIP cannot transport application symlink: {item['path']}")
            path = selected / item["path"]
            hashes[item["path"]] = item["sha256"]
            files[f"applications/{state['run_id']}/{item['path']}"] = path
        provenance = ("git-archive-provisional" if snapshot_source else
                      "published" if published and selected == published.resolve() else "imported-at-packaging")
        cases.append({"run_id": state["run_id"], "variant": state.get("variant"),
                      "competition": state["competition"], "task": state["task"],
                      "requirements_sha256": requirement_hash, "files": hashes,
                      "application_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                      "application_manifest": app_manifest,
                      "source_application": {**application_source(state, run, app_manifest, provenance),
                                             **(snapshot_source or {})},
                      "provenance": provenance})
    manifest = {"mode": "artifact-replay", "delay_seconds": 3, "cases": cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(Path(__file__).with_name("arc_replay.py"), "main.py")
                archive.write(Path(__file__).with_name("arc_artifacts.py"), "arc_artifacts.py")
                archive.writestr("requirements.txt", "")
                archive.writestr("replay-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                for name, path in files.items():
                    archive.write(path, name)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--git-repo", type=Path, help="从指定 Git 仓库冻结阶段应用；必须配合 --ref，且只接受一个 --run")
    parser.add_argument("--ref", help="解析一次为 commit 后以 git archive 导出；不读取未提交工作树")
    args = parser.parse_args()
    manifest = package(args.run, args.output, git_repo=args.git_repo, ref=args.ref)
    print(json.dumps({"package": str(args.output), "runs": [case["run_id"] for case in manifest["cases"]]}))


if __name__ == "__main__":
    main()
