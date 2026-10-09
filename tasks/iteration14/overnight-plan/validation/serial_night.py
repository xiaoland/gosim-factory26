#!/usr/bin/env python3
"""有限的 stage-B 串行执行器；只消费已保存的 Lab 状态。"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import math
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from copy import deepcopy

PROJECT = Path(__file__).resolve().parents[4]


TERMINAL = {"completed", "failed", "stopped", "cancelled", "blocked"}


def load(path: Path):
    return json.loads(path.read_text())


def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if path.exists():
        try:
            previous = load(path)
            if isinstance(previous, dict) and "process_birth" in previous and "process_birth" not in value:
                value = dict(value, process_birth=previous["process_birth"])
        except (OSError, ValueError):
            pass
    with temporary.open("w") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def process_birth():
    try:
        sys.path.insert(0, str(PROJECT / "scripts"))
        from agent_support import process_identity
        return process_identity(os.getpid())
    except Exception as exc:
        return {"pid": os.getpid(), "error": {"type": type(exc).__name__, "message": str(exc)}}


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def validate_seed(seed_path: Path, execution: dict):
    manifest_path = seed_path / "application-manifest.json"
    provenance_path = seed_path / "seed-provenance.json"
    if not manifest_path.is_file() or not provenance_path.is_file():
        raise RuntimeError("published seed lacks application-manifest.json or seed-provenance.json")
    manifest = load(manifest_path)
    provenance = load(provenance_path)
    if (manifest.get("kind") != "factory26.harness.application" or manifest.get("schema_version") != 2 or
            manifest.get("status") != "published" or manifest.get("delivery_kind") != "final"):
        raise RuntimeError("A seed manifest is not a published final application v2")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if provenance.get("manifest_sha256") != manifest_sha:
        raise RuntimeError("A seed provenance does not bind its manifest hash")
    for key in ("attempt_id", "run_id", "submission_id"):
        expected = execution.get(key)
        if expected and provenance.get(key) != expected:
            raise RuntimeError(f"A seed provenance does not bind execution {key}")
    if not isinstance(manifest.get("files"), dict) or not manifest.get("source_identity"):
        raise RuntimeError("A seed manifest lacks source identity or file inventory")
    return {"manifest_sha256": manifest_sha, "files_sha256": canonical_sha(manifest["files"]),
            "requirements_sha256": manifest.get("requirements_sha256"),
            "application_id": manifest.get("application_id"), "provenance": provenance}


def baseline_dependencies(template: Path):
    value = load(template)
    rows = deepcopy(value.get("productions", {}))
    for row in rows.values():
        row.pop("application_seed", None)
        row.pop("producer", None)
    sys.path.insert(0, str(PROJECT))
    from scripts.package_agent import plan_material
    result = {name: plan_material(**row) for name, row in rows.items()}
    return {"template_sha256": hashlib.sha256(template.read_bytes()).hexdigest(),
            "dependencies": result, "canonical_sha256": canonical_sha(result)}


def update_monitor(path: Path, update):
    value = load(path) if path.exists() else {"schema_version": 1, "experiments": []}
    experiments = value.setdefault("experiments", [])
    if not isinstance(experiments, list):
        raise ValueError("monitor-contract experiments must be a list")
    current = next((row for row in experiments if row.get("stage") == "B"), None)
    if current is None:
        experiments.append(update)
    else:
        current.update(update)
    value["stage"] = update.get("phase", value.get("stage"))
    value["updated_at"] = time.time()
    save(path, value)


def under(root: Path, path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes WorkSSD run root: {path}")
    return path


def state_status(value):
    for key in ("status", "phase", "state"):
        if isinstance(value.get(key), str):
            return value[key].lower()
    return "unknown"


def find_execution(experiment: Path):
    candidates = sorted(experiment.glob("**/execution.json"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None
    raise RuntimeError(f"stage A has multiple execution records: {candidates}")


def complete_score(value, execution_path=None):
    result = value.get("platform_result") or {}
    status = result.get("status", value.get("remote_status"))
    score = result.get("score")
    passed = result.get("passed_count")
    failed = result.get("failed_count")
    total = result.get("total_tests")
    valid_number = lambda item: type(item) in (int, float) and math.isfinite(item)
    valid_count = lambda item: type(item) is int and item >= 0
    if total is None and valid_count(passed) and valid_count(failed):
        total = passed + failed
    complete = (status in {"PASSED", "FAILED"} and valid_number(score) and 0 <= score <= 100 and
                valid_count(passed) and valid_count(failed) and valid_count(total) and
                total == passed + failed and total > 0)
    return complete, {"status": status, "score": score,
                      "passed_count": passed, "failed_count": failed, "total_tests": total}


def wait_for_final(experiment: Path, interval: float, report: Path):
    last = None
    terminal_seen = None
    while True:
        path = find_execution(experiment)
        if path is None:
            save(report, {"kind": "serial-night-observation", "status": "waiting",
                          "experiment": str(experiment), "observed_at": time.time()})
            time.sleep(interval)
            continue
        try:
            value = load(path)
        except (OSError, ValueError) as exc:
            save(report, {"status": "blocked", "reason": "execution record unreadable", "error": str(exc),
                          "state": str(path)})
            raise
        status = state_status(value)
        seed = value.get("application_seed") or {}
        marker = (status, value.get("remote_status"), seed.get("status"),
                  seed.get("path"), complete_score(value, path)[1])
        if marker != last:
            save(report, {"kind": "serial-night-observation", "state": str(path),
                          "status": status, "observed_at": time.time(), "marker": marker})
            last = marker
        if status == "exited":
            terminal_seen = terminal_seen or time.monotonic()
            if value.get("remote_status") not in {"PASSED", "FAILED", "CANCELLED"}:
                save(report, {"status": "blocked", "reason": "unknown remote terminal status", "state": str(path)})
                raise RuntimeError("stage A exited without a recognized remote terminal status")
            complete, score = complete_score(value, path)
            if not complete:
                save(report, {"status": "blocked", "reason": "incomplete score/counts", "score": score})
                raise RuntimeError(f"stage A score/counts incomplete: {score}")
            if seed.get("status") != "published" or not seed.get("path"):
                seed_status = path.parent / "application-seed-status.json"
                archive = value.get("archive") or {}
                if not seed_status.exists() and archive.get("status", "not-exported") == "not-exported" and time.monotonic() - terminal_seen < 600:
                    save(report, {"status": "waiting-export", "state": str(path), "observed_at": time.time()})
                    time.sleep(interval)
                    continue
                save(report, {"status": "blocked", "reason": "published application seed missing", "state": str(path)})
                raise RuntimeError("stage A terminal without published application seed")
            seed_path = Path(seed["path"]).resolve()
            if not seed_path.is_dir():
                save(report, {"status": "blocked", "reason": "published application seed is not a directory"})
                raise RuntimeError(f"published application seed is not a directory: {seed_path}")
            seed_identity = validate_seed(seed_path, value)
            return seed_path, path, score, {**seed, **seed_identity}
        if status in {"failed", "stopped", "cancelled", "blocked", "unknown"}:
            save(report, {"status": "blocked", "reason": "controller or execution state unavailable", "state": str(path)})
            raise RuntimeError(f"stage A is terminal without a complete score: {status}")
        if status in {"active", "running"}:
            controllers = sorted(experiment.glob("**/controller.json"))
            try:
                controller_states = [state_status(load(item)) for item in controllers]
            except (OSError, ValueError) as exc:
                save(report, {"status": "blocked", "reason": "controller record unreadable", "error": str(exc)})
                raise
            dead = [item for item in controller_states if item in {"failed", "blocked", "lost", "exited"}]
            if controllers and len(dead) == len(controllers):
                save(report, {"status": "blocked", "reason": "all controller records are dead"})
                raise RuntimeError("stage A controllers are dead while execution remains active")
        time.sleep(interval)


def wait_for_b_final(experiment: Path, interval: float, report: Path, expected_manifest: str,
                     audit_ordinal: int):
    """B may legally finish with a complete_no_change audit and no published app."""
    terminal_seen = None
    while True:
        path = find_execution(experiment)
        if path is None:
            save(report, {"status": "waiting", "opportunity": audit_ordinal,
                          "experiment": str(experiment), "observed_at": time.time()})
            time.sleep(interval)
            continue
        try:
            value = load(path)
        except (OSError, ValueError) as exc:
            save(report, {"status": "blocked", "reason": "B execution record unreadable", "error": str(exc),
                          "state": str(path)})
            raise
        if state_status(value) == "exited":
            terminal_seen = terminal_seen or time.monotonic()
            candidates = sorted([path.parent / "audit-status.json", *path.parent.glob("monitor/**/runtime-evidence/**/audit-status.json")],
                                key=lambda item: item.stat().st_mtime_ns if item.exists() else 0)
            audit = None
            audit_path = None
            for candidate in candidates[-1:]:
                try:
                    audit = load(candidate)
                    audit_path = candidate
                except (OSError, ValueError):
                    continue
            report_path = audit_path.with_name("audit-report.json") if audit_path else None
            try:
                audit_report = load(report_path) if report_path and report_path.is_file() else None
            except (OSError, ValueError):
                audit_report = None
            identities = ("a_manifest_sha256", "requirements_sha256", "candidate_commit")
            bound = (audit and audit_report and all(audit.get(key) and audit_report.get(key) and
                                                    audit[key] == audit_report[key] for key in identities) and
                     audit.get("a_manifest_sha256") == expected_manifest)
            if (audit and audit_report and audit.get("status") == "complete_no_change" and
                    audit_report.get("status") == "complete" and audit_report.get("mode") == "seed-audit" and bound):
                return None, path, {"status": "complete_no_change"}
            seed = value.get("application_seed") or {}
            if seed.get("status") == "published" and seed.get("path"):
                complete, score = complete_score(value, path)
                if not complete:
                    raise RuntimeError("B published application lacks complete official score/counts")
                seed_path = Path(seed["path"]).resolve()
                if not seed_path.is_relative_to(experiment.resolve()):
                    raise RuntimeError("B published application seed escapes experiment root")
                validate_seed(seed_path, value)
                return seed_path, path, score
            receipt = path.parent / "application-seed-status.json"
            if not audit_report and not receipt.exists() and time.monotonic() - terminal_seen < 600:
                save(report, {"status": "waiting-export", "opportunity": audit_ordinal,
                              "state": str(path), "observed_at": time.time()})
                time.sleep(interval)
                continue
            save(report, {"status": "blocked", "reason": "B terminal without audit report or published seed",
                          "state": str(path)})
            raise RuntimeError("B terminal without audit report or published seed")
        if state_status(value) in {"failed", "stopped", "cancelled", "blocked"}:
            raise RuntimeError("B terminal without complete audit evidence")
        time.sleep(interval)


def derive_intent(template: Path, output: Path, seed: Path):
    text = template.read_text()
    marker = "${APPLICATION_SEED}"
    if marker not in text:
        raise ValueError(f"stage-B intent must contain {marker} marker")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.replace(marker, str(seed)))
    return output


def write_process_log(root: Path, index: int, stream: str, text: str):
    path = root / "serial-night-logs" / f"step-{index}-{stream}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--stage-a-experiment", type=Path, required=True)
    parser.add_argument("--stage-b-intent-template", type=Path, required=True)
    parser.add_argument("--stage-b-intent-output", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--compiled", type=Path, required=True)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--deployment", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--monitor-contract", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=30.0)
    # Kept as an argv compatibility guard; the durable ledger assigns the
    # actual ordinal under its lock so resumed runs cannot invent one.
    parser.add_argument("--opportunity", type=int, choices=(2, 3), default=None)
    args = parser.parse_args()

    root = args.run_root.resolve()
    if not root.is_relative_to(Path("/Volumes/WorkSSD").resolve()):
        raise ValueError("serial-night outputs must be on WorkSSD")
    owner_lock = (root / "serial-night.owner.lock").open("a+")
    try:
        fcntl.flock(owner_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        save(under(root, args.report), {"status": "already-running", "observed_at": time.time()})
        return 0
    save(under(root, args.report), {"status": "waiting-for-A", "owner_pid": os.getpid(),
                                    "process_birth": process_birth(), "started_at": time.time(),
                                    "owner_lock": str(root / "serial-night.owner.lock")})
    stage_a = under(root, args.stage_a_experiment)
    template = under(root, args.stage_b_intent_template)
    intent = under(root, args.stage_b_intent_output)
    environment = under(root, args.environment)
    compiled = under(root, args.compiled)
    experiment = under(root, args.experiment)
    deployment = under(root, args.deployment)
    ledger = under(root, args.ledger)
    monitor_contract = under(root, args.monitor_contract)
    report = under(root, args.report)
    baseline_path = under(root, root / "stage-b/baseline-dependencies.json")
    try:
        baseline = baseline_dependencies(template)
        save(baseline_path, baseline)
    except Exception as exc:
        save(report, {"status": "blocked", "reason": "baseline material planning failed", "error": str(exc)})
        raise
    seed, execution, score, seed_record = wait_for_final(stage_a, args.interval, report.with_name("stage-a-wait.json"))
    if not seed.is_relative_to(root):
        raise RuntimeError("published application seed escapes the WorkSSD run root")
    current_baseline = baseline_dependencies(template)
    if current_baseline["canonical_sha256"] != baseline["canonical_sha256"]:
        save(report, {"status": "blocked", "reason": "stage-B baseline material dependencies changed"})
        raise RuntimeError("stage-B baseline material dependencies changed")
    update_monitor(monitor_contract, {"stage": "B", "phase": "A-verified",
                                      "a_manifest_sha256": seed_record.get("manifest_sha256"),
                                      "a_files_sha256": seed_record.get("files_sha256"),
                                      "a_requirements_sha256": seed_record.get("requirements_sha256"),
                                      "a_provenance": seed_record.get("provenance")})

    ledger.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger.with_suffix(ledger.suffix + ".lock")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = load(ledger) if ledger.exists() else {"schema_version": 1, "limit": 3, "opportunities": []}
        opportunities = current.setdefault("opportunities", [])
        if not isinstance(opportunities, list):
            raise ValueError("opportunity-ledger opportunities must be a list")
        if current.get("limit") != 3 or len(opportunities) >= 3:
            raise RuntimeError("opportunity ledger must retain limit=3 and room for audit-B")
        existing = next((row for row in opportunities if row.get("key") == "audit-B"), None)
        if existing is not None:
            audit_ordinal = existing.get("ordinal")
            if type(audit_ordinal) is not int or audit_ordinal < 1:
                audit_ordinal = next((index + 1 for index, row in enumerate(opportunities)
                                      if row is existing), len(opportunities) + 1)
                existing["ordinal"] = audit_ordinal
                save(ledger, current)
        else:
            audit_ordinal = len(opportunities) + 1
            if audit_ordinal > int(current.get("limit", 3)):
                raise RuntimeError("opportunity ordinal exceeds ledger limit")
        if existing:
            save(report, {"status": "already-claimed", "opportunity": audit_ordinal, "row": existing})
            return 0
        if len(opportunities) >= int(current.get("limit", 3)):
            raise RuntimeError("opportunity ledger is full; no new model-bearing run allowed")
        row = {"key": "audit-B", "ordinal": audit_ordinal}
        row.update({"phase": "claimed", "reserved_at": time.time(), "seed": str(seed),
                    "source_execution": str(execution), "score": score,
                    "experiment": str(experiment), "metadata_phase": "reserved"})
        if existing is None:
            opportunities.append(row)
        save(ledger, current)
        derived_intent = derive_intent(template, intent, seed)
        row.update({"phase": "prepared", "metadata_phase": "prepared",
                    "intent": str(derived_intent), "compiled": str(compiled)})
        save(ledger, current)
        update_monitor(monitor_contract, {"stage": "B", "phase": "prepared",
                                          "experiment": str(experiment), "compiled": str(compiled),
                                          "source_execution": str(execution), "application_seed": str(seed),
                                          "runtime": str(environment)})
    results = []
    try:
        commands = [
            [sys.executable, "-B", "-m", "lab.exp", "compile", str(intent), "--environment", str(environment), "--directory", str(compiled)],
            [sys.executable, "-B", "-m", "lab.exp", "build", str(compiled / "recipe.json"), "--environment", str(environment), "--directory", str(experiment)],
            [sys.executable, "-B", "-m", "lab.exp", "start", str(experiment), "--deployment", str(deployment)],
        ]
        for index, argv in enumerate(commands):
            started = time.time()
            child_env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[4]), os.environ.get("PYTHONPATH", ""))).strip(os.pathsep))
            result = subprocess.run(argv, cwd=Path(__file__).resolve().parents[4], env=child_env,
                                    capture_output=True, text=True)
            stdout_path = write_process_log(root, index, "stdout", result.stdout)
            stderr_path = write_process_log(root, index, "stderr", result.stderr)
            item = {"index": index, "argv": argv, "started_at": started,
                    "finished_at": time.time(), "returncode": result.returncode,
                    "stdout_log": str(stdout_path), "stderr_log": str(stderr_path),
                    "stdout_tail": result.stdout[-16000:], "stderr_tail": result.stderr[-16000:]}
            results.append(item)
            save(report, {"status": "running", "opportunity": audit_ordinal, "results": results,
                          "application_seed": str(seed)})
            if result.returncode:
                raise RuntimeError(f"stage-B step {index} failed with {result.returncode}")
            if index == 1:
                recipe = compiled / "recipe.json"
                update_monitor(monitor_contract, {"stage": "B", "phase": "built",
                                                  "experiment": str(experiment),
                                                  "frozen_runtime": str(environment),
                                                  "frozen_source": str(experiment / "source"),
                                                  "recipe_sha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
                                                  "baseline_sha256": baseline["canonical_sha256"]})
            if index == 2:
                attempt_path = find_execution(experiment)
                update_monitor(monitor_contract, {"stage": "B", "phase": "started",
                                                  "actual_attempt": str(attempt_path) if attempt_path else None})
        b_seed, b_execution, b_score = wait_for_b_final(
            experiment, args.interval, report.with_name("stage-b-wait.json"),
            seed_record.get("manifest_sha256"), audit_ordinal)
        update_monitor(monitor_contract, {"stage": "B", "phase": "terminal",
                                          "actual_attempt": str(b_execution), "score": b_score})
    except BaseException as exc:
        with lock_path.open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            current = load(ledger)
            row = next(row for row in current["opportunities"] if row.get("key") == "audit-B")
            row.update({"phase": "failed", "error": str(exc), "finished_at": time.time()})
            save(ledger, current)
        save(report, {"status": "failed", "opportunity": audit_ordinal, "results": results,
                      "error": str(exc)})
        raise
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = load(ledger)
        row = next(row for row in current["opportunities"] if row.get("key") == "audit-B")
        row.update({"phase": "completed", "metadata_phase": "completed", "finished_at": time.time(),
                    "experiment": str(experiment), "b_execution": str(b_execution),
                    "b_seed": str(b_seed), "b_score": b_score})
        save(ledger, current)
    update_monitor(monitor_contract, {"stage": "B", "phase": "completed",
                                      "experiment": str(experiment), "compiled": str(compiled),
                                      "source_execution": str(execution), "application_seed": str(seed)})
    save(report, {"status": "completed", "opportunity": audit_ordinal, "results": results,
                  "monitor_contract": str(monitor_contract)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
