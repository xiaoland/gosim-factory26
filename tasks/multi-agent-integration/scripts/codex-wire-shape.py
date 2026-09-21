#!/usr/bin/env python3
"""Replay a retained Codex Responses turn through local LiteLLM only."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import factory


def _port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def _replay_input(path):
    items = []
    for line in Path(path).read_text().splitlines():
        payload = json.loads(line).get('payload') or {}
        kind = payload.get('type')
        if kind == 'message':
            items.append({key: payload[key] for key in ('type', 'role', 'content') if key in payload})
        elif kind == 'function_call':
            items.append({key: payload[key] for key in ('type', 'id', 'name', 'arguments', 'call_id') if key in payload})
        elif kind == 'function_call_output':
            items.append({key: payload[key] for key in ('type', 'id', 'call_id', 'output') if key in payload})
    if not any(item.get('type') == 'function_call' for item in items):
        raise RuntimeError('rollout has no function_call response item')
    if not any(item.get('type') == 'function_call_output' for item in items):
        raise RuntimeError('rollout has no function_call_output response item')
    return items


def _strict_gateway():
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            received.append(body)
            empty = any(
                isinstance(message.get('content'), list)
                and any(
                    isinstance(block, dict)
                    and block.get('type') == 'text'
                    and block.get('text') == ''
                    for block in message['content']
                )
                for message in body.get('messages', [])
            )
            if empty:
                payload = {'error': {'message': 'text content is empty', 'type': 'invalid_request_error'}}
                status = 400
            else:
                payload = {
                    'id': 'chatcmpl-local-shape', 'object': 'chat.completion',
                    'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'ok'}, 'finish_reason': 'stop'}],
                    'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2},
                }
                status = 200
            encoded = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, received


def _run_adapter(config_path, port, gateway_port, compat, output):
    config = {
        'model_list': [{
            'model_name': 'kimi-k3',
            'litellm_params': {
                'model': 'openai/kimi-k3',
                'api_base': f'http://127.0.0.1:{gateway_port}/v1',
                'api_key': 'local-shape-fixture',
                'use_chat_completions_api': True,
            },
            'model_info': {'mode': 'chat'},
        }],
        'litellm_settings': {
            'telemetry': False,
            'callbacks': ['responses_compat.proxy_handler_instance'] if compat else [],
        },
    }
    factory.save(config_path, config)
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'scripts'), FACTORY26_API_KEY='local-shape-fixture')
    log_path = output / ('adapter-compat.log' if compat else 'adapter-baseline.log')
    with log_path.open('w') as log:
        process = subprocess.Popen(
            [str(ROOT / '.adapter/bin/litellm'), '--config', str(config_path), '--host', '127.0.0.1', '--port', str(port)],
            cwd=ROOT, env=env, stdout=log, stderr=log, start_new_session=True,
        )
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{port}/health/liveliness', timeout=1)
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError(f'LiteLLM did not start; see {log_path}')
            return process
        except BaseException:
            process.kill()
            process.wait()
            raise


def replay(rollout):
    output = ROOT / 'runs/integration' / f'codex-wire-replay-{time.strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:6]}'
    output.mkdir(parents=True)
    items = _replay_input(rollout)
    server, received = _strict_gateway()
    try:
        results = {}
        for compat in (False, True):
            port = _port()
            process = _run_adapter(output / ('adapter-compat.json' if compat else 'adapter-baseline.json'), port, server.server_port, compat, output)
            try:
                request = urllib.request.Request(
                    f'http://127.0.0.1:{port}/v1/responses',
                    data=json.dumps({'model': 'kimi-k3', 'input': items, 'stream': False}).encode(),
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer local-shape-fixture'},
                )
                try:
                    with urllib.request.urlopen(request, timeout=20) as response:
                        results['compat' if compat else 'baseline'] = response.status
                except urllib.error.HTTPError as error:
                    results['compat' if compat else 'baseline'] = error.code
            finally:
                process.terminate(); process.wait(timeout=10)
        baseline, fixed = received[-2], received[-1]
        assert results == {'baseline': 400, 'compat': 200}, results
        assert any(
            block.get('type') == 'text' and block.get('text') == ''
            for message in baseline.get('messages', [])
            if isinstance(message.get('content'), list)
            for block in message['content']
            if isinstance(block, dict)
        ), 'baseline did not preserve the failing empty text block'
        assert not any(
            block.get('type') == 'text' and block.get('text') == ''
            for message in fixed.get('messages', [])
            if isinstance(message.get('content'), list)
            for block in message['content']
            if isinstance(block, dict)
        ), 'compat request still contains empty text'
        expected_calls = {
            value for item in items if item.get('type') == 'function_call'
            for value in (item.get('id'), item.get('call_id')) if value
        }
        actual_calls = {
            call.get('id') for message in fixed['messages'] for call in message.get('tool_calls', [])
            if call.get('id')
        }
        assert expected_calls & actual_calls, 'function call identity was lost'
        assert any(message.get('role') == 'tool' for message in fixed['messages']), 'function output was lost'
        assert any(
            part.get('type') == 'image_url'
            for message in fixed['messages']
            if isinstance(message.get('content'), list)
            for part in message['content']
            if isinstance(part, dict)
        ), 'image output was lost'
        factory.save(output / 'result.json', {'rollout': str(rollout), 'results': results, 'baseline_chat': baseline, 'compat_chat': fixed})
        print(json.dumps({'output': str(output), 'results': results}, ensure_ascii=False))
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay-rollout', type=Path, required=True)
    replay(parser.parse_args().replay_rollout)
