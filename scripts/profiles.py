"""Resolve Factory presets; Braid receives only ordinary profiles and bindings."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VARIANT = 'pi-generalist'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError(f'invalid configuration identifier: {value!r}')
    return value


def material(path, root=ROOT):
    file = (root/path).resolve(strict=True)
    if not file.is_relative_to((root/'harness').resolve()):
        raise ValueError(f'material outside harness: {path}')
    return file.read_text()


def resolve(variant=DEFAULT_VARIANT, root=ROOT):
    preset = read(root/'variants'/identifier(variant)/'preset.json')
    if set(preset) != {'profiles', 'defaults'}:
        raise ValueError('preset owns profiles and defaults only')
    ids = preset['profiles']
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('preset requires distinct profile IDs')
    if set(preset['defaults']) != {'issue', 'pr'} or not set(preset['defaults'].values()) <= set(ids):
        raise ValueError('default assignment must reference a selected profile')
    catalog = read(root/'harness/models.json')
    dependencies = read(root/'harness/dependencies.lock.json')
    common = {'navigation': material('harness/AGENTS.md', root),
              'npm_sha256': hashlib.sha256((root/dependencies['npm_lock']).read_bytes()).hexdigest()}
    expanded = {}
    for profile_id in ids:
        profile = read(root/'harness/profiles'/f'{identifier(profile_id)}.json')
        if set(profile) != {'id','core','model','reasoning','instructions','skills','cli','native_subagents','mcp'}:
            raise ValueError(f'unknown or missing profile fields: {profile_id}')
        if profile.get('id') != profile_id or profile.get('core') not in ('pi', 'codex'):
            raise ValueError(f'invalid profile {profile_id}')
        if profile.get('mcp') != []:
            raise ValueError('MCP configuration has no runtime consumer yet')
        if profile.get('cli') != ['svc', 'braid', 'agent-browser']:
            raise ValueError('unsupported CLI capability selection')
        instructions = '\n\n'.join(material(p, root) for p in profile['instructions'])
        roles, skills, models = {}, {}, {}
        for role_id in profile['native_subagents']:
            role = read(root/'harness/subagents'/f'{identifier(role_id)}.json')
            if set(role) != {'id','name','model','reasoning','skills','tools','instructions','mcp'}:
                raise ValueError(f'unknown or missing native role fields: {role_id}')
            if role.get('id') != role_id or role['name'] in roles or role.get('mcp') != []:
                raise ValueError(f'invalid/duplicate native role {role_id}')
            roles[role['name']] = dict(role, instructions=material(role['instructions'], root))
        for user in [profile, *roles.values()]:
            model = user['model']
            if model not in catalog['models'] or user['reasoning'] != 'high':
                raise ValueError(f'unsupported model/reasoning in {user["id"]}')
            models[model] = catalog['models'][model]
            for skill in user['skills']:
                identifier(skill)
                directory = root/'harness/skills'/skill
                files = {str(p.relative_to(directory)): material(str(p.relative_to(root)), root)
                         for p in sorted(directory.rglob('*')) if p.is_file()}
                if 'SKILL.md' not in files:
                    raise ValueError(f'missing skill: {skill}')
                skills[skill] = files
        payload = dict(profile=profile, instructions=instructions, roles=roles, skills=skills,
                       models=models, common=common, provider={k:v for k,v in catalog.items() if k!='models'},
                       core_version=dependencies['codex'] if profile['core']=='codex' else '0.85.1')
        if profile['core']=='pi':
            payload['lifecycle_extension'] = material('harness/extensions/factory-subagent-lifecycle.ts', root)
        expanded[profile_id] = dict(payload, effective_profile_digest=digest(payload))
    cores = {p['profile']['core'] for p in expanded.values()}
    if len(cores) != 1:
        raise ValueError('current Factory run selects a single native core')
    result = dict(schema_version=1, variant=variant, defaults=preset['defaults'], profiles=expanded,
                  provider={k:v for k,v in catalog.items() if k != 'models'})
    return dict(result, effective_digest=digest(result))


def configuration(variant=DEFAULT_VARIANT, task='keep', root=ROOT):
    effective = resolve(variant, root)
    experiment = read(root/'experiments/multi-agent-lite.json')
    if task not in experiment['tasks']:
        raise ValueError(f'task not selected for this batch: {task}')
    first = effective['profiles'][effective['defaults']['issue']]['profile']
    return dict(variant=variant, task=task, backend=first['core'], model=first['model'],
                thinking=first['reasoning'], svc=True, workflow='braid',
                base_url=effective['provider']['base_url'], deployment=experiment['deployment'],
                benchmark_url=experiment['benchmark_url'], benchmark_revision=experiment['benchmark_revision'],
                effective=effective)
