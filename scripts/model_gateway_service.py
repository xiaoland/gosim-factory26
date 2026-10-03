"""Explicitly selected run-owned native model gateway service."""
import hashlib,json,os,secrets,shutil,time,subprocess,signal
from pathlib import Path
if __package__:
    from .agent_support import save,_signal_process,_wait_process,process_identity,process_evidence
    from .state_writer import spawn, closed
else:
    from agent_support import save,_signal_process,_wait_process,process_identity,process_evidence
    from state_writer import spawn, closed

def read_provider_environment(path, allowed=None):
    """Read one private provider-env JSON for the run-owned gateway only."""
    path = Path(path).resolve(strict=True)
    if path.stat().st_mode & 0o077:
        raise ValueError('private provider input must already be installed with mode 600')
    value = json.loads(path.read_text())
    if isinstance(value, dict) and set(value) == {'environment'}:
        value = value['environment']
    if not isinstance(value, dict) or not value:
        raise ValueError('provider-env must be a non-empty object')
    if allowed is not None and set(value) - set(allowed):
        raise ValueError('provider-env contains an undeclared credential')
    if any(not isinstance(name, str) or not name.isidentifier() or
           not isinstance(secret, str) or not secret for name, secret in value.items()):
        raise ValueError('provider-env contains an invalid name or empty credential')
    return value

def start_model_gateway(runtime, run, env, config, *, bindings=None, gateway_routes=None,
                        port=4011, host='127.0.0.1', provider_env=None,
                        preserve_parameters=None):
    """Start one run-owned frozen LiteLLM gateway and return its local contract.

    ``bindings`` is the already-frozen native route map.  The returned
    ``pi_environment`` contains only the local gateway token plus the rewritten
    bindings; upstream provider secrets stay in the gateway child.
    """
    if preserve_parameters is None:
        raise ValueError('gateway preserve_parameters must be frozen explicitly')
    runtime = Path(runtime).resolve(strict=True)
    run = Path(run).resolve(strict=True)
    config = Path(config).resolve(strict=True)
    launcher = runtime/'bin/litellm'
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise FileNotFoundError(f'冻结 runtime 缺少 LiteLLM launcher: {launcher}')
    if not config.is_file() or not config.resolve().is_relative_to(run):
        raise ValueError('gateway config must be a run-local frozen file')
    if not 0 < int(port) < 65536 or host not in {'127.0.0.1', '::1'}:
        raise ValueError('run-owned gateway must use a loopback unprivileged port')
    environment = dict(env)
    values = read_provider_environment(provider_env) if provider_env is not None else {}
    if gateway_routes is not None:
        if isinstance(gateway_routes, (str, Path)):
            route_path = Path(gateway_routes).resolve(strict=True)
            gateway_routes = json.loads(route_path.read_text())
        if not isinstance(gateway_routes, dict):
            raise ValueError('gateway-routes must be an object keyed by stable alias')
        if any(not isinstance(alias, str) or not isinstance(chain, list) or
               not chain or any(not isinstance(item, str) or not item for item in chain)
               for alias, chain in gateway_routes.items()):
            raise ValueError('gateway-routes values must be non-empty deployment ID lists')
    environment.update(values)
    state = run/'model-gateway'
    state.mkdir(mode=0o700, exist_ok=True)
    log = state/'gateway.log'
    (state/'bindings').mkdir(mode=0o700, exist_ok=True)
    code = state/'code'
    code.mkdir(mode=0o700, exist_ok=True)
    support_root = Path(__file__).resolve().parent
    for name in ('hackathon_gateway_compat.py', 'responses_compat.py'):
        shutil.copy2(support_root/name, code/name)
    route_record = state/'gateway-routes.json'
    if gateway_routes is not None:
        route_record.write_text(json.dumps(gateway_routes, ensure_ascii=False, indent=2) + '\n')
        route_record.chmod(0o600)
    local_token = secrets.token_urlsafe(32)
    master_key = secrets.token_urlsafe(32)
    binding_id = hashlib.sha256(local_token.encode()).hexdigest()
    binding_path = state/'bindings'/f'{binding_id}.json'
    binding = {'binding_id': binding_id,
               'run_id': environment.get('FACTORY26_EXP_RUN_ID', run.name),
               'attempt_id': environment.get('FACTORY26_EXP_ATTEMPT_ID'),
               'experiment_id': environment.get('FACTORY26_EXP_EXPERIMENT_ID'),
               'incarnation': environment.get('FACTORY26_EXP_INCARNATION_ID'),
               'config_sha256': None}
    # Materialize the run-owned config so direct callers cannot accidentally
    # omit auth/callbacks or leave upstream base URLs unresolved.
    config_value = json.loads(config.read_text())
    config_value.setdefault('general_settings', {}).update(
        master_key='os.environ/LITELLM_MASTER_KEY',
        custom_auth='hackathon_gateway_compat.user_api_key_auth')
    config_value.setdefault('litellm_settings', {}).update(
        telemetry=False, callbacks=['hackathon_gateway_compat.proxy_handler_instance'])
    selected_env = set()
    for entry in config_value.get('model_list', []):
        params = entry.setdefault('litellm_params', {})
        params.setdefault('use_chat_completions_api', True)
        base = params.get('api_base')
        if isinstance(base, str) and base.startswith('os.environ/'):
            name = base.removeprefix('os.environ/')
            selected_env.add(name)
            if not environment.get(name):
                raise ValueError(f'gateway config references missing provider endpoint: {name}')
            params['api_base'] = environment[name]
        key_ref = params.get('api_key')
        if isinstance(key_ref, str) and key_ref.startswith('os.environ/'):
            selected_env.add(key_ref.removeprefix('os.environ/'))
    if set(values) - selected_env:
        raise ValueError('provider-env contains credentials outside the selected gateway catalog')
    config.write_text(json.dumps(config_value, ensure_ascii=False, indent=2) + '\n')
    config.chmod(0o600)
    binding['config_sha256'] = hashlib.sha256(config.read_bytes()).hexdigest()
    binding_path.write_text(json.dumps(binding, ensure_ascii=False) + '\n')
    binding_path.chmod(0o600)
    environment.update(LITELLM_MASTER_KEY=master_key,
                       GATEWAY_REQUEST_LOG=str(state/'request-metadata.jsonl'),
                       GATEWAY_BINDINGS_DIR=str(state/'bindings'),
                       GATEWAY_PRESERVE_PARAMETERS='1' if preserve_parameters else '0',
                       PYTHONPATH=os.pathsep.join((str(code), str(runtime/'python'),
                                                   environment.get('PYTHONPATH', ''))).strip(os.pathsep))
    command = [str(launcher), '--config', str(config), '--host', host, '--port', str(port)]
    with log.open('a') as stream:
        child = spawn(command, environment=environment, role='service',cwd=run, stdout=stream,
                                 stderr=subprocess.STDOUT, start_new_session=True)
    identity = process_identity(child.pid)
    process_evidence(run, 'operations.jsonl', {'kind': 'process_started', 'role': 'model-gateway',
                                               'process': identity, 'log': str(log)})
    try:
        from urllib.request import urlopen
        deadline = time.monotonic() + 30
        while child.poll() is None and time.monotonic() < deadline:
            try:
                with urlopen(f'http://{host}:{port}/health/liveliness', timeout=1) as response:
                    if response.status == 200:
                        endpoint = f'http://{host}:{port}/v1'
                        local_bindings = None
                        if bindings is not None:
                            local_bindings = {}
                            for name, route in bindings.items():
                                route = dict(route)
                                route['base_url'] = endpoint
                                route['credential_env'] = 'FACTORY26_GATEWAY_TOKEN'
                                local_bindings[name] = route
                        # Remove only the credentials explicitly assembled for this
                        # gateway.  Tool credentials (for example Context7/Exa) have
                        # a separate contract and must remain available to Pi.
                        pi_environment = {key: value for key, value in env.items()
                                          if key not in values}
                        pi_environment['FACTORY26_GATEWAY_TOKEN'] = local_token
                        if local_bindings is not None:
                            pi_environment['FACTORY26_MODEL_BINDINGS'] = json.dumps(local_bindings, separators=(',', ':'))
                        handle = {'owner': 'run', 'process': child, 'identity': identity,
                                  'pid': child.pid, 'endpoint': endpoint, 'port': port,
                                  'config': str(config), 'log': str(log),
                                  'routes': str(route_record) if gateway_routes is not None else None,
                                  'pi_environment': pi_environment}
                        save(run/'model-gateway.json', {key: value for key, value in handle.items()
                                                       if key not in {'process', 'pi_environment'}})
                        return handle
            except OSError:
                pass
            time.sleep(.2)
        raise RuntimeError(f'model gateway readiness timed out; raw output: {log}')
    except BaseException:
        _signal_process(child, signal.SIGTERM, run, 'model-gateway-start-failed')
        raise

def stop_model_gateway(handle, run):
    """Close the exact run-owned service and its authority registration."""
    child = handle['process'] if isinstance(handle, dict) else handle
    if child.poll() is None:
        _signal_process(child, signal.SIGTERM, run, 'model-gateway-stop')
    result = _wait_process(child, run, 'model-gateway-stop', timeout=5)
    closed(getattr(child, '_state_writer', None))
    return result
