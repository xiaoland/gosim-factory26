"""只使用假 HTTP 响应与短子进程，不请求模型或启动官方评测。"""
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import concurrency


def report(statuses):
    return {"suites": [{"specs": [{"file": "keep.spec.ts", "title": title,
                                  "tests": [{"projectName": "chromium", "status": status}]}]
                         } for title, status in statuses.items()]}


class ConcurrencyTest(unittest.TestCase):
    def test_429_is_not_success_and_key_stays_out_of_arguments_and_output(self):
        key = "secret-test-key"
        seen_headers = []

        def curl(command, **kwargs):
            self.assertNotIn(key, " ".join(command))
            self.assertNotIn(key, kwargs["input"])
            self.assertNotIn("max_tokens", kwargs["input"])
            self.assertNotIn("--retry", command)
            self.assertEqual(command[1], "--disable")
            headers = Path(command[command.index("--header") + 1].removeprefix("@"))
            self.assertEqual(stat.S_IMODE(headers.stat().st_mode), 0o600)
            self.assertEqual(headers.read_text(), "Authorization: Bearer " + key + "\n")
            seen_headers.append(headers)
            Path(command[command.index("--dump-header") + 1]).write_text("HTTP/2 429\nRetry-After: 7\n")
            Path(command[command.index("--output") + 1]).write_text(json.dumps({
                "choices": [{"message": {"content": "OK", "reasoning_content": "PRIVATE REASONING"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6}}))
            return subprocess.CompletedProcess(command, 0, "429", "")

        with tempfile.TemporaryDirectory() as temp, patch.object(concurrency.subprocess, "run", side_effect=curl) as request:
            result = concurrency.run_probe({"base_url": "https://example.invalid/v1", "model": "test"}, key, Path(temp), jobs=[2])
            self.assertEqual(request.call_count, 2)
            self.assertFalse(result["success"])
            for item in result["groups"][0]["requests"]:
                self.assertEqual(item["http_status"], 429)
                self.assertTrue(item["nonempty_response"])
                self.assertTrue(item["rate_limited"])
                self.assertFalse(item["success"])
                self.assertEqual(item["retry_after"], "7")
            recorded = (Path(temp) / "probe.json").read_text()
            self.assertNotIn(key, recorded)
            self.assertNotIn("PRIVATE REASONING", recorded)
            self.assertTrue(all(not path.exists() for path in seen_headers))

    def test_parallel_jobs_keep_distinct_evaluation_paths_and_fixed_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / "runs/example"
            reference = run / "evaluation/001"
            reference.mkdir(parents=True)
            summary = {"status": "completed", "workers": 1, "passed": 1, "failed": 0, "flaky": 0, "skipped": 0, "total": 1}
            (reference / "summary.json").write_text(json.dumps(summary))
            (reference / "results.json").write_text(json.dumps(report({"REQ-2.2": "expected"})))
            later = run / "evaluation/002"
            later.mkdir()
            (later / "summary.json").write_text('{"status":"evaluation_error"}')
            runner = root / "factory.py"
            runner.write_text("""import json, os, sys, time
from pathlib import Path
run = Path(sys.argv[sys.argv.index('--run') + 1])
folder = run / 'evaluation' / ('003-' + str(os.getpid()))
folder.mkdir()
print('[评测] ' + str(folder), flush=True)
time.sleep(0.2)
(folder / 'summary.json').write_text(json.dumps(SUMMARY))
(folder / 'results.json').write_text(json.dumps(REPORT))
""".replace("SUMMARY", repr(dict(summary, passed=0, failed=1))).replace("REPORT", repr(report({"REQ-2.2": "unexpected"}))))
            with patch.object(concurrency, "FACTORY_SCRIPT", runner), patch.object(concurrency, "validate_snapshot") as validate:
                result = concurrency.evaluate_batch(run, 2, root / "batch")
            validate.assert_called_once_with(run.resolve())
            self.assertEqual(result["reference"]["path"], str(reference.resolve()))
            self.assertEqual(len({job["evaluation"] for job in result["jobs"]}), 2)
            self.assertEqual(result["status"], "completed")
            self.assertFalse(result["equivalent"])
            self.assertLess(max(job["started_at"] for job in result["jobs"]), min(job["finished_at"] for job in result["jobs"]))
            for job in result["jobs"]:
                self.assertEqual(job["comparison"]["differences"][0]["actual"], "unexpected")
                self.assertTrue(Path(job["log"]).is_file())
            self.assertTrue((root / "batch/batch.json").is_file())
            with patch.object(concurrency, "ROOT", root):
                status = concurrency.batch_status(root / "batch/batch.json")
            self.assertEqual(status["status"], "completed")
            self.assertFalse(status["jobs"][0]["comparison"]["equal"])

    def test_status_uses_downloaded_copy_without_claiming_completion_or_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            run = root / "runs/example"
            evaluation = run / "evaluation/003"
            evaluation.mkdir(parents=True)
            summary_path = evaluation / "summary.json"
            summary_path.write_text(json.dumps({"status": "starting", "phase": "tests", "phase_log": "test.log",
                                                "target_url": "http://127.0.0.1:1234", "passed": 1, "failed": 0,
                                                "flaky": 0, "skipped": 0, "total": 1}))
            (evaluation / "test.log").write_text("old output\n" * 7000 +
                "  ✓  11 [chromium] › keep/tests/REQ-2.spec.ts › REQ-2 (100ms)\n"
                "  ✘  12 [chromium] › keep/tests/REQ-3.spec.ts › REQ-3 (1.0m)\n"
                "     12.1 [chromium] › step output\n"
                "  1) [chromium] › failure detail\n")
            batch = root / "batch"
            batch.mkdir()
            log = batch / "job-00.log"
            remote = root / "remote"
            source_run = remote / "runs/example"
            source_evaluation = source_run / "evaluation/003"
            source_evaluation.mkdir(parents=True)
            (source_evaluation / "summary.json").write_text('{"status":"completed","phase":"completed"}')
            source_log = remote / "runs/concurrency/batch/job-00.log"
            source_log.parent.mkdir(parents=True)
            source_log.write_text(f"[评测] {source_evaluation}\n")
            log.write_text(f"[评测] {source_evaluation}\n")
            manifest_path = batch / "batch.json"
            manifest_path.write_text(json.dumps({"kind": "eval", "status": "running", "host": "wsl-test", "run": str(source_run), "jobs": [
                {"job": 0, "log": str(source_log), "evaluation": str(source_evaluation), "comparison": {"equal": True}}]}))
            before = {path: path.read_bytes() for path in (manifest_path, log, summary_path)}
            original_open = Path.open

            def open_local(path, *args, **kwargs):
                self.assertFalse(path.is_relative_to(remote), "status 不能读取来源主机路径，即使该路径存在")
                return original_open(path, *args, **kwargs)

            with patch.object(concurrency, "ROOT", root), patch.object(Path, "open", open_local), \
                 patch.object(concurrency, "save", side_effect=AssertionError("status 不能写文件")):
                status = concurrency.batch_status(batch)
                self.assertEqual(status, concurrency.batch_status(manifest_path))
            self.assertEqual(status["status"], "running")
            self.assertEqual(status["host"], "wsl-test")
            self.assertEqual(status["run"], str(run))
            self.assertEqual(status["source_run"], str(source_run))
            self.assertEqual(status["jobs"][0]["status"], "starting")
            self.assertEqual(status["jobs"][0]["evaluation"], str(evaluation))
            self.assertEqual(status["jobs"][0]["source_evaluation"], str(source_evaluation))
            self.assertEqual(status["jobs"][0]["log"], str(log))
            self.assertEqual(status["jobs"][0]["source_log"], str(source_log))
            self.assertEqual(status["jobs"][0]["phase"], "tests")
            self.assertEqual(status["jobs"][0]["phase_log"], "test.log")
            self.assertEqual(status["jobs"][0]["target_url"], "http://127.0.0.1:1234")
            self.assertIsNone(status["jobs"][0]["comparison"])
            self.assertEqual(status["jobs"][0]["progress"]["observed_completed_cases"],12)
            self.assertIn("REQ-3",status["jobs"][0]["progress"]["latest_completed_case"])
            self.assertNotIn("passed", status["jobs"][0])
            self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_equal_totals_do_not_hide_changed_or_missing_cases(self):
        reference = concurrency.case_states(report({"REQ-2.2": "expected", "REQ-2.3": "unexpected", "REQ-2.4": "skipped"}))
        actual = concurrency.case_states(report({"REQ-2.2": "unexpected", "REQ-2.3": "expected", "REQ-2.4": "skipped"}))
        comparison = concurrency.compare_cases(reference, actual)
        self.assertFalse(comparison["equal"])
        self.assertEqual(len(comparison["differences"]), 2)
        actual.pop(("keep.spec.ts", "REQ-2.4", "chromium"))
        self.assertIsNone(concurrency.compare_cases(reference, actual)["differences"][-1]["actual"])


if __name__ == "__main__":
    unittest.main()
