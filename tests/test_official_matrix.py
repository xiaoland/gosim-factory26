"""Matrix acceptance uses externally observable job order and replay count."""
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from zipfile import ZipFile
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import official_matrix


class MatrixTest(unittest.TestCase):
    def fixture(self, root):
        package = root/'agent.zip'; package.write_bytes(b'frozen')
        spec = {'competition':'arc-bench-lite', 'tasks':[{'id':'arc-bench-lite--keep'}, {'id':'arc-bench-lite--bookstack'}],
                'variants':[{'id':name, 'package':'agent.zip', 'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
                             'model_config':{'model':'text'}} for name in ('a','b')]}
        manifest = root/'matrix.json'; manifest.write_text(json.dumps(spec))
        return manifest

    def test_snapshot_order_and_completed_matrix_never_replays(self):
        calls = []
        class Controller:
            def __init__(self, path, **kw): self.name = path.name
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def run_all(self, **kw): calls.append(('run-two-tasks', self.name))
            def summary(self): return {'status':'completed','score_status':'complete'}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); manifest=self.fixture(root)
            with patch.object(official_matrix.competition,'prepare',side_effect=lambda path,*a,**kw: calls.append(('snapshot',path.name))), \
                 patch.object(official_matrix.competition,'Controller',Controller):
                result=official_matrix.execute(manifest,root/'run',secret='test')
                self.assertEqual(result['status'],'completed')
                self.assertEqual(calls,[('snapshot','a'),('run-two-tasks','a'),('snapshot','b'),('run-two-tasks','b')])
                official_matrix.execute(manifest,root/'run',secret='test')
                self.assertEqual(len(calls),4)
                (root/'agent.zip').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):
                    official_matrix.execute(manifest,root/'run',secret='test')

    def test_incomplete_variant_blocks_later_snapshots(self):
        calls=[]
        class Controller:
            def __init__(self,*a,**kw): pass
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def run_all(self,**kw):
                current=json.loads((root/'run/matrix.json').read_text())
                assert current['status']=='running' and 'finished_at' not in current
            def summary(self): return {'status':'blocked'}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); manifest=self.fixture(root)
            with patch.object(official_matrix.competition,'prepare',side_effect=lambda path,*a,**kw: calls.append(path.name)), \
                 patch.object(official_matrix.competition,'Controller',Controller):
                result=official_matrix.execute(manifest,root/'run',secret='test')
                self.assertEqual(result['status'],'blocked')
                self.assertEqual(calls,['a'])
                official_matrix.execute(manifest,root/'run',secret='test')
                self.assertEqual(calls,['a','a'])

    def test_local_slots_overlap_and_use_separate_workspace_identities(self):
        barrier = threading.Barrier(2)
        paths = []
        guard = threading.Lock()
        class Controller:
            def __init__(self, *a, **kw): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def run_all(self, **kw): pass
            def summary(self): return {'status':'completed','score_status':'complete'}
        def local(*args, **kwargs):
            with guard: paths.append(args[4])
            barrier.wait(timeout=2)
            return {'phase':'collected', 'result':{'passed':0,'total':1}}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); manifest=self.fixture(root)
            spec=json.loads(manifest.read_text())
            spec['local']={'runner':'fixed','image':'qualified','workers':2}
            for task in spec['tasks']:
                task.update(slug=task['id'].split('--')[-1], requirements='frozen-req', tests='frozen-tests')
            manifest.write_text(json.dumps(spec))
            with patch.object(official_matrix.competition,'prepare'), \
                 patch.object(official_matrix.competition,'Controller',Controller), \
                 patch.object(official_matrix.local_runner,'execute',side_effect=local):
                result=official_matrix.execute(manifest,root/'run',secret='test')
            self.assertEqual(result['status'],'completed')
            self.assertEqual(len(paths),4)
            self.assertEqual(len(set(paths)),4)

    def test_freeze_uses_packaged_models_and_rejects_partial_matrix(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); packages=[]
            for name in ('a','b','c','d'):
                path=root/(name+'.zip'); packages.append(path)
                with ZipFile(path,'w') as archive:
                    archive.writestr('package-manifest.json',json.dumps({'capabilities':{'variant':name}}))
                    archive.writestr('variants/factory/config.json',json.dumps({'base_url':'https://model.invalid/v1','model':name,
                        'effective':{'variant':name,'profiles':{'p':{'roles':{'vision':{'provider':'visual','model':'vision'}}}}}}))
            spec=official_matrix.freeze(packages,root/'frozen.json')
            self.assertEqual([v['model_config']['model'] for v in spec['variants']], ['a','b','c','d'])
            self.assertTrue(all(v['package_sha256']==hashlib.sha256(Path(v['package']).read_bytes()).hexdigest() for v in spec['variants']))
            with self.assertRaisesRegex(ValueError,'four distinct'):
                official_matrix.freeze(packages[:3],root/'partial.json')
            self.assertFalse((root/'partial.json').exists())
