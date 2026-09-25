"""Build a competition matrix for the published ARC-Bench local Runner."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def verify_case(base, competition, task, requirements_only=False):
    identity = f"{competition}--{task}"
    source = json.loads((base / "source.json").read_text())
    if source.get("task_id") != identity:
        raise ValueError(f"input identity does not match {identity}")
    if requirements_only:
        inventories = ((base / "requirements", (source,)),)
    else:
        tests = json.loads((base / "tests-source.json").read_text())
        assets = json.loads((base / "assets-source.json").read_text())
        if tests.get("task_id") != identity:
            raise ValueError(f"test identity does not match {identity}")
        inventories = ((base / "requirements", (source, assets)),
                       (base / "tests", (tests,)))
    for folder, records in inventories:
        expected = {name: digest for record in records for name, digest in record["files_sha256"].items()}
        actual = {str(path.relative_to(folder)) for path in folder.rglob("*") if path.is_file()}
        if actual != set(expected):
            raise ValueError(f"input inventory differs from frozen source: {identity}")
        for name, digest in expected.items():
            path = folder / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"input checksum mismatch: {path}")


def build(variants, cases, inputs_root, runner, image=None, env_file=None, workers=2,
          prepare_only=False, container_otlp_host="host.docker.internal", separate_evaluation=False,
          requirements_only=False):
    if not prepare_only and not image:
        raise ValueError("--image is required for a Runner run")
    adapter = Path(__file__).with_name("arc_bench_adapter.py").resolve()
    noop = Path(__file__).with_name("arc_bench_noop.py").resolve()
    jobs = []
    checked = set()
    for variant in variants:
        name, separator, artifact = variant.partition("=")
        if not separator or not name or not artifact:
            raise ValueError(f"variant must be NAME=AGENT_ZIP: {variant}")
        agent = Path(artifact).expanduser().resolve(strict=True)
        for case in cases:
            competition, separator, task = case.partition("/")
            if separator != "/" or any(not part or part in (".", "..") or Path(part).name != part
                                       for part in (competition, task)):
                raise ValueError(f"case must be COMPETITION/TASK: {case}")
            base = Path(inputs_root).expanduser().resolve(strict=True) / competition / task
            if base not in checked:
                verify_case(base, competition, task, requirements_only)
                checked.add(base)
            inputs = {"adapter": str(adapter), "runner": str(Path(runner).expanduser().resolve(strict=True)),
                      "agent": str(agent), "requirements": str(base / "requirements")}
            if not requirements_only:
                inputs["tests"] = str(base / "tests")
            if separate_evaluation and not requirements_only:
                inputs["noop"] = str(noop)
            for item in ("source", "tests-source", "assets-source"):
                path = base / (item + ".json")
                if path.is_file():
                    inputs[item.replace("-", "_")] = str(path)
            for key in (("requirements",) if requirements_only else ("requirements", "tests")):
                if not Path(inputs[key]).is_dir():
                    raise ValueError(f"missing {key}: {inputs[key]}")
            command = [sys.executable, "{adapter}", "--runner", "{runner}",
                       "--agent", "{agent}", "--requirements", "{requirements}",
                       "--workspace", "{workspace}",
                       "--competition", competition, "--task", task]
            if not requirements_only:
                command += ["--tests", "{tests}"]
            if prepare_only:
                command.append("--prepare-only")
            else:
                command += ["--image", image]
            if separate_evaluation:
                command += ["--separate-evaluation"]
                if not requirements_only:
                    command += ["--noop-script", "{noop}"]
            if requirements_only:
                command += ["--requirements-only"]
            if env_file:
                command += ["--env-file", str(Path(env_file).expanduser().resolve(strict=True))]
            if container_otlp_host != "host.docker.internal":
                command += ["--container-otlp-host", container_otlp_host]
            jobs.append({"variant": name, "competition": competition, "task": task,
                         "venue": "official-local-prepare" if prepare_only else
                                  "official-local-generation" if requirements_only else "official-local-simulation",
                         "inputs": inputs, "command": command})
    return {"schema_version": 1, "max_parallel": workers, "jobs": jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", action="append", required=True, help="NAME=AGENT_ZIP; repeatable")
    parser.add_argument("--case", action="append", required=True, help="COMPETITION/TASK; repeatable")
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--image")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--container-otlp-host", default="host.docker.internal")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--separate-evaluation", action="store_true")
    parser.add_argument("--requirements-only", action="store_true",
                        help="Run published requirements without unavailable local tests; no score is produced")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.variant, args.case, args.inputs_root, args.runner, args.image,
                   args.env_file, args.workers, args.prepare_only, args.container_otlp_host,
                   args.separate_evaluation, args.requirements_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
