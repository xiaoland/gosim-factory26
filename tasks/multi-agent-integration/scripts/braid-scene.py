#!/usr/bin/env python3
"""Run one short real Braid journey with a root description rebuild."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

_bootstrap = argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--package', type=Path)
_bootstrap.add_argument('--output', type=Path)
_bootstrap_args, _ = _bootstrap.parse_known_args()
PACKAGE = _bootstrap_args.package or (Path(os.environ['FACTORY26_QUALIFICATION_PACKAGE'])
                                      if os.environ.get('FACTORY26_QUALIFICATION_PACKAGE') else None)
ROOT = PACKAGE.resolve() if PACKAGE else Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import factory
import submission
from braid_runtime import archive_state, export_delivery, initialize_repository, load_delivery
from core import archive_sessions


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def configuration(backend):
    if PACKAGE:
        manifest = submission.verify_package(ROOT)
        config = submission.platform_config(ROOT, manifest)
        if config['backend'] != backend:
            raise ValueError(f'资格包 backend 是 {config["backend"]}，不是 {backend}')
        return config
    raise ValueError('本地 scene 入口已退役；请通过 --package 使用独立 variant 制品')


def run(backend, selected_output=None):
    config = configuration(backend)
    selected_output = selected_output or (Path(os.environ['FACTORY26_QUALIFICATION_OUTPUT'])
                                          if os.environ.get('FACTORY26_QUALIFICATION_OUTPUT') else None)
    if selected_output:
        output = selected_output.resolve()
    elif PACKAGE:
        raise ValueError('包模式必须传 --output 或 FACTORY26_QUALIFICATION_OUTPUT')
    else:
        output = ROOT / 'runs/integration' / f'{time.strftime("%Y%m%d-%H%M%S")}-{backend}-braid-{uuid.uuid4().hex[:6]}'
    output.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix='f26-braid-', dir='/tmp')).resolve()
    app = work / 'application'
    app.mkdir()
    record = dict(kind='multi-agent-joint-braid-stage', backend=backend, status='running',
                  started_at=time.time(), workspace=str(work), root_context_rebuilds=[])
    factory.save(output / 'check.json', record)
    factory.save(output / 'effective-config.json', config['effective'])
    if PACKAGE:
        shutil.copy2(ROOT / 'package-manifest.json', output / 'package-manifest.json')
    elif (ROOT / 'sources').is_dir():
        sources = __import__('sources')
        sources.archive('braid', output / 'sources')
        sources.archive('svc', output / 'sources')

    initialize_repository(app)
    native, env = factory.runtime_environment(work, config)
    state = work / 'braid-state'
    (work / 'bin').mkdir()
    executable = work / 'bin/braid'
    braid_binary = ROOT / 'runtime/bin/braid'
    if not braid_binary.is_file():
        braid_binary = __import__('sources').binary()
    shutil.copy2(braid_binary, executable)
    env['PATH'] = str(executable.parent) + os.pathsep + env['PATH']

    def cli(*args):
        return subprocess.run([str(executable), '--state', str(state), '--external', *args],
                              cwd=app, env=env, text=True, capture_output=True, check=True)

    final_description = '''完成这个小型交付任务：

1. 使用一个原生 executor 子代理，在当前根 Issue 工作树实现 `calc.py` 的 `add(a, b)`，支持整数、负数和零，并在实现或自检中执行 `add(2, 3) == 5` 与 `add(-4, 1) == -3` 断言。
2. 用 `pr create --issue 1` 创建至少一个 PR。PR Agent 必须实现并验证这项变更，在本地提交后执行 `pr ready`。
3. 根 Issue 核对 PR 和交付文件，执行 `pr merge`，再从交付分支验证 `calc.add(2, 3) == 5` 与 `calc.add(-4, 1) == -3`，最后执行 `issue close 1 --reason completed`。

这是唯一的应用需求。不要再次修改根 Issue description，不要创建子 Issue，不要 push，也不要修改本次任务之外的文件。'''
    initial_prompt = f'''这是一次受控的 Braid 根 Issue 验收。当前根 Issue description 只是启动说明。

先使用本轮给出的 writer-turn CLI 身份，执行一次 `issue edit 1 --body-file FILE`，把根 Issue description 完整替换为下面的最终任务；这是唯一一次 description edit，提交后等待新的上下文，不要在旧上下文继续写入：

{final_description}

description 重建后，严格按新的完整 description 工作。使用明确的本地 CLI 命令和一个原生 executor 完成局部实现，再通过至少一个 PR 提交、ready、merge，验证断言并关闭根 Issue。'''
    proc = None
    try:
        with factory.responses_adapter(config, output) as responses_url:
            request = factory.braid_request(config, work, app, native, initial_prompt, state,
                                            output.name, responses_url)
            factory.save(work / 'request.json', request)
            factory.save(output / 'request.json', request)
            with (output / 'braid.log').open('w') as log:
                proc = subprocess.Popen([str(executable), 'local', str(work / 'request.json')],
                                        cwd=app, env=env, stdout=log, stderr=log,
                                        start_new_session=True)
                proc.wait()
                if proc.returncode:
                    raise RuntimeError(f'Braid exit {proc.returncode}; see braid.log')
                roots = [row for row in read_json(state / 'sessions.json', [])
                         if row.get('work_item_kind') == 'issue' and str(row.get('work_item_id')) == '1']
                session_ids = {row.get('session_id') for row in roots}
                context_paths = {row.get('context_path') for row in roots if row.get('context_path')}
                assert len(session_ids) >= 2, '根 Issue 没有两个不同 session 记录'
                assert len(context_paths) >= 2, '根 Issue 没有两个不同 context 记录'
                item = json.loads(cli('issue', 'view', '1', '--json').stdout)
                assert 'calc.py' in item.get('body', '') and '不要再次修改根 Issue description' in item.get('body', ''), \
                    '根 Issue description 未进入最终任务'
                record['root_context_rebuilds'] = [
                    {'session_id': row.get('session_id'), 'context_path': row.get('context_path')}
                    for row in roots
                ]
                factory.save(output / 'check.json', record)

            delivery = load_delivery(state, app, work, request)
            entries = read_json(state / 'sessions.json', [])
            pr_entries = [row for row in entries if row.get('work_item_kind') == 'pr']
            assert pr_entries, '没有可核验的 PR session'
            prs = json.loads(cli('pr', 'list', '--json').stdout)
            assert any(pr.get('state') == 'MERGED' for pr in prs), '没有已合入的 PR'
            export_delivery(app, delivery['delivery_commit'], output / 'application')
            subprocess.run([sys.executable, '-c',
                            'from calc import add; assert add(2,3)==5; assert add(-4,1)==-3'],
                           cwd=output / 'application', check=True)
            record.update(status='passed', delivery=delivery)
    except BaseException as error:
        record.update(status='failed', error=f'{type(error).__name__}: {error}')
        factory.save(output / 'check.json', record)
        raise
    finally:
        if proc and proc.poll() is None:
            factory.stop(proc)
        # Persist the application result before collecting optional native evidence.
        record['finished_at'] = time.time()
        factory.save(output / 'check.json', record)
        if state.exists():
            try:
                archive_state(state, output)
                archived = archive_sessions(output, native, work, read_json(state / 'sessions.json', []))
                if read_json(output / 'native/manifest.json', {}).get('diagnostic_status') != 'complete':
                    factory.save(output / 'archive-partial.json', {'status': 'partial', 'entries': archived})
                else:
                    factory.save(output / 'archive.json', {'status': 'complete', 'entries': archived})
            except BaseException as error:
                factory.save(output / 'archive-partial.json', {
                    'status': 'partial', 'error': f'{type(error).__name__}: {error}'
                })
        if record['status'] == 'passed':
            shutil.rmtree(work, ignore_errors=True)
        factory.save(output / 'check.json', record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    if record['status'] != 'passed':
        raise RuntimeError(record['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('pi', 'codex'), required=True)
    parser.add_argument('--package', type=Path, help='已解包且冻结的 Linux x86_64 资格包根目录')
    parser.add_argument('--output', type=Path, help='本次资格证据目录；包模式必填')
    args = parser.parse_args()
    run(args.backend, args.output)
