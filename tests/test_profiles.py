"""Capability assembly preserves public identity and exact runtime consumers."""
import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native_profiles
import profiles


VARIANTS = {
    'pi-team-deepseek': (['pi-deepseek-fast'], 'pi-deepseek-fast', 'pi-deepseek-fast'),
    'pi-team-glm': (['pi-glm-fast'], 'pi-glm-fast', 'pi-glm-fast'),
    'pi-team-mixed': (['pi-glm-fast', 'pi-deepseek-fast'], 'pi-glm-fast', 'pi-deepseek-fast'),
    'pi-team-vv': (['pi-glm-fast', 'pi-deepseek-fast'], 'pi-glm-fast', 'pi-deepseek-fast'),
}


class ProfileBoundaryTest(unittest.TestCase):
    def copied_root(self, temporary):
        root = Path(temporary)
        for name in ('harness', 'variants', 'sources/svc'):
            shutil.copytree(profiles.ROOT / name, root / name)
        return root

    def test_four_variants_have_two_public_assignees_and_five_explicit_roles(self):
        for variant, (ids, issue, pull_request) in VARIANTS.items():
            effective = profiles.resolve(variant)
            self.assertEqual(list(effective['profiles']), ids)
            self.assertEqual(effective['defaults'], {'issue': issue, 'pr': pull_request})
            self.assertFalse(any((profiles.ROOT / 'variants').glob('*/preset.json')))
            for item in effective['profiles'].values():
                profile = item['profile']
                self.assertIn(profile['assignee_login'], ('glm', 'deepseek'))
                self.assertLessEqual(len(profile['assignee_description'].encode()), 240)
                self.assertEqual(profile['mcp'], [])
                self.assertEqual(set(item['roles']),
                                 {'explorer', 'executor', 'browser-operator', 'vision', 'specialist'})
                for role in item['roles'].values():
                    self.assertEqual(role['mcp'], [])
                    self.assertEqual(role['context'], {'mode': 'fresh'})
                    self.assertIn(role['reasoning'], item['models'][role['model']]['reasoning_levels'])

    def test_effective_defaults_match_braid_request_schema(self):
        source = (profiles.ROOT / 'sources/braid/src/config.rs').read_text()
        body = re.search(r'pub struct ProfileDefaults\s*\{([^}]*)\}', source, re.DOTALL).group(1)
        rust_fields = set(re.findall(r'pub\s+(\w+)\s*:', body))
        self.assertEqual(rust_fields, {'issue', 'pr'})
        self.assertEqual(set(profiles.resolve('pi-team-mixed')['defaults']), rust_fields)

    def test_vv_diff_is_only_canonical_svc_preload_and_resulting_digests(self):
        mixed = profiles.resolve('pi-team-mixed')
        vv = profiles.resolve('pi-team-vv')
        self.assertEqual([item['path'] for item in vv['svc']['preload']],
                         ['methods/design/test.md', 'verification/index.md'])
        self.assertEqual(mixed['svc']['preload'], [])
        self.assertEqual(vv['svc']['source_revision'],
                         '393b9352fae1e8b22d86b28a65ff2f7ded267a38')
        self.assertEqual([item['sha256'] for item in vv['svc']['preload']], [
            'bf80281aad0dae8b4c020f1f2e9d214b6511b339f3821e80b879f5d7c3fadbbd',
            '2ffeb3b9e67f946cafc475ea2abd667caad0493a8102b862dfdd887537223381'])
        for profile_id in mixed['profiles']:
            left = copy.deepcopy(mixed['profiles'][profile_id])
            right = copy.deepcopy(vv['profiles'][profile_id])
            for item in (left, right):
                item.pop('effective_profile_digest')
                item.pop('svc_preload')
            self.assertEqual(left, right)

    def test_materializer_projects_assignee_and_routes_visual_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            cache = work / 'cache'
            (cache / 'node_modules/.bin').mkdir(parents=True)
            (cache / 'node_modules/.bin/pi').touch()
            (cache / 'bin').mkdir()
            (cache / 'bin/pi').touch()
            (cache / 'node_modules/pi-subagents').mkdir(parents=True)
            (cache / 'node_modules/pi-subagents/index.ts').touch()
            effective = profiles.resolve('pi-team-vv')
            with patch.object(native_profiles, 'browser_wrapper'), \
                    patch.object(native_profiles, 'runtime_cache', return_value=cache), \
                    patch.object(native_profiles, 'executable', return_value=str(cache / 'bin/pi')):
                projected, bindings = native_profiles.materialize(
                    effective, work, 'https://text.example/v1', 'fixture', 'https://visual.example/v1')
            self.assertEqual({item['assignee_login'] for item in projected}, {'glm', 'deepseek'})
            self.assertTrue(all(item['display_name'] == item['id'] for item in projected))
            self.assertTrue(all('methods/design/test.md' in item['user_instructions'] for item in projected))
            template = Path(bindings['pi-glm-fast']['native_template'])
            catalog = json.loads((template / 'models.json').read_text())['providers']
            self.assertEqual(catalog['factory26']['apiKey'], '$FACTORY26_API_KEY')
            self.assertEqual(catalog['factory26-visual']['apiKey'], '$FACTORY26_VISUAL_API_KEY')
            self.assertEqual(catalog['factory26-visual']['baseUrl'], 'https://visual.example/v1')
            browser = (template / 'agents/browser-operator.md').read_text()
            self.assertIn('model: "factory26-visual/deepseek-v4-flash-vision-exp"', browser)
            self.assertIn('defaultContext: "fresh"', browser)
            self.assertNotIn('reviewer', {path.stem for path in (template / 'agents').glob('*.md')})

    def test_packaged_browser_wrapper_uses_canonical_chromium_launcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root/'runtime'
            (cache/'bin').mkdir(parents=True)
            (cache/'bin/agent-browser').touch()
            chromium = cache/'bin/chromium'
            chromium.touch()
            native_profiles.browser_wrapper(root/'work', 'fixture', cache)
            wrapper = (root/'work/bin/agent-browser').read_text()
            self.assertIn(repr(str(chromium)), wrapper)
            self.assertNotIn('.agent-browser/browsers/chrome-', wrapper)

    def test_digest_tracks_consumed_role_and_invalid_public_identity_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_root(temporary)
            original = profiles.resolve('pi-team-mixed', root)
            shutil.copytree(root / 'variants/pi-team-mixed', root / 'variants/pi-team-alias')
            self.assertEqual(original['effective_digest'],
                             profiles.resolve('pi-team-alias', root)['effective_digest'])
            instruction = root / 'harness/instructions/executor.md'
            instruction.write_text(instruction.read_text() + '\n额外可观察约束。\n')
            changed = profiles.resolve('pi-team-mixed', root)
            self.assertNotEqual(original['effective_digest'], changed['effective_digest'])
            for profile_id in original['profiles']:
                self.assertNotEqual(original['profiles'][profile_id]['effective_profile_digest'],
                                    changed['profiles'][profile_id]['effective_profile_digest'])
            profile = root / 'harness/profiles/pi-deepseek-fast.json'
            value = json.loads(profile.read_text())
            value['assignee_login'] = 'glm'
            profile.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'duplicate assignee'):
                profiles.resolve('pi-team-mixed', root)

    def test_unknown_material_and_svc_escape_fail_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_root(temporary)
            profile = root / 'harness/profiles/pi-glm-fast.json'
            value = json.loads(profile.read_text())
            value['skills'] = ['missing']
            profile.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'missing skill'):
                profiles.resolve('pi-team-glm', root)
            value['skills'] = []
            value['unknown'] = True
            profile.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'unknown or missing profile fields'):
                profiles.resolve('pi-team-glm', root)
            value.pop('unknown')
            profile.write_text(json.dumps(value))
            variant = root / 'variants/pi-team-glm/variant.json'
            selection = json.loads(variant.read_text())
            selection['svc']['index'] = '../README.md'
            variant.write_text(json.dumps(selection))
            with self.assertRaisesRegex(ValueError, 'invalid SVC path'):
                profiles.resolve('pi-team-glm', root)


if __name__ == '__main__':
    unittest.main()
