"""实验终态、诊断收尾与低频观测的无模型检查。"""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import factory


class ExperimentTest(unittest.TestCase):
    def test_terminal_is_published_after_analysis_without_masking_original_result(self):
        cases=[('success',None,None),('generation',RuntimeError('stream failed'),RuntimeError('export failed')),
               ('evaluation',RuntimeError('SSH disconnected'),None),('generation',KeyboardInterrupt(),None),
               ('analysis',None,RuntimeError('export failed'))]
        for stage,error,analysis_error in cases:
            with self.subTest(stage=stage,error=type(error).__name__), tempfile.TemporaryDirectory() as temp:
                root=Path(temp); observed=[]; analyses=[]
                @contextmanager
                def monitor(run):
                    yield
                    observed.append(json.loads((run/'outcome.json').read_text()))
                def generate(config,run):
                    (run/'native').mkdir()
                    factory.save(run/'native/manifest.json',{'sessions':[]})
                    if stage=='generation': raise error
                    return run
                def evaluate(run,attempt):
                    self.assertEqual(attempt,'explicit-id')
                    if stage=='evaluation': raise error
                    return run/'evaluation'/attempt
                def analyze(run,source):
                    current=json.loads((run/'outcome.json').read_text())
                    self.assertEqual(current['status'],'running')
                    self.assertIsNone(current['finished_at'])
                    analyses.append(run)
                    if analysis_error: raise analysis_error
                with patch.object(factory,'ROOT',root), patch.object(factory,'generate',side_effect=generate), \
                     patch.object(factory,'evaluation_id',return_value='explicit-id'), \
                     patch.object(factory,'evaluate',side_effect=evaluate), patch.object(factory,'analyze',side_effect=analyze), \
                     patch.dict(sys.modules,{'run_feedback':types.SimpleNamespace(monitor=monitor)}):
                    if error:
                        with self.assertRaises(type(error)) as raised:
                            factory.run_experiment({'task':'keep','variant':'fake'})
                        self.assertIs(raised.exception,error)
                    else:
                        factory.run_experiment({'task':'keep','variant':'fake'})
                self.assertEqual(len(analyses),1)
                self.assertEqual(len(observed),1)
                result=observed[0]
                expected='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed' if error else 'completed'
                self.assertEqual(result['status'],expected)
                self.assertIsNotNone(result['finished_at'])
                self.assertEqual(result['analysis']['status'],'failed' if analysis_error else 'completed')
                if error:
                    self.assertEqual(result['failed_stage'],stage)
                    self.assertEqual(result['error']['type'],type(error).__name__)
                    if stage=='evaluation': self.assertEqual(result['evaluation_id'],'explicit-id')
                else:
                    self.assertIsNone(result['error'])
                    self.assertEqual(result['evaluation_id'],'explicit-id')

    def test_preflight_failure_has_result_even_without_native_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            from contextlib import nullcontext
            with patch.object(factory,'ROOT',Path(temp)), \
                 patch.object(factory,'generate',side_effect=RuntimeError('preflight failed')), \
                 patch.object(factory,'analyze') as analyze, \
                 patch.dict(sys.modules,{'run_feedback':types.SimpleNamespace(monitor=lambda _:nullcontext())}):
                with self.assertRaisesRegex(RuntimeError,'preflight failed'):
                    factory.run_experiment({'task':'keep'})
            result=json.loads(next(Path(temp).glob('runs/*/outcome.json')).read_text())
            self.assertEqual(result['status'],'failed')
            self.assertEqual(result['analysis']['status'],'unavailable')
            analyze.assert_not_called()

    def test_remote_observation_waits_three_minutes_but_exit_has_no_extra_delay(self):
        process=Mock(); observe=Mock()
        process.wait.side_effect=[subprocess.TimeoutExpired('ssh',180),0]
        self.assertEqual(factory.wait_for_remote(process,observe),0)
        self.assertEqual([call.kwargs['timeout'] for call in process.wait.call_args_list],[180,180])
        observe.assert_called_once_with()
        process=Mock();process.wait.return_value=1;observe=Mock()
        self.assertEqual(factory.wait_for_remote(process,observe),1)
        observe.assert_not_called()
