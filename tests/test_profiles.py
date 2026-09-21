"""Selection and material edits must affect only the consumers that use them."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import profiles
import native_profiles


class ProfileBoundaryTest(unittest.TestCase):
    def test_codex_materializes_model_window_for_root_and_native_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)
            with patch.object(native_profiles,'browser_wrapper'), patch.object(native_profiles,'executable',return_value='/bin/false'):
                # Only installation presence is needed; no core is executed.
                cache=work/'cache'; (cache/'node_modules/.bin').mkdir(parents=True)
                (cache/'node_modules/.bin/pi').touch()
                with patch.object(native_profiles,'runtime_cache',return_value=cache):
                    effective=profiles.resolve('codex-generalist')
                    _,bindings=native_profiles.materialize(effective,work,'http://127.0.0.1:1/v1','fixture')
            item=effective['profiles']['codex-generalist']
            folder=Path(bindings['codex-generalist']['native_template'])
            configs=[(tomllib.loads((folder/'config.toml').read_text()),item['profile'])]
            configs += [(tomllib.loads((folder.parent/(name+'.toml')).read_text()),role) for name,role in item['roles'].items()]
            for config,source in configs:
                self.assertEqual(config['model'],source['model'])
                self.assertEqual(config['model_context_window'],item['models'][source['model']]['descriptor']['contextWindow'])

    def test_presets_and_native_roles_are_distinct_and_explicit(self):
        expected = {'pi-generalist':1,'codex-generalist':1,'pi-team':3,'pi-verification':2}
        for variant,count in expected.items():
            effective=profiles.resolve(variant)
            self.assertEqual(len(effective['profiles']),count)
            for item in effective['profiles'].values():
                self.assertEqual('reviewer' in item['roles'],variant=='pi-verification')
                self.assertNotIn('contract-reviewer',item['roles'])
                self.assertEqual(item['profile']['mcp'],[])
                self.assertNotIn('agent-browser',item['profile']['skills'])
                self.assertIn('agent-browser',item['roles']['executor']['skills'])

    def test_changed_role_invalidates_its_consumers_and_unknown_assignment_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('harness','variants','experiments'):
                shutil.copytree(profiles.ROOT/name,root/name)
            original=profiles.resolve('pi-team',root)
            role=root/'harness/subagents/executor-ui.json'
            value=json.loads(role.read_text());value['model']='kimi-k3';role.write_text(json.dumps(value))
            changed=profiles.resolve('pi-team',root)
            self.assertNotEqual(original['profiles']['team-ui']['effective_profile_digest'],changed['profiles']['team-ui']['effective_profile_digest'])
            for name in ('team-coordinator','team-app'):
                self.assertEqual(original['profiles'][name],changed['profiles'][name])
            preset=root/'variants/pi-team/preset.json'
            value=json.loads(preset.read_text());value['defaults']['issue']='absent';preset.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'default assignment'):
                profiles.resolve('pi-team',root)

    def test_unknown_material_and_path_escape_fail_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('harness','variants'):
                shutil.copytree(profiles.ROOT/name,root/name)
            file=root/'harness/profiles/pi-generalist.json'
            value=json.loads(file.read_text());value['skills']=['missing'];file.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'missing skill'):
                profiles.resolve('pi-generalist',root)
            value['skills']=[];value['unknown_option']=True;file.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'unknown or missing profile fields'):
                profiles.resolve('pi-generalist',root)
            del value['unknown_option']
            value['skills']=[];value['instructions']=['variants/pi-generalist/preset.json'];file.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'outside harness'):
                profiles.resolve('pi-generalist',root)
