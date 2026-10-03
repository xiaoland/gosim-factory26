"""Namespace-local execution facts; artifact members never become host paths."""
import json
import os
from pathlib import Path, PurePosixPath


def member_join(base, relative):
    values = []
    for text in (base, relative):
        path = PurePosixPath(text)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('definition member must remain inside its artifact')
        values.extend(part for part in path.parts if part != '.')
    return '/'.join(values) or '.'


def write(path, value, *, private=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644), 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read(path=None):
    path = path or os.environ.get('FACTORY26_EXECUTION_CONTEXT')
    if not path:
        return None
    value = json.loads(Path(path).read_text())
    if value.get('kind') != 'factory26.execution.context' or value.get('schema_version') != 1:
        raise ValueError('unsupported execution context')
    if value.get('status') != 'ready':
        raise ValueError('execution context is not ready')
    for row in value['assembly']['definitions']:
        member_join(row.get('member', '.'), '.')
        root = Path(row['local_root'])
        if not root.is_absolute() or not root.exists():
            raise ValueError('definition role is unavailable in this namespace: ' + row['role'])
    return value


def role(value, name):
    rows = [row for row in value['assembly']['definitions'] if row['role'] == name]
    if len(rows) != 1:
        raise ValueError('execution context needs exactly one definition role: ' + name)
    return Path(rows[0]['local_root'])


def state_root(output=None):
    value = read()
    if value is None:
        return None
    root = Path(value['assembly']['state']['root'])
    if not root.is_absolute():
        raise ValueError('state root must be namespace-local absolute path')
    return root


def environment(value):
    """Derive old entry variables from one context, never from parallel claims."""
    services = value['services']
    result = {'FACTORY26_EXP_ATTEMPT_ID': value['attempt_id'],
              'FACTORY26_EXP_INCARNATION': value['incarnation_id'],
              'FACTORY26_EXP_SERVICES': json.dumps(services),
              'FACTORY26_EXP_INPUT_BINDINGS': json.dumps({**value['assembly'].get('inputs',{}), **{row['role']: {
                  'reference': row.get('reference'), 'member': row.get('member', '.'),
                  'store': row.get('store'), 'root': row['local_root']}
                  for row in value['assembly']['definitions'] if row.get('reference')}})}
    resource = services.get('resource_evidence', {})
    if resource.get('status') == 'ready':
        result['FACTORY26_EXP_RESOURCE_SAMPLE'] = resource['sample_path']
    receiver = services.get('telemetry', {})
    if receiver.get('status') == 'ready':
        binding = receiver['binding']
        result['FACTORY26_EXP_TELEMETRY_BINDING'] = json.dumps(binding)
        result.update(OTEL_EXPORTER_OTLP_ENDPOINT=binding['endpoint'],
                      OTEL_EXPORTER_OTLP_PROTOCOL='http/protobuf',
                      OTEL_EXPORTER_OTLP_HEADERS='x-experiment-token=' + binding['token'])
        for signal in ('TRACES', 'LOGS', 'METRICS'):
            result['OTEL_EXPORTER_OTLP_' + signal + '_ENDPOINT'] = binding['endpoint'] + '/v1/' + signal.lower()
            result['OTEL_EXPORTER_OTLP_' + signal + '_PROTOCOL'] = 'http/protobuf'
            result['OTEL_EXPORTER_OTLP_' + signal + '_HEADERS'] = result['OTEL_EXPORTER_OTLP_HEADERS']
    return result


def create(assembly, services, attempt_id, incarnation_id, path, model_policy=None):
    value = {'kind': 'factory26.execution.context', 'schema_version': 1, 'status': 'ready',
             'assembly': assembly, 'attempt_id': attempt_id, 'incarnation_id': incarnation_id,
             'services': services, 'model_policy':dict(model_policy or {}),
             'credential_variables':sorted({row['credential_env'] for row in json.loads((model_policy or {}).get('FACTORY26_MODEL_BINDINGS','{}')).values()})}
    for name in ('resource_evidence', 'telemetry'):
        service = services.get(name, {})
        if service.get('status') not in ('ready', 'disabled'):
            raise ValueError('required execution service is unavailable: ' + name)
    if services['telemetry']['status'] == 'ready':
        binding = services['telemetry'].get('binding', {})
        if binding.get('attempt_id') != attempt_id or not all(binding.get(name) for name in ('endpoint', 'token', 'stream_id', 'collector_epoch')):
            raise ValueError('telemetry instance does not bind this execution context')
    write(path, value, private=True)
    return value
