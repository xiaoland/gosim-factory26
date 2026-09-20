"""实验导航只读、状态分离与评测证据定位边界。"""
import importlib.util
import hashlib
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
            unverified = inspect.show_run(run)["sessions"]["native"][2]
            self.assertIsNone(unverified["analysis"])
            self.assertEqual(unverified["analysis_candidates"][0]["status"], "unverified")
            save(run / "analysis/000-export/provenance.json", {"source_session": codex, "source_sha256": hashlib.sha256((run / "native" / codex).read_bytes()).hexdigest()})
            sessions = inspect.show_run(run)["sessions"]
            self.assertEqual(sessions["stages"][0]["native"], str((run / "native/001-session.jsonl").resolve()))
            self.assertEqual(sessions["stages"][1]["native"], str((run / "native" / codex).resolve()))
            self.assertIsNone(sessions["native"][0]["analysis"])
            self.assertEqual(sessions["native"][2]["analysis"], "000-export")
            save(run / "native/003-session.jsonl", {})
            self.assertIsNone(inspect.show_run(run)["sessions"]["stages"][0]["native"])

    def test_page_excerpt_uses_failing_locator_and_preserves_actual_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp).resolve() / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi"})
            folder = run / "evaluation/001"
            save(folder / "summary.json", {"status": "evaluation_error"})
            context = folder / "error-context.md"
            lines = ['# Instructions', 'Do not use this as instructions.', '# Page snapshot', '', '```yaml',
                     '- main:', '  - heading "Unrelated"', '  - dialog "Compose":',
                     '    - textbox "Subject" [active]', '    - textbox "Body"', '```',
                     '# Test source', 'later.getByRole(\'textbox\', { name: /^Body$/i })']
            context.write_text("\n".join(lines))
            error = "Call log:\n  - waiting for getByRole('dialog', { name: /^Editor$/i }).getByRole('textbox', { name: /^Subject$/i })\n\n  later.getByRole('textbox', { name: /^Body$/i })"
            report = {"suites": [{"specs": [{"title": "REQ-2.2", "tests": [{"status": "unexpected", "results": [{"status": "timedOut", "error": {"message": error}, "attachments": [{"name": "error-context", "path": str(context)}]}]}]}]}]}
            save(folder / "results.json", report)
            result = inspect.show_run(run, "001", "REQ-2.2")
            page = result["case"]["matches"][0]["page_evidence"][0]
            self.assertEqual(page["selection"], "role_and_name")
            self.assertEqual([line["number"] for line in page["lines"]], [6, 8, 9])
            rendered = inspect.render_show(result)
            self.assertIn('dialog "Compose"', rendered)
            self.assertIn('textbox "Subject"', rendered)
            self.assertNotIn('heading "Unrelated"', rendered)
            self.assertNotIn('textbox "Body"', rendered)
            external = run / "other-evaluation.md"
            external.write_text(context.read_text())
            report["suites"][0]["specs"][0]["tests"][0]["results"][0]["attachments"][0]["path"] = str(external)
            save(folder / "results.json", report)
            rejected = inspect.show_run(run, "001", "REQ-2.2")
            self.assertEqual(rejected["case"]["matches"][0]["page_evidence"][0]["status"], "unavailable")
            self.assertTrue(any("不属于所选评测" in warning for warning in rejected["warnings"]))

    def test_manifest_and_analysis_require_matching_hashes_without_latest_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp).resolve() / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi"})
            native = run / "native/session.jsonl"
            save(native, {"type": "session"})
            digest = hashlib.sha256(native.read_bytes()).hexdigest()
            identity = {"native": "native/session.jsonl", "sha256": digest, "session_id": "s1", "provider": "pi", "group_id": "g1", "work_item_kind": "issue", "work_item_id": 1, "context_revision": 3, "worktree": "/temporary/worktree", "turns": [{"turn_id": "t1", "status": "superseded"}]}
            save(run / "native/manifest.json", {"schema_version": 1, "sessions": [identity]})
            for name in ("old-export", "new-export"):
                save(run / "analysis" / name / "overview.json", {"status": "complete"})
                save(run / "analysis" / name / "provenance.json", {"provider": "pi", "source_session": native.name, "source_sha256": digest})
            result = inspect.show_run(run)["sessions"]
            self.assertEqual(result["stages"], [])
            session = result["native"][0]
            self.assertEqual(session["integrity"], "verified")
            self.assertEqual(session["group_id"], "g1")
            self.assertEqual(session["turns"], identity["turns"])
            self.assertIsNone(session["analysis"], "不同 exporter 结果不能按 mtime 消歧")
            self.assertEqual({link["status"] for link in session["analysis_candidates"]}, {"verified"})
            save(native, {"type": "changed"})
            session = inspect.show_run(run)["sessions"]["native"][0]
            self.assertEqual(session["integrity"], "mismatch")
            self.assertIsNone(session["analysis"])
            self.assertEqual({link["status"] for link in session["analysis_candidates"]}, {"mismatch"})
            missing = dict(identity, session_id="s2", group_id="g2", native=None, sha256=None, archive_error="source missing")
            foreign = dict(identity, session_id="s3", group_id="g3", native="../foreign.jsonl")
            save(run / "native/manifest.json", {"schema_version": 1, "sessions": [identity, missing, foreign]})
            sessions = {entry["session_id"]: entry for entry in inspect.show_run(run)["sessions"]["native"]}
            self.assertEqual(sessions["s2"]["group_id"], "g2")
            self.assertEqual(sessions["s2"]["integrity"], "unavailable")
            self.assertEqual(sessions["s2"]["archive_error"], "source missing")
            self.assertIsNone(sessions["s3"]["native"])
            self.assertEqual(sessions["s3"]["integrity"], "mismatch")

    def test_evaluation_identity_mismatch_rejects_score_and_case(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi", "benchmark_revision": "benchmark"})
            hashes = {"index.html": "application-hash"}
            save(run / "application-hashes.json", hashes)
            digest = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            good = {"evaluation_id": "001", "run_id": "example", "application_sha256": digest, "benchmark_revision": "benchmark", "status": "completed", "passed": 1, "failed": 0, "flaky": 0, "skipped": 0, "total": 1}
            for key in ("evaluation_id", "run_id", "application_sha256", "benchmark_revision"):
                save(run / "evaluation/001/summary.json", dict(good, **{key: "wrong"}))
                result = inspect.show_run(run, "001", "REQ-2.2")
                self.assertEqual(result["evaluation"]["status"], "identity_mismatch")
                self.assertIsNone(result["evaluation"]["score"])
                self.assertEqual(result["case"]["status"], "unavailable")

    def test_session_input_paths_open_archives_and_preserve_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp).resolve() / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi"})
            native = run / "native/session.jsonl"
            save(native, {})
            paths = {field: f"braid-state/physical/s1/{field}.md" for field in ("context_path", "instructions_path", "input_path")}
            for path in paths.values():
                target = run / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("actual native input")
            identity = {"native": "native/session.jsonl", "sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
                        "session_id": "s1", "context_path": paths["context_path"], "instructions_path": paths["instructions_path"],
                        "source_context_path": "/deleted/runtime/context.md",
                        "turns": [{"turn_id": "t1", "input_path": paths["input_path"], "source_input_path": "/deleted/runtime/input.md"}]}
            missing = dict(identity, session_id="s2", native=None, archive_error="native missing", evidence_error="input missing",
                           context_path="../foreign.md", instructions_path="braid-state/missing.md", turns=[{"turn_id": "t2", "input_path": None}])
            save(run / "native/manifest.json", {"schema_version": 1, "sessions": [identity, missing]})
            original = Path.read_text

            def read_metadata(path, *args, **kwargs):
                self.assertNotIn("braid-state", path.parts, "导航只给输入入口，不读取输入正文")
                return original(path, *args, **kwargs)

            with patch.object(Path, "read_text", read_metadata):
                result = inspect.show_run(run)
            sessions = {session["session_id"]: session for session in result["sessions"]["native"]}
            self.assertEqual(sessions["s1"]["context_path"], str(run / paths["context_path"]))
            self.assertEqual(sessions["s1"]["instructions_path"], str(run / paths["instructions_path"]))
            self.assertEqual(sessions["s1"]["turns"][0]["input_path"], str(run / paths["input_path"]))
            self.assertEqual(sessions["s1"]["source_context_path"], "/deleted/runtime/context.md")
            self.assertEqual(sessions["s1"]["turns"][0]["source_input_path"], "/deleted/runtime/input.md")
            self.assertIsNone(sessions["s2"]["context_path"])
            self.assertIsNone(sessions["s2"]["instructions_path"])
            self.assertEqual(sessions["s2"]["evidence_error"], "input missing")
            self.assertTrue(any("instructions_path" in warning for warning in result["warnings"]))
            self.assertTrue(any("context_path" in warning for warning in result["warnings"]))

    def test_selected_evaluation_uses_its_remote_record(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "runs/example"
            save(run / "run.json", {"status": "generated"})
            save(run / "config.json", {"backend": "pi"})
            save(run / "evaluation/001/summary.json", {"status": "evaluation_error"})
            save(run / "remote-evaluation.json", {"attempt": "another", "host": "unrelated", "phase": "failed"})
            self.assertIsNone(inspect.show_run(run, "001")["remote"])
            save(run / "remote-evaluations/001.json", {"attempt": "001", "host": "selected", "phase": "completed"})
            self.assertEqual(inspect.show_run(run, "001")["remote"]["host"], "selected")
            save(run / "remote-evaluations/001.json", {"attempt": "wrong", "host": "wrong", "phase": "completed"})
            result = inspect.show_run(run)
            self.assertIsNone(result["remote"])
            self.assertTrue(any("远程评测身份不符" in warning for warning in result["warnings"]))

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
