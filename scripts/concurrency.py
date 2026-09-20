#!/usr/bin/env python3
"""探测 2/4 路模型请求，或并行运行彼此隔离的单 worker 评测。"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import platform
import socket
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
import uuid

from factory import api_key, save, validate_snapshot


ROOT = Path(__file__).resolve().parents[1]
FACTORY_SCRIPT = Path(__file__).with_name("factory.py")


def probe_request(config, key, index):
    """只保存响应指标；凭据和模型正文不进入输出目录。"""
    started = time.time()
    begin = time.monotonic()
    result = {"request": index, "started_at": started, "http_status": None,
              "curl_exit_code": None, "finish_reason": None, "usage": None,
              "nonempty_response": False, "response_is_ok": False,
              "rate_limited": False, "retry_after": None, "success": False, "error": None}
    with tempfile.TemporaryDirectory(prefix="factory26-probe-") as temporary:
        folder = Path(temporary)
        headers = folder / "authorization.headers"
        descriptor = os.open(headers, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("Authorization: Bearer " + key + "\n")
        body = {"model": config["model"], "messages": [{"role": "user", "content": "请只回复 OK。"}], "stream": False}
        command = ["curl", "--disable", "--silent", "--show-error", "--request", "POST",
                   "--header", "@" + str(headers), "--header", "Content-Type: application/json",
                   "--data-binary", "@-", "--dump-header", str(folder / "response.headers"),
                   "--output", str(folder / "response.json"), "--write-out", "%{http_code}",
                   "--connect-timeout", "30", "--max-time", "180",
                   config["base_url"].rstrip("/") + "/chat/completions"]
        try:
            response = subprocess.run(command, input=json.dumps(body), text=True, capture_output=True)
            result["curl_exit_code"] = response.returncode
            status = response.stdout.strip()
            result["http_status"] = int(status) if status.isdigit() and status != "000" else None
            result["rate_limited"] = result["http_status"] == 429
            if response.stderr:
                result["error"] = response.stderr.replace(key, "[已隐藏]")[:500]
            for line in (folder / "response.headers").read_text().splitlines():
                if line.lower().startswith("retry-after:"):
                    result["retry_after"] = line.split(":", 1)[1].strip()
            payload = json.loads((folder / "response.json").read_text())
            choices = payload.get("choices") or []
            choice = choices[0] if choices else {}
            content = (choice.get("message") or {}).get("content")
            result.update(finish_reason=choice.get("finish_reason"), usage=payload.get("usage"),
                          nonempty_response=isinstance(content, str) and bool(content.strip()),
                          response_is_ok=isinstance(content, str) and content.strip() == "OK")
            result["success"] = (response.returncode == 0 and result["http_status"] is not None
                                 and 200 <= result["http_status"] < 300 and result["nonempty_response"]
                                 and result["finish_reason"] == "stop")
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            # 错误响应正文可能含模型内容，因此只保留异常类型，不写原始载荷。
            result["error"] = result["error"] or type(exc).__name__
    result.update(finished_at=time.time(), wall_seconds=time.monotonic() - begin)
    return result


def run_probe(config, key, output, jobs=(2, 4)):
    """依次运行指定并发组，每组只发 jobs 次请求，429 不重试。"""
    endpoint = urlsplit(config["base_url"])
    if endpoint.scheme != "https" or not endpoint.netloc or endpoint.username or endpoint.password:
        raise ValueError("模型 base_url 必须为不含凭据的 HTTPS URL")
    if not key or any(char in key for char in "\r\n"):
        raise ValueError("模型凭据为空或含换行")
    if not jobs or any(count not in (2, 4) for count in jobs):
        raise ValueError("并发数只能是 2 或 4")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"kind": "probe", "base_url": config["base_url"], "model": config["model"],
                "started_at": time.time(), "status": "running", "request_timeout_seconds": 180,
                "platform":f'{platform.system()} {platform.release()} {platform.machine()}', "host":socket.gethostname(),
                "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "retries": 0, "groups": []}
    save(output / "probe.json", manifest)
    print(f"[批次] {output / 'probe.json'}",flush=True)
    for count in jobs:
        group = {"concurrency": count, "started_at": time.time(), "requests": []}
        manifest["groups"].append(group)
        begin = time.monotonic()
        with ThreadPoolExecutor(max_workers=count) as pool:
            futures = [pool.submit(probe_request, config, key, index) for index in range(count)]
            for future in as_completed(futures):
                group["requests"].append(future.result())
                save(output / "probe.json", manifest)
        group.update(finished_at=time.time(), wall_seconds=time.monotonic() - begin)
        group["requests"].sort(key=lambda item: item["request"])
        group["success"] = all(item["success"] for item in group["requests"])
        save(output / "probe.json", manifest)
    manifest.update(status="completed", finished_at=time.time(), success=all(group["success"] for group in manifest["groups"]))
    save(output / "probe.json", manifest)
    return manifest


def case_states(report):
    """以 file/title/project 定位用例，拒绝缺失状态或有歧义的重复身份。"""
    states = {}

    def visit(suite):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                key = (spec["file"], spec["title"], test.get("projectName") or test.get("projectId") or "")
                if key in states or test.get("status") not in ("expected", "unexpected", "skipped", "flaky"):
                    raise ValueError(f"用例身份重复或状态无效: {key}")
                states[key] = test["status"]
        for child in suite.get("suites", []):
            visit(child)

    if not isinstance(report.get("suites"), list):
        raise ValueError("评测报告缺少 suites")
    visit(report)
    if not states:
        raise ValueError("评测报告没有用例，无法比较")
    return states


def compare_cases(reference, actual):
    differences = [{"file": key[0], "title": key[1], "project": key[2],
                    "reference": reference.get(key), "actual": actual.get(key)}
                   for key in sorted(reference.keys() | actual.keys()) if reference.get(key) != actual.get(key)]
    return {"equal": not differences, "reference_count": len(reference),
            "actual_count": len(actual), "differences": differences}


def _completed(summary):
    counts = [summary.get(key) for key in ("passed", "failed", "flaky", "skipped")]
    return (summary.get("status") == "completed" and not summary.get("errors")
            and all(type(value) is int and value >= 0 for value in counts)
            and sum(counts) > 0 and sum(counts) == summary.get("total"))


def _reference(run, selected):
    candidates = sorted((run / "evaluation").glob("*/summary.json"), reverse=True)
    if selected is not None:
        folder = Path(selected)
        folder = run / "evaluation" / folder if len(folder.parts) == 1 else folder.resolve()
        if folder / "summary.json" not in candidates:
            raise ValueError("reference 不属于该 run 或缺少 summary.json")
        candidates = [folder / "summary.json"]
    for path in candidates:
        summary = json.loads(path.read_text())
        if _completed(summary):
            results = path.with_name("results.json")
            states = case_states(json.loads(results.read_text()))
            if len(states) != summary["total"]:
                raise ValueError("reference 用例数与完整评测 summary 不一致")
            return {"path": str(path.parent), "summary": summary,
                    "summary_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "results_sha256": hashlib.sha256(results.read_bytes()).hexdigest(),
                    "cases": [{"file": key[0], "title": key[1], "project": key[2], "status": status}
                              for key, status in sorted(states.items())]}, states
    raise ValueError("没有已有完整评测可作 reference，无法比较")


def _evaluation_path(job, run):
    with Path(job["log"]).open() as log:
        paths = [Path(line.removeprefix("[评测] ").strip())
                 for line in log if line.startswith("[评测] ")]
    if not paths:
        return None
    if len(paths) != 1 or paths[0].parent != run / "evaluation":
        raise ValueError("job 日志未唯一标明该 run 的评测目录")
    return paths[0]


def _collect_job(job, run, reference):
    try:
        folder = _evaluation_path(job, run)
        if folder is None:
            raise ValueError("job 日志未唯一标明该 run 的评测目录")
        job["evaluation"] = str(folder)
        job["summary_path"] = str(folder / "summary.json")
        job["results_path"] = str(folder / "results.json")
        job["summary"] = json.loads((folder / "summary.json").read_text())
        if (folder / "results.json").is_file():
            actual = case_states(json.loads((folder / "results.json").read_text()))
            job["comparison"] = compare_cases(reference, actual)
        job["success"] = (job["exit_code"] == 0 and _completed(job["summary"])
                          and job["summary"].get("workers") == 1 and job["comparison"] is not None
                          and job["comparison"]["actual_count"] == job["summary"]["total"])
        if not job["success"]:
            job["error"] = "评测未完整结束、未保持单 worker，或缺少用例结果；参阅 job 日志与 summary"
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        job["error"] = str(exc)
    return job


def batch_status(source):
    """依据本地批次副本定位日志和 run，保留来源路径，不推断进程终态。"""
    path = Path(source).resolve()
    if path.is_dir():
        path = path / "batch.json"
    manifest = json.loads(path.read_text())
    if manifest.get("kind") != "eval":
        raise ValueError("status 需要 eval 批次的目录或 JSON 文件")
    source_run = Path(manifest["run"])
    run = ROOT.resolve() / "runs" / source_run.name
    result = {"batch": str(path), "status": manifest.get("status") or "unknown",
              "host": manifest.get("host"), "run": str(run), "source_run": str(source_run),
              "error": manifest.get("error"), "jobs": []}
    for job in manifest["jobs"]:
        log = path.parent / Path(job["log"]).name
        entry = {"job": job["job"], "status": "unknown", "evaluation": None,
                 "log": str(log), "source_log": job["log"], "source_evaluation": job.get("evaluation"),
                 "phase": None, "phase_log": None, "target_url": None,
                 "error": job.get("error"), "comparison": None, "progress": None, "read_error": None}
        try:
            source_folder = _evaluation_path(dict(job, log=str(log)), source_run)
            if source_folder is not None:
                folder = run / "evaluation" / source_folder.name
                entry["source_evaluation"] = str(source_folder)
                entry["evaluation"] = str(folder)
                summary = json.loads((folder / "summary.json").read_text())
                entry.update(status=summary.get("status") or "unknown",
                             **{key: summary.get(key) for key in ("phase", "phase_log", "target_url")})
                entry["error"] = summary.get("error") or entry["error"]
                test_log = folder / "test.log"
                if summary.get("phase") == "tests" and test_log.exists():
                    # The pinned list reporter numbers completed tests; retries remain zero.
                    # Read a bounded tail and ignore step rows and the final failure listing.
                    with test_log.open("rb") as stream:
                        stream.seek(max(0, test_log.stat().st_size - 65536))
                        tail = stream.read(65536).decode(errors="replace")
                    matches = re.findall(r"(?m)^\s*[✓✘-]\s+(\d+)\s+(\[[^\n]+)", tail)
                    if matches:
                        count, latest = matches[-1]
                        entry["progress"] = {"observed_completed_cases": int(count), "latest_completed_case": latest,
                                             "reference_total": len(manifest.get("reference", {}).get("cases", [])) or None}
                if job.get("exit_code") == 0 and _completed(summary):
                    entry["comparison"] = job.get("comparison")
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            entry["read_error"] = str(exc)
        result["jobs"].append(entry)
    return result


def evaluate_batch(run, jobs, output, reference=None):
    """启动独立 factory.py eval 进程；各 job 只关联自己日志中的评测目录。"""
    if jobs not in (2, 4):
        raise ValueError("并发数只能是 2 或 4")
    run = Path(run).resolve()
    validate_snapshot(run)
    frozen_reference, expected = _reference(run, reference)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"kind": "eval", "run": str(run), "concurrency": jobs, "workers_per_job": 1,
                "reference": frozen_reference, "started_at": time.time(), "status": "running", "jobs": [],
                "platform":f'{platform.system()} {platform.release()} {platform.machine()}', "host":socket.gethostname(),
                "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    save(output / "batch.json", manifest)
    print(f"[批次] {output / 'batch.json'}",flush=True)
    begin = time.monotonic()
    processes = []
    try:
        for index in range(jobs):
            job = {"job": index, "started_at": time.time(), "log": str(output / f"job-{index:02}.log"),
                   "evaluation": None, "summary": None, "comparison": None, "success": False, "error": None}
            manifest["jobs"].append(job)
            with Path(job["log"]).open("w") as log:
                process = subprocess.Popen([sys.executable, str(FACTORY_SCRIPT), "eval", "--run", str(run)],
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            job["pid"] = process.pid
            processes.append((process, job))
            save(output / "batch.json", manifest)
        pending = list(processes)
        while pending:
            for process, job in pending[:]:
                code = process.poll()
                if code is None:
                    continue
                job.update(exit_code=code, finished_at=time.time())
                job["wall_seconds"] = job["finished_at"] - job["started_at"]
                _collect_job(job, run, expected)
                pending.remove((process, job))
                save(output / "batch.json", manifest)
            if pending:
                time.sleep(0.1)
    except (KeyboardInterrupt, OSError) as exc:
        manifest["error"] = str(exc) or type(exc).__name__
        for process, _ in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
        for process, job in processes:
            job.update(exit_code=process.wait(), finished_at=time.time())
            job["wall_seconds"] = job["finished_at"] - job["started_at"]
            _collect_job(job, run, expected)
    manifest.update(finished_at=time.time(), wall_seconds=time.monotonic() - begin,
                    status="failed" if manifest.get("error") or not all(job["success"] for job in manifest["jobs"]) else "completed")
    paths = [job["evaluation"] for job in manifest["jobs"] if job["evaluation"]]
    if len(paths) != len(set(paths)):
        manifest.update(status="failed", error="多个 job 指向同一评测目录，不能作为独立并发结果")
    manifest["equivalent"] = (manifest["status"] == "completed" and
                              all(job["comparison"]["equal"] for job in manifest["jobs"]))
    save(output / "batch.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("probe", help="每组只发送 2 或 4 条短模型请求")
    probe.add_argument("--config", type=Path, default=ROOT / "variants/pi-svc/config.json")
    probe.add_argument("--jobs", type=int, nargs="+", choices=(2, 4), default=[2, 4])
    probe.add_argument("--key-stdin", action="store_true", help="从 stdin 接收模型凭据，不保存或打印")
    evaluate = sub.add_parser("eval", help="同时运行独立的单 worker 评测")
    evaluate.add_argument("--run", type=Path, required=True)
    evaluate.add_argument("--jobs", type=int, choices=(2, 4), required=True)
    evaluate.add_argument("--reference", help="已有完整 evaluation 的目录名或路径")
    status = sub.add_parser("status", help="只读查看已有 eval 批次与各 job 的当前阶段")
    status.add_argument("batch", type=Path, help="批次目录或 batch.json")
    args = parser.parse_args()
    output = ROOT / "runs/concurrency" / (time.strftime("%Y%m%d-%H%M%S") + "-" + args.command + "-" + uuid.uuid4().hex[:8])
    try:
        if args.command == "status":
            print(json.dumps(batch_status(args.batch), ensure_ascii=False, indent=2))
            return 0
        if args.command == "probe":
            key = sys.stdin.read().strip() if args.key_stdin else api_key()
            result = run_probe(json.loads(args.config.read_text()), key, output, args.jobs)
            print(f"探测结果: {output / 'probe.json'}")
            return 0 if result["success"] else 1
        result = evaluate_batch(args.run, args.jobs, output, args.reference)
        print(f"并发评测结果: {output / 'batch.json'}")
        return 0 if result["equivalent"] else 1
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"无法执行: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
