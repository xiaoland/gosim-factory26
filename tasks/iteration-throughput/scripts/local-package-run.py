#!/usr/bin/env python3
"""Run one frozen Agent ZIP locally, then evaluate its delivered app with ARC tests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import factory


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def frozen_config(archive):
    with ZipFile(archive) as package:
        return json.loads(package.read("variants/factory/config.json"))


def delivered_run(output):
    runs = [path.parent for path in (output / ".factory26").glob("*/delivery.json")
            if json.loads(path.read_text()).get("status") == "delivered"]
    return runs[-1] if runs else None


def run(args):
    archive = args.package.resolve()
    requirements = args.requirements.resolve(strict=True)
    work = args.work.resolve()
    output = work / "output"
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    config = frozen_config(archive)
    if args.task not in ("keep", "bookstack"):
        raise ValueError("task must be keep or bookstack")
    key = os.environ.get("OPENAI_API_KEY") or factory.api_key()
    env = dict(os.environ, OPENAI_API_KEY=key, OPENAI_BASE_URL=config["base_url"],
               MODEL=config["model"])
    visual = {role["model"] for profile in config.get("effective", {}).get("profiles", {}).values()
              for role in profile.get("roles", {}).values() if role.get("provider") == "visual"}
    if len(visual) == 1:
        env.update(VISUAL_API_KEY=key, VISUAL_BASE_URL=config["base_url"], VISUAL_MODEL=visual.pop())

    run_dir = delivered_run(output)
    state = {"venue": "local-cpython-arcbench", "phase": "reusing" if run_dir else "generating",
             "package_sha256": sha256(archive), "task": args.task, "started_at": time.time()}
    factory.save(evidence / "state.json", state)
    if run_dir is None:
        stage = work / "package"
        stage.mkdir(parents=True, exist_ok=True)
        with ZipFile(archive) as package:
            package.extractall(stage)
        stdout, stderr = evidence / "generation.stdout", evidence / "generation.stderr"
        with stdout.open("w") as out, stderr.open("w") as err:
            result = subprocess.run([sys.executable, str(stage / "main.py"), str(requirements),
                                     "--output-dir", str(output)], cwd=stage, env=env,
                                    stdout=out, stderr=err)
        if result.returncode:
            state.update(phase="generation_failed", exit_code=result.returncode)
            factory.save(evidence / "state.json", state)
            raise RuntimeError(f"package generation failed; see {stderr}")
        run_dir = delivered_run(output)
        if run_dir is None:
            raise RuntimeError("package completed without delivered .factory26 run")

    eval_dir = evidence / "evaluation-input"
    if not eval_dir.exists():
        shutil.copytree(run_dir / "application", eval_dir / "application")
        shutil.copy2(run_dir / "application-hashes.json", eval_dir / "application-hashes.json")
        shutil.copy2(run_dir / "run.json", eval_dir / "run.json")
        factory.save(eval_dir / "config.json", {
            "task": args.task, "deployment": "arcbench",
            "benchmark_revision": config["benchmark_revision"]})
    factory.save(evidence / "source.json", {
        "package_sha256": state["package_sha256"], "submission_run": str(run_dir),
        "application_hashes": str(run_dir / "application-hashes.json"),
        "benchmark_revision": config["benchmark_revision"]})
    state.update(phase="evaluating", submission_run=str(run_dir))
    factory.save(evidence / "state.json", state)
    try:
        result = factory.evaluate(eval_dir)
    except Exception as error:
        state.update(phase="evaluation_failed", error=str(error), finished_at=time.time())
        factory.save(evidence / "state.json", state)
        raise
    state.update(phase="completed", evaluation=str(result), finished_at=time.time())
    factory.save(evidence / "state.json", state)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--task", choices=("keep", "bookstack"), required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"evaluation": str(run(args))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
