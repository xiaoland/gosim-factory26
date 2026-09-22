"""验证实验边界，不测试生成应用的具体实现。"""
from contextlib import nullcontext
import importlib.util
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location("factory", Path(__file__).resolve().parents[1] / "scripts/factory.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


class BaselineBoundaryTest(unittest.TestCase):
    def test_default_selects_mixed_variant_and_backend_cannot_replace_it(self):
        default = factory.load_config()
        self.assertEqual((default['variant'],default['backend'],default['workflow'],default['svc']),
                         ('pi-team-mixed','pi','braid',True))
        with patch.object(sys,'argv',['factory.py','generate','--variant','pi-team-deepseek']), \
             patch.object(factory,'generate') as generate:
            factory.main()
        selected=generate.call_args.args[0]
        self.assertEqual((selected['variant'],selected['backend']),('pi-team-deepseek','pi'))
        self.assertEqual(selected['effective']['defaults']['issue'],'pi-deepseek-fast')
        with self.assertRaisesRegex(ValueError,'backend'):
            factory.load_config(variant='pi-team-mixed',backend='codex')
        with tempfile.TemporaryDirectory() as temp:
            archived=Path(temp)/'config.json'
            archived.write_text(json.dumps(dict(model='old',backend='pi',workflow='single')))
            old=archived.read_bytes()
            custom=factory.load_config(archived,backend='codex')
            self.assertEqual((custom['variant'],custom['backend'],custom['workflow']),('custom','codex','single'))
            self.assertEqual(archived.read_bytes(),old)

    def test_cli_rejects_retired_variants_and_frozen_run_overrides_before_execution(self):
        for args in (['generate','--variant','pi-svc'],['eval','--run','missing','--backend','pi']):
            with self.subTest(args=args), patch.object(sys,'argv',['factory.py']+args), \
                 patch('sys.stderr',io.StringIO()), patch.object(factory,'generate') as generate, \
                 patch.object(factory,'evaluate') as evaluate:
                with self.assertRaises(SystemExit) as error: factory.main()
                self.assertEqual(error.exception.code,2)
                generate.assert_not_called()
                evaluate.assert_not_called()

    def test_svc_off_is_independent_of_braid_and_has_no_corpus_install(self):
        for backend in ('pi', 'codex'):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                with patch.object(factory, 'ROOT', root), patch.object(factory, 'api_key', return_value='test'):
                    native, env=factory.runtime_environment(root, {'backend':backend,'workflow':'braid','svc':False})
                self.assertFalse((native/'AGENTS.md').exists())
                self.assertFalse((root/'runtime').exists())
                self.assertEqual(env['HOME'],str(root/'home'))

    def test_truncated_pi_response_is_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            session = Path(temp) / "session.jsonl"
            session.write_text('{"message":{"role":"assistant","stopReason":"length"}}\n')
            with self.assertRaisesRegex(RuntimeError, "Pi 未正常完成"):
                factory.pi_usage(session)
            session.write_text(json.dumps({'message':{'role':'assistant','stopReason':'error',
                'errorMessage':'Unterminated string in JSON at position 180',
                'usage':{'input':5,'output':2,'totalTokens':7}}}))
            with self.assertRaisesRegex(RuntimeError, 'Pi 未正常完成：Unterminated string'):
                factory.pi_usage(session)
            self.assertEqual(factory.pi_usage(session,require_completed=False)['tokens']['totalTokens'],7)

    def test_pi_usage_includes_compaction(self):
        with tempfile.TemporaryDirectory() as temp:
            session=Path(temp)/'session.jsonl'
            usage={'input':1,'output':2,'cacheRead':3,'cacheWrite':0,'reasoning':1,'totalTokens':6}
            entries=[{'message':{'role':'assistant','stopReason':'stop','usage':usage}},
                     {'type':'compaction','usage':usage}]
            session.write_text('\n'.join(json.dumps(e) for e in entries))
            result=factory.pi_usage(session)
            self.assertEqual(result['tokens']['totalTokens'],12)
            self.assertEqual(result['tokens']['reasoning'],2)

    def test_invalidated_pi_session_keeps_consumed_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            session=Path(temp)/'session.jsonl'
            session.write_text(json.dumps({'message':{'role':'assistant','stopReason':'aborted',
                                                     'usage':{'input':5,'output':2,'totalTokens':7}}}))
            self.assertEqual(factory.pi_usage(session,require_completed=False)['tokens']['totalTokens'],7)
            with self.assertRaises(RuntimeError): factory.pi_usage(session)

    def test_failed_braid_workspace_retains_common_git_data(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)
            with self.assertRaisesRegex(RuntimeError,'disconnected'):
                with factory.generation_workspace(run,retain_failure=True) as work:
                    (work/'repo.git').write_text('recovery object source')
                    raise RuntimeError('disconnected')
            self.assertEqual(json.loads((run/'recovery-workspace.json').read_text())['path'],str(work))
            self.assertTrue((work/'repo.git').exists())
            factory.shutil.rmtree(work)
            with factory.generation_workspace(run,retain_failure=True) as complete:
                (complete/'done').touch()
            self.assertFalse(complete.exists())

    def test_freeze_cannot_follow_application_link_to_host_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);app=root/'app';app.mkdir()
            (root/'external').write_text('outside allowed application')
            (app/'leak').symlink_to(root/'external')
            with self.assertRaisesRegex(RuntimeError,'工作区外'):
                factory.copy_application(app,root/'frozen')

    def test_case_inventory_rejects_missing_and_skipped_execution(self):
        listed={'suites':[{'specs':[{'id':'case-one','tests':[{'projectId':'chromium'}]}]}]}
        report=json.loads(json.dumps(listed))
        test=report['suites'][0]['specs'][0]['tests'][0]
        test['results']=[{'status':'timedOut'}]
        self.assertEqual(factory.verify_case_completion(listed,report),1)
        test['results'][0]['status']='skipped'
        with self.assertRaisesRegex(RuntimeError,'跳过'): factory.verify_case_completion(listed,report)
        with self.assertRaisesRegex(RuntimeError,'不一致'): factory.verify_case_completion(listed,{'suites':[]})

    def test_evaluation_request_cannot_claim_another_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp); app_hashes={'app.js':'abc'}
            factory.save(run/'application-hashes.json',app_hashes)
            config={'benchmark_revision':'pinned'}
            summary={'evaluation_id':'wanted','run_id':run.name,'benchmark_revision':'pinned',
                     'application_sha256':factory.digest(app_hashes)}
            factory.check_evaluation_identity(summary,run,config,'wanted')
            for key in summary:
                wrong=dict(summary); wrong[key]='other'
                with self.subTest(key=key), self.assertRaisesRegex(RuntimeError,'身份'):
                    factory.check_evaluation_identity(wrong,run,config,'wanted')
            with self.assertRaises(ValueError): factory.evaluation_id('../outside')

    def test_cleanup_reaches_detached_workspace_process(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp).resolve()
            proc=subprocess.Popen(['sleep','60'],cwd=work,start_new_session=True)
            try:
                self.assertIn(proc.pid,factory.cleanup_workspace(work))
                self.assertNotEqual(proc.wait(timeout=3),0)
            finally:
                factory.stop(proc)

    def test_completed_generation_cleanup_error_requires_workspace_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp)
            errors=[]
            with patch.object(factory,'stop',side_effect=PermissionError('group denied')):
                self.assertEqual(factory.logged(['true'],work,None,work/'log',errors),0)
                self.assertEqual(errors[0]['exit_code'],0)
                with self.assertRaises(PermissionError):
                    factory.logged(['true'],work,None,work/'log')
            with patch.object(factory,'workspace_processes',return_value=[]):
                self.assertEqual(factory.cleanup_workspace(work),[])
            with patch.object(factory,'workspace_processes',return_value=[999999]), patch.object(factory.os,'kill'):
                with self.assertRaisesRegex(RuntimeError,'remain after cleanup'):
                    factory.cleanup_workspace(work)

    def test_score_and_snapshot(self):
        result = factory.score({"stats": {"expected": 2, "unexpected": 1, "flaky": 0, "skipped": 1, "duration": 1000}})
        self.assertEqual((result["total"], result["pass_rate"]), (4, 0.5))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "application"
            app.mkdir()
            (app / "app.js").write_text("first")
            factory.save(root / "application-hashes.json", factory.hashes(app))
            factory.save(root / "config.json", {})
            factory.save(root / "run.json", {"status": "generated"})
            (app / "app.js").write_text("changed")
            with self.assertRaisesRegex(RuntimeError, "快照已被修改"):
                factory.evaluate(root)
            with self.assertRaisesRegex(RuntimeError, "快照已被修改"):
                factory.evaluate_remote(root,"unused-host")

    def test_generation_failure_and_cancel_survive_archive_cleanup(self):
        for failure,expected in [(RuntimeError('agent error'),'generation_failed'),(KeyboardInterrupt(),'interrupted')]:
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); bench=root/'bench'
                requirements=bench/'arc-bench/webapp/keep/requirements'
                requirements.mkdir(parents=True); (requirements/'requirements.md').write_text('input')
                for name in ['scripts','harness']:
                    (root/name).mkdir(parents=True)
                def runtime(work,config):
                    native=work/'native'; native.mkdir()
                    return native,{}
                with patch.object(factory,'ROOT',root), patch.object(factory,'BENCH',bench), \
                     patch.object(factory.platform,'platform',return_value='test-platform'), \
                     patch.object(factory,'capture',side_effect=['fixed','','pi-version','node-version']), \
                     patch.object(factory,'responses_adapter',return_value=nullcontext(None)), \
                     patch.object(factory,'runtime_environment',side_effect=runtime), \
                     patch.object(factory,'isolation_prefix',return_value=[]), \
                     patch.object(factory.subprocess,'run',side_effect=[subprocess.CompletedProcess([],1),subprocess.CompletedProcess([],0)]), \
                     patch.object(factory,'logged',side_effect=failure), \
                     patch.object(factory,'cleanup_workspace',return_value=[]):
                    with self.assertRaises(type(failure)):
                        factory.generate({'benchmark_revision':'fixed','task':'keep',
                                          'model':'test','thinking':'high','base_url':'http://unused'})
                metadata=json.loads(next((root/'runs').glob('*/run.json')).read_text())
                self.assertEqual((metadata['status'],metadata['phase'],metadata['failed_phase']),
                                 (expected,'interrupted' if expected=='interrupted' else 'failed','agent'))
                self.assertEqual(metadata['phase_log'],'pi-events.jsonl')
                self.assertNotIn('runtime',metadata)

                self.assertEqual(metadata['error'],str(failure) or type(failure).__name__)

    def test_pi_exit_zero_requires_native_stop_before_freeze(self):
        usage={'input':5,'output':2,'cacheRead':0,'cacheWrite':0,'reasoning':1,'totalTokens':7}

        def generated(stop_reason):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); bench=root/'bench'
                requirements=bench/'arc-bench/webapp/keep/requirements'
                requirements.mkdir(parents=True); (requirements/'requirements.md').write_text('input')
                (bench/'package.json').write_text('{}')
                for name in ('scripts','harness'): (root/name).mkdir()

                def runtime(work,config):
                    native=work/'native'; native.mkdir()
                    return native,{}

                def pi(command, *_):
                    session=Path(command[command.index('--session')+1])
                    session.write_text(json.dumps({'type':'session','id':'native-session'})+'\n'+json.dumps({'message':{
                        'role':'assistant','stopReason':stop_reason,
                        'errorMessage':'Unterminated string in JSON at position 180' if stop_reason == 'error' else None,
                        'usage':usage}})+'\n')
                    return 0

                original_run=subprocess.run
                def preflight(command, *args, **kwargs):
                    if command[-1] == str(bench/'package.json'): return subprocess.CompletedProcess(command,1)
                    if command[-1] == str(requirements/'requirements.md'): return subprocess.CompletedProcess(command,0)
                    return original_run(command,*args,**kwargs)

                config={'benchmark_revision':'fixed','task':'keep','model':'test','thinking':'high','base_url':'http://unused'}
                with patch.object(factory,'ROOT',root), patch.object(factory,'BENCH',bench), \
                     patch.object(factory,'capture',side_effect=['fixed','','pi-version','node-version']), \
                     patch.object(factory,'responses_adapter',return_value=nullcontext(None)), \
                     patch.object(factory,'runtime_environment',side_effect=runtime), \
                     patch.object(factory,'isolation_prefix',return_value=[]), \
                     patch.object(factory.subprocess,'run',side_effect=preflight), \
                     patch.object(factory,'logged',side_effect=pi), \
                     patch.object(factory,'cleanup_workspace',return_value=[]):
                    try: run=factory.generate(config)
                    except RuntimeError as exc: run=None; error=exc
                    else: error=None
                frozen=next((root/'runs').glob('*'))
                return run,error,json.loads((frozen/'run.json').read_text()),json.loads((frozen/'native/manifest.json').read_text())

        run,error,failed,manifest=generated('error')
        self.assertIsNone(run)
        self.assertIn('Unterminated string',str(error))
        self.assertEqual((failed['status'],failed['phase'],failed['failed_phase']),('generation_failed','failed','agent'))
        self.assertEqual(failed['process_exit_code'],0)
        self.assertIn('Unterminated string',failed['error'])
        self.assertEqual(failed['usage']['tokens']['totalTokens'],7)
        self.assertEqual(manifest['sessions'][0]['turns'][0]['status'],'failed')

        run,error,completed,manifest=generated('stop')
        self.assertIsNotNone(run)
        self.assertIsNone(error)
        self.assertEqual((completed['status'],completed['phase']),('generated','frozen'))
        self.assertEqual(completed['usage']['tokens']['totalTokens'],7)
        self.assertEqual(manifest['sessions'][0]['turns'][0]['status'],'completed')

    def test_failed_install_preserves_stage_and_log(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)
            (run/'application').mkdir()
            (run/'application/package.json').write_text('{}')
            with patch.object(factory,'validate_snapshot',return_value={'benchmark_revision':'fixed'}), \
                 patch.object(factory,'capture',side_effect=['fixed','','v24']), \
                 patch.object(factory,'logged',return_value=1):
                with self.assertRaisesRegex(RuntimeError,'安装失败'):
                    factory.evaluate(run)
            summary=json.loads(next((run/'evaluation').glob('*/summary.json')).read_text())
            self.assertEqual((summary['status'],summary['phase'],summary['failed_phase']),
                             ('evaluation_error','failed','install'))
            self.assertEqual(summary['phase_log'],'install.log')
            self.assertGreaterEqual(summary['finished_at'],summary['started_at'])

    def test_interrupt_retains_evaluation_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp); (run/'application').mkdir()
            (run/'application/package.json').write_text('{}')
            with patch.object(factory,'validate_snapshot',return_value={'benchmark_revision':'fixed'}), \
                 patch.object(factory,'capture',side_effect=['fixed','','v24']), \
                 patch.object(factory,'logged',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): factory.evaluate(run)
            summary=json.loads(next((run/'evaluation').glob('*/summary.json')).read_text())
            self.assertEqual(summary['status'],'interrupted')
            self.assertEqual(summary['failed_phase'],'install')
            self.assertEqual(summary['error'],'KeyboardInterrupt')

    def test_analysis_source_change_reexports_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); run=root/'run'; source=root/'svc'
            (run/'native').mkdir(parents=True); (source/'cli/src').mkdir(parents=True)
            (run/'run.json').write_text('{"backend":"pi"}')
            (run/'native/session.jsonl').write_text('{}')
            code=source/'cli/src/exporter.py'; code.write_text('first')
            exported=[]
            def capture(*args,**kwargs):
                if 'export' in args:
                    output=Path(args[args.index('--output')+1]); output.write_bytes(b'evidence')
                    exported.append(output)
                    return '{}'
                return 'version-or-revision'
            response=subprocess.CompletedProcess([],0,stdout='{"status":"complete"}')
            with patch.object(factory,'capture',side_effect=capture), patch.object(factory.subprocess,'run',return_value=response) as query:
                factory.analyze(run,source); factory.analyze(run,source)
                self.assertEqual(len(exported),1)
                original=factory.hashes(run/'analysis')
                code.write_text('second')
                query.side_effect=subprocess.CalledProcessError(1,'query')
                with self.assertRaises(subprocess.CalledProcessError): factory.analyze(run,source)
                self.assertEqual(factory.hashes(run/'analysis'),original)
                query.side_effect=None
                factory.analyze(run,source)
                self.assertEqual(len(exported),3)
                self.assertEqual(len(list((run/'analysis').glob('*/provenance.json'))),2)
                (run/'native/session.jsonl').write_text('{"new":"bytes"}')
                factory.analyze(run,source)
                self.assertEqual(len(list((run/'analysis').glob('*/provenance.json'))),3)

    def test_remote_connection_failure_is_observable(self):
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)
            with patch.object(factory,'validate_snapshot',return_value={}), \
                 patch.object(factory,'capture',side_effect=OSError('host unavailable')):
                with self.assertRaises(OSError): factory.evaluate_remote(run,'test-host')
            status=json.loads((run/'remote-evaluation.json').read_text())
            self.assertEqual((status['phase'],status['failed_phase']),('failed','connect'))
            self.assertIn('host unavailable',status['error'])

    @unittest.skipUnless(platform.system() == "Darwin", "macOS isolation boundary")
    def test_agent_cannot_read_evaluator_or_modify_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            evaluator, inputs = root / "evaluator", root / "input"
            evaluator.mkdir()
            inputs.mkdir()
            secret, requirement = evaluator / "test.js", inputs / "requirements.md"
            secret.write_text("external assertion")
            requirement.write_text("allowed requirement")
            profile = root / "profile.sb"
            profile.write_text(factory.sandbox_profile([evaluator], inputs))
            prefix = ["sandbox-exec", "-f", str(profile)]
            self.assertNotEqual(subprocess.run(prefix + ["cat", str(secret)], capture_output=True).returncode, 0)
            allowed = subprocess.run(prefix + ["cat", str(requirement)], capture_output=True)
            self.assertEqual(allowed.stdout, b"allowed requirement")
            self.assertNotEqual(subprocess.run(prefix + ["touch", str(requirement)], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
