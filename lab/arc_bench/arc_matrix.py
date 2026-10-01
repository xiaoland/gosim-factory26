"""Build a competition matrix for the published ARC-Bench local Runner."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from ..assets import host_runtime
from .arc_artifacts import package_metadata


def positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def nonnegative_float(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return number


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
          prepare_only=False, container_otlp_host=None, separate_evaluation=False,
          requirements_only=False, gateway_state=None, gateway_include_vars=(), *, candidates=None,
          experiment_key=None, storage=None, host_runtime_receipt=None, shared_docker_slots=None,
          memory=None, cpus=None):
    if shared_docker_slots is not None and (type(shared_docker_slots) is not int or shared_docker_slots <= 0):
        raise ValueError("shared Docker slots must be a positive integer")
    if memory is not None and (not isinstance(memory, str) or not memory.strip()):
        raise ValueError("Docker memory limit must be a nonempty string")
    if cpus is not None and (not math.isfinite(float(cpus)) or float(cpus) <= 0):
        raise ValueError("Docker CPU quota must be positive and finite")
    if not prepare_only and not image:
        raise ValueError("--image is required for a Runner run")
    if storage and host_runtime_receipt is None:
        raise ValueError("schema v3 requires --host-runtime")
    runtime = host_runtime(host_runtime_receipt) if host_runtime_receipt else None
    python = runtime["launcher"] if runtime else sys.executable
    runtime_dependency = ({"purpose": "execution_cleanup", "kind": "host-lab-runtime",
                           "location": runtime["root"], "launcher": runtime["launcher"],
                           "receipt": runtime["receipt"], "identity": runtime["identity"]}
                          if runtime else {"purpose": "execution_cleanup", "kind": "python",
                                           "location": str(Path(sys.executable).absolute())})
    adapter = Path(__file__).resolve().parent
    noop = Path(__file__).with_name("arc_bench_noop.py").resolve()
    jobs = []
    checked = set()
    used = set()
    for entry in (candidates if candidates is not None else variants):
        name, separator, artifact = entry.partition("=")
        if not separator or not name or not artifact:
            raise ValueError(f"candidate or variant must be NAME=AGENT_ZIP: {entry}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) or name in used:
            raise ValueError(f"duplicate or invalid candidate name: {name}")
        used.add(name)
        agent = Path(artifact).expanduser().resolve(strict=True)
        metadata = package_metadata(agent)
        if candidates is None and metadata["variant"] and metadata["variant"] != name:
            raise ValueError(f"declared variant {name!r} differs from package {metadata['variant']!r}; use --candidate for a case alias")
        for case in cases:
            competition, separator, task = case.partition("/")
            if separator != "/" or any(not part or part in (".", "..") or Path(part).name != part
                                       for part in (competition, task)):
                raise ValueError(f"case must be COMPETITION/TASK: {case}")
            base = Path(inputs_root).expanduser().resolve(strict=True) / competition / task
            if base not in checked:
                verify_case(base, competition, task, requirements_only)
                checked.add(base)
            labels = {"operation": metadata["operation"]}
            if experiment_key:
                labels["experiment_key"] = experiment_key
            if candidates is not None:
                labels["case"] = name
            else:
                labels["declared_variant"] = name
            origin = None
            variant = metadata["variant"]
            if metadata["operation"] == "replay":
                requirement_hash = hashlib.sha256((base / "requirements/requirements.yaml").read_bytes()).hexdigest()
                matches = [source for source in metadata["source_applications"]
                           if source["requirements_sha256"] == requirement_hash]
                if len(matches) != 1:
                    raise ValueError(f"replay package has no unique application for {competition}/{task}")
                origin = matches[0]
                variant = origin.get("variant")
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
            command = [python, "{adapter}/arc_bench_adapter.py", "--runner", "{runner}",
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
            if env_file and not gateway_state:
                command += ["--env-file", str(Path(env_file).expanduser().resolve(strict=True))]
            if gateway_state:
                gateway = Path(__file__).resolve().parents[2] / "scripts/hackathon_gateway.py"
                inputs["gateway"] = str(gateway)
                inputs["gateway_service"] = str(Path(gateway_state).expanduser().resolve(strict=True) / "service.json")
                inputs["gateway_callback"] = str(Path(gateway_state).expanduser().resolve(strict=True) /
                                                  "code/hackathon_gateway_compat.py")
                wrapper = [python, "{gateway}", "wrap", "--service-state",
                           str(Path(gateway_state).expanduser().resolve(strict=True)),
                           "--url-env", "OPENAI_BASE_URL", "--key-env", "OPENAI_API_KEY",
                           "--env-file-var", "ARC_MODEL_ENV_FILE"]
                if env_file:
                    wrapper += ["--client-env", str(Path(env_file).expanduser().resolve(strict=True))]
                for variable in gateway_include_vars:
                    wrapper += ["--include-var", variable]
                command = wrapper + ["--"] + command
            for flag, value in (("--memory", memory), ("--cpus", cpus)):
                if value is not None:
                    command += [flag, str(value)]
            if shared_docker_slots is not None:
                command += ["--shared-docker-slots", str(shared_docker_slots)]
            if container_otlp_host:
                command += ["--container-otlp-host", container_otlp_host]
            handlers = {action: [[python, "{adapter}/arc_bench_adapter.py",
                                   "resource", action, "--workspace", "{workspace}"]]
                        for action in ("inspect", "cleanup")}
            if gateway_state:
                for action in handlers:
                    handlers[action].append([python, "{gateway}", "resource", action,
                                             "--service-state", str(Path(gateway_state).expanduser().resolve(strict=True)),
                                             "--run-dir", "{run_dir}", "--run-id", "{run_id}"])
            arc_root = ("workspace/official-generation/template/.arc" if separate_evaluation or requirements_only
                        else "workspace/official/template/.arc")
            arc_artifacts = [f"{arc_root}/traceability", f"{arc_root}/runner-events.jsonl",
                             f"{arc_root}/runtime-reporting"]
            if separate_evaluation and not requirements_only:
                arc_artifacts.extend(("workspace/official-evaluation/template/.arc/traceability",
                                      "workspace/official-evaluation/template/.arc/runner-events.jsonl"))
            jobs.append({"id": f"{name}--{competition}--{task}",
                         **({"variant": variant} if variant else {}), "competition": competition, "task": task,
                         "labels": labels, **({"source_application": origin} if origin else {}),
                         "adapter_kind": "arc-bench", "result_path": "workspace/experiment-result.json",
                         "docker": not prepare_only,
                         "artifact_paths": arc_artifacts,
                         "resource_handlers": handlers,
                         "dependencies": [runtime_dependency],
                         "venue": "official-local-prepare" if prepare_only else
                                  "official-local-generation" if requirements_only else "official-local-simulation",
                         "inputs": inputs, "command": command})
    result = {"schema_version": 3 if storage else 2, "max_parallel": workers, "jobs": jobs}
    if storage:
        result["storage"] = storage
        result["controller_runtime"] = runtime_dependency
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entries = parser.add_mutually_exclusive_group(required=True)
    entries.add_argument("--variant", action="append", help="declared VARIANT=AGENT_ZIP; repeatable; must agree with package")
    entries.add_argument("--candidate", action="append", help="experiment CASE=AGENT_ZIP; repeatable; variant comes from package")
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", action="append", required=True, help="COMPETITION/TASK; repeatable")
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--host-runtime", type=Path, required=True,
                        help="asset.json from scripts/runtime.py host-lab")
    parser.add_argument("--image")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--gateway-state", type=Path, help="running local gateway state with per-run binding")
    parser.add_argument("--gateway-include-var", action="append", default=[],
                        help="copy one additional name from --env-file into the run client env")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--memory", help="explicit Docker memory limit for each run, e.g. 2g")
    parser.add_argument("--cpus", type=positive_float, help="explicit Docker CPU quota for each run")
    parser.add_argument("--shared-docker-slots", type=int,
                        help="same-host shared execution capacity on the frozen Docker daemon")
    parser.add_argument("--workspace-cap-gib", type=positive_float, required=True,
                        help="each concurrent run's workspace limit")
    parser.add_argument("--telemetry-cap-gib", type=positive_float, required=True,
                        help="each concurrent run's raw OTLP limit")
    parser.add_argument("--finalization-scratch-gib", type=positive_float, required=True,
                        help="scratch required to finish one run without deleting active evidence")
    parser.add_argument("--host-reserve-gib", type=positive_float, default=50,
                        help="filesystem free-space floor; default: 50 GiB")
    parser.add_argument("--build-cap-gib", type=nonnegative_float, default=0,
                        help="additional package/image build peak")
    parser.add_argument("--archive-level", choices=("decision",),
                        default="decision")
    parser.add_argument("--container-otlp-host", help="explicit reachable collector host; remote default collects files")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--separate-evaluation", action="store_true")
    parser.add_argument("--requirements-only", action="store_true",
                        help="Run published requirements without unavailable local tests; no score is produced")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    gib = 1024 ** 3
    storage = {"host_reserve_bytes": math.ceil(args.host_reserve_gib * gib),
               "workspace_bytes_per_run": math.ceil(args.workspace_cap_gib * gib),
               "telemetry_bytes_per_run": math.ceil(args.telemetry_cap_gib * gib),
               "finalization_scratch_bytes_per_run": math.ceil(args.finalization_scratch_gib * gib),
               "build_bytes": math.ceil(args.build_cap_gib * gib),
               "archive_level": args.archive_level, "inode_reserve_percent": 10}
    result = build(args.variant, args.case, args.inputs_root, args.runner, args.image,
                   args.env_file, args.workers, args.prepare_only, args.container_otlp_host,
                   args.separate_evaluation, args.requirements_only,
                   args.gateway_state, args.gateway_include_var, candidates=args.candidate,
                   experiment_key=args.experiment_key, storage=storage,
                   host_runtime_receipt=args.host_runtime, shared_docker_slots=args.shared_docker_slots,
                   memory=args.memory, cpus=args.cpus)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
