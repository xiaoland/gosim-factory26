import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from core import archive_sessions


def write_jsonl(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + '\n')


class NativeArchiveTest(unittest.TestCase):
    def test_pi_manifest_parent_file_overrides_launch_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            native_home = work / 'pi-home'
            alias = native_home / 'parent.jsonl'
            canonical = native_home / 'sessions' / 'parent.jsonl'
            write_jsonl(alias, {'type': 'message', 'id': 'alias'})
            write_jsonl(canonical, {'type': 'session', 'id': 'pi-root'})
            (native_home / '.factory').mkdir(parents=True)
            (native_home / '.factory' / 'session-tree.json').write_text(json.dumps({
                'schema_version': 1, 'parent_native_session_id': 'pi-root',
                'parent_session_file': str(canonical), 'children': [],
            }))
            rows = archive_sessions(work / 'run', work / 'home', work, [{
                'provider': 'pi', 'session_id': str(alias), 'native_session_id': 'pi-root',
                'native_home': str(native_home),
                'native_session_path': str(alias),
            }])
            self.assertEqual(rows[0]['native_id'], 'pi-root')
            self.assertEqual(rows[0]['source_path'], str(canonical))
            self.assertNotIn('archive_error', rows[0])

    def test_pi_finds_canonical_root_and_prefers_terminal_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            native_home = work/'pi-home'
            alias = native_home/'missing.jsonl'
            canonical = native_home/'sessions'/'project'/f'run_pi-root.jsonl'
            child = native_home/'child.jsonl'
            write_jsonl(canonical, {'type':'session','id':'pi-root'})
            write_jsonl(child, {'type':'session','id':'pi-child'})
            factory = native_home/'.factory'
            factory.mkdir(parents=True)
            (factory/'session-tree.json').write_text(json.dumps({
                'schema_version':1, 'parent_native_session_id':'pi-root',
                'parent_session_file':str(alias), 'children':[{'mode':'foreground'}],
            }))
            (factory/'subagent-stop.json').write_text(json.dumps({
                'schema_version':1, 'state':'stopped', 'parent_native_session_id':'pi-root',
                'children':[{'mode':'foreground','run_id':'run-1','parent_session_id':'pi-root',
                    'child_session_id':'pi-child','session_file':str(child),
                    'evidence_source':'pi-subagents:interrupt/parent-process-tree'}],
            }))
            rows = archive_sessions(work/'run',work/'unused',work,[{
                'provider':'pi','session_id':str(alias),'native_session_id':'pi-root',
                'native_home':str(native_home),'native_session_path':str(alias),
                'native_teardown_configured':True,
            }])
            self.assertEqual([row.get('native_id') for row in rows],['pi-root','pi-child'])
            self.assertTrue(all('archive_error' not in row for row in rows))
            self.assertTrue(rows[0]['session_tree_manifest'].endswith('subagent-stop.json'))

    def test_pi_tree_archives_two_connected_levels_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            output = work / 'run'
            home = work / 'unused-home'
            native_home = work / 'pi-home'
            root = native_home / 'root.jsonl'
            child_one = work / 'child-one.jsonl'
            child_two = work / 'child-two.jsonl'
            write_jsonl(root, {'type': 'session', 'id': 'pi-root'})
            write_jsonl(child_one, {'type': 'session', 'id': 'pi-child-1'})
            write_jsonl(child_two, {'type': 'session', 'id': 'pi-child-2'})
            tree = {
                'schema_version': 1,
                'parent_native_session_id': 'pi-root',
                'children': [
                    {'mode': 'foreground', 'run_id': 'run-1', 'parent_session_id': 'pi-root',
                     'child_session_id': 'pi-child-1', 'session_file': str(child_one),
                     'evidence_source': 'pi-subagents:status/foregroundRuns'},
                    {'mode': 'background', 'run_id': 'run-2', 'parent_session_id': 'pi-child-1',
                     'child_session_id': 'pi-child-2', 'session_file': str(child_two),
                     'evidence_source': 'pi-subagents:status/processTerminal',
                     'proof': {'process_terminal_observed': True, 'process_terminal': {'runId': 'run-2', 'state': 'observed'}}},
                ],
            }
            (native_home / '.factory').mkdir(parents=True)
            (native_home / '.factory' / 'session-tree.json').write_text(json.dumps(tree))
            rows = archive_sessions(output, home, work, [{
                'provider': 'pi', 'session_id': 'pi-root', 'native_home': str(native_home),
                'native_session_path': str(root), 'profile_id': 'p1',
                'effective_profile_digest': 'digest', 'work_item_kind': 'issue',
                'work_item_id': '1', 'assignment_generation': 2,
            }])
            self.assertEqual(len(rows), 3)
            self.assertTrue(all('archive_error' not in row for row in rows))
            children = {row['native_id']: row for row in rows}
            self.assertEqual(children['pi-child-1']['native_parent'], 'pi-root')
            self.assertEqual(children['pi-child-2']['native_parent'], 'pi-child-1')
            self.assertEqual(children['pi-child-2']['profile_id'], 'p1')
            self.assertEqual(children['pi-child-2']['lifecycle_proof'], tree['children'][1]['proof'])
            self.assertNotIn('assignment_generation', children['pi-child-2'])
            self.assertEqual((output / rows[0]['session_tree_manifest']).read_text(), (native_home / '.factory' / 'session-tree.json').read_text())
            self.assertEqual(json.loads((output / 'native' / 'manifest.json').read_text())['sessions'], rows)

    def test_pi_missing_escape_and_conflict_are_explicit_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            output = work / 'run'
            native_home = work / 'pi-home'
            root = native_home / 'root.jsonl'
            good = work / 'good.jsonl'
            other = work / 'other.jsonl'
            mismatch = work / 'mismatch.jsonl'
            escaped = work.parent / 'escaped.jsonl'
            write_jsonl(root, {'type': 'session', 'id': 'root'})
            write_jsonl(good, {'type': 'session', 'id': 'duplicate'})
            write_jsonl(other, {'type': 'session', 'id': 'duplicate', 'different': True})
            write_jsonl(mismatch, {'type': 'session', 'id': 'actual-id'})
            write_jsonl(escaped, {'type': 'session', 'id': 'escape'})
            (native_home / '.factory').mkdir(parents=True)
            (native_home / '.factory' / 'session-tree.json').write_text(json.dumps({
                'schema_version': 1, 'parent_native_session_id': 'root', 'children': [
                    {'parent_session_id': 'root', 'child_session_id': 'missing', 'evidence_source': 'test'},
                    {'parent_session_id': 'root', 'child_session_id': 'escape', 'session_file': str(escaped), 'evidence_source': 'test'},
                    {'parent_session_id': 'root', 'child_session_id': 'duplicate', 'session_file': str(good), 'evidence_source': 'test'},
                    {'parent_session_id': 'root', 'child_session_id': 'duplicate', 'session_file': str(other), 'evidence_source': 'test'},
                    {'parent_session_id': 'root', 'child_session_id': 'declared-id', 'session_file': str(mismatch), 'evidence_source': 'test'},
                ],
            }))
            rows = archive_sessions(output, work / 'home', work, [{
                'provider': 'pi', 'session_id': 'root', 'native_home': str(native_home),
                'native_session_path': str(root),
            }])
            errors = [row['archive_error'] for row in rows if row.get('archive_error')]
            self.assertEqual(len(errors), 4)
            self.assertTrue(any('缺少' in error for error in errors))
            self.assertTrue(any('不属于本次隔离目录' in error for error in errors))
            self.assertTrue(any('原生身份冲突' in error for error in errors))
            self.assertTrue(any('header 身份' in error for error in errors))
            self.assertEqual(len([row for row in rows if row.get('native_id') == 'duplicate']), 1)

    def test_codex_rollout_header_relation_discovers_two_levels(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            output = work / 'run'
            native_home = work / 'codex-home'
            root = native_home / 'sessions' / 'rollout-root.jsonl'
            child_one = native_home / 'sessions' / 'rollout-one.jsonl'
            child_two = native_home / 'sessions' / 'rollout-two.jsonl'
            write_jsonl(root, {'payload': {'id': 'codex-root'}})
            write_jsonl(child_one, {'payload': {'id': 'codex-one', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'codex-root', 'agent_role': 'explorer'}}}}})
            write_jsonl(child_two, {'payload': {'id': 'codex-two', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'codex-one', 'agent_role': 'executor'}}}}})
            rows = archive_sessions(output, work / 'unused-home', work, [{
                'provider': 'codex', 'session_id': 'codex-root', 'native_home': str(native_home),
                'native_session_path': str(root), 'profile_id': 'codex-profile',
                'work_item_kind': 'pr', 'work_item_id': '7', 'assignment_generation': 1,
            }])
            self.assertEqual([row['native_id'] for row in rows], ['codex-root', 'codex-one', 'codex-two'])
            self.assertEqual(rows[1]['parent_native_session_id'], 'codex-root')
            self.assertEqual(rows[2]['parent_native_session_id'], 'codex-one')
            self.assertEqual(rows[1]['native_role'], 'explorer')
            self.assertTrue(all(row['profile_id'] == 'codex-profile' for row in rows))
            self.assertNotIn('assignment_generation', rows[1])

    def test_legacy_entry_without_native_home_keeps_existing_behavior(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            source = work / 'legacy.jsonl'
            write_jsonl(source, {'type': 'session', 'id': 'legacy'})
            rows = archive_sessions(work / 'run', work / 'home', work, [{
                'provider': 'pi', 'session_id': str(source), 'native_session_path': str(source),
                'group_id': 'old', 'turns': [{'status': 'completed'}],
            }])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['group_id'], 'old')
            self.assertNotIn('archive_error', rows[0])

    def test_pi_message_id_cannot_masquerade_as_session_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp).resolve()
            source = work/'alias.jsonl'
            write_jsonl(source, {'type':'message','id':'79c55250','message':{'role':'user'}})
            rows = archive_sessions(work/'run',work/'home',work,[{
                'provider':'pi','session_id':str(source),'native_session_path':str(source)}])
            self.assertIn('session header',rows[0]['archive_error'])
            self.assertIsNone(rows[0]['native'])


if __name__ == '__main__':
    unittest.main()
