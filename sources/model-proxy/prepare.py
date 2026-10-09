"""Freeze an independent proxy instance from the existing provider catalog."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_proxy(selected, routes, values, state, run_id, listen, *,
                 catalog_sha256, routes_sha256):
    """Freeze an already-selected catalog without choosing routes or reading secrets."""
    state = Path(state).resolve()
    if sys.platform == 'darwin':
        volume = Path('/Volumes/WorkSSD').resolve(strict=True)
        parent = state
        while not parent.exists():
            parent = parent.parent
        if not state.is_relative_to(volume) or parent.stat().st_dev != volume.stat().st_dev:
            raise ValueError('Mac proxy state must physically reside on WorkSSD')
    if not isinstance(routes, dict) or not routes or any(
        not isinstance(alias, str) or not alias or
        not isinstance(ids, list) or not 1 <= len(ids) <= 4 or
        any(not isinstance(item, str) or not item for item in ids)
        for alias, ids in routes.items()
    ):
        raise ValueError('routes must contain one to four ordered deployment IDs per alias')
    deployments, provider_env, selected_env, observed = [], {}, set(), {}
    for entry in selected['model_list']:
        params, info = entry['litellm_params'], entry['model_info']
        if set(params) - {'model', 'api_base', 'api_key', 'order', 'use_chat_completions_api'}:
            raise ValueError('selected catalog contains unsupported request-affecting parameters')
        if params.get('use_chat_completions_api', True) is not True:
            raise ValueError('Rust proxy requires native Chat deployments')
        if not params['model'].startswith('openai/'):
            raise ValueError('only native OpenAI-compatible Chat deployments are supported')
        if any(not params[field].startswith('os.environ/') for field in ('api_base', 'api_key')):
            raise ValueError('selected provider references must be explicit environment names')
        for field in ('contextWindow', 'maxTokens'):
            if field in info and (isinstance(info[field], bool) or
                                  not isinstance(info[field], int) or info[field] <= 0):
                raise ValueError(f'{field} must be a positive integer')
        if 'compat' in info and not isinstance(info['compat'], dict):
            raise ValueError('model_info.compat must be an object')
        base_env = params['api_base'].removeprefix('os.environ/')
        key_env = params['api_key'].removeprefix('os.environ/')
        if not values.get(base_env) or not values.get(key_env):
            raise ValueError(f'selected deployment requires {base_env} and {key_env}')
        selected_env.update((base_env, key_env))
        provider_env[key_env] = values[key_env]
        observed.setdefault(entry['model_name'], []).append(
            (params['order'], info['factory26_deployment_id']))
        deployments.append(dict(alias=entry['model_name'], order=params['order'],
                                deployment_id=info['factory26_deployment_id'],
                                provider=info['factory26_provider'], plan=info['factory26_plan'],
                                wire_model=params['model'].removeprefix('openai/'),
                                model_info=dict(info),
                                base_url=values[base_env], credential_env=key_env))
    expected = {alias: list(enumerate(ids)) for alias, ids in routes.items()}
    if {alias: sorted(chain) for alias, chain in observed.items()} != expected:
        raise ValueError('selected catalog does not match the frozen ordered routes')
    if set(values) != selected_env:
        raise ValueError('provider environment must exactly supply selected references')
    token = secrets.token_urlsafe(32)
    total_ms = 600000
    config = dict(run_id=run_id, listen=listen,
                  catalog_sha256=catalog_sha256, routes_sha256=routes_sha256,
                  deployments=deployments,
                              limits=dict(connect_ms=10000, headers_ms=600000, body_ms=30000,
                              stream_idle_ms=60000, total_ms=total_ms, shutdown_ms=8000,
                              error_bytes=4096))
    state.mkdir(parents=True, exist_ok=False)
    private = state / '.private'
    private.mkdir(mode=0o700)
    provider_env['FACTORY26_GATEWAY_TOKEN'] = token
    config_bytes = (json.dumps(config, ensure_ascii=False, indent=2) + '\n').encode()
    (state / 'config.json').write_bytes(config_bytes)
    (state / 'config.json').chmod(0o444)
    (state / 'config.sha256').write_text(hashlib.sha256(config_bytes).hexdigest() + '\n')
    for path, content in (
        (private / 'provider-env.json', json.dumps({'environment': provider_env}) + '\n'),
        (private / 'client.env', f'FACTORY26_GATEWAY_TOKEN={token}\n'
         f'FACTORY26_BASE_URL=http://{listen}/v1\n'),
    ):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as output:
            output.write(content)
    return {'state': str(state), 'run_id': run_id, 'token': token,
            'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
            'credential_names': sorted(selected_env), 'aliases': list(routes),
            'shutdown_seconds': config['limits']['shutdown_ms'] / 1000}


def main():
    # Installed support supplies this adjacent module; source CLI uses scripts/.
    if (ROOT / 'tooling/scripts/hackathon_gateway.py').is_file():
        sys.path.insert(0, str(ROOT / 'tooling/scripts'))
    from hackathon_gateway import read_assignments, prepare_catalog
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--routes', type=Path, required=True)
    parser.add_argument('--credentials', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--listen', default='127.0.0.1:4021')
    args = parser.parse_args()
    routes = json.loads(args.routes.read_text())
    selected, _ = prepare_catalog(args.catalog, routes, aliases=list(routes))
    references = {entry['litellm_params'][field].removeprefix('os.environ/')
                  for entry in selected['model_list'] for field in ('api_base', 'api_key')}
    values = read_assignments(args.credentials)
    result = freeze_proxy(selected, routes, {key: values[key] for key in references if key in values}, args.state,
                          args.run_id, args.listen, catalog_sha256=digest(args.catalog),
                          routes_sha256=digest(args.routes))
    print(json.dumps({key: value for key, value in result.items() if key != 'token'}))


if __name__ == '__main__':
    main()
