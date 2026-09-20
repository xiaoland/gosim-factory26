"""实验导航只读、状态分离与评测证据定位边界。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("inspect_runs", Path(__file__).resolve().parents[1] / "scripts/inspect_runs.py")
inspect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspect)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


class RunNavigationTest(unittest.TestCase):
    def test_latest_failed_evaluation_does_not_reuse_old_score(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / "runs/example"
            save(run / "run.json", {"status": "generated", "variant": "custom", "task": "keep"})
            save(run / "config.json", {"backend": "pi", "svc": True})
            save(run / "evaluation/001/summary.json", {"status": "completed", "passed": 0, "failed": 2, "flaky": 0, "skipped": 0, "total": 2})
            save(run / "evaluation/002/summary.json", {"status": "evaluation_error", "phase": "build", "phase_log": "build.log", "passed": 0, "total": 2, "error": "build failed"})
            row = inspect.list_runs(root, variant="custom", task="keep")[0]
            self.assertFalse(row["variant_inferred"])
            self.assertEqual(row["evaluation"]["id"], "002")
            self.assertEqual(row["evaluation"]["status"], "evaluation_error")
            self.assertEqual(row["evaluation"]["phase"], "build")
            self.assertIsNone(row["evaluation"]["score"])
            self.assertIn("未知", inspect.render_list([row]))
            failed = inspect.render_show(inspect.show_run(run))
            self.assertIn("评测阶段: build", failed)
            self.assertIn("评测阶段日志: evaluation/002/build.log", failed)
            previous = inspect.show_run(run, evaluation="001")
            self.assertEqual(previous["evaluation"]["score"]["pass_rate"], 0)
            self.assertIn("0/2 (0.000%)", inspect.render_show(previous))
            with self.assertRaises(ValueError):
                inspect.show_run(run, evaluation="missing")

    def test_partial_coverage_and_session_stage_do_not_change_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "runs/example"
            save(run / "run.json", {"status": "generated", "phase": "frozen", "updated_at": 123, "phase_log": "generation.log", "runtime": {"work": "/tmp/work"}})
            save(run / "config.json", {"backend": "pi", "workflow": "braid", "svc": True})
            save(run / "analysis/000/overview.json", {"status": "partial", "coverage": [{"domain": "terminal_state", "status": "unavailable"}]})
            (run / "analysis/000/evidence-v4.zip").touch()
            save(run / "braid-state/001-design/session.json", {"id": "/tmp/session.jsonl", "stage": "design"})
            save(run / "braid-state/001-design/terminal.json", {"status": "completed"})
            save(run / "remote-evaluation.json", {"phase": "downloading", "host": "test-host", "remote_run": "/remote/example", "updated_at": 124, "observed_at": 120, "attempt": "002", "summary": {"phase": "tests"}, "observation_error": "offline"})
            save(run / "native/000-session.jsonl", {"must_not": "be read"})
            original = Path.read_text

            def read_metadata(path, *args, **kwargs):
                self.assertNotEqual(path.suffix, ".jsonl", "导航不能读取原生 rollout")
                return original(path, *args, **kwargs)

            with patch.object(Path, "read_text", read_metadata):
                result = inspect.show_run(run)
            self.assertEqual(result["generation"]["status"], "generated")
            self.assertEqual(result["generation"]["phase"], "frozen")
            self.assertEqual(result["analysis"][0]["status"], "partial")
            self.assertEqual(result["variant"], "pi-svc-braid")
            self.assertTrue(result["variant_inferred"])
            self.assertEqual(result["remote"]["phase"], "downloading")
            self.assertEqual(result["remote"]["observed_at"], 120)
            self.assertIn("上次状态可能已过时", inspect.render_show(result))
            self.assertEqual(result["sessions"]["native"][0]["stages"], ["001-design"])
            self.assertEqual(result["sessions"]["stages"][0]["status"], "completed")
            self.assertIn("partial 不等于生成失败", inspect.render_show(result))

    def test_case_lookup_uses_selected_report_and_local_attachments(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi"})
            folder = run / "evaluation/001"
            save(folder / "summary.json", {"status": "evaluation_error"})
            screenshot = folder / "test-results/create/test-failed-1.png"
            screenshot.parent.mkdir(parents=True)
            screenshot.touch()
            report = {"suites": [{"specs": [
                {"title": "REQ-2.20: Other", "tests": [{"status": "expected"}]},
                {"title": "REQ-2.2: Create Note", "tests": [{"status": "unexpected", "projectName": "chromium", "results": [{"status": "timedOut", "errors": [{"message": "\u001b[31mNote editor\u001b[0m " + "x" * 5000}], "attachments": [
                    {"name": "screenshot", "path": "/remote/runs/example/evaluation/001/test-results/create/test-failed-1.png"},
                    {"name": "trace", "path": "test-results/create/trace.zip"}]}]}]}]}]}
            save(folder / "results.json", report)
            save(run / "evaluation/002/summary.json", {"status": "evaluation_error"})
            result = inspect.show_run(run, evaluation="001", case="REQ-2.2")
            matches = result["case"]["matches"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["attempts"], ["timedOut"])
            self.assertTrue(matches[0]["error"]["truncated"])
            self.assertNotIn("\u001b", matches[0]["error"]["text"])
            self.assertEqual(len(matches[0]["error"]["text"]), inspect.ERROR_LIMIT)
            self.assertEqual(matches[0]["attachments"][0]["path"], str(screenshot.resolve()))
            self.assertTrue(matches[0]["attachments"][0]["exists"])
            self.assertFalse(matches[0]["attachments"][1]["exists"])
            json_before = json.dumps(result)
            rendered = inspect.render_show(result)
            self.assertEqual(json.dumps(result), json_before)
            self.assertIn("错误已截断", rendered)
            self.assertLess(len(rendered), 2500)
            self.assertLess(rendered.index("用例 REQ-2.2"), rendered.index("评测报告:"))
            self.assertNotIn("config.json:", rendered)
            self.assertEqual(result["evidence"]["config.json"], str((run / "config.json").resolve()))
            self.assertEqual(result["evaluation"]["evidence"]["results.json"], str((folder / "results.json").resolve()))
            self.assertEqual(inspect.show_run(run, "001", "REQ-9.9")["case"]["status"], "not_found")
            self.assertEqual(inspect.show_run(run, case="REQ-2.2")["case"]["status"], "unavailable")

    def test_session_mapping_requires_complete_identity_and_uses_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi", "workflow": "braid"})
            save(run / "braid-state/001-design/session.json", {"id": "/tmp/session.jsonl", "stage": "design"})
            save(run / "braid-state/001-design/terminal.json", {"status": "completed"})
            save(run / "native/000-other-session.jsonl", {})
            self.assertIsNone(inspect.show_run(run)["sessions"]["stages"][0]["native"])
            save(run / "native/001-session.jsonl", {})
            thread = "01a0bd72-fb85-7823-8b3a-166edd857323"
            codex = f"002-rollout-2026-09-20T14-13-44-{thread}.jsonl"
            save(run / "native" / codex, {})
            save(run / "braid-state/002-implement/session.json", {"id": thread, "stage": "implement"})
            save(run / "braid-state/002-implement/terminal.json", {"status": "completed"})
            save(run / "analysis/000-export/overview.json", {"status": "partial"})
            save(run / "analysis/000-export/provenance.json", {"source_session": codex})
            sessions = inspect.show_run(run)["sessions"]
            self.assertEqual(sessions["stages"][0]["native"], str((run / "native/001-session.jsonl").resolve()))
            self.assertEqual(sessions["stages"][1]["native"], str((run / "native" / codex).resolve()))
            self.assertIsNone(sessions["native"][0]["analysis"])
            self.assertEqual(sessions["native"][2]["analysis"], "000-export")
            save(run / "native/003-session.jsonl", {})
            self.assertIsNone(inspect.show_run(run)["sessions"]["stages"][0]["native"])

    def test_missing_or_corrupt_metadata_remains_visible_as_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ignored, broken = root / "runs/ignored", root / "runs/broken"
            ignored.mkdir(parents=True)
            broken.mkdir()
            (broken / "run.json").write_text("{")
            save(broken / "evaluation/001/summary.json", {"status": "completed", "passed": 0, "total": 0})
            rows = inspect.list_runs(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["generation"]["status"], "unknown")
            self.assertIsNone(rows[0]["variant"])
            self.assertIsNone(rows[0]["evaluation"]["score"])
            self.assertGreaterEqual(len(rows[0]["warnings"]), 3)
            self.assertIn("警告:", inspect.render_list(rows))
            self.assertEqual(inspect.show_run(ignored)["generation"]["status"], "unknown")
            (broken / "run.json").write_text("[]")
            self.assertIn("顶层必须是 JSON 对象", inspect.show_run(broken)["warnings"][0])


if __name__ == "__main__":
    unittest.main()
