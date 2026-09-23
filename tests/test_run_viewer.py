"""Observable boundaries for the archived-run HTML snapshot."""

import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_viewer import build, file_link, score_from_platform


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class RunViewerTest(unittest.TestCase):
    def test_complete_failed_score_is_distinct_from_running_or_partial(self):
        complete = {"status": "FAILED", "passed_count": 13, "failed_count": 21,
                    "total_tests": 34, "score": 38.2}
        self.assertEqual(score_from_platform(complete),
                         {"passed": 13, "failed": 21, "total": 34, "score": 38.2})
        self.assertIsNone(score_from_platform(dict(complete, status="RUNNING")))
        self.assertIsNone(score_from_platform(dict(complete, total_tests=35)))

    def test_build_discovers_declared_runs_and_escapes_archive_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = root / "runs"
            factory = runs / "factory-one"
            write(factory / "run.json", {"status": "generated", "task": "keep"})
            write(factory / "config.json", {"backend": "pi"})
            write(runs / "competition" / "matrix" / "analysis" / "run.json", {"status": "generated"})

            hosted = runs / "competition" / "matrix" / "hosted" / "team"
            write(hosted / "inputs.json", {"competition_id": "bench", "package_sha256": "abc", "variant": "team"})
            write(hosted / "state.json", {"competition_id": "bench", "package_sha256": "abc", "tasks": {
                "bookstack": {"run_id": "hosted-failed", "remote_status": "FAILED", "phase": "collected",
                              "platform_result": {"score": 38.2, "passed_count": 13, "failed_count": 21, "total_tests": 34}},
                "keep": {"run_id": "hosted-running", "remote_status": "RUNNING", "phase": "agent"}}})
            write(hosted / "tasks" / "bookstack" / "status.json", {"observed_at": 123,
                "value": {"id": "hosted-failed", "requirement_id": "bookstack", "status": "FAILED",
                          "failure_reason": "<script>alert(1)</script>",
                          "tests": [{"name": "REQ-2.2: Login", "status": "timedOut", "error": "timeout"}]}})
            write(hosted / "tasks" / "keep" / "status.json", {"observed_at": 100,
                "value": {"id": "hosted-running", "requirement_id": "keep", "status": "FAILED",
                          "tests": [{"name": "REQ-9: stale test", "status": "failed"}]}})
            write(runs / "playground" / "play-one" / "status.json", {"id": "play-one", "status": "PASSED",
                "passed_count": 1, "failed_count": 0, "score": 100, "tests": [{"name": "REQ-1", "status": "passed"}]})
            write(runs / "playground" / "wrong" / "status.json", {"id": "another", "status": "PASSED"})

            index, count, warnings = build(root)
            self.assertEqual(count, 4)
            self.assertEqual(len(list(index.parent.glob("*.html"))), 5)
            self.assertIn("平台 run ID 与目录不符", " ".join(warnings))
            source = index.read_text()
            self.assertIn("13/34", source)
            self.assertIn("hosted-running", source)
            detail = next(path.read_text() for path in index.parent.glob("competition*.html")
                          if "hosted-failed" in path.read_text())
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", detail)
            self.assertNotIn("<script>alert(1)</script>", detail)
            self.assertIn("REQ-2.2", detail)
            running = next(path.read_text() for path in index.parent.glob("competition*.html")
                           if "hosted-running" in path.read_text())
            self.assertNotIn("stale test", running)
            self.assertIn("不展示旧逐用例结果", running)
            self.assertEqual(file_link(root / "outside.log", "outside", index.parent, runs), "")
            stale = index.parent / "competition-obsolete.html"
            stale.write_text("old snapshot")
            build(root)
            self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
