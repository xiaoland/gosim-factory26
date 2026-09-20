"""Protocol completion must belong to the requested turn, including child activity."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('core',Path(__file__).resolve().parents[1]/'scripts/core.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

class ProtocolTest(unittest.TestCase):
    def test_child_completion_cannot_complete_parent_and_failures_propagate(self):
        for status in ('completed','failed'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                server=root/'server.py'
                server.write_text('''import sys,json
for line in sys.stdin:
 f=json.loads(line)
 if 'id' not in f: continue
 result={}
 if f['method']=='thread/start':result={'thread':{'id':'parent'}}
 if f['method']=='turn/start':
  print(json.dumps({'method':'turn/completed','params':{'threadId':'child','turn':{'id':'other','status':'completed'}}}),flush=True)
  result={'turn':{'id':'requested'}}
 print(json.dumps({'id':f['id'],'result':result}),flush=True)
 if f['method']=='turn/start':
  print(json.dumps({'method':'turn/completed','params':{'threadId':'parent','turn':{'id':'requested','status':sys.argv[1]}}}),flush=True)
''')
                import sys
                command=[sys.executable,str(server),status]
                if status=='failed':
                    with self.assertRaisesRegex(RuntimeError,'failed'):
                        core.codex_turn(command,root,dict(os.environ),'task',root,'model','high')
                else:
                    self.assertEqual(core.codex_turn(command,root,dict(os.environ),'task',root,'model','high')['thread_id'],'parent')
