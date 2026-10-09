"""Explicitly selected run-owned native model gateway service."""
import hashlib,json,os,secrets,time,subprocess,signal,threading,importlib.util
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
                        preserve_parameters=None, implementation='litellm', binary_sha256=None):
    """Start the explicitly selected gateway; keep provider secrets out of clients."""
    if implementation == 'rust':
        return _start_rust_gateway(runtime, run, env, config, bindings=bindings,
            gateway_routes=gateway_routes, port=port, host=host, provider_env=provider_env,
            preserve_parameters=preserve_parameters, binary_sha256=binary_sha256)
    if implementation != 'litellm':
        raise ValueError(f'unknown model gateway implementation: {implementation}')
    return _start_litellm_gateway(runtime, run, env, config, bindings=bindings,
        gateway_routes=gateway_routes, port=port, host=host, provider_env=provider_env,
        preserve_parameters=preserve_parameters)


def _start_litellm_gateway(runtime, run, env, config, *, bindings=None, gateway_routes=None,
                           port=4011, host='127.0.0.1', provider_env=None,
                           preserve_parameters=None):
    """Retain the frozen LiteLLM contract for callers selecting the historical backend.

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
    # The selected gateway role already freezes these modules; only mutable
    # configuration and receipts belong to the run's private state.
    code = Path(__file__).resolve().parent
    for name in ('hackathon_gateway_compat.py', 'responses_compat.py'):
        if not (code/name).is_file():
            raise FileNotFoundError(code/name)
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
                        handle = {'owner': 'run', 'implementation': 'litellm', 'process': child, 'identity': identity,
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
        stop_model_gateway({'process': child}, run)
        raise


def _capture_gateway_log(child, log, run, *, cap_bytes=8*1024*1024):
    """Drain stdout after the retention cap so diagnostics cannot block the proxy."""
    def capture():
        retained, dropped = 0, 0
        try:
            with log.open('xb', buffering=0) as output, child.stdout:
                while chunk := child.stdout.read1(65536):
                    keep = chunk[:max(0, cap_bytes-retained)]
                    if keep:
                        output.write(keep)
                        retained += len(keep)
                    dropped += len(chunk)-len(keep)
                    if dropped and not log.with_suffix('.capped.json').exists():
                        save(log.with_suffix('.capped.json'), {'cap_bytes': cap_bytes,
                            'retained_bytes': retained, 'later_output': 'drained-without-retention'})
        except OSError as error:
            process_evidence(run, 'operations.jsonl', {'kind': 'gateway_log_error',
                'log': str(log), 'error': {'type': type(error).__name__, 'message': str(error)}})
    thread = threading.Thread(target=capture, name='model-gateway-log', daemon=True)
    thread.start()
    return thread


def _start_rust_gateway(runtime, run, env, config, *, bindings, gateway_routes,
                        port, host, provider_env, preserve_parameters, binary_sha256):
    from lab.control import process_identity as physical_identity, process_state
    if preserve_parameters is not True:
        raise ValueError('Rust gateway requires preserve_parameters=True')
    runtime, run, config = (Path(path).resolve(strict=True) for path in (runtime, run, config))
    if not config.is_file() or not config.is_relative_to(run):
        raise ValueError('gateway config must be a run-local frozen file')
    if type(port) is not int or not 1024 <= port < 65536 or host not in {'127.0.0.1', '::1'}:
        raise ValueError('run-owned gateway must use a loopback unprivileged port')
    launcher = runtime/'bin/factory26-model-proxy'
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise FileNotFoundError(f'冻结 runtime 缺少 Rust proxy: {launcher}')
    actual_binary_sha = hashlib.sha256(launcher.read_bytes()).hexdigest()
    if binary_sha256 is not None and actual_binary_sha != binary_sha256:
        raise ValueError('Rust proxy binary differs from the explicitly frozen identity')
    if provider_env is None or gateway_routes is None:
        raise ValueError('Rust gateway requires explicit private provider-env and ordered routes')
    source_routes = Path(gateway_routes).resolve(strict=True) if isinstance(gateway_routes, (str, Path)) else None
    source_route_bytes = source_routes.read_bytes() if source_routes else None
    routes = json.loads(source_route_bytes) if source_route_bytes is not None else gateway_routes
    route_bytes = (json.dumps(routes, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
    route_sha = hashlib.sha256(route_bytes).hexdigest()
    source_bytes = config.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    selected = json.loads(source_bytes)
    code = Path(__file__).resolve().parent
    adapter = code/'model_proxy_prepare.py'
    if not adapter.is_file():
        adapter = code.parents[1]/'sources/model-proxy/prepare.py'
    spec = importlib.util.spec_from_file_location('model_proxy_prepare', adapter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    listen = f'[{host}]:{port}' if host == '::1' else f'{host}:{port}'
    state = run/'model-gateway'
    values = read_provider_environment(provider_env)
    frozen = module.freeze_proxy(selected, routes, values, state,
        env.get('FACTORY26_EXP_RUN_ID', run.name), listen,
        catalog_sha256=source_sha, routes_sha256=route_sha)
    (state/'gateway-routes.json').write_bytes(route_bytes)
    (state/'gateway-routes.json').chmod(0o444)
    endpoint = f'http://{listen}/v1'
    # Strip every catalog-declared provider variable, including inactive rows,
    # without stripping separately authorized tool credentials.
    provider_names = set(values)
    catalog = code/'model-gateway.json'
    if not catalog.is_file():
        catalog = code.parents[1]/'materials/model-gateway.json'
    for entry in json.loads(catalog.read_text())['model_list']:
        for field in ('api_base', 'api_key'):
            provider_names.add(entry['litellm_params'][field].removeprefix('os.environ/'))
    provider_names.update(('OPENAI_API_KEY', 'FACTORY26_API_KEY', 'VISUAL_API_KEY',
                           'FACTORY26_VISUAL_API_KEY', 'LITELLM_MASTER_KEY', 'FACTORY26_PROVIDER_ENV'))
    pi_environment = {key: value for key, value in env.items() if key not in provider_names}
    pi_environment.update(FACTORY26_GATEWAY_TOKEN=frozen['token'], FACTORY26_BASE_URL=endpoint)
    if any(key.startswith('E2E_') for key in env):
        pi_environment.update(E2E_API_KEY=frozen['token'], E2E_BASE_URL=endpoint)
    local_bindings = None
    if bindings is not None:
        local_bindings = {name: dict(route, base_url=endpoint, credential_env='FACTORY26_GATEWAY_TOKEN')
                          for name, route in bindings.items()}
        pi_environment['FACTORY26_MODEL_BINDINGS'] = json.dumps(local_bindings, separators=(',', ':'))
    # Rust reads selected secrets from its private file. Even the proxy does not
    # need to inherit provider or tool credentials in its process environment.
    environment = {key: value for key, value in pi_environment.items()
                   if key not in {'FACTORY26_GATEWAY_TOKEN', 'CONTEXT7_API_KEY', 'EXA_API_KEY', 'E2E_API_KEY'}}
    log = state/'gateway.log'
    command = [str(launcher), '--config', str(state/'config.json'),
               '--credentials', str(state/'.private/provider-env.json')]
    child = spawn(command, environment=environment, role='service', cwd=run,
                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    physical = physical_identity(child.pid)
    capture = _capture_gateway_log(child, log, run)
    handle = {'owner': 'run', 'implementation': 'rust', 'process': child,
              'identity': process_identity(child.pid), 'physical': physical, 'pid': child.pid,
              'endpoint': endpoint, 'port': port, 'config': str(state/'config.json'),
              'config_sha256': frozen['config_sha256'], 'source_config': str(config),
              'source_config_sha256': source_sha, 'binary': str(launcher),
              'binary_sha256': actual_binary_sha, 'routes': str(state/'gateway-routes.json'),
              'routes_sha256': route_sha, 'source_routes': str(source_routes) if source_routes else None,
              'source_routes_sha256': hashlib.sha256(source_route_bytes).hexdigest() if source_route_bytes is not None else None,
              'log': str(log), 'log_thread': capture,
              'shutdown_seconds': frozen['shutdown_seconds'], 'bindings': local_bindings,
              'pi_environment': pi_environment}
    process_evidence(run, 'operations.jsonl', {'kind': 'process_started', 'role': 'model-gateway',
        'implementation': 'rust', 'process': physical, 'log': str(log), 'binary_sha256': actual_binary_sha})
    try:
        from urllib.request import build_opener, ProxyHandler
        opener = build_opener(ProxyHandler({}))
        deadline = time.monotonic()+30
        while child.poll() is None and time.monotonic() < deadline:
            if not physical.get('boot_id') or not physical.get('process_start'):
                raise RuntimeError(f'gateway birth identity unavailable: {physical}')
            if log.is_file():
                with log.open('rb') as output:
                    lines = output.read(65536).split(b'\n')[:-1]
                ready = any(row.get('event') == 'ready' and row.get('run_id') == frozen['run_id']
                            and row.get('listen') == listen and row.get('config_sha256') == frozen['config_sha256']
                            for line in lines if line.startswith(b'{') for row in [json.loads(line)])
                if ready:
                    try:
                        with opener.open(f'http://{listen}/health/liveliness', timeout=1) as response:
                            if response.status == 200 and process_state(physical) == 'alive':
                                save(run/'model-gateway.json', {key: value for key, value in handle.items()
                                    if key not in {'process', 'pi_environment', 'log_thread'}})
                                return handle
                    except OSError:
                        pass
            time.sleep(.1)
        raise RuntimeError(f'Rust gateway failed readiness: exit={child.poll()}; raw output: {log}')
    except BaseException:
        stop_model_gateway(handle, run)
        raise


def stop_model_gateway(handle, run):
    """Close the exact run-owned service and its authority registration."""
    from lab.control import process_state
    child = handle['process'] if isinstance(handle, dict) else handle
    physical = handle.get('physical') if isinstance(handle, dict) else None
    def signal_owned(sig):
        if child.poll() is not None:
            return
        if physical is not None and process_state(physical) != 'alive':
            raise RuntimeError(f'gateway signal refused: birth identity is not confirmed: {physical}')
        _signal_process(child, sig, run, 'model-gateway-stop')
    if child.poll() is None:
        signal_owned(signal.SIGTERM)
    grace = handle.get('shutdown_seconds', 3)+2 if isinstance(handle, dict) else 5
    try:
        result = _wait_process(child, run, 'model-gateway-stop', timeout=grace)
    except subprocess.TimeoutExpired:
        signal_owned(signal.SIGKILL)
        result = _wait_process(child, run, 'model-gateway-kill', timeout=5)
    if isinstance(handle, dict) and handle.get('log_thread'):
        handle['log_thread'].join(timeout=2)
    closed(getattr(child, '_state_writer', None))
    return result
