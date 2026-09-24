"""Build a Lite/Web matrix for the published ARC-Bench local Runner."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_TESTS = {"arc-bench-lite/keep": 32, "arc-bench-lite/bookstack": 34,
                  "arc-bench-web/12306": 135, "arc-bench-web/bookstack": 34,
                  "arc-bench-web/ctrip": 125, "arc-bench-web/keep": 32,
                  "arc-bench-web/prestashop": 87, "arc-bench-web/stackoverflow": 67}


def verify_case(base, competition, task):
    identity = f"{competition}--{task}"
    source = json.loads((base / "source.json").read_text())
    tests = json.loads((base / "tests-source.json").read_text())
    assets = json.loads((base / "assets-source.json").read_text())
    if source.get("task_id") != identity or tests.get("task_id") != identity:
        raise ValueError(f"input identity does not match {identity}")
    for folder, records in ((base / "requirements", (source, assets)),
                            (base / "tests", (tests,))):
        expected = {name: digest for record in records for name, digest in record["files_sha256"].items()}
        actual = {str(path.relative_to(folder)) for path in folder.rglob("*") if path.is_file()}
        if actual != set(expected):
            raise ValueError(f"input inventory differs from frozen source: {identity}")
        for name, digest in expected.items():
            path = folder / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"input checksum mismatch: {path}")


def build(variants, cases, inputs_root, runner, image=None, env_file=None, workers=2,
          prepare_only=False, container_otlp_host="host.docker.internal", separate_evaluation=False):
    if not prepare_only and not image:
        raise ValueError("--image is required for a scored run")
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
            if separator != "/" or competition not in ("arc-bench-lite", "arc-bench-web", "hackathon") or not task:
                raise ValueError(f"case must be arc-bench-lite/TASK, arc-bench-web/TASK or hackathon/TASK: {case}")
            base = Path(inputs_root).expanduser().resolve(strict=True) / competition / task
            if base not in checked:
                verify_case(base, competition, task)
                checked.add(base)
            inputs = {"adapter": str(adapter), "runner": str(Path(runner).expanduser().resolve(strict=True)),
                      "agent": str(agent), "requirements": str(base / "requirements"),
                      "tests": str(base / "tests")}
            if separate_evaluation:
                inputs["noop"] = str(noop)
            for item in ("source", "tests-source", "assets-source"):
                path = base / (item + ".json")
                if path.is_file():
                    inputs[item.replace("-", "_")] = str(path)
            for key in ("requirements", "tests"):
                if not Path(inputs[key]).is_dir():
                    raise ValueError(f"missing {key}: {inputs[key]}")
            command = [sys.executable, "{adapter}", "--runner", "{runner}",
                       "--agent", "{agent}", "--requirements", "{requirements}",
                       "--tests", "{tests}", "--workspace", "{workspace}",
                       "--competition", competition, "--task", task]
            if prepare_only:
                command.append("--prepare-only")
            else:
                command += ["--image", image]
                if case in EXPECTED_TESTS:
                    command += ["--expected-tests", str(EXPECTED_TESTS[case])]
            if separate_evaluation:
                command += ["--separate-evaluation", "--noop-script", "{noop}"]
            if env_file:
                command += ["--env-file", str(Path(env_file).expanduser().resolve(strict=True))]
            if container_otlp_host != "host.docker.internal":
                command += ["--container-otlp-host", container_otlp_host]
            jobs.append({"variant": name, "competition": competition, "task": task,
                         "venue": "official-local-prepare" if prepare_only else "official-local-simulation",
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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.variant, args.case, args.inputs_root, args.runner, args.image,
                   args.env_file, args.workers, args.prepare_only, args.container_otlp_host,
                   args.separate_evaluation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
