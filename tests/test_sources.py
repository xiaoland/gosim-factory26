"""A local source edit must invalidate a build and survive the run archive."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sources


class SourceBuildTest(unittest.TestCase):
    def test_uncommitted_inputs_and_artifacts_cannot_masquerade_as_prior_build(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(sources, 'ROOT', Path(temp)):
            root=Path(temp); source=root/'sources/braid'; source.mkdir(parents=True)
            subprocess.run(['git','init','-q',str(source)],check=True)
            # Empty tree commit supplies a source identity without touching user config.
            tree=subprocess.check_output(['git','mktree'],input=b'',cwd=source).strip()
            import os
            env=dict(os.environ,GIT_AUTHOR_NAME='test',GIT_AUTHOR_EMAIL='test@example.com',
                     GIT_COMMITTER_NAME='test',GIT_COMMITTER_EMAIL='test@example.com')
            commit=subprocess.check_output(['git','commit-tree',tree.decode()],input=b'test\n',cwd=source,env=env).strip()
            subprocess.run(['git','update-ref','HEAD',commit.decode()],cwd=source,check=True)
            code=source/'local.rs'; code.write_text('first')
            (source/'.gitignore').write_text('target/\n')
            artifact=sources.binary(); artifact.parent.mkdir(parents=True); artifact.write_bytes(b'first binary')
            (root/'.bootstrap').mkdir()
            stamp=root/'.bootstrap/braid-build.json'
            def record():
                stamp.write_text(json.dumps({'source':sources.snapshot('braid'), 'artifacts':sources.artifact_hashes('braid')}))
            record()
            output=root/'archive'; sources.archive('braid',output)
            with tarfile.open(output/'braid.tar.gz') as bundle:
                self.assertEqual(bundle.extractfile('local.rs').read(),b'first')
                self.assertNotIn('target/debug/braid',bundle.getnames())
            code.write_text('second')
            with self.assertRaisesRegex(RuntimeError,'source changed'): sources.require_build('braid')
            record(); artifact.write_bytes(b'unrecorded binary')
            with self.assertRaisesRegex(RuntimeError,'installation differs'): sources.require_build('braid')
            record(); self.assertEqual(sources.require_build('braid')['source']['files']['local.rs'],
                                       sources.snapshot('braid')['files']['local.rs'])
