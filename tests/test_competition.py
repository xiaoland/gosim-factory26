"""Competition observable boundaries, without network or model requests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import competition


TASKS = ['arc-bench-lite--keep', 'arc-bench-lite--bookstack']


class FakeCompetition:
    def __init__(self, directory):
        self.directory = directory
        self.calls = []
        self.snapshots = []
        self.runs = {}
        self.lose_response = None
        self.log_cursors = []

    def request(self, path, method='GET', **kwargs):
        self.calls.append((method, path))
        if method == 'POST':
            journal = json.loads((self.directory/'state.json').read_text())
            assert journal['pending']['path'] == path
            if path == '/submissions':
                assert kwargs['fields']['catalog'] == 'competition'
                assert kwargs['fields']['competition_id'] == 'arc-bench-lite'
                assert 'api_key' not in kwargs['fields']
                assert kwargs['secret'] == 'secret-not-for-journal'
                item = {'id': 'snapshot-1', 'task_scores': []}
                self.snapshots.append(item)
                value = {'submission': {'id': item['id'], 'api_key': kwargs['secret']}}
            elif path == '/runs':
                fields = kwargs['fields']
                run_id = 'run-'+str(len(self.runs)+1)
                self.runs[run_id] = {'id': run_id, **fields, 'status': 'PENDING'}
                self.snapshots[-1]['task_scores'].append({'task_id': fields['requirement_id'], 'run_id': run_id})
                value = {'run': {'id': run_id}}
            elif path.endswith('/start'):
                self.runs[path.split('/')[2]]['status'] = 'PASSED'
                value = {'ok': True}
            else:
                raise AssertionError(path)
            if self.lose_response == path:
                self.lose_response = None
                raise RuntimeError('transport failed with secret-not-for-journal')
            return value
        if path == '/competitions/arc-bench-lite':
            return {'id': 'arc-bench-lite', 'template_required': False, 'tasks': [{'id': task} for task in TASKS]}
        if path.endswith('/submissions'):
            return self.snapshots
        if '/logs?' in path:
            self.log_cursors.append(path)
            return {'log_offset': 7, 'last_event_id': 'event-7', 'stdout': 'line', 'runner_events': []}
        if '/traceability?' in path:
            return {'interfaces': [], 'tests': []}
        if path.endswith('/commit-history'):
            return {'commits': []}
        if path.startswith('/runs/'):
            return self.runs[path.split('/')[2]]
        raise AssertionError((method, path))


class CompetitionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root/'state'
        self.package = self.root/'fixture.zip'
        payload = {'main.py': b'print("fixture")\n', 'requirements.txt': b''}
        manifest = {'schema_version': 1, 'platform': 'linux-x86_64', 'python': '3.12',
                    'backend': 'pi', 'sources': {}, 'capabilities': {'variant': 'pi-team-mixed'},
                    'files': {name: {'sha256': hashlib.sha256(data).hexdigest(), 'executable': False}
                              for name, data in payload.items()}}
        with ZipFile(self.package, 'w') as archive:
            for name, data in payload.items():
                archive.writestr(name, data)
            archive.writestr('package-manifest.json', json.dumps(manifest))
        self.inputs = competition.prepare(self.directory, self.package, competition_id='arc-bench-lite',
            variant='pi-team-mixed', tasks=TASKS, model_config={'base_url': 'https://example.invalid/v1', 'model': 'test'})
        self.client = FakeCompetition(self.directory)

    def controller(self):
        return competition.Controller(self.directory, self.client, secret='secret-not-for-journal',
                                      lock_root=self.root/'locks')

    def posts(self):
        return [path for method, path in self.client.calls if method == 'POST']

    def test_single_snapshot_two_tasks_resume_without_repeating_terminal_runs(self):
        original = self.package.read_bytes()
        self.package.write_bytes(b'caller later replaced source')
        with self.controller() as controller:
            result = controller.run_all()
        self.assertEqual((self.directory/'agent.zip').read_bytes(), original)
        self.assertEqual(result['phase'], 'collected')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['score_status'], 'unavailable')
        self.assertEqual(self.posts(), ['/submissions', '/runs', '/runs/run-1/start', '/runs', '/runs/run-2/start'])
        with self.controller() as controller:
            controller.run_all()
        self.assertEqual(len(self.posts()), 5)
        for task in TASKS:
            self.assertTrue((self.directory/'tasks'/task/'traceability.json').is_file())
            self.assertEqual(result['tasks'][task]['phase'], 'collected')
        for path in self.directory.rglob('*.json'):
            self.assertNotIn('secret-not-for-journal', path.read_text())

    def test_http_rejection_retains_safe_details_without_retrying(self):
        original = self.client.request
        def rejected(path, method='GET', **kwargs):
            if method == 'POST':
                self.client.calls.append((method, path))
                raise competition.ApiError(413, {'detail': 'too large: secret-not-for-journal',
                                                 'api_key': 'private'})
            return original(path, method, **kwargs)
        with self.controller() as controller:
            with patch.object(self.client, 'request', side_effect=rejected):
                with self.assertRaises(competition.Blocked):
                    controller.snapshot()
            pending = json.loads((self.directory/'state.json').read_text())['pending']
            self.assertEqual(pending['http_status'], 413)
            self.assertEqual(pending['error_detail'],
                             {'detail': 'too large: [redacted]', 'api_key': '[redacted]'})
            with self.assertRaises(competition.Blocked):
                controller.run_all()
        self.assertEqual(self.posts(), ['/submissions'])

    def test_unknown_snapshot_never_reuploads_without_hash_evidence(self):
        self.client.lose_response = '/submissions'
        with self.controller() as controller:
            with self.assertRaises(competition.Blocked):
                controller.snapshot()
        with self.controller() as controller:
            with self.assertRaisesRegex(competition.Blocked, 'package hash'):
                controller.run_all()
            self.client.snapshots[0]['package_sha256'] = self.inputs['package_sha256']
            controller.recover()
            self.assertEqual(controller.state['submission_id'], 'snapshot-1')
        self.assertEqual(self.posts(), ['/submissions'])

    def test_unknown_create_recovers_unique_history_run_then_starts_once(self):
        with self.controller() as controller:
            controller.snapshot()
            self.client.lose_response = '/runs'
            with self.assertRaises(competition.Blocked):
                controller.create(TASKS[0])
        with self.controller() as controller:
            controller.run_all()
        self.assertEqual(self.posts().count('/runs'), 2)
        self.assertEqual(self.posts().count('/runs/run-1/start'), 1)

    def test_unknown_create_wrong_explicit_run_cannot_bind(self):
        with self.controller() as controller:
            controller.snapshot()
            self.client.lose_response = '/runs'
            with self.assertRaises(competition.Blocked):
                controller.create(TASKS[0])
            self.client.runs['run-1']['submission_id'] = 'other'
            with self.assertRaisesRegex(competition.Blocked, 'snapshot/task'):
                controller.recover(run_id='run-1')
            self.assertIsNotNone(controller.state['pending'])
            self.assertEqual(controller.summary()['status'], 'blocked')

    def test_unknown_start_pending_is_not_proof_and_never_restarts(self):
        with self.controller() as controller:
            controller.snapshot()
            controller.create(TASKS[0])
            self.client.lose_response = '/runs/run-1/start'
            with self.assertRaises(competition.Blocked):
                controller.start(TASKS[0])
            self.client.runs['run-1']['status'] = 'PENDING'
            with self.assertRaisesRegex(competition.Blocked, '已启动证据'):
                controller.recover()
            self.client.runs['run-1']['status'] = 'PASSED'
            controller.recover()
            controller.run_all()
        self.assertEqual(self.posts().count('/runs/run-1/start'), 1)

    def test_saved_response_recovers_after_local_apply_interruption(self):
        with self.controller() as controller:
            with patch.object(controller, '_apply_receipt', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    controller.snapshot()
        with self.controller() as controller:
            self.assertEqual(controller.state['submission_id'], 'snapshot-1')
            self.assertIsNone(controller.state['pending'])
        self.assertEqual(self.posts(), ['/submissions'])

    def test_malformed_success_response_remains_recoverable_without_reposting(self):
        original = self.client.request
        def missing_id(path, method='GET', **kwargs):
            value = original(path, method, **kwargs)
            return {} if method == 'POST' else value
        with self.controller() as controller:
            with patch.object(self.client, 'request', side_effect=missing_id):
                with self.assertRaises(competition.Blocked):
                    controller.snapshot()
        self.client.snapshots[0]['package_sha256'] = self.inputs['package_sha256']
        with self.controller() as controller:
            controller.recover()
            self.assertEqual(controller.state['submission_id'], 'snapshot-1')
        self.assertEqual(self.posts(), ['/submissions'])

    def test_terminal_with_missing_artifact_is_not_complete_or_rerun(self):
        original = self.client.request
        def missing_artifact(path, method='GET', **kwargs):
            if path.endswith('/commit-history'):
                raise RuntimeError('unavailable')
            return original(path, method, **kwargs)
        with self.controller() as controller:
            with patch.object(self.client, 'request', side_effect=missing_artifact):
                with self.assertRaises(competition.Blocked):
                    controller.run_all()
            self.assertEqual(controller.summary()['status'], 'blocked')
            controller.run_all()
        self.assertEqual(self.posts().count('/runs/run-1/start'), 1)

    def test_unknown_status_stops_watch_without_claiming_terminal(self):
        with self.controller() as controller:
            controller.snapshot()
            controller.create(TASKS[0])
            controller.start(TASKS[0])
            self.client.runs['run-1']['status'] = 'FUTURE_STATE'
            with patch.object(competition.time, 'sleep', side_effect=AssertionError('must stop')):
                with self.assertRaisesRegex(competition.Blocked, '未知'):
                    controller.watch(TASKS[0])
            self.assertEqual(controller.state['tasks'][TASKS[0]]['observation'], 'unknown')
            self.assertNotIn(controller.state['tasks'][TASKS[0]]['phase'], {'terminal', 'collected'})

    def test_cursor_publish_failure_replays_same_chunk_without_data_loss(self):
        with self.controller() as controller:
            controller.snapshot()
            controller.create(TASKS[0])
            original = competition.atomic_json
            def fail_cursor(path, value):
                if Path(path).name == 'log-cursor.json':
                    raise OSError('disk full')
                original(path, value)
            with patch.object(competition, 'atomic_json', side_effect=fail_cursor):
                with self.assertRaises(OSError):
                    controller.logs(TASKS[0])
            controller.logs(TASKS[0])
        self.assertEqual(self.client.log_cursors[0], self.client.log_cursors[1])
        self.assertEqual(len(list((self.directory/'tasks'/TASKS[0]/'logs').glob('*.json'))), 1)
        cursor = json.loads((self.directory/'tasks'/TASKS[0]/'log-cursor.json').read_text())
        self.assertEqual(cursor, {'log_offset': 7, 'after_event_id': 'event-7'})

    def test_superseded_snapshot_cannot_create_second_task(self):
        with self.controller() as controller:
            controller.snapshot()
            self.client.snapshots = [{'id': 'newer', 'is_latest': True}]
            with self.assertRaisesRegex(competition.Blocked, '最新'):
                controller.create(TASKS[0])
        self.assertEqual(self.posts(), ['/submissions'])

    def test_unfinished_previous_variant_blocks_new_snapshot(self):
        self.client.snapshots = [{'id': 'older', 'task_scores': []}]
        with self.controller() as controller:
            with self.assertRaisesRegex(competition.Blocked, '上一个 snapshot'):
                controller.snapshot()
        self.assertEqual(self.posts(), [])

    def test_controller_lock_and_package_identity_prevent_competing_writes(self):
        with self.controller():
            with self.assertRaises(competition.Blocked):
                with self.controller():
                    pass
        frozen = self.directory/'agent.zip'
        frozen.chmod(0o600)
        frozen.write_bytes(b'changed')
        with self.assertRaisesRegex(competition.Blocked, 'identity'):
            with self.controller():
                pass
        self.assertEqual(self.posts(), [])

    def test_watch_interval_and_manifest_checks_happen_before_network(self):
        with self.controller() as controller:
            with self.assertRaises(ValueError):
                controller.run_all(interval=1)
        self.assertEqual(self.client.calls, [])
        broken = self.root/'broken.zip'
        with ZipFile(broken, 'w') as archive:
            archive.writestr('../main.py', '')
        with self.assertRaises(ValueError):
            competition.package_identity(broken)

    def test_prepare_resume_reuses_exact_inputs_and_rejects_changed_contract(self):
        options = dict(competition_id='arc-bench-lite', variant='pi-team-mixed', tasks=TASKS,
                       model_config={'base_url': 'https://example.invalid/v1', 'model': 'test'})
        before = {p: p.read_bytes() for p in self.directory.iterdir() if p.is_file()}
        self.assertEqual(competition.prepare(self.directory, self.package, **options), self.inputs)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        options['tasks'] = TASKS[:1]
        with self.assertRaises(competition.Blocked):
            competition.prepare(self.directory, self.package, **options)

    def test_score_requires_observed_full_counts_and_numeric_score(self):
        with self.controller() as controller:
            controller.run_all()
            for item in controller.state['tasks'].values():
                item.update(remote_status='FAILED', platform_result={'score': 0, 'passed_count': 0,
                            'failed_count': 32, 'total_tests': 32})
            self.assertEqual(controller.summary()['score_status'], 'complete')
            controller.state['tasks'][TASKS[0]]['platform_result']['score'] = None
            self.assertEqual(controller.summary()['score_status'], 'unavailable')
            controller.state['tasks'][TASKS[0]]['platform_result'] = {'score': 0}
            self.assertEqual(controller.summary()['score_status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
