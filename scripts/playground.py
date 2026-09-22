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

from factory import ROOT, api_key, load_config, save

API = 'https://arc-bench.com/api'
CONFIG = Path.home()/'.config/factory26'
COOKIE = CONFIG/'playground.cookies.txt'
TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}
OBSERVATION_MAX_AGE = 360
PRIVATE = {'api_key', 'password', 'access_token', 'refresh_token', 'authorization', 'cookie', 'apikey', 'access_key', 'accesskey', 'token'}


def redact(value):
    if isinstance(value, dict):
        return {k: '[redacted]' if k.lower() in PRIVATE else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class ApiError(RuntimeError):
    def __init__(self, status, detail=None):
        self.status = status
        self.detail = detail
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
                try:
                    detail = json.loads(response.read_bytes())
                except (ValueError, UnicodeDecodeError):
                    detail = None
                raise ApiError(status, detail)
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
    if value.get('id') != run_id:
        raise ValueError('平台状态的 run ID 与请求不符，未保存')
    save(output_dir(run_id)/'status.json', value)
    record_observation(output_dir(run_id), 'status', run_path(run_id))
    return value


def record_observation(folder, kind, endpoint):
    path = folder/'observation.json'
    value = json.loads(path.read_text()) if path.exists() else {}
    value[kind] = {'observed_at': time.time(), 'source': API+endpoint}
    save(path, value)


def summary(value, *, events=(), observation=None, traceability=None, now=None):
    """区分源事件、采集时间与终态；旧记录没有采集时间时保持未知。"""
    result={key:value.get(key) for key in ('id','status','passed_count','failed_count','failure_reason') if key in value}
    result['terminal'] = value.get('status') in TERMINAL
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
    unique = {}
    for event in events:
        identity = event.get('event_id')
        if identity:
            unique[identity] = event
    ordered = sorted(unique.values(), key=lambda event: str(event.get('timestamp') or ''))
    for heartbeat, key in ((False, 'last_progress_event'), (True, 'last_heartbeat')):
        selected = [event for event in ordered if event.get('heartbeat') is heartbeat]
        if selected:
            result[key] = {name: selected[-1].get(name) for name in ('event_id', 'timestamp', 'stage', 'status', 'summary', 'artifact_reference')}
    if result.get('last_progress_event'):
        result.pop('progress', None)
    if observation is not None:
        current = time.time() if now is None else now
        result['observation'] = {}
        for kind in ('status', 'logs'):
            stamp = observation.get(kind, {}).get('observed_at')
            age = current - stamp if type(stamp) in (int, float) else None
            result['observation'][kind] = {'observed_at': stamp, 'age_seconds': round(age, 1) if age is not None else None,
                                           'freshness': 'unknown' if age is None or age < 0 else 'stale' if age > OBSERVATION_MAX_AGE else 'fresh'}
        result['observation']['stale_after_seconds'] = OBSERVATION_MAX_AGE
        known = isinstance(traceability, dict) and isinstance(traceability.get('interfaces'), list) and isinstance(traceability.get('tests'), list)
        result['traceability'] = {'status': 'available' if known and (traceability['interfaces'] or traceability['tests']) else 'empty' if known else 'unavailable',
                                  'source': observation.get('traceability', {}).get('source'),
                                  'producer': traceability.get('producer') if known else None,
                                  'version': traceability.get('version') if known else None,
                                  'kind': 'explicit_links_not_causal_trace'}
        if known:
            result['traceability'].update(interfaces=len(traceability['interfaces']), tests=len(traceability['tests']))
    # Counts during RUNNING are partial, never a completed score.
    if value.get('status') == 'PASSED': result['test_pass_rate']=value.get('test_pass_rate')
    return result


def saved_summary(run_id, value=None, *, now=None):
    """只读已采集产物；不联网，不以文件 mtime 冒充平台观测时间。"""
    run_path(run_id)
    folder = ROOT/'runs/playground'/run_id
    if value is None:
        value = json.loads((folder/'status.json').read_text())
    if value.get('id') != run_id:
        raise ValueError('已保存状态的 run ID 不符，拒绝关联')
    chunks = [json.loads(path.read_text()) for path in (folder/'logs').glob('*.json')]
    chunks.sort(key=lambda chunk: chunk.get('log_offset', 0))
    events = [event for chunk in chunks for event in chunk.get('runner_events', [])]
    path = folder/'observation.json'
    observation = json.loads(path.read_text()) if path.exists() else {}
    path = folder/'traceability.json'
    traceability = json.loads(path.read_text()) if path.exists() else None
    result = summary(value, events=events, observation=observation, traceability=traceability, now=now)
    if traceability is not None:
        result['traceability']['source'] = observation.get('traceability', {}).get('source') or str(path)
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
    record_observation(folder, 'logs', run_path(run_id)+'/logs')
    return chunk


def collect(client, run_id):
    value = status(client, run_id)
    logs(client, run_id)
    folder = output_dir(run_id)
    for endpoint, filename in [('traceability?node_id=__all__', 'traceability.json'), ('commit-history', 'commit-history.json')]:
        save(folder/filename, redact(client.request(run_path(run_id)+'/'+endpoint)))
        record_observation(folder, filename.removesuffix('.json'), run_path(run_id)+'/'+endpoint)
    return value


def submit(client, package, requirement, name, offline=False, catalog='benchmark', config_path=None, *, practice=False):
    if not (practice or offline):
        raise ValueError('此接口仅用于练习；请显式选择 --practice。正式评测使用队长的平台入口和平台内置 key。')
    package = Path(package).resolve()
    with ZipFile(package) as archive:
        if not {'main.py', 'requirements.txt'}.issubset(archive.namelist()):
            raise ValueError('Python ZIP 根目录必须有 main.py 和 requirements.txt')
    config = load_config(config_path or ROOT/'variants/factory/config.json')
    folder = ROOT/'runs/playground'/('upload-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    manifest = {'package': str(package), 'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
                'requirement': requirement, 'catalog': catalog, 'model': config['model'], 'offline': offline,
                'model_config': {'model':config['model'],'base_url':config['base_url']},
                'configuration_scope': 'model-settings-only',
                'submission_kind': 'probe' if offline else 'practice', 'ranking_eligible': False,
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


def practice_record(*, submission_id=None, run_id=None):
    key, value = ('submission_id', submission_id) if submission_id else ('run_id', run_id)
    for path in (ROOT/'runs/playground').glob('*/submission.json'):
        record = json.loads(path.read_text())
        if record.get(key) == value and record.get('submission_kind') in ('practice', 'probe'):
            return record
    raise ValueError('此写操作仅接受本工具已记录的练习/探针 ID；未知或正式 ID 请通过平台管理')


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
    upload.add_argument('--config', type=Path, help='网关/模型配置；默认 factory 配置；不改变 ZIP 中的 harness')
    upload.add_argument('--practice', action='store_true', help='自带 key 的练习提交，不计正式成绩')
    upload.add_argument('--offline', action='store_true', help='仅用于不会调用模型的探针；使用非凭据占位符')
    rerun=commands.add_parser('run')
    rerun.add_argument('--submission',required=True)
    rerun.add_argument('--requirement',required=True)
    for action in ('status', 'logs', 'collect', 'watch', 'start', 'cancel'):
        command = commands.add_parser(action); command.add_argument('run_id')
        if action == 'watch':
            command.add_argument('--interval', type=int, default=180)
            command.add_argument('--after-event', help='已处理的终态通知 ID；相同结果保持静默')
        if action == 'status': command.add_argument('--saved', action='store_true', help='只读本地已采集证据，不联网')
    args = parser.parse_args()
    if args.command == 'login':
        login(args.credentials); return
    if args.command == 'status' and args.saved:
        print(json.dumps(saved_summary(args.run_id), ensure_ascii=False, indent=2)); return
    client = Client()
    if args.command == 'whoami':
        value = client.request('/auth/me')
        print(json.dumps({'authenticated': True, 'user_id': value.get('user', {}).get('id')}, ensure_ascii=False)); return
    if args.command == 'requirements':
        items=client.request('/requirements?'+urlencode({'catalog':args.catalog}))
        print(json.dumps([{k:v.get(k) for k in ('id','title','total_tests')} for v in items],ensure_ascii=False,indent=2));return
    if args.command == 'submit':
        value = submit(client, args.package, args.requirement, args.name, args.offline, args.catalog, args.config, practice=args.practice)
    elif args.command == 'run':
        previous=practice_record(submission_id=args.submission)
        created=client.request('/runs','POST',fields={'submission_id':args.submission,'requirement_id':args.requirement})
        run_id=created['run']['id']
        folder=output_dir(run_id)
        value={'submission_id':args.submission,'requirement':args.requirement,'run_id':run_id,'phase':'start',
               'submission_kind':previous['submission_kind'],'ranking_eligible':False}
        save(folder/'submission.json',value)
        client.request(run_path(run_id)+'/start','POST')
        value['phase']='started';save(folder/'submission.json',value)
    elif args.command == 'watch':
        if args.interval < 180: parser.error('interval 不得小于 180 秒')
        while True:
            value = status(client, args.run_id)
            logs(client, args.run_id)
            if value.get('status') in TERMINAL or value.get('status') == 'PAUSED':
                event_id = f"{args.run_id}:{value['status']}:{value.get('finished_at') or ''}"
                if event_id == args.after_event: return
                value = collect(client, args.run_id)
                if value.get('status') not in TERMINAL and value.get('status') != 'PAUSED':
                    time.sleep(args.interval)
                    continue
                event_id = f"{args.run_id}:{value['status']}:{value.get('finished_at') or ''}"
                if event_id == args.after_event: return
                result = saved_summary(args.run_id,value)
                result['event_id'] = event_id
                print(json.dumps(result,ensure_ascii=False,indent=2))
                return
            time.sleep(args.interval)
    elif args.command in ('start', 'cancel'):
        practice_record(run_id=args.run_id)
        client.request(run_path(args.run_id)+'/'+args.command, 'POST')
        value = status(client, args.run_id)
    elif args.command == 'logs':
        value = logs(client, args.run_id)
        value = {k: value.get(k) for k in ('log_offset', 'last_event_id')}
    else:
        value = {'status': status, 'collect': collect}[args.command](client, args.run_id)
        if args.command == 'status': logs(client, args.run_id)
    print(json.dumps(saved_summary(args.run_id, value) if args.command in ('status', 'watch', 'collect', 'start', 'cancel') else value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit('已停止本地等待；云端 run 状态未改变') from None
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
