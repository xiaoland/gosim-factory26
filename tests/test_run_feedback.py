import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_feedback


class FeedbackTest(unittest.TestCase):
    def test_pi_retries_are_grouped_and_final_message_is_not_duplicated(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generating", "phase": "agent"}))
        events = [
            {"type": "auto_retry_start", "attempt": 1, "maxAttempts": 3,
             "delayMs": 2000, "errorMessage": "Unterminated string in JSON at position 140"},
            {"type": "message_end", "message": {"role": "assistant", "stopReason": "error",
                                                   "errorMessage": "Unterminated string in JSON at position 140"}},
            {"type": "auto_retry_end", "attempt": 1, "success": True},
        ]
        (run / "pi-events.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n")
        brief = run_feedback.collect(run)
        self.assertEqual(brief["status"], "running")
        self.assertEqual(brief["event_id"], run_feedback.collect(run)["event_id"])
        self.assertEqual(brief["retries"][0]["attempt"], 1)
        self.assertEqual(brief["error_count"], 1)
        self.assertEqual(len(brief["errors"]), 1)
        self.assertEqual(brief["errors"][0]["count"], 1)
        self.assertEqual(brief["errors"][0]["evidence"], ["pi-events.jsonl:1"])
        self.assertEqual(brief['errors'][0]['scope'],'historical')
        self.assertIsNone(brief['error'])

    def test_codex_stream_error_keeps_retry_and_turn_fields(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generating", "phase": "agent"}))
        event = {"method": "error", "params": {"error": {
            "message": "Reconnecting... 1/5",
            "codexErrorInfo": {"responseStreamDisconnected": {"httpStatusCode": None}},
            "additionalDetails": "stream disconnected before completion",
        }, "willRetry": True, "threadId": "thread-1", "turnId": "turn-1"}}
        (run / "codex-events.jsonl").write_text(json.dumps(event) + "\n")
        brief = run_feedback.collect(run)
        self.assertEqual(brief["retries"][0]["turn_id"], "turn-1")
        self.assertTrue(brief["retries"][0]["will_retry"])
        self.assertEqual(brief["errors"][0]["category"], "codex:response_stream_disconnected")

    def test_interruption_and_outcome_precedence(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generated"}))
        (run / "interruption.json").write_text(json.dumps({"stopped": True}))
        self.assertEqual(run_feedback.collect(run)["status"], "interrupted")
        (run / "interruption.json").write_text(json.dumps({"stopped": False}))
        (run / "outcome.json").write_text(json.dumps({"schema_version": 1, "run_id": run.name,
                                                         "status": "running", "stage": "analysis"}))
        result = run_feedback.collect(run)
        self.assertFalse(result["terminal"])
        self.assertEqual(result["stage"], "analysis")

        (run / "run.json").write_text(json.dumps({"status": "interrupted", "phase": "agent"}))
        (run / "outcome.json").unlink()
        self.assertEqual(run_feedback.collect(run)["status"], "interrupted")

    def test_invalid_manifest_is_unknown_and_does_not_scan_unrelated_files(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generated"}))
        native = run / "native"
        native.mkdir()
        outside = run / "outside.jsonl"
        outside.write_text(json.dumps({"type": "message", "message": {"role": "assistant",
                                                                           "stopReason": "error",
                                                                           "errorMessage": "outside"}}))
        (native / "manifest.json").write_text(json.dumps({"schema_version": 1, "sessions": [
            {"provider": "pi", "native": str(outside), "sha256": "bad"},
            {"provider": "pi", "native": "native/missing.jsonl"},
        ]}))
        brief = run_feedback.collect(run)
        self.assertEqual(brief["error_count"], 0)
        self.assertTrue(any("manifest" in value for value in brief["unknowns"]))
        self.assertTrue(brief["unknown_evidence"])

    def test_non_object_and_string_codex_error_info_are_safe(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generating"}))
        events = [
            [],
            {"method":"error","params":"malformed"},
            {"type":"event_msg","payload":"malformed"},
            {"method": "error", "params": {"error": {
                "message": "stream closed", "codexErrorInfo": "responseStreamDisconnected",
            }, "willRetry": False}},
        ]
        (run / "codex-events.jsonl").write_text("\n".join(json.dumps(event) for event in events))
        brief = run_feedback.collect(run)
        self.assertEqual(brief["parse_error_count"], 3)
        self.assertEqual(brief["errors"][0]["category"], "codex:response_stream_disconnected")

    def test_braid_native_pi_and_codex_formats_are_scanned(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generation_failed", "failed_phase": "braid"}))
        native = run / "native"
        native.mkdir()
        pi = native / "pi.jsonl"
        pi.write_text(json.dumps({"type": "message", "message": {"role": "assistant",
                                                                        "stopReason": "error",
                                                                        "errorMessage": "Unterminated string"}}) + "\n")
        codex = native / "codex.jsonl"
        codex.write_text(json.dumps({"type": "event_msg", "payload": {"type": "error",
                                                                           "message": "stream disconnected",
                                                                           "will_retry": True}}) + "\n")
        entries = []
        for path, provider in ((pi, "pi"), (codex, "codex")):
            entries.append({"provider": provider, "native": str(path.relative_to(run)),
                            "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest()})
        (native / "manifest.json").write_text(json.dumps({"schema_version": 1, "sessions": entries}))
        brief = run_feedback.collect(run)
        self.assertEqual({entry["category"] for entry in brief["errors"]},
                         {"pi:json_parse", "codex:response_stream_disconnected"})

    def test_no_error_does_not_claim_health_and_interval_is_bounded(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generating"}))
        brief = run_feedback.collect(run)
        self.assertIn("未发现结构化错误；这不等于健康", brief["unknowns"])
        with self.assertRaises(ValueError):
            run_feedback.monitor(run, interval=179)
        with self.assertRaises(ValueError):
            run_feedback.watch(run, interval=179)

    def test_monitor_suppresses_unchanged_running_state(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generating"}))
        output = []
        with patch("builtins.print", side_effect=output.append):
            watcher = run_feedback._Monitor(run, 180)
            watcher._emit(run_feedback.collect(run))
            watcher._emit(run_feedback.collect(run))
        self.assertEqual(output, [])

    def test_monitor_persists_latest_brief(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generated", "variant": "pi", "task": "keep"}))
        watcher = run_feedback._Monitor(run, 180)
        with patch("builtins.print"):
            watcher.sample()
        saved = json.loads((run / "feedback.json").read_text())
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(saved["run_id"], run.name)

    def test_observer_failure_does_not_replace_experiment_error(self):
        with tempfile.TemporaryDirectory() as temp:
            original=RuntimeError('generation failed')
            with patch.object(run_feedback,'collect',side_effect=OSError('cannot read evidence')), \
                 patch('builtins.print') as printed:
                with self.assertRaises(RuntimeError) as raised:
                    with run_feedback.monitor(Path(temp)):
                        raise original
            self.assertIs(raised.exception,original)
            events=[json.loads(call.args[0]) for call in printed.call_args_list]
            self.assertEqual(len(events),1)
            self.assertEqual(events[0]['status'],'observer_error')

    def test_cli_watch_is_silent_for_seen_terminal_event(self):
        self.run = tempfile.TemporaryDirectory()
        self.addCleanup(self.run.cleanup)
        run = Path(self.run.name)
        (run / "run.json").write_text(json.dumps({"status": "generated"}))
        event_id = run_feedback.collect(run)["event_id"]
        output = io.StringIO()
        with patch("sys.argv", ["run_feedback.py", "watch", str(run), "--after-event", event_id]), \
             patch("sys.stdout", output):
            run_feedback.main()
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
