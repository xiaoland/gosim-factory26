"""Build a competition matrix for the published ARC-Bench local Runner."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from lab.exp.core import read, require
from lab.exp.core import record
from .arc_artifacts import package_metadata
from .local_job import job as local_job, sdk_role


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
          memory=None, cpus=None, endpoint=None, admission_volume=None, budget=None, runner_runtime_receipt=None, authorization=None, model_config=None, pids=None, replay_policy=None, authority_handoff=None):
    if env_file or gateway_state:
        raise ValueError("new exp uses private deployment credential_file; old env/gateway writer wiring is retired")
    if separate_evaluation:
        if prepare_only or not replay_policy:
            raise ValueError("independent hosted evaluation needs explicit replay_policy")
        for key in ("model_config", "credential_mode", "allow_competition_credit"):
            if key not in replay_policy:
                raise ValueError("replay_policy lacks frozen " + key)
        requirements_only = True
    if shared_docker_slots is not None and (type(shared_docker_slots) is not int or shared_docker_slots <= 0):
        raise ValueError("shared Docker slots must be a positive integer")
    if memory is not None and (not isinstance(memory, str) or not memory.strip()):
        raise ValueError("Docker memory limit must be a nonempty string")
    if cpus is not None and (not math.isfinite(float(cpus)) or float(cpus) <= 0):
        raise ValueError("Docker CPU quota must be positive and finite")
    if not prepare_only and not image:
        raise ValueError("--image is required for a Runner run")
    if host_runtime_receipt is None or runner_runtime_receipt is None or storage is None or budget is None:
        raise ValueError("new exp requires explicit controller runtime, storage and budget")
    if not prepare_only and (memory is None or cpus is None or pids is None):
        raise ValueError("ARC SDK requires explicit memory, CPU and PID limits")
    memory_bytes = None
    if memory is not None:
        match = re.fullmatch(r"([0-9]+)([kmgKMG]?)", memory)
        if not match:
            raise ValueError("Docker memory must be integer bytes or K/M/G")
        memory_bytes = int(match[1]) * (1024 ** {"": 0, "k": 1, "m": 2, "g": 3}[match[2].lower()])
    if not prepare_only and (endpoint is None or not admission_volume or shared_docker_slots is None):
        raise ValueError("ARC execution requires frozen endpoint, admission volume and shared capacity")
    if not prepare_only and authority_handoff is None:
        raise ValueError('ARC execution requires explicit daemon retirement handoff')
    if not authorization:
        raise ValueError("explicit authorization scope is required")
    sdk_role(runner)
    runtime = require(read(runner_runtime_receipt), "runtime") if host_runtime_receipt else None
    python = runtime["launcher"] if runtime else sys.executable
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
            if metadata["operation"] != "replay" and not prepare_only:
                if not requirements_only:
                    raise ValueError("new generation jobs consume requirements only; frozen application evaluation is a separate job")
                if not model_config or any(not model_config.get(k) for k in ("model", "visual_model", "base_url", "provider")):
                    raise ValueError("generation recipe must explicitly freeze models/provider/endpoint")
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
            inputs = {"runner": str(Path(runner).expanduser().resolve(strict=True)),
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
            generated = local_job(f'{name}--{competition}--{task}',
                {key: {'source': value} for key, value in inputs.items()},
                {'wall_seconds': budget['wall_seconds_per_attempt'], 'storage_bytes': storage['workspace_bytes_per_run'],
                 'telemetry_bytes': storage['telemetry_bytes_per_run'],
                 **({'memory_bytes': memory_bytes, 'cpus': float(cpus), 'pids': pids} if not prepare_only else {})},
                {'endpoint': endpoint, 'image_id': image, 'slots': shared_docker_slots,
                 'admission_volume': admission_volume, 'authority_handoff': authority_handoff},
                competition, task, python=python,
                purpose='prepare' if prepare_only else 'evaluate' if metadata['operation'] == 'replay' else 'generate',
                requirements_only=requirements_only, prepare_only=prepare_only,
                labels=labels, model_config=model_config, container_otlp_host=container_otlp_host)
            if variant:
                generated['variant'] = variant
            if origin:
                generated['source_application'] = origin
            jobs.append(generated)
            if separate_evaluation and metadata['operation'] != 'replay':
                source_job = jobs[-1]['id']
                jobs.append({'id': source_job + '--evaluation', 'purpose': 'evaluate', 'source_job': source_job,
                             'inputs': {'application': {'from_job': source_job, 'output': 'application'},
                                        'application_receipt': {'from_job': source_job, 'output': 'application_receipt'},
                                        'requirements': {'source': str(base / 'requirements')}},
                             'outputs': [], 'limits': {
                                 'wall_seconds': budget['wall_seconds_per_attempt'],
                                 'storage_bytes': storage['workspace_bytes_per_run'],
                                 'telemetry_bytes': storage['telemetry_bytes_per_run']},
                             'backend': {'kind': 'hosted', 'competition_id': competition,
                                         'variant': variant or name, 'task': competition + '--' + task,
                                         'model_config': replay_policy['model_config'],
                                         'credential_mode': replay_policy['credential_mode'],
                                         'allow_competition_credit': replay_policy['allow_competition_credit']}})
    result = record('experiment', experiment_id=experiment_key or 'arc-matrix', max_parallel=workers,
                    jobs=jobs, storage=storage, budget=budget, authorization=authorization,
                    controller_runtime=str(Path(host_runtime_receipt).resolve()),
                    runner_runtime=str(Path(runner_runtime_receipt).resolve()))

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entries = parser.add_mutually_exclusive_group(required=True)
    entries.add_argument("--variant", action="append", help="declared VARIANT=AGENT_ZIP; repeatable; must agree with package")
    entries.add_argument("--candidate", action="append", help="experiment CASE=AGENT_ZIP; repeatable; variant comes from package")
    parser.add_argument("--replay-policy", type=Path)
    parser.add_argument('--authority-handoff', type=Path)
    parser.add_argument("--model-config", type=Path)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", action="append", required=True, help="COMPETITION/TASK; repeatable")
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--host-runtime", type=Path, required=True,
                        help="new controller runtime receipt")
    parser.add_argument("--runner-runtime", type=Path, required=True)
    parser.add_argument("--image")
    parser.add_argument("--docker-endpoint", type=Path, required=True)
    parser.add_argument("--admission-volume", required=True)
    parser.add_argument("--wall-seconds", type=positive_float, required=True)
    parser.add_argument("--max-attempts", type=int, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--pids", type=int)
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
                   None, args.workers, args.prepare_only, args.container_otlp_host,
                   args.separate_evaluation, args.requirements_only,
                   None, (), candidates=args.candidate,
                   experiment_key=args.experiment_key, storage=storage,
                   host_runtime_receipt=args.host_runtime, shared_docker_slots=args.shared_docker_slots,
                   memory=args.memory, cpus=args.cpus, endpoint=json.loads(args.docker_endpoint.read_text()),
                   admission_volume=args.admission_volume,
                   budget={"wall_seconds_per_attempt": math.ceil(args.wall_seconds), "max_attempts": args.max_attempts},
                   runner_runtime_receipt=args.runner_runtime, authorization=args.authorization, model_config=json.loads(args.model_config.read_text()) if args.model_config else None, pids=args.pids, replay_policy=json.loads(args.replay_policy.read_text()) if args.replay_policy else None, authority_handoff=json.loads(args.authority_handoff.read_text()) if args.authority_handoff else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
