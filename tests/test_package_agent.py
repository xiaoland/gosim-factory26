"""Packaging boundaries: exact context, portable links, hashes, no overwrites."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import package_agent


class PackageTest(unittest.TestCase):
    def test_zip_materializes_links_and_records_executable_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = root / 'bundle'; bundle.mkdir()
            (bundle / 'tool').write_bytes(b'hello'); (bundle / 'tool').chmod(0o755)
            (bundle / 'alias').symlink_to('tool')
            output = root / 'agent.zip'
            package_agent.write_zip(bundle, output, 'pi', {})
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read('package-manifest.json'))
                self.assertNotIn('package-manifest.json', manifest['files'])
                for name in ('tool', 'alias'):
                    self.assertEqual(archive.read(name), b'hello')
                    self.assertEqual(manifest['files'][name], {
                        'sha256': hashlib.sha256(b'hello').hexdigest(), 'executable': True})
                    self.assertTrue(stat.S_ISREG(archive.getinfo(name).external_attr >> 16))
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                package_agent.write_zip(bundle, output, 'pi', {})
            self.assertEqual(output.read_bytes(), before)

    def test_links_cannot_escape_or_recurse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = root / 'bundle'; bundle.mkdir()
            (root / 'secret').write_text('secret')
            link = bundle / 'link'; link.symlink_to('../secret')
            with self.assertRaisesRegex(ValueError, '越出'):
                list(package_agent.bundle_files(bundle))
            link.unlink(); link.symlink_to('.')
            with self.assertRaisesRegex(ValueError, '循环'):
                list(package_agent.bundle_files(bundle))

    def test_context_preserves_snapshot_bytes_and_rejects_changed_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'submission').mkdir()
            for name in ('Dockerfile', 'build.py'):
                (root / 'submission' / name).write_text('build input')
            source = root / 'sources/braid'; (source / 'src').mkdir(parents=True)
            code = source / 'src/main.rs'; code.write_bytes(b'current local edit')
            (source / '.env').write_text('never copied')
            records = {'braid': {'revision': 'revision', 'files': {
                'src/main.rs': hashlib.sha256(code.read_bytes()).hexdigest(),
                '.env': hashlib.sha256(b'never copied').hexdigest()}}}
            context = root / 'context'; context.mkdir()
            with patch.object(package_agent, 'ROOT', root), patch.object(package_agent.sources, 'ROOT', root):
                package_agent.prepare_context(context, records)
                self.assertEqual((context / 'sources/braid/src/main.rs').read_bytes(), b'current local edit')
                self.assertFalse((context / 'sources/braid/.env').exists())
                code.write_text('changed after snapshot')
                with self.assertRaisesRegex(RuntimeError, '源码发生变化'):
                    package_agent.prepare_context(context, records)

    def test_context_includes_build_inputs_only(self):
        for name, path in [('braid', 'migrations/0001_initial.sql'),
                           ('braid', 'src/main.rs'), ('svc', 'corpus/version.json'),
                           ('svc', 'cli/pdm_build.py')]:
            self.assertTrue(package_agent.source_input(name, path))
        for name, path in [('braid', '.git/config'), ('braid', 'target/debug/braid'),
                           ('svc', 'cli/tests/test_cli.py'), ('svc', '.env')]:
            self.assertFalse(package_agent.source_input(name, path))


if __name__ == '__main__':
    unittest.main()
