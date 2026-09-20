#!/usr/bin/env python3
"""ARC-bench Playground HTTP 客户端；日常运行不依赖浏览器。"""
import argparse
from collections import Counter
from datetime import datetime
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.parse import quote, urlencode
import uuid
from zipfile import ZipFile

from factory import ROOT, api_key, save

API = 'https://arc-bench.com/api'
CONFIG = Path.home()/'.config/factory26'
COOKIE = CONFIG/'playground.cookies.txt'
TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}
PRIVATE = {'api_key', 'password', 'access_token', 'refresh_token', 'authorization', 'cookie', 'apikey', 'access_key', 'accesskey', 'token'}


def redact(value):
    if isinstance(value, dict):
        return {k: '[redacted]' if k.lower() in PRIVATE else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class ApiError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'Playground HTTP {status}' + ('：请先运行 login 更新网站会话' if status == 401 else ''))


class Client:
    def __init__(self, cookie=COOKIE):
        self.cookie = Path(cookie)

    def request(self, path, method='GET', body=None, fields=None, package=None, secret=None, login=False):
        """No automatic retry of writes: an uncertain POST may already have succeeded."""
        with tempfile.TemporaryDirectory(prefix='factory26-http-') as temp:
            response = Path(temp)/'response'
            command = ['curl', '-q', '--silent', '--show-error', '--proto', '=https',
                       '--request', method, '--cookie', str(self.cookie),
                       '--output', str(response), '--write-out', '%{http_code}', API+path]
            if login:
                command += ['--cookie-jar', str(self.cookie)]
            payload = None
            if body is not None:
                command += ['--header', 'Content-Type: application/json', '--data-binary', '@-']
                payload = json.dumps(body).encode()
            if fields is not None:
                for name, value in fields.items():
                    command += ['--form-string', f'{name}={value}']
            if package is not None:
                # A fixed safe name avoids curl's multipart filename grammar for user paths.
                archive = Path(temp)/'agent.zip'
                archive.write_bytes(Path(package).read_bytes())
                command += ['--form', f'file=@{archive};type=application/zip']
            if secret is not None:
                key_file = Path(temp)/'key'
                key_file.write_text(secret); key_file.chmod(0o600)
                command += ['--form', f'api_key=<{key_file}']
            result = subprocess.run(command, input=payload, capture_output=True)
            if result.returncode:
                raise RuntimeError(f'HTTP 传输失败（curl {result.returncode}）；写请求结果可能未知，不能盲目重试')
            status = int(result.stdout)
            if not 200 <= status < 300:
                raise ApiError(status)
            return json.loads(response.read_bytes()) if status != 204 else None


def login(credentials=None):
    if credentials:
        path = Path(credentials)
        if path.stat().st_mode & 0o077:
            raise ValueError('登录文件权限必须为 600')
        values = json.loads(path.read_text())
    else:
        values = {'email': input('网站邮箱: ').strip(), 'password': getpass.getpass('网站密码: ')}
    if not values.get('email') or not values.get('password'):
        raise ValueError('请填写网站 email 和 password；比赛 LLM key 不是这里的登录输入')
    CONFIG.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.playground-cookie-', dir=CONFIG)
    os.close(descriptor)
    temporary = Path(name)
    try:
        client = Client(temporary)
        client.request('/auth/login', 'POST', body={'email': values['email'], 'password': values['password']}, login=True)
        client.request('/auth/me')
        if not temporary.read_text().strip():
            raise RuntimeError('登录未返回可保存的 Cookie')
        temporary.replace(COOKIE)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'网站会话已保存：{COOKIE}（600）；后续命令不需要浏览器')


def run_path(run_id):
    if not run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in run_id):
        raise ValueError('无效的 run ID')
    return '/runs/'+quote(run_id, safe='')


def output_dir(run_id):
    run_path(run_id)
    folder = ROOT/'runs/playground'/run_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def status(client, run_id):
    value = redact(client.request(run_path(run_id)))
    save(output_dir(run_id)/'status.json', value)
    return value


def summary(value):
    result={key:value.get(key) for key in ('id','status','passed_count','failed_count','failure_reason') if key in value}
    if value.get('finished_at') and value.get('started_at'):
        # The hosted API has returned duration=0 for real 34–43 second runs.
        try:
            result['elapsed_seconds'] = (datetime.fromisoformat(value['finished_at']) - datetime.fromisoformat(value['started_at'])).total_seconds()
        except (TypeError, ValueError):
            result['elapsed_seconds'] = None
    if value.get('status') in TERMINAL and value.get('tests'):
        result['test_status_counts'] = dict(Counter(test.get('status', 'unknown') for test in value['tests']))
    steps=value.get('steps') or []
    active=next((step for step in steps if step.get('status') not in ('completed','pending')),None)
    if active:
        result['stage']=active.get('key')
        meaningful=[line for line in active.get('logs',[]) if not line.startswith('Still working:')]
        result['progress']=meaningful[-1] if meaningful else active.get('description')
    # Counts during RUNNING are partial, never a completed score.
    if value.get('status') == 'PASSED': result['test_pass_rate']=value.get('test_pass_rate')
    return result


def logs(client, run_id):
    folder = output_dir(run_id)
    cursor_file = folder/'log-cursor.json'
    cursor = json.loads(cursor_file.read_text()) if cursor_file.exists() else {'log_offset': 0}
    query = urlencode({k: v for k, v in cursor.items() if v is not None})
    chunk = redact(client.request(run_path(run_id)+'/logs?'+query))
    chunks = folder/'logs'; chunks.mkdir(exist_ok=True)
    # A replay at the same cursor replaces its chunk; advance only after durable storage.
    chunk_id = hashlib.sha256(json.dumps(cursor, sort_keys=True).encode()).hexdigest()[:16]
    save(chunks/(chunk_id+'.json'), chunk)
    save(cursor_file, {'log_offset': chunk.get('log_offset', cursor.get('log_offset', 0)),
                       'after_event_id': chunk.get('last_event_id', cursor.get('after_event_id'))})
    return chunk


def collect(client, run_id):
    value = status(client, run_id)
    logs(client, run_id)
    folder = output_dir(run_id)
    for endpoint, filename in [('traceability?node_id=__all__', 'traceability.json'), ('commit-history', 'commit-history.json')]:
        save(folder/filename, redact(client.request(run_path(run_id)+'/'+endpoint)))
    return value


def submit(client, package, requirement, name, variant, offline=False, catalog='benchmark'):
    package = Path(package).resolve()
    with ZipFile(package) as archive:
        if not {'main.py', 'requirements.txt'}.issubset(archive.namelist()):
            raise ValueError('Python ZIP 根目录必须有 main.py 和 requirements.txt')
    if Path(variant).name != variant or variant in ('.', '..'):
        raise ValueError('无效的 variant')
    config = json.loads((ROOT/'variants'/variant/'config.json').read_text())
    folder = ROOT/'runs/playground'/('upload-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    manifest = {'package': str(package), 'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
                'requirement': requirement, 'catalog': catalog, 'variant': variant, 'model': config['model'], 'offline': offline,
                'phase': 'upload', 'created_at': time.time()}
    path = folder/'submission.json'; save(path, manifest)
    print(f'提交状态：{path}', flush=True)
    try:
        value = client.request('/submissions', 'POST', fields={
            'requirement_id': requirement, 'runtime': 'python', 'catalog': catalog,
            'agent_source': 'upload', 'display_name': name, 'base_url': config['base_url'],
            'model': config['model'], 'visual_model': config['model']}, package=package,
            secret='unused-offline-probe' if offline else api_key())
        manifest.update(submission_id=value['submission']['id'], phase='create_run'); save(path, manifest)
        value = client.request('/runs', 'POST', fields={'submission_id': manifest['submission_id'], 'requirement_id': requirement})
        manifest.update(run_id=value['run']['id'], phase='start'); save(path, manifest)
        client.request(run_path(manifest['run_id'])+'/start', 'POST')
        manifest.update(phase='started'); save(path, manifest)
        save(output_dir(manifest['run_id'])/'submission.json', manifest)
        return manifest
    except Exception as exc:
        manifest.update(error=str(exc), updated_at=time.time()); save(path, manifest)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    auth = commands.add_parser('login'); auth.add_argument('--credentials', type=Path)
    commands.add_parser('whoami')
    catalog=commands.add_parser('requirements')
    catalog.add_argument('--catalog',choices=['benchmark','playground'],default='benchmark')
    upload = commands.add_parser('submit')
    upload.add_argument('--package', required=True, type=Path)
    upload.add_argument('--requirement', required=True)
    upload.add_argument('--name', required=True)
    upload.add_argument('--catalog',choices=['benchmark','playground'],default='benchmark')
    upload.add_argument('--variant', default='pi-svc')
    upload.add_argument('--offline', action='store_true', help='仅用于不会调用模型的探针；使用非凭据占位符')
    rerun=commands.add_parser('run')
    rerun.add_argument('--submission',required=True)
    rerun.add_argument('--requirement',required=True)
    for action in ('status', 'logs', 'collect', 'watch', 'start', 'cancel'):
        command = commands.add_parser(action); command.add_argument('run_id')
        if action == 'watch': command.add_argument('--interval', type=int, default=15)
    args = parser.parse_args()
    if args.command == 'login':
        login(args.credentials); return
    client = Client()
    if args.command == 'whoami':
        value = client.request('/auth/me')
        print(json.dumps({'authenticated': True, 'user_id': value.get('user', {}).get('id')}, ensure_ascii=False)); return
    if args.command == 'requirements':
        items=client.request('/requirements?'+urlencode({'catalog':args.catalog}))
        print(json.dumps([{k:v.get(k) for k in ('id','title','total_tests')} for v in items],ensure_ascii=False,indent=2));return
    if args.command == 'submit':
        value = submit(client, args.package, args.requirement, args.name, args.variant, args.offline, args.catalog)
    elif args.command == 'run':
        created=client.request('/runs','POST',fields={'submission_id':args.submission,'requirement_id':args.requirement})
        run_id=created['run']['id']
        folder=output_dir(run_id)
        value={'submission_id':args.submission,'requirement':args.requirement,'run_id':run_id,'phase':'start'}
        save(folder/'submission.json',value)
        client.request(run_path(run_id)+'/start','POST')
        value['phase']='started';save(folder/'submission.json',value)
    elif args.command == 'watch':
        if args.interval < 1: parser.error('interval 必须为正整数')
        previous = None
        while True:
            value = status(client, args.run_id)
            state = summary(value)
            if state != previous:
                print(json.dumps(state, ensure_ascii=False), flush=True); previous = state
            logs(client, args.run_id)
            if value.get('status') in TERMINAL or value.get('status') == 'PAUSED':
                value = collect(client, args.run_id); break
            time.sleep(args.interval)
    elif args.command in ('start', 'cancel'):
        client.request(run_path(args.run_id)+'/'+args.command, 'POST')
        value = status(client, args.run_id)
    elif args.command == 'logs':
        value = logs(client, args.run_id)
        value = {k: value.get(k) for k in ('log_offset', 'last_event_id')}
    else:
        value = {'status': status, 'collect': collect}[args.command](client, args.run_id)
    print(json.dumps(summary(value) if args.command in ('status', 'watch', 'collect', 'start', 'cancel') else value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit('已停止本地等待；云端 run 状态未改变') from None
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
