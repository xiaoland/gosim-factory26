"""Observable controller recovery boundaries; runner scores remain upstream-owned."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import local_runner


class LocalRunnerTest(unittest.TestCase):
    def test_prepare_is_reused_and_changed_package_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root/'agent.zip'; package.write_bytes(b'fixed')
            req = root/'requirements'; req.mkdir(); (req/'requirements.yaml').write_text('fixed')
            tests = root/'tests'; tests.mkdir()
            args = (root, package, req, tests, root/'run', 'keep')
            def capture(command, **kwargs):
                return local_runner.REVISION if command[-1] == 'HEAD' else ''
            with patch.object(local_runner.subprocess, 'check_output', side_effect=capture), \
                 patch.object(local_runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as execute:
                first = local_runner.execute(*args, prepare_only=True)
                self.assertEqual(first['phase'], 'prepared')
                self.assertEqual(local_runner.execute(*args, prepare_only=True), first)
                execute.assert_called_once()
                package.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'inputs changed'):
                    local_runner.execute(*args, prepare_only=True)
                execute.assert_called_once()

    def test_interrupted_execution_is_not_resampled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root/'agent.zip'; package.write_bytes(b'fixed')
            req = root/'req'; req.mkdir()
            tests = root/'tests'; tests.mkdir()
            args = (root, package, req, tests, root/'run', 'keep')
            with patch.object(local_runner.subprocess, 'check_output', side_effect=lambda cmd, **kw: local_runner.REVISION if cmd[-1]=='HEAD' else ''), \
                 patch.object(local_runner.subprocess, 'run', side_effect=KeyboardInterrupt) as execute:
                with self.assertRaises(KeyboardInterrupt):
                    local_runner.execute(*args, prepare_only=True)
                self.assertEqual(json.loads((root/'run/state.json').read_text())['phase'], 'unknown')
                with self.assertRaisesRegex(ValueError, 'explicit diagnosis'):
                    local_runner.execute(*args, prepare_only=True)
                execute.assert_called_once()
