#!/usr/bin/env python3
"""Competition 快照与逐任务运行；不确定写入只核查，不自动重发。"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import time
from urllib.parse import urlencode, urlsplit
from zipfile import ZipFile

from playground import ApiError, Client, CONFIG, api_key, redact, run_path

TERMINAL = {'PASSED', 'FAILED', 'CANCELLED'}
ACTIVE = {'QUEUED', 'PENDING', 'RUNNING', 'PAUSE_REQUESTED', 'RESUME_REQUESTED'}


class Blocked(RuntimeError):
    """已保留状态，继续前需要外部证据或人工处理。"""


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('无效的 Competition/task/run identity')
    return value


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, value):
    """发布完整文件后同步目录；写请求只在该记录持久化后发生。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Blocked('另一个 Competition controller 正在使用此状态或比赛') from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def package_identity(package):
    """只校验冻结 ZIP 的结构和载荷身份，不把它称为部署或模型资格。"""
    with ZipFile(package) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(set(names)) != len(names):
            raise ValueError('ZIP 含重复路径')
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if (name.is_absolute() or '..' in name.parts or '\\' in entry.filename
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError('ZIP 包含越界路径或符号链接')
        if not {'main.py', 'requirements.txt', 'package-manifest.json'} <= set(names):
            raise ValueError('ZIP 根目录缺少 main.py、requirements.txt 或 package-manifest.json')
        manifest = json.loads(archive.read('package-manifest.json'))
        if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), dict):
            raise ValueError('package manifest 缺少载荷清单')
        actual = {e.filename for e in entries if not e.is_dir()} - {'package-manifest.json'}
        if actual != set(manifest['files']):
            raise ValueError('ZIP 载荷与 manifest 不一致')
        for name, record in manifest['files'].items():
            with archive.open(name) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != record.get('sha256'):
                    raise ValueError('ZIP 载荷哈希不匹配')
    return manifest


def prepare(directory, package, *, competition_id, variant, tasks, model_config, name=None):
    """一次 variant 对应一个冻结 ZIP 和多个 task；相同输入只读复用。"""
    competition_id, variant = identifier(competition_id), identifier(variant)
    tasks = [identifier(task) for task in tasks]
    if not tasks or len(set(tasks)) != len(tasks):
        raise ValueError('task 列表必须非空且不重复')
    settings = {key: model_config.get(key) for key in ('base_url', 'model', 'visual_model')}
    if not settings['base_url'] or not settings['model']:
        raise ValueError('model_config 需要 base_url 与 model')
    url = urlsplit(settings['base_url'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('模型地址必须是无凭据的 HTTPS URL')
    settings['visual_model'] = settings['visual_model'] or settings['model']
    directory = Path(directory).resolve()
    if directory.exists():
        try:
            existing = json.loads((directory/'inputs.json').read_text())
            expected = {'competition_id': competition_id, 'variant': variant, 'tasks': tasks,
                        'model_config': settings, 'display_name': name or variant,
                        'package_sha256': digest(package)}
            if (any(existing.get(key) != value for key, value in expected.items())
                    or digest(directory/'agent.zip') != existing['package_sha256']
                    or not (directory/'state.json').is_file()):
                raise Blocked('既有 prepare identity 不同，拒绝覆盖')
            return existing
        except (OSError, KeyError, json.JSONDecodeError):
            raise Blocked('既有 prepare 目录不完整，保留现场，不覆盖') from None
    directory.mkdir(parents=True, exist_ok=False)
    frozen = directory/'agent.zip'
    # Validate the copy, so later edits to the caller's ZIP cannot change this snapshot.
    with Path(package).open('rb') as source, frozen.open('xb') as target:
        shutil.copyfileobj(source, target)
        target.flush()
        os.fsync(target.fileno())
    manifest = package_identity(frozen)
    if manifest.get('variant') and manifest['variant'] != variant:
        raise ValueError('package manifest 的 variant 与准备参数不同')
    frozen.chmod(0o400)
    value = dict(schema_version=1, venue='hosted', competition_id=competition_id,
                 variant=variant, package_sha256=digest(frozen), package='agent.zip',
                 package_manifest=redact(manifest), model_config=settings, tasks=tasks,
                 display_name=name or variant, created_at=time.time())
    atomic_json(directory/'inputs.json', value)
    state = dict(schema_version=1, venue='hosted', competition_id=competition_id,
                 package_sha256=value['package_sha256'], phase='prepared', submission_id=None,
                 pending=None, tasks={task: {'phase': 'prepared', 'run_id': None} for task in tasks})
    atomic_json(directory/'state.json', state)
    return value


def latest_snapshot(history):
    if not isinstance(history, list) or any(not isinstance(item, dict) for item in history):
        raise Blocked('Competition submission history schema 未识别')
    if not history:
        return None
    selected = [item for item in history if item.get('is_latest') is True]
    if len(selected) == 1:
        return selected[0]
    if len(history) == 1:
        return history[0]
    try:
        ordered = sorted(history, key=lambda item: datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')))
        if datetime.fromisoformat(ordered[-1]['created_at'].replace('Z', '+00:00')) != datetime.fromisoformat(ordered[-2]['created_at'].replace('Z', '+00:00')):
            return ordered[-1]
    except (KeyError, ValueError, TypeError):
        pass
    raise Blocked('无法从 history 唯一确定最新 snapshot，停止写入')


class Controller:
    """在 with 块内使用；持有本地状态锁与同 Cookie/比赛的排他锁。"""
    def __init__(self, directory, client=None, *, secret=None, lock_root=None):
        self.directory = Path(directory).resolve()
        self.client = client if client is not None else Client()
        self.secret = secret
        self.lock_root = Path(lock_root) if lock_root else CONFIG/'competition-locks'

    def __enter__(self):
        from contextlib import ExitStack
        self.locks = ExitStack()
        try:
            self.locks.enter_context(locked(self.directory/'controller.lock'))
            self.inputs = json.loads((self.directory/'inputs.json').read_text())
            competition = identifier(self.inputs['competition_id'])
            self.locks.enter_context(locked(self.lock_root/(competition+'.lock')))
            self.state = json.loads((self.directory/'state.json').read_text())
            self.check_identity()
            self._apply_receipt()
            return self
        except BaseException:
            self.locks.close()
            raise

    def __exit__(self, *exc):
        self.locks.close()

    def safe(self, value):
        value = redact(value)
        if isinstance(value, dict):
            return {key: self.safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.safe(item) for item in value]
        if isinstance(value, str) and self.secret:
            return value.replace(self.secret, '[redacted]')
        return value

    def save(self):
        self.state['updated_at'] = time.time()
        atomic_json(self.directory/'state.json', self.safe(self.state))

    def check_identity(self):
        if (self.state.get('venue') != 'hosted'
                or self.state.get('competition_id') != self.inputs['competition_id']
                or self.state.get('package_sha256') != self.inputs['package_sha256']
                or list(self.state['tasks']) != self.inputs['tasks']
                or digest(self.directory/'agent.zip') != self.inputs['package_sha256']):
            raise Blocked('冻结包与 journal identity 不一致')

    def record(self, relative, value, source):
        atomic_json(self.directory/relative,
                    {'observed_at': time.time(), 'source': source, 'value': self.safe(value)})

    def history(self):
        path = '/competitions/'+identifier(self.inputs['competition_id'])+'/submissions'
        value = self.client.request(path)
        self.record('history.json', value, path)
        latest_snapshot(value)
        return value

    def _post(self, operation, path, *, task=None, prior_ids=None, **kwargs):
        if self.state['pending']:
            raise Blocked('上次写入结果不明，请先 recover；不会重发 POST')
        pending = {'operation': operation, 'task': task, 'path': path, 'requested_at': time.time()}
        if prior_ids is not None:
            pending['prior_ids'] = prior_ids
        self.state['pending'] = pending
        self.save()
        try:
            response = self.client.request(path, 'POST', **kwargs)
        except Exception as exc:
            # Transport/error text may contain credentials or server response bodies.
            pending['error_class'] = type(exc).__name__
            if isinstance(exc, ApiError):
                pending['http_status'] = exc.status
                pending['error_detail'] = self.safe(exc.detail)
            self.save()
            raise Blocked(operation+' 写入结果未确认，已保留 journal；先只读核查') from None
        pending['response'] = self.safe(response)
        self.save()
        self._apply_receipt()
        if self.state['pending']:
            raise Blocked('POST 响应缺少有效 identity，保留原响应等待核查')

    def _apply_receipt(self):
        pending = self.state['pending']
        if not pending or 'response' not in pending:
            return
        response, task = pending['response'], pending['task']
        try:
            if pending['operation'] == 'snapshot':
                self.state.update(submission_id=identifier(response['submission']['id']), phase='snapshot-saved')
            elif pending['operation'] == 'create':
                self.state['tasks'][task].update(run_id=identifier(response['run']['id']), phase='run-created')
            else:
                if self.state['tasks'][task]['phase'] not in {'terminal', 'collected'}:
                    self.state['tasks'][task]['phase'] = 'started'
        except (KeyError, TypeError, ValueError):
            pending['error_class'] = 'InvalidResponse'
            self.save()
            return
        self.state['pending'] = None
        self.save()

    def _validate_run(self, value, task, run_id, *, require_links=False):
        if not isinstance(value, dict) or value.get('id') != run_id:
            raise Blocked('返回的 run identity 不匹配')
        for key, expected in [('submission_id', self.state['submission_id']), ('requirement_id', task)]:
            if (require_links or key in value) and value.get(key) != expected:
                raise Blocked('返回的 run 不属于冻结 snapshot/task')

    def snapshot(self):
        if self.state['submission_id']:
            return self.state['submission_id']
        if self.state['pending']:
            raise Blocked('snapshot 写入结果不明，请先 recover')
        detail_path = '/competitions/'+self.inputs['competition_id']
        detail = self.client.request(detail_path)
        self.record('competition.json', detail, detail_path)
        if detail.get('id') != self.inputs['competition_id'] or detail.get('template_required'):
            raise Blocked('比赛 identity 不符或需要尚未实现的 template selection')
        if not set(self.state['tasks']) <= {item['id'] for item in detail.get('tasks', [])}:
            raise Blocked('准备的 task 不属于此比赛')
        history = self.history()
        previous = latest_snapshot(history)
        if previous and previous.get('is_complete') is not True:
            scores = previous.get('task_scores', [])
            ids = {item['task_id']: item.get('run_id') for item in scores}
            if not {item['id'] for item in detail['tasks']} <= ids.keys() or not all(ids.values()):
                raise Blocked('上一个 snapshot 尚无全部 task 结果，禁止提前上传新 variant')
            for task, run_id in ids.items():
                value = self.client.request(run_path(identifier(run_id)))
                if value.get('id') != run_id or value.get('status') not in TERMINAL:
                    raise Blocked('上一个 snapshot 仍有未终结任务，禁止提前上传新 variant')
        if not self.secret:
            raise ValueError('snapshot 需要通过内存提供模型 key；不会写入 journal')
        self._post('snapshot', '/submissions', fields={
            'competition_id': self.inputs['competition_id'], 'runtime': 'python',
            'catalog': 'competition', 'agent_source': 'upload',
            'display_name': self.inputs['display_name'], **self.inputs['model_config']},
            package=self.directory/'agent.zip', secret=self.secret,
            prior_ids=[item['id'] for item in history])
        return self.state['submission_id']

    def create(self, task):
        item = self.state['tasks'][task]
        if item['run_id']:
            return item['run_id']
        if not self.state['submission_id']:
            raise Blocked('请先保存 snapshot')
        latest = latest_snapshot(self.history())
        if not latest or latest.get('id') != self.state['submission_id']:
            raise Blocked('此 snapshot 已不是最新，禁止创建新 task run')
        if any(score.get('task_id') == task and score.get('run_id') for score in latest.get('task_scores', [])):
            raise Blocked('此 snapshot/task 已有远端 run，禁止重复创建；先核查现有 identity')
        self._post('create', '/runs', task=task, fields={
            'submission_id': self.state['submission_id'], 'requirement_id': task})
        return item['run_id']

    def start(self, task):
        item = self.state['tasks'][task]
        if item['phase'] in {'started', 'terminal', 'collected'}:
            return
        if item['phase'] != 'run-created':
            raise Blocked('必须先创建 task run')
        self._post('start', run_path(item['run_id'])+'/start', task=task)

    def status(self, task):
        item = self.state['tasks'][task]
        path = run_path(item['run_id'])
        value = self.client.request(path)
        self._validate_run(value, task, item['run_id'])
        self.record('tasks/'+task+'/status.json', value, path)
        remote = value.get('status')
        item.update(remote_status=remote, observed_at=time.time())
        item['platform_result'] = {key: value[key] for key in
            ('score', 'test_pass_rate', 'feature_implementation_rate', 'passed_count', 'failed_count',
             'total_tests', 'run_duration_seconds', 'token_count', 'token_cost', 'token_cost_usd', 'token_cost_currency',
             'started_at', 'finished_at') if key in value}
        # The platform exposes the full test rows, not a total_tests field.
        if isinstance(value.get('tests'), list):
            item['platform_result']['total_tests'] = len(value['tests'])
        if remote in TERMINAL:
            item['observation'] = 'known'
            if item['phase'] != 'collected':
                item['phase'] = 'terminal'
        elif remote not in ACTIVE and remote != 'PAUSED':
            item['observation'] = 'unknown'
        else:
            item['observation'] = 'known'
        self.save()
        return value

    def logs(self, task):
        folder = self.directory/'tasks'/task
        cursor_file = folder/'log-cursor.json'
        cursor = json.loads(cursor_file.read_text()) if cursor_file.exists() else {'log_offset': 0}
        path = run_path(self.state['tasks'][task]['run_id'])+'/logs?'+urlencode({k: v for k, v in cursor.items() if v is not None})
        value = self.client.request(path)
        if not isinstance(value, dict):
            raise Blocked('日志响应 schema 无效，原 cursor 保留')
        chunk_id = hashlib.sha256(json.dumps(cursor, sort_keys=True).encode()).hexdigest()[:16]
        self.record('tasks/'+task+'/logs/'+chunk_id+'.json', value, path)
        offset = value.get('log_offset', cursor.get('log_offset', 0))
        if not isinstance(offset, int) or offset < cursor.get('log_offset', 0):
            raise Blocked('日志 offset 回退或 schema 无效，原 cursor 保留')
        next_cursor = {'log_offset': offset, 'after_event_id': value.get('last_event_id', cursor.get('after_event_id'))}
        atomic_json(cursor_file, next_cursor)
        return next_cursor

    def collect(self, task):
        value = self.status(task)
        self.logs(task)
        item = self.state['tasks'][task]
        errors = {}
        for endpoint, name in [('traceability?node_id=__all__', 'traceability'), ('commit-history', 'commit-history')]:
            path = run_path(item['run_id'])+'/'+endpoint
            try:
                artifact = self.client.request(path)
                self.record('tasks/'+task+'/'+name+'.json', artifact, path)
            except Exception as exc:
                errors[name] = type(exc).__name__
        item['collection_errors'] = errors
        item['artifact_handles'] = {'directory': 'tasks/'+task,
                                    'submission_archive': '/submissions/'+self.state['submission_id']+'/archive',
                                    'archive_downloaded': False}
        if value.get('status') in TERMINAL:
            item['phase'] = 'collected'
        self.save()
        return self.summary()

    def recover(self, *, run_id=None):
        """核查未确认 POST。缺少唯一远端 identity 时保留 pending。"""
        self._apply_receipt()
        pending = self.state['pending']
        if not pending:
            return self.summary()
        operation, task = pending['operation'], pending['task']
        if operation == 'snapshot':
            matches = [item for item in self.history()
                       if item.get('display_name') == self.inputs['display_name']
                       and item.get('id') not in pending.get('prior_ids', [])]
            if len(matches) != 1:
                raise Blocked('history 无唯一的新同名 submission，保留现场以便核查')
            pending['response'] = {'submission': {'id': identifier(matches[0]['id'])}}
        elif operation == 'create':
            if run_id is None:
                snapshots = [item for item in self.history() if item.get('id') == self.state['submission_id']]
                candidates = {score.get('run_id') for item in snapshots for score in item.get('task_scores', [])
                              if score.get('task_id') == task and score.get('run_id')}
                if len(candidates) != 1:
                    raise Blocked('history 无唯一 task run；可提供 --run-id 只读核查，禁止重建')
                run_id = candidates.pop()
            run_id = identifier(run_id)
            value = self.client.request(run_path(run_id))
            self._validate_run(value, task, run_id, require_links=True)
            self.record('tasks/'+task+'/recovery.json', value, run_path(run_id))
            pending['response'] = {'run': {'id': run_id}}
        else:
            value = self.status(task)
            if not value.get('started_at') and value.get('status') not in (TERMINAL | {'QUEUED', 'RUNNING', 'PAUSED', 'PAUSE_REQUESTED', 'RESUME_REQUESTED'}):
                raise Blocked('start 尚无已启动证据；保留 pending，不重复启动')
            pending['response'] = {}
        self.save()
        self._apply_receipt()
        return self.summary()

    def watch(self, task, *, interval=180):
        if interval < 180:
            raise ValueError('watch interval 不得小于 180 秒')
        while True:
            value = self.status(task)
            if value.get('status') in TERMINAL:
                return self.collect(task)
            self.logs(task)
            if value.get('status') == 'PAUSED' or value.get('status') not in ACTIVE:
                raise Blocked('远端任务已暂停或状态未知；停止本地等待，不改变远端状态')
            time.sleep(interval)

    def run_all(self, *, interval=180):
        """同一 snapshot 按声明顺序完成任务；已有终态不重跑。"""
        if interval < 180:
            raise ValueError('watch interval 不得小于 180 秒')
        if self.state['pending']:
            self.recover()
        self.snapshot()
        for task, item in self.state['tasks'].items():
            if item['phase'] == 'collected':
                continue
            if item['phase'] == 'terminal':
                self.collect(task)
            else:
                self.create(task)
                self.start(task)
                self.watch(task, interval=interval)
            if item['phase'] != 'collected':
                raise Blocked('终态证据尚未收齐，保留当前 variant，不开始下一项')
        self.state['phase'] = 'collected'
        self.save()
        return self.summary()

    def summary(self):
        result = {key: self.safe(self.state[key]) for key in
                  ('venue', 'competition_id', 'package_sha256', 'phase', 'submission_id', 'tasks')}
        pending = self.state['pending']
        result['pending'] = ({key: pending.get(key) for key in ('operation', 'task', 'requested_at', 'error_class')}
                             if pending else None)
        complete = self.state['phase'] == 'collected' and all(item['phase'] == 'collected'
            and item.get('remote_status') in TERMINAL
            for item in self.state['tasks'].values())
        blocked = bool(pending) or any(item.get('observation') == 'unknown' or item.get('remote_status') == 'PAUSED'
                                      for item in self.state['tasks'].values())
        result['status'] = 'completed' if complete else 'blocked' if blocked else 'running'
        for item in result['tasks'].values():
            score = item.get('platform_result', {})
            passed, failed, total = (score.get(key) for key in ('passed_count', 'failed_count', 'total_tests'))
            counts = all(type(value) is int and value >= 0 for value in (passed, failed, total))
            numeric_score = type(score.get('score')) in (int, float) and math.isfinite(score['score'])
            item['score_status'] = ('complete' if item.get('remote_status') in TERMINAL and counts
                                    and total > 0 and passed + failed == total and numeric_score else 'unavailable')
        result['score_status'] = ('complete' if complete and all(item['score_status'] == 'complete'
                                  for item in result['tasks'].values()) else 'unavailable')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--state', required=True, type=Path)
    prep.add_argument('--package', required=True, type=Path)
    prep.add_argument('--competition', required=True)
    prep.add_argument('--variant', required=True)
    prep.add_argument('--task', action='append', required=True)
    prep.add_argument('--model-config', required=True, type=Path)
    prep.add_argument('--name')
    prep.add_argument('--json', action='store_true', help='输出完整结构化结果；默认只显示身份与证据路径')
    for action in ('snapshot', 'create', 'start', 'status', 'logs', 'collect', 'recover', 'watch', 'run-all'):
        command = commands.add_parser(action)
        command.add_argument('--state', required=True, type=Path)
        command.add_argument('--json', action='store_true', help='输出完整 summary；默认只显示阶段、run ID 与证据路径')
        if action in {'create', 'start', 'status', 'logs', 'collect', 'watch'}:
            command.add_argument('--task', required=True)
        if action in {'watch', 'run-all'}:
            command.add_argument('--interval', type=int, default=180)
        if action in {'snapshot', 'run-all'}:
            command.add_argument('--offline', action='store_true', help='仅无模型 fixture：传递非凭据占位符')
        if action == 'recover':
            command.add_argument('--run-id', help='创建响应丢失时，以 GET 校验这个 run 的归属')
    args = parser.parse_args()
    if args.command == 'prepare':
        value = prepare(args.state, args.package, competition_id=args.competition, variant=args.variant,
                        tasks=args.task, model_config=json.loads(args.model_config.read_text()), name=args.name)
        value = {key: value[key] for key in ('venue', 'variant', 'competition_id', 'package_sha256')}
    else:
        secret = None
        if args.command in {'snapshot', 'run-all'}:
            secret = 'unused-offline-probe' if args.offline else api_key()
        with Controller(args.state, secret=secret) as controller:
            if args.command in {'watch', 'run-all'}:
                method = controller.watch if args.command == 'watch' else controller.run_all
                method(*([args.task] if args.command == 'watch' else []), interval=args.interval)
            elif args.command == 'recover':
                controller.recover(run_id=args.run_id)
            else:
                getattr(controller, args.command)(*([args.task] if hasattr(args, 'task') else []))
            value = controller.summary()
    if not args.json:
        compact = {key: value[key] for key in ('status', 'phase', 'submission_id', 'score_status', 'package_sha256') if key in value}
        compact['evidence'] = str(args.state.resolve())
        if 'tasks' in value:
            compact['tasks'] = {task: {key: item[key] for key in ('phase', 'run_id', 'score_status') if key in item}
                                for task, item in value['tasks'].items()}
        value = compact
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit('已停止本地控制器；远端任务未取消，重新执行时先核查 journal') from None
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        raise SystemExit(str(exc)) from None
