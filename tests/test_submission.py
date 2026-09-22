"""参赛运行边界；不调用模型或读取任何正式测试。"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import factory
import submission
import playground


def application(root):
    for directory, script in (('frontend', 'build'), ('backend', 'start')):
        (root/directory).mkdir(parents=True)
        (root/directory/'package.json').write_text(json.dumps({'scripts':{script:'node main.js'}}))


class SubmissionTest(unittest.TestCase):
    def test_platform_credentials_have_no_developer_fallback(self):
        config = {'backend':'pi', 'workflow':'braid', 'svc':True}
        with patch.object(factory, 'load_config', return_value=config), patch.dict(os.environ, {}, clear=True), \
             patch.object(factory, 'api_key', side_effect=AssertionError('不得读取个人 key')):
            with self.assertRaisesRegex(ValueError, '平台模型配置不完整'):
                submission.platform_config(Path('/unused'), {'backend':'pi'})
            os.environ.update(OPENAI_API_KEY='secret-main', OPENAI_BASE_URL='https://example.invalid/v1', MODEL='main')
            actual = submission.platform_config(Path('/unused'), {'backend':'pi'})
            self.assertEqual(submission.model_key(actual), 'secret-main')
            self.assertNotIn('secret-main', json.dumps(actual))
            # env.example includes a visual model name without visual credentials.
            os.environ['VISUAL_MODEL'] = 'vision'
            self.assertEqual(submission.platform_config(Path('/unused'), {'backend':'pi'})['model'], 'main')
            os.environ['VISUAL_API_KEY'] = 'secret-vision'
            with self.assertRaisesRegex(ValueError, '平台模型配置不完整'):
                submission.platform_config(Path('/unused'), {'backend':'pi'})
            os.environ['VISUAL_BASE_URL'] = 'https://example.invalid/vision'
            actual = submission.platform_config(Path('/unused'), {'backend':'codex'})
            self.assertEqual((actual['backend'],actual['model'],actual['image_input']), ('codex','main',False))
            self.assertEqual(submission.model_key(actual), 'secret-main')
            self.assertEqual(submission.model_key(actual, visual=True), 'secret-vision')
            self.assertEqual(actual['visual_base_url'], 'https://example.invalid/vision')
            self.assertNotIn('secret-vision', json.dumps(actual))

    def test_frozen_variant_rejects_platform_model_substitution(self):
        config = {'backend':'pi', 'workflow':'braid', 'svc':True, 'model':'text',
                  'effective': {'profiles': {'p': {'roles': {'vision': {'provider':'visual','model':'vision'}}}}}}
        env = {'OPENAI_API_KEY':'main-key','OPENAI_BASE_URL':'https://example.invalid/v1','MODEL':'other'}
        with patch.object(factory, 'load_config', side_effect=lambda *args: dict(config)), patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, '主模型与冻结'):
                submission.platform_config(Path('/unused'), {'backend':'pi'})
            os.environ.update(MODEL='text', VISUAL_API_KEY='vision-key', VISUAL_BASE_URL='https://vision.invalid/v1', VISUAL_MODEL='wrong')
            with self.assertRaisesRegex(ValueError, '视觉模型与冻结'):
                submission.platform_config(Path('/unused'), {'backend':'pi'})
            os.environ['VISUAL_MODEL']='vision'
            actual = submission.platform_config(Path('/unused'), {'backend':'pi'})
            with tempfile.TemporaryDirectory() as temp:
                runtime = submission.adapter_environment(actual, Path(temp))
                self.assertEqual(runtime['FACTORY26_API_KEY'], 'main-key')
                self.assertEqual(runtime['FACTORY26_VISUAL_API_KEY'], 'vision-key')

    def test_upload_cannot_be_mistaken_for_official_evaluation(self):
        with patch.object(playground.Client, 'request', side_effect=AssertionError('不能发请求')):
            with self.assertRaisesRegex(ValueError, '--practice'):
                playground.submit(playground.Client(), Path('/missing.zip'), 'task', 'name')

    def test_adapter_receives_only_selected_credentials_and_private_home(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ,
                {'OPENAI_API_KEY':'unused','VISUAL_API_KEY':'selected','OTHER_SECRET':'not-for-adapter'},clear=True):
            env=submission.adapter_environment({'key_environment':'VISUAL_API_KEY'},Path(temp))
            self.assertEqual(env['FACTORY26_API_KEY'],'selected')
            self.assertTrue(Path(env['HOME']).is_relative_to(Path(temp)))
            for name in ('OPENAI_API_KEY','VISUAL_API_KEY','OTHER_SECRET'):
                self.assertNotIn(name,env)

    def test_practice_mutations_reject_unknown_ids_before_network(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(playground,'ROOT',Path(temp)), \
             patch.object(playground.Client,'request',side_effect=AssertionError('拒绝前不能发请求')):
            for arguments in (['run','--submission','unknown','--requirement','keep'], ['start','unknown'], ['cancel','unknown']):
                with self.subTest(arguments=arguments), patch.object(sys,'argv',['playground.py']+arguments):
                    with self.assertRaisesRegex(ValueError,'未知或正式'):
                        playground.main()
            directory=Path(temp)/'runs/playground/saved';directory.mkdir(parents=True)
            (directory/'submission.json').write_text(json.dumps({'submission_id':'known','run_id':'run',
                                                                'submission_kind':'practice'}))
            self.assertEqual(playground.practice_record(submission_id='known')['run_id'],'run')
            self.assertEqual(playground.practice_record(run_id='run')['submission_id'],'known')

    def test_delivery_preserves_platform_files_and_rejects_invalid_app(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app = root/'app'; output = root/'output'
            application(app); output.mkdir()
            for name in submission.RESERVED:
                (output/name).mkdir(); (output/name/'sentinel').write_text(name)
            submission.deliver(app, output)
            for name in submission.RESERVED:
                self.assertEqual((output/name/'sentinel').read_text(), name)
            with self.assertRaisesRegex(ValueError, '拒绝覆盖'):
                submission.deliver(app, output)
            (app/'deploy.sh').write_text('exit 0')
            with self.assertRaisesRegex(ValueError, 'deploy.sh'):
                submission.validate_application(app)
            (app/'deploy.sh').unlink()
            (app/'backend/package.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'start'):
                submission.validate_application(app)

    def test_manifest_rejects_changed_or_extra_payload_and_restores_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); tool = root/'tool'; tool.write_text('tool'); tool.chmod(0o600)
            manifest = {'schema_version':1,'platform':'linux-x86_64','python':'3.12',
                        'files':{'tool':{'sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),'executable':True}}}
            (root/'package-manifest.json').write_text(json.dumps(manifest))
            with patch.object(submission.platform, 'system', return_value='Linux'), \
                 patch.object(submission.platform, 'machine', return_value='x86_64'), \
                 patch.object(submission.sys, 'version_info', (3,12)):
                submission.verify_package(root)
                self.assertTrue(tool.stat().st_mode & 0o111)
                (root/'answer.txt').write_text('unlisted')
                with self.assertRaisesRegex(ValueError, '未登记'):
                    submission.verify_package(root)
                (root/'answer.txt').unlink(); tool.write_text('changed')
                with self.assertRaisesRegex(ValueError, '哈希'):
                    submission.verify_package(root)

    def test_new_contract_does_not_rewrite_legacy_contract(self):
        self.assertIn('/api/health', factory.application_contract({}))
        self.assertIn('frontend/package.json', factory.application_contract({'deployment':'arcbench'}))

    def test_arcbench_evaluator_builds_frontend_before_starting_backend(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp); app=run/'application'; application(app)
            calls=[]
            def logged(command,cwd,env,log):
                calls.append((command,Path(cwd).name))
                if log.name=='discovery.log':
                    (log.parent/'listed.json').write_text(json.dumps({'suites':[{'specs':[{'id':'one','tests':[{'projectId':'chromium'}]}]}]}))
                if log.name=='test.log':
                    report={'stats':{'expected':1,'unexpected':0,'flaky':0,'skipped':0,'duration':1},
                            'suites':[{'specs':[{'id':'one','tests':[{'projectId':'chromium','results':[{'status':'passed'}]}]}]}]}
                    (log.parent/'results.json').write_text(json.dumps(report))
                return 0
            process=Mock(); process.poll.return_value=None
            response=Mock(); response.__enter__=Mock(return_value=response); response.__exit__=Mock(return_value=False); response.status=200
            with patch.object(factory,'validate_snapshot',return_value={'benchmark_revision':'fixed','task':'keep','deployment':'arcbench'}), \
                 patch.object(factory.platform,'platform',return_value='test-platform'), \
                 patch.object(factory,'capture',side_effect=['fixed','','node-version']), \
                 patch.object(factory,'logged',side_effect=logged), \
                 patch.object(factory.subprocess,'Popen',return_value=process) as start, \
                 patch.object(factory.urllib.request,'urlopen',return_value=response) as health, \
                 patch.object(factory,'stop'):
                result=factory.evaluate(run)
            self.assertEqual([cwd for _,cwd in calls[:3]],['frontend','frontend','backend'])
            self.assertEqual(calls[1][0],['npm','run','build'])
            self.assertEqual(start.call_args.kwargs['cwd'].name,'backend')
            self.assertEqual(start.call_args.kwargs['env']['HOST'],'0.0.0.0')
            self.assertTrue(health.call_args.args[0].endswith('/'))
            self.assertEqual(json.loads((result/'summary.json').read_text())['test_timeout_ms'],10000)

if __name__ == '__main__':
    unittest.main()
