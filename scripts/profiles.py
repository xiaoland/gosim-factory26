"""Resolve one Factory variant into its complete runtime capability contract."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VARIANT = 'pi-team-mixed'
PROFILE_FIELDS = {'id', 'assignee_login', 'assignee_description', 'core', 'provider', 'model',
                  'reasoning', 'instructions', 'skills', 'cli', 'native_subagents', 'mcp', 'context'}
ROLE_FIELDS = {'id', 'name', 'provider', 'model', 'reasoning', 'skills', 'tools', 'instructions',
               'mcp', 'context'}
INTERNAL_DESCRIPTION_WORDS = ('braid', 'profile', 'preset', 'variant', 'model', 'provider',
                              'digest', 'generation', 'session')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError(f'invalid configuration identifier: {value!r}')
    return value


def assignee_login(value):
    if not isinstance(value, str) or len(value) > 39 or not re.fullmatch(
            r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError(f'invalid assignee login: {value!r}')
    return value


def assignee_description(value):
    if (not isinstance(value, str) or not value or '\n' in value or '\r' in value
            or len(value.encode()) > 240 or any(word in value.lower() for word in INTERNAL_DESCRIPTION_WORDS)):
        raise ValueError('invalid assignee description')
    return value


def resolve(variant=DEFAULT_VARIANT, root=ROOT):
    root = root.resolve()
    materials = {}

    def bytes_at(relative, boundary=root):
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(boundary.resolve()):
            raise ValueError(f'material outside allowed root: {relative}')
        data = path.read_bytes()
        materials[Path(relative).as_posix()] = hashlib.sha256(data).hexdigest()
        return data

    def json_at(relative, boundary=root):
        return json.loads(bytes_at(relative, boundary))

    def harness_text(relative):
        if not Path(relative).parts or Path(relative).parts[0] != 'harness':
            raise ValueError(f'material outside harness: {relative}')
        return bytes_at(relative, root / 'harness').decode()

    variant_path = f'variants/{identifier(variant)}/variant.json'
    selected = json_at(variant_path)
    if set(selected) != {'schema_version', 'profiles', 'defaults', 'svc'} or selected['schema_version'] != 1:
        raise ValueError('unknown or missing variant fields')
    ids = selected['profiles']
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('variant requires distinct profile IDs')
    selected_defaults = selected['defaults']
    if set(selected_defaults) != {'issue', 'pull_request'}:
        raise ValueError('variant defaults must select issue and pull_request assignees')

    svc_source = selected['svc']
    if (set(svc_source) != {'source_revision', 'index', 'preload'}
            or not re.fullmatch(r'[0-9a-f]{40}', svc_source['source_revision'])):
        raise ValueError('invalid SVC selection')
    svc_root = root / 'sources/svc/corpus'

    def svc_entry(relative, content=False):
        if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError(f'invalid SVC path: {relative!r}')
        body = bytes_at(f'sources/svc/corpus/{relative}', svc_root)
        result = {'path': relative, 'sha256': hashlib.sha256(body).hexdigest()}
        if content:
            result['content'] = body.decode()
        return result

    if len(set(svc_source['preload'])) != len(svc_source['preload']):
        raise ValueError('duplicate SVC preload')
    svc = {'source_revision': svc_source['source_revision'],
           'index': svc_entry(svc_source['index']),
           'preload': [svc_entry(path, True) for path in svc_source['preload']]}

    catalog = json_at('harness/models.json', root / 'harness')
    package = json_at('harness/npm/package.json', root / 'harness')
    npm_lock = bytes_at('harness/npm/package-lock.json', root / 'harness')
    common = {'navigation': harness_text('harness/AGENTS.md'),
              'npm_sha256': hashlib.sha256(npm_lock).hexdigest()}
    expanded = {}
    logins = set()
    profiles_by_login = {}
    for profile_id in ids:
        profile_id = identifier(profile_id)
        profile = json_at(f'harness/profiles/{profile_id}.json', root / 'harness')
        if set(profile) != PROFILE_FIELDS or profile.get('id') != profile_id or profile.get('core') != 'pi':
            raise ValueError(f'unknown or missing profile fields: {profile_id}')
        login = assignee_login(profile['assignee_login'])
        assignee_description(profile['assignee_description'])
        if login in logins:
            raise ValueError(f'duplicate assignee login: {login}')
        logins.add(login)
        profiles_by_login[login] = profile_id
        if (profile['provider'] != 'text' or profile['mcp'] != []
                or profile['cli'] != ['svc', 'braid', 'agent-browser']
                or set(profile['context']) != {'soft_ratio', 'hard_bytes'}
                or not 0 < profile['context']['soft_ratio'] < 1
                or not isinstance(profile['context']['hard_bytes'], int)
                or profile['context']['hard_bytes'] <= 0):
            raise ValueError(f'invalid profile capability contract: {profile_id}')
        instructions = '\n\n'.join(harness_text(path) for path in profile['instructions'])
        roles, skills, models = {}, {}, {}
        for role_id in profile['native_subagents']:
            role_id = identifier(role_id)
            role = json_at(f'harness/subagents/{role_id}.json', root / 'harness')
            if set(role) != ROLE_FIELDS or role.get('id') != role_id or role['name'] in roles:
                raise ValueError(f'unknown or duplicate native role: {role_id}')
            if (role['provider'] not in ('text', 'visual') or role.get('mcp') != []
                    or role.get('context') != {'mode': 'fresh'}):
                raise ValueError(f'invalid native role capability contract: {role_id}')
            roles[role['name']] = dict(role, instructions=harness_text(role['instructions']))
        for consumer in [profile, *roles.values()]:
            model = consumer['model']
            if model not in catalog['models'] or consumer['reasoning'] not in catalog['models'][model]['reasoning_levels']:
                raise ValueError(f'unsupported model/reasoning in {consumer["id"]}')
            if consumer['provider'] == 'visual' and 'image' not in catalog['models'][model]['descriptor']['input']:
                raise ValueError(f'visual role lacks image model: {consumer["id"]}')
            models[model] = catalog['models'][model]
            for skill in consumer['skills']:
                identifier(skill)
                directory = root / 'harness/skills' / skill
                files = {str(path.relative_to(directory)): harness_text(str(path.relative_to(root)))
                         for path in sorted(directory.rglob('*')) if path.is_file()}
                if 'SKILL.md' not in files:
                    raise ValueError(f'missing skill: {skill}')
                skills[skill] = files
        payload = dict(profile=profile, instructions=instructions, roles=roles, skills=skills,
                       models=models, common=common,
                       provider={key: value for key, value in catalog.items() if key != 'models'},
                       core_version=package['dependencies']['@earendil-works/pi-coding-agent'],
                       observer_extension=harness_text('harness/extensions/factory-subagent-observer.ts'),
                       svc_preload=svc['preload'])
        expanded[profile_id] = dict(payload, effective_profile_digest=digest(payload))
    if not set(selected_defaults.values()) <= set(profiles_by_login):
        raise ValueError('default assignment must reference a selected assignee')
    defaults = {'issue': profiles_by_login[selected_defaults['issue']],
                'pr': profiles_by_login[selected_defaults['pull_request']]}
    result = dict(schema_version=2, variant=variant, defaults=defaults, profiles=expanded, svc=svc,
                  provider={key: value for key, value in catalog.items() if key != 'models'},
                  materials=materials)
    semantic = {key: value for key, value in result.items() if key not in ('variant', 'materials')}
    return dict(result, effective_digest=digest(semantic))


def configuration(variant=DEFAULT_VARIANT, task='keep', root=ROOT):
    effective = resolve(variant, root)
    experiment = json.loads((root / 'experiments/multi-agent-lite.json').read_text())
    if task not in experiment['tasks']:
        raise ValueError(f'task not selected for this batch: {task}')
    first = effective['profiles'][effective['defaults']['issue']]['profile']
    return dict(variant=variant, task=task, backend=first['core'], model=first['model'],
                thinking=first['reasoning'], svc=True, workflow='braid',
                base_url=effective['provider']['base_url'], deployment=experiment['deployment'],
                benchmark_url=experiment['benchmark_url'], benchmark_revision=experiment['benchmark_revision'],
                effective=effective)
