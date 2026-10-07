#!/usr/bin/env python3
"""读取历史 Factory 证据或本地实验；分析原生会话，不生成应用或执行评测。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from tooling.scripts.agent_support import save, hashes, digest
from .inspect_runs import list_runs, show_run, render_list, render_show

ROOT = Path(__file__).resolve().parents[2]


def capture(*args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def analyze(run, svc_source=None):
    svc = ['pdm','run','-p',str(svc_source),'svc'] if svc_source else [str(ROOT/'.venv/bin/svc')]
    provenance={'command':svc,'version':capture(*svc,'--version')}
    if svc_source:
        provenance.update(source=str(svc_source), revision=capture('git','rev-parse','HEAD',cwd=svc_source),
                          source_hashes=hashes(svc_source/'cli/src'))
    else:
        package=Path(capture(str(ROOT/'.venv/bin/python'),'-c',
                            'import svc_cli; print(next(iter(svc_cli.__path__)))'))
        provenance['source_hashes']=hashes(package)
    requests=[{'version':3,'intent':'overview'},{'version':3,'intent':'profile','breakdown':'model'}]
    provenance['requests']=requests
    metadata=json.loads((run/'run.json').read_text())
    manifest = run/'native/manifest.json'
    if manifest.exists():
        entries = json.loads(manifest.read_text())['sessions']
        if any(entry.get('archive_error') or not entry.get('native') for entry in entries):
            raise RuntimeError('原生清单包含缺失证据；不能关联 analysis')
    else:
        paths=sorted((run/'native').glob('*.jsonl'))
        if not paths and (run/'pi-session.jsonl').exists(): paths=[run/'pi-session.jsonl']
        entries = [{'native':str(path.relative_to(run)), 'provider':metadata['backend']} for path in paths]
    if not entries:
        raise RuntimeError('没有可分析的原生会话')
    output=run/'analysis'; output.mkdir(exist_ok=True)
    for index, entry in enumerate(entries):
        source = (run/entry['native']).resolve(strict=True)
        if not source.is_relative_to(run.resolve()):
            raise RuntimeError('原生清单指向 run 以外的路径')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if entry.get('sha256') is not None and source_hash != entry['sha256']:
            raise RuntimeError('原生清单内容哈希不一致')
        inputs = dict(provenance, source_session=source.name, source_sha256=source_hash,
                      provider=entry['provider'],
                      session_identity={k:entry.get(k) for k in ('native_id','profile_id','effective_profile_digest','parent_native_session_id','native_role','work_item_kind','work_item_id','assignment_generation')})
        fingerprint = digest(inputs)[:20]
        # Both the exporter and exact native bytes determine a reusable analysis.
        folder=output/f'{index:03}-{fingerprint}'
        if folder.exists():
            cached = json.loads((folder/'provenance.json').read_text())
            if any(cached.get(key) != value for key, value in inputs.items()):
                raise RuntimeError(f'analysis 缓存来源不匹配: {folder}')
            if any(not (folder/name).is_file() or hashlib.sha256((folder/name).read_bytes()).hexdigest() != sha
                   for name, sha in cached['artifacts'].items()):
                raise RuntimeError(f'analysis 缓存内容已改变: {folder}')
            print(f'[缓存] {folder}',flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix='.analysis-',dir=output) as temp:
            staging=Path(temp)
            evidence=staging/'evidence-v4.zip'
            result=capture(*svc,'telemetry','agent-thread','export','--provider',entry['provider'],
                           '--source',str(source),'--output',str(evidence),'--json')
            (staging/'export.json').write_text(result+'\n')
            for request in requests:
                response=subprocess.run([*svc,'analysis','query','--input',str(evidence),'--request','-'],
                                        input=json.dumps(request),capture_output=True,text=True,check=True)
                save(staging/f"{request['intent']}.json",json.loads(response.stdout))
            if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
                raise RuntimeError('原生会话在 analysis 导出期间改变')
            save(staging/'provenance.json',dict(inputs,created_at=time.time(),artifacts=hashes(staging)))
            staging.rename(folder)
    print(f'[svc] {output}，{len(entries)} 个原生会话',flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'show', 'watch', 'analyze'])
    parser.add_argument('run_id', nargs='?')
    parser.add_argument('--run', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT, help='包含 runs/ 的项目或实验根目录')
    parser.add_argument('--variant')
    parser.add_argument('--backend')
    parser.add_argument('--task')
    parser.add_argument('--eval', dest='evaluation')
    parser.add_argument('--profile')
    parser.add_argument('--session')
    parser.add_argument('--case')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--svc-source', type=Path)
    args = parser.parse_args()
    if args.command == 'list':
        result = list_runs(args.root, variant=args.variant, task=args.task, backend=args.backend)
        output = render_list(result)
    else:
        selected = args.run or (args.root/'runs'/args.run_id if args.run_id else None)
        if selected is None:
            parser.error('show/watch/analyze 需要 --run 或 run ID')
        if args.command == 'analyze':
            analyze(selected.resolve(), args.svc_source.resolve() if args.svc_source else None)
            return
        if args.command == 'watch':
            selected = selected.resolve()
            while True:
                result = show_run(selected)
                row = {'observed_at': time.time(), 'run_id': result['id'], 'phase': result['status'],
                       'runtime_blocker': result.get('runtime_blocker')}
                if result.get('warnings'):
                    row['warnings'] = result['warnings']
                print(json.dumps(row, ensure_ascii=False), flush=True)
                if row['runtime_blocker'] and row['runtime_blocker']['status'] == 'blocked':
                    return 2
                if row['phase'] in {'completed', 'failed', 'interrupted', 'finished', 'cancelled', 'lost'}:
                    return 0
                started = json.loads((selected/'run.json').read_text()).get('started_at') or row['observed_at']
                time.sleep(180 if row['observed_at'] - started < 600 else 480)
        result = show_run(selected, evaluation=args.evaluation, case=args.case, profile=args.profile, session=args.session)
        output = render_show(result)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else output)


if __name__ == '__main__':
    raise SystemExit(main())
