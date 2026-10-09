"""The host SDK, Linux material and child-domain boundary for ARC local execution."""
import ast
from copy import deepcopy
import json
import math
from pathlib import Path
from zipfile import ZipFile

from lab.exp.core import digest, identifier, require


def sdk_role(root):
    """Read the real host SDK interface without importing or executing its module."""
    root = Path(root).resolve(strict=True)
    entry = root / 'local_submit.py'
    tree = ast.parse(entry.read_text(), filename=str(entry))
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not {'main', 'run_container'} <= functions.keys():
        raise ValueError('ARC requires host SDK local_submit.py with main/run_container; image-internal runner is a different role')
    return {'kind': 'factory26.arc.host-sdk', 'schema_version': 1, 'entry': 'local_submit.py',
            'entry_sha256': digest(entry), 'environment_transfer': 'verified-at-child-create',
            'interface': ['main', 'run_container']}


def generation_inputs(inputs, sdk, *, expected_sdk=None, agent_provenance=None):
    """Validate bound producer output roles; unproduced references remain plans."""
    role = sdk_role(sdk)
    if expected_sdk is not None and role != expected_sdk:
        raise ValueError('bound ARC host SDK differs from the compiled role')
    required = {'agent', 'requirements', 'runner'}
    if not required <= inputs.keys():
        raise ValueError('ARC generation needs agent, requirements and host SDK inputs')
    agent, requirements = (Path(inputs[name]).resolve(strict=True) for name in ('agent', 'requirements'))
    if not requirements.is_dir() or not (requirements / 'requirements.yaml').is_file():
        raise ValueError('ARC generation requirements must be a directory containing requirements.yaml')
    def member(name, limit=None):
        if agent.is_dir():
            with (agent / name).open('rb') as stream:
                return stream.read() if limit is None else stream.read(limit)
        with ZipFile(agent) as archive:
            with archive.open(name) as stream:
                return stream.read() if limit is None else stream.read(limit)
    if agent.is_dir() and not (agent / 'package-manifest.json').is_file():
        if agent_provenance and agent_provenance.get('producer') == 'harness.delivery':
            definition = agent_provenance['definition']
            manifest = {'capabilities':definition['capabilities'], 'variant':definition['variant']}
        elif not agent_provenance or agent_provenance.get('producer') != 'harness' or not agent_provenance.get('material_id'):
            raise ValueError('directory Harness material needs its real bound producer provenance')
        else:
            manifest = {'capabilities': agent_provenance['capabilities'],
                        'variant': agent_provenance['dependencies']['variant']}
    else:
        manifest = json.loads(member('package-manifest.json'))
    replay = (agent / 'replay-manifest.json').is_file() if agent.is_dir() else False
    if not agent.is_dir():
        with ZipFile(agent) as archive:
            replay = 'replay-manifest.json' in archive.namelist()
    if replay:
        raise ValueError('ARC generation cannot consume an application replay as an agent')
    if agent.is_dir() and (agent/'delivery-layout.json').is_file() and json.loads((agent/'delivery-layout.json').read_text()).get('mode')=='sdk-components':
        return {'sdk':role,'agent':{'variant':manifest['variant'],'role_readiness':'authenticated at actual child placement'},'requirements':{'entry':'requirements.yaml','sha256':digest(requirements/'requirements.yaml')}}
    # Braid also uses the Pi backend; its frozen launcher lives under support/.
    pi = manifest.get('backend') == 'pi' and 'runtime/bin/braid' not in manifest.get('files', {})
    for name in (('runtime/bin/node',) if pi else ('runtime/bin/node', 'runtime/bin/braid')):
        header = member(name, 20)
        if header[:4] != b'\x7fELF' or header[4:6] != b'\x02\x01' or header[18:20] != b'\x3e\x00':
            raise ValueError('ARC Linux/amd64 Harness material needs a real ELF x86_64 binary: ' + name)
    for name in (('runtime/bin/pi', 'agent_support.py') if pi else ('support/agent_support.py', 'support/runtime_resources.py')):
        if not member(name, 1):
            raise ValueError('ARC Harness member is empty: ' + name)
    return {'sdk': role, 'agent': {'variant': manifest.get('capabilities', {}).get('variant', manifest.get('variant'))},
            'requirements': {'entry': 'requirements.yaml', 'sha256': digest(requirements / 'requirements.yaml')}}


def job(job_id, inputs, limits, target, competition, task, *, python='{runtime_python}',
        purpose='generate', requirements_only=True, labels=None, model_config=None,
        prepare_only=False, container_otlp_host=None, arc_contract=None):
    """Construct the shared host-SDK argv and owned child-domain recipe."""
    identifier(competition); identifier(task)
    needed = ('wall_seconds', 'storage_bytes', 'telemetry_bytes') + (() if prepare_only else ('memory_bytes', 'cpus', 'pids'))
    if any((type(limits.get(key)) not in (int, float) if key == 'cpus' else type(limits.get(key)) is not int)
           or not math.isfinite(limits.get(key, 0)) or limits.get(key, 0) <= 0 for key in needed):
        raise ValueError('ARC job needs positive explicit limits: ' + ', '.join(needed))
    if not prepare_only:
        if set(target) - {'endpoint', 'image_id', 'slots', 'admission_volume', 'authority_handoff', 'python'}:
            raise ValueError('unsupported ARC child target fields')
        if not all(target.get(key) for key in ('endpoint', 'image_id', 'slots', 'admission_volume', 'authority_handoff')):
            raise ValueError('ARC target needs endpoint/image/slots/admission/handoff')
        if not target['image_id'].startswith('sha256:'):
            raise ValueError('ARC target image must be an immutable image ID')
        endpoint = target['endpoint']
        if any(key not in endpoint for key in ('argv', 'daemon_id', 'remote')) or type(endpoint['remote']) is not bool:
            raise ValueError('ARC target must bind a complete frozen Docker endpoint including remote')
        require(target['authority_handoff'], 'authority-handoff')
        from lab.exp.admission import _target
        _target(target)
    command = [python, '-m', 'lab.arc_bench.arc_bench_adapter', '--runner', '{runner}',
               '--agent', '{agent}', '--requirements', '{requirements}', '--workspace', '{workspace}',
               '--competition', competition, '--task', task]
    if 'template' in inputs:
        command += ['--template', '{template}']
    if not requirements_only:
        command += ['--tests', '{tests}']
    if prepare_only:
        command += ['--prepare-only']
    else:
        command += ['--image', target['image_id'], '--memory', str(limits['memory_bytes']), '--cpus', str(limits['cpus']),
                    '--shared-docker-slots', str(target['slots']), '--admission-volume', target['admission_volume']]
    if requirements_only:
        command += ['--requirements-only']
    if container_otlp_host:
        command += ['--container-otlp-host', container_otlp_host]
    outputs = [{'name': 'workspace', 'type': 'terminal-archive', 'path': '.'},
               {'name': 'result', 'type': 'result', 'path': 'experiment-result.json'}]
    if purpose == 'generate' and not prepare_only:
        outputs += [{'name': 'application', 'type': 'application', 'path': 'official-generation/.lab-artifacts/application'},
                    {'name': 'application_receipt', 'type': 'application-receipt', 'path': 'official-generation/.lab-artifacts/receipt.json'}]
    result = {'id': job_id, 'purpose': purpose, 'inputs': deepcopy(inputs), 'limits': deepcopy(limits),
              'command': command, 'outputs': outputs,
              'backend': {'kind': 'local', 'capabilities_required': ['arc-sdk-host-docker'], 'external_docker': deepcopy(target)},
              'competition': competition, 'task': task, 'labels': deepcopy(labels or {})}
    if model_config:
        result['model_config'] = deepcopy(model_config)
        result['environment'] = {'MODEL': model_config['model'], 'VISUAL_MODEL': model_config['visual_model'],
                                 'OPENAI_BASE_URL': model_config['base_url'], 'FACTORY26_MODEL_PROVIDER': model_config['provider']}
    if arc_contract:
        result['arc_contract'] = deepcopy(arc_contract)
    return result
