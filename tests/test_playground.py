"""Playground 的凭据、失败恢复信息与增量日志边界。"""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import playground


class PlaygroundTest(unittest.TestCase):
    def test_events_separate_heartbeat_progress_terminal_and_observation_age(self):
        progress = {'event_id': 'progress', 'timestamp': '2026-09-20 08:00:00', 'stage': 'Evaluating result', 'status': 'info', 'summary': 'Playwright started', 'heartbeat': False}
        heartbeat = {'event_id': 'heartbeat', 'timestamp': '2026-09-20 08:05:00', 'stage': 'Evaluating result', 'status': 'info', 'summary': 'Test progress 0/135', 'heartbeat': True}
        value = {'id': 'example', 'status': 'RUNNING', 'test_pass_rate': 0}
        observation = {'status': {'observed_at': 990}, 'logs': {'observed_at': 800}}
        result = playground.summary(value, events=[heartbeat, progress, heartbeat], observation=observation, traceability={'interfaces': [], 'tests': []}, now=1000)
        self.assertFalse(result['terminal'])
        self.assertEqual(result['last_progress_event']['event_id'], 'progress')
        self.assertEqual(result['last_heartbeat']['event_id'], 'heartbeat')
        self.assertEqual(result['last_progress_event']['timestamp'], progress['timestamp'])
        self.assertEqual(result['observation']['status']['freshness'], 'fresh')
        self.assertEqual(result['observation']['logs']['freshness'], 'stale')
        self.assertEqual(result['traceability']['status'], 'empty')
        self.assertNotIn('test_pass_rate', result)
        value['status'] = 'FAILED'
        result = playground.summary(value, events=[progress, heartbeat], observation={}, now=1000)
        self.assertTrue(result['terminal'])
        self.assertEqual(result['observation']['status']['freshness'], 'unknown')
        self.assertEqual(result['traceability']['status'], 'unavailable')

    def test_saved_status_is_read_only_and_preserves_explicit_link_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root/'runs/playground/example'
            (folder/'logs').mkdir(parents=True)
            (folder/'status.json').write_text(json.dumps({'id': 'example', 'status': 'FAILED'}))
            (folder/'traceability.json').write_text(json.dumps({'interfaces': [{'req_ids': ['REQ-1'], 'file_path': 'app.py', 'first_line': '10'}], 'tests': [], 'producer': 'agent-sdk', 'version': '1'}))
            (folder/'logs/one.json').write_text(json.dumps({'log_offset': 10, 'stdout': 'Do not display full stdout', 'runner_events': []}))
            before = {str(path): path.read_bytes() for path in folder.rglob('*') if path.is_file()}
            output = io.StringIO()
            with patch.object(playground, 'ROOT', root), patch.object(sys, 'argv', ['playground.py', 'status', 'example', '--saved']), patch.object(sys, 'stdout', output), patch.object(playground.Client, 'request', side_effect=AssertionError('离线重放不能联网')):
                playground.main()
            result = json.loads(output.getvalue())
            self.assertEqual(result['traceability']['status'], 'available')
            self.assertEqual(result['traceability']['producer'], 'agent-sdk')
            self.assertEqual(result['traceability']['version'], '1')
            self.assertEqual(result['traceability']['source'], str(folder/'traceability.json'))
            self.assertEqual(result['traceability']['kind'], 'explicit_links_not_causal_trace')
            self.assertEqual(result['observation']['status']['freshness'], 'unknown')
            self.assertNotIn('Do not display full stdout', output.getvalue())
            self.assertEqual(before, {str(path): path.read_bytes() for path in folder.rglob('*') if path.is_file()})

    def test_status_rejects_wrong_run_and_records_local_observation_only_on_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = playground.Client()
            with patch.object(playground, 'ROOT', root), patch.object(client, 'request', return_value={'id': 'other', 'status': 'PASSED'}):
                with self.assertRaisesRegex(ValueError, 'run ID'):
                    playground.status(client, 'example')
            self.assertFalse((root/'runs/playground/example/status.json').exists())
            with patch.object(playground, 'ROOT', root), patch.object(client, 'request', return_value={'id': 'example', 'status': 'RUNNING'}), patch.object(playground.time, 'time', return_value=123):
                playground.status(client, 'example')
            observation = json.loads((root/'runs/playground/example/observation.json').read_text())
            self.assertEqual(observation['status']['observed_at'], 123)
            self.assertEqual(observation['status']['source'], playground.API+'/runs/example')
            self.assertEqual(json.loads((root/'runs/playground/example/status.json').read_text()), {'id': 'example', 'status': 'RUNNING'})

    def test_watch_collects_and_exits_on_observed_passed_status(self):
        value={'id':'example','status':'PASSED','passed_count':1,'failed_count':0,'test_pass_rate':1}
        with patch.object(sys,'argv',['playground.py','watch','example']), \
             patch.object(playground,'status',return_value=value) as status, \
             patch.object(playground,'logs'), \
             patch.object(playground,'collect',return_value=value) as collect, \
             patch.object(playground.time,'sleep',side_effect=AssertionError('terminal status must exit')):
            playground.main()
        status.assert_called_once()
        collect.assert_called_once()
        self.assertEqual(playground.summary(value)['test_pass_rate'],1)

    def test_terminal_summary_uses_timestamps_instead_of_broken_platform_duration(self):
        value={'status':'FAILED','run_duration_seconds':0,'started_at':'2026-09-20T08:20:00',
               'finished_at':'2026-09-20T08:20:34.5','tests':[{'status':'timedOut'},{'status':'timedOut'}]}
        brief=playground.summary(value)
        self.assertEqual(brief['elapsed_seconds'],34.5)
        self.assertEqual(brief['test_status_counts'],{'timedOut':2})
        self.assertNotIn('run_duration_seconds',brief)
        self.assertNotIn('test_pass_rate',brief)
        self.assertEqual(value['run_duration_seconds'],0)

    def test_credentials_use_private_files_or_stdin_and_http_failure_is_explicit(self):
        secret='test-secret-never-in-argv'
        def curl(command, input=None, capture_output=False):
            self.assertNotIn(secret,str(command))
            output=Path(command[command.index('--output')+1])
            output.write_text('{"api_key":"not-for-output"}')
            fields=[v for v in command if v.startswith('api_key=<')]
            if fields:
                key=Path(fields[0].split('<',1)[1])
                self.assertEqual(key.read_text(),secret)
                self.assertEqual(key.stat().st_mode & 0o777,0o600)
            else:
                self.assertEqual(json.loads(input)['password'],secret)
            return subprocess.CompletedProcess(command,0,stdout=b'401',stderr=b'')
        with patch.object(playground.subprocess,'run',side_effect=curl):
            for payload in ({'body':{'password':secret}},{'fields':{},'secret':secret}):
                with self.assertRaises(playground.ApiError) as failure:
                    playground.Client().request('/auth/login','POST',**payload)
                self.assertEqual(failure.exception.status,401)
                self.assertNotIn('not-for-output',str(failure.exception))

    def test_uncertain_create_run_does_not_reupload_or_discard_submission_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); variant=root/'variants/pi-svc';variant.mkdir(parents=True)
            (variant/'config.json').write_text('{"model":"test","base_url":"https://example.invalid"}')
            package=root/'probe.zip'
            with ZipFile(package,'w') as z:
                z.writestr('main.py','');z.writestr('requirements.txt','')
            client=playground.Client()
            with patch.object(playground,'ROOT',root), patch.object(client,'request',side_effect=[{'submission':{'id':'uploaded'}},RuntimeError('uncertain')]) as request:
                with self.assertRaisesRegex(RuntimeError,'uncertain'):
                    playground.submit(client,package,'keep','test','pi-svc',offline=True)
                self.assertEqual(request.call_count,2)
            manifest=json.loads(next(root.glob('runs/playground/upload-*/submission.json')).read_text())
            self.assertEqual(manifest['submission_id'],'uploaded')
            self.assertEqual(manifest['phase'],'create_run')
            self.assertNotIn('api_key',manifest)

    def test_cursor_advances_after_chunk_is_saved_and_heartbeat_is_not_progress(self):
        with tempfile.TemporaryDirectory() as temp:
            client=playground.Client()
            value={'log_offset':12,'last_event_id':'event-1','stdout':'hello','runner_events':[]}
            with patch.object(playground,'ROOT',Path(temp)), patch.object(client,'request',return_value=value):
                playground.logs(client,'example')
                folder=playground.output_dir('example')
                self.assertEqual(json.loads((folder/'log-cursor.json').read_text())['log_offset'],12)
                self.assertEqual(json.loads(next((folder/'logs').glob('*.json')).read_text())['stdout'],'hello')
                with patch.object(playground,'save',side_effect=OSError('disk full')):
                    with self.assertRaises(OSError): playground.logs(client,'example')
                self.assertEqual(json.loads((folder/'log-cursor.json').read_text())['log_offset'],12)
            brief=playground.summary({'status':'RUNNING','test_pass_rate':0,'steps':[{'key':'run_tests','status':'running','logs':['Test progress 0/1','Still working: Test progress 0/1']}]})
            self.assertEqual(brief['progress'],'Test progress 0/1')
            self.assertNotIn('test_pass_rate',brief)


if __name__=='__main__':
    unittest.main()
