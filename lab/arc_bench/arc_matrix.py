"""Build a competition matrix for the published ARC-Bench local Runner."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from .arc_artifacts import package_metadata


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
          requirements_only=False, gateway_state=None, gateway_include_vars=(), *, candidates=None, experiment_key=None):
    if not prepare_only and not image:
        raise ValueError("--image is required for a Runner run")
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
            command = [sys.executable, "{adapter}/arc_bench_adapter.py", "--runner", "{runner}",
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
                wrapper = [sys.executable, "{gateway}", "wrap", "--service-state",
                           str(Path(gateway_state).expanduser().resolve(strict=True)),
                           "--url-env", "OPENAI_BASE_URL", "--key-env", "OPENAI_API_KEY",
                           "--env-file-var", "ARC_MODEL_ENV_FILE"]
                if env_file:
                    wrapper += ["--client-env", str(Path(env_file).expanduser().resolve(strict=True))]
                for variable in gateway_include_vars:
                    wrapper += ["--include-var", variable]
                command = wrapper + ["--"] + command
            if container_otlp_host != "host.docker.internal":
                command += ["--container-otlp-host", container_otlp_host]
            handlers = {action: [[sys.executable, "{adapter}/arc_bench_adapter.py",
                                   "resource", action, "--workspace", "{workspace}"]]
                        for action in ("inspect", "cleanup")}
            if gateway_state:
                for action in handlers:
                    handlers[action].append([sys.executable, "{gateway}", "resource", action,
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
                         "artifact_paths": arc_artifacts,
                         "resource_handlers": handlers,
                         "venue": "official-local-prepare" if prepare_only else
                                  "official-local-generation" if requirements_only else "official-local-simulation",
                         "inputs": inputs, "command": command})
    return {"schema_version": 2, "max_parallel": workers, "jobs": jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entries = parser.add_mutually_exclusive_group(required=True)
    entries.add_argument("--variant", action="append", help="declared VARIANT=AGENT_ZIP; repeatable; must agree with package")
    entries.add_argument("--candidate", action="append", help="experiment CASE=AGENT_ZIP; repeatable; variant comes from package")
    parser.add_argument("--experiment-key")
    parser.add_argument("--case", action="append", required=True, help="COMPETITION/TASK; repeatable")
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--image")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--gateway-state", type=Path, help="running local gateway state with per-run binding")
    parser.add_argument("--gateway-include-var", action="append", default=[],
                        help="copy one additional name from --env-file into the run client env")
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
                   args.separate_evaluation, args.requirements_only,
                   args.gateway_state, args.gateway_include_var, candidates=args.candidate, experiment_key=args.experiment_key)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
