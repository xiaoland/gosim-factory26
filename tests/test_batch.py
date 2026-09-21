import contextlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import batch


class BatchTest(unittest.TestCase):
    def manifest(self, root, **changes):
        value = {
            'benchmark_url': 'unused', 'benchmark_revision': 'rev',
            'variants': ['pi-generalist', 'pi-team', 'codex-generalist', 'pi-verification'],
            'tasks': ['keep', 'bookstack'], 'generation_workers': 2,
            'evaluation_workers': 4, 'deployment': 'arcbench',
        }
        value.update(changes)
        path = root / 'manifest.json'
        path.write_text(json.dumps(value))
        return path

    def config(self, variant, task):
        return {'backend': 'pi', 'task': task, 'variant': variant, 'benchmark_revision': 'rev'}

    def run_execute(self, manifest, directory, generate, evaluate):
        with patch.object(batch.profiles, 'configuration', side_effect=self.config), \
             patch.object(batch.sources, 'require_build', return_value={'revision': 'source'}), \
             patch.object(batch, 'generate', side_effect=generate), \
             patch.object(batch, 'evaluate', side_effect=evaluate):
            return batch.execute(manifest, directory)

    def test_fixed_capacities_and_eight_jobs_have_bounded_parallelism(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            manifest = self.manifest(root)
            directory = root / 'batch'
            lock = threading.Lock()
            generation_barrier = threading.Barrier(2)
            evaluation_barrier = threading.Barrier(4)
            active_generation = active_evaluation = 0
            max_generation = max_evaluation = 0
            generation_calls = evaluation_calls = 0

            def generate(job, _directory):
                nonlocal active_generation, max_generation, generation_calls
                with lock:
                    generation_calls += 1
                    active_generation += 1
                    max_generation = max(max_generation, active_generation)
                generation_barrier.wait(timeout=2)
                with lock:
                    active_generation -= 1
                return {'status': 'generated'}

            def evaluate(job, _directory):
                nonlocal active_evaluation, max_evaluation, evaluation_calls
                with lock:
                    evaluation_calls += 1
                    active_evaluation += 1
                    max_evaluation = max(max_evaluation, active_evaluation)
                evaluation_barrier.wait(timeout=2)
                with lock:
                    active_evaluation -= 1
                return {'status': 'completed'}

            state = self.run_execute(manifest, directory, generate, evaluate)
            self.assertEqual(state['status'], 'completed')
            self.assertEqual(generation_calls, 8)
            self.assertEqual(evaluation_calls, 8)
            self.assertLessEqual(max_generation, 2)
            self.assertLessEqual(max_evaluation, 4)
            self.assertEqual({row['status'] for row in state['jobs'].values()}, {'completed'})

    def test_generation_failure_pauses_new_work_but_inflight_generation_is_evaluated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            manifest = self.manifest(root)
            first_two = threading.Barrier(2)

            def generate(job, _directory):
                first_two.wait(timeout=2)
                return {'status': 'failed', 'pause_queue': True} if job['run_id'] == 'pi-generalist-keep' else {'status': 'generated'}

            state = self.run_execute(manifest, root / 'batch', generate,
                                     lambda job, _directory: {'status': 'completed'})
            statuses = [row['status'] for row in state['jobs'].values()]
            self.assertEqual(state['status'], 'paused')
            self.assertIn('failed', statuses)
            self.assertIn('completed', statuses)
            self.assertEqual(statuses.count('queued'), 6)

    def test_terminal_jobs_are_not_rerun_and_interrupted_writer_blocks_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            manifest = self.manifest(root)
            directory = root / 'batch'
            initial = self.run_execute(manifest, directory,
                                       lambda job, _directory: {'status': 'generated'},
                                       lambda job, _directory: {'status': 'completed'})
            self.assertEqual(initial['status'], 'completed')
            calls = []
            resumed = self.run_execute(manifest, directory,
                                       lambda job, _directory: calls.append(job['run_id']) or {'status': 'generated'},
                                       lambda job, _directory: calls.append(job['run_id']) or {'status': 'completed'})
            self.assertEqual(resumed['status'], 'completed')
            self.assertEqual(calls, [])
            state_path = directory / 'batch.json'
            saved = json.loads(state_path.read_text())
            saved['jobs']['pi-team-keep']['status'] = 'generating'
            state_path.write_text(json.dumps(saved))
            blocked = self.run_execute(manifest, directory,
                                       lambda job, _directory: calls.append(job['run_id']) or {'status': 'generated'},
                                       lambda job, _directory: calls.append(job['run_id']) or {'status': 'completed'})
            self.assertEqual(blocked['status'], 'blocked')
            self.assertEqual(blocked['jobs']['pi-team-keep']['status'], 'unknown')
            self.assertEqual(calls, [])

    def test_frozen_inputs_and_capacity_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            too_many = self.manifest(root, generation_workers=3)
            with patch.object(batch.profiles, 'configuration', side_effect=self.config), \
                 patch.object(batch.sources, 'require_build', return_value={'revision': 'source'}):
                with self.assertRaisesRegex(ValueError, 'generation_workers'):
                    batch.execute(too_many, root / 'too-many')
            manifest = self.manifest(root)
            self.run_execute(manifest, root / 'batch',
                             lambda job, _directory: {'status': 'generated'},
                             lambda job, _directory: {'status': 'completed'})
            changed = json.loads(manifest.read_text())
            changed['deployment'] = 'changed'
            manifest.write_text(json.dumps(changed))
            with patch.object(batch.profiles, 'configuration', side_effect=self.config), \
                 patch.object(batch.sources, 'require_build', return_value={'revision': 'source'}):
                with self.assertRaisesRegex(ValueError, 'batch inputs changed'):
                    batch.execute(manifest, root / 'batch')

    def test_generation_error_runs_analysis_before_terminal_status(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            job = {'run_id': 'example', 'variant': 'pi-generalist', 'task': 'keep',
                   'config': {'backend': 'pi'}}
            calls = []

            @contextlib.contextmanager
            def no_monitor(_run):
                yield

            def fail_generate(_config, run):
                (run / 'native').mkdir()
                (run / 'native' / 'manifest.json').write_text('{"sessions": []}')
                calls.append('generate')
                raise RuntimeError('generation failed')

            def analyze(_run):
                calls.append('analyze')

            with patch.object(batch, 'monitor', no_monitor), \
                 patch.object(batch.factory, 'generate', side_effect=fail_generate), \
                 patch.object(batch.factory, 'analyze', side_effect=analyze), \
                 patch.object(batch, 'collect', return_value={'status': 'failed'}):
                result = batch.generate(job, root)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(calls, ['generate', 'analyze'])


if __name__ == '__main__':
    unittest.main()
