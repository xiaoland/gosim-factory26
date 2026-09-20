"""The accepted Git commit, not an Agent's cwd, determines the frozen app."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from braid_runtime import initialize_repository, load_delivery, export_delivery
from core import archive_sessions


class DeliveryTest(unittest.TestCase):
    def test_delivery_export_ignores_uncommitted_files_and_rejects_wrong_ref(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp).resolve(); app=work/'app'; app.mkdir()
            initialize_repository(app)
            def git(*args):
                return subprocess.check_output(['git','-C',str(app),*args],text=True).strip()
            git('checkout','-qb','braid-delivery')
            (app/'one.txt').write_text('accepted')
            git('add','one.txt');git('commit','-qm','first PR')
            (app/'two.txt').write_text('also accepted')
            git('add','two.txt');git('commit','-qm','second PR')
            commit=git('rev-parse','HEAD')
            (app/'one.txt').write_text('uncommitted')
            state=work/'state';state.mkdir()
            (state/'objects.db').touch();(state/'sessions.json').write_text('[]')
            request={'run_id':'expected-run','delivery_ref':'refs/heads/braid-delivery'}
            result={'schema_version':1,'status':'completed','repository':str(app),'run_id':'expected-run',
                    'root_issue':{'kind':'issue','id':'1'},
                    'delivery_ref':'refs/heads/braid-delivery','delivery_commit':commit,
                    'objects_database':str(state/'objects.db'),'sessions_manifest':str(state/'sessions.json')}
            (state/'result.json').write_text(json.dumps(result))
            self.assertEqual(load_delivery(state,app,work,request)['delivery_commit'],commit)
            export_delivery(app,commit,work/'frozen')
            self.assertEqual((work/'frozen/one.txt').read_text(),'accepted')
            self.assertTrue((work/'frozen/two.txt').exists())
            result['delivery_ref']='refs/heads/factory-source'
            (state/'result.json').write_text(json.dumps(result))
            result['delivery_commit']=git('rev-parse','factory-source')
            (state/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(RuntimeError,'不一致'): load_delivery(state,app,work,request)
            result.update(delivery_ref=request['delivery_ref'],delivery_commit=commit,run_id='another-run')
            (state/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(RuntimeError,'不一致'): load_delivery(state,app,work,request)

    def test_sessions_from_multiple_worktrees_keep_identity_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp).resolve(); output=work/'run';output.mkdir(); home=work/'home';home.mkdir()
            entries=[]
            for name in ('issue','pr'):
                folder=work/name;folder.mkdir();source=folder/'session.jsonl'
                source.write_text(json.dumps({'type':'session','id':name})+'\n')
                entries.append({'session_id':str(source),'provider':'pi','group_id':name,
                                'native_session_path':str(source),'turns':[{'status':'interrupted'}]})
            entries.append({'session_id':'missing','provider':'codex','group_id':'old'})
            result=archive_sessions(output,home,work,entries)
            self.assertEqual([r['group_id'] for r in result],['issue','pr','old'])
            self.assertNotEqual(result[0]['native'],result[1]['native'])
            self.assertTrue(all((output/r['native']).exists() for r in result[:2]))
            self.assertIn('archive_error',result[2])
