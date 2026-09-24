#!/usr/bin/env python3
"""从实验 run 的 OTLP Backend 生成可离线浏览的 Braid 诊断网站。"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from otlp_store import list_batches, read_batch

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def browser_values(item):
    """浏览器用字符串显示超出安全整数范围的身份及计量值，原始下载不变。"""
    if isinstance(item, int) and abs(item) > 2**53 - 1:
        return str(item)
    if isinstance(item, dict):
        return {key: browser_values(v) for key, v in item.items()}
    if isinstance(item, list):
        return [browser_values(v) for v in item]
    return item


def value(item):
    if not item:
        return None
    for key in ('stringValue', 'intValue', 'doubleValue', 'boolValue', 'bytesValue'):
        if key in item:
            return item[key]
    if 'arrayValue' in item:
        return [value(v) for v in item['arrayValue'].get('values', [])]
    if 'kvlistValue' in item:
        return attributes(item['kvlistValue'].get('values', []))
    return item


def attributes(items):
    return {item['key']: value(item.get('value')) for item in items}


def resources(decoded):
    for batch in decoded['batches']:
        signal = batch['signal']
        key = {'logs': 'resourceLogs', 'traces': 'resourceSpans', 'metrics': 'resourceMetrics'}[signal]
        for resource in batch['data'].get(key, []):
            attrs = attributes((resource.get('resource') or {}).get('attributes', []))
            yield signal, batch['file'], resource, attrs


def diagnostics(decoded, run_id):
    result = {'spans': [], 'logs': [], 'metrics': [], 'errors': decoded['errors']}
    for signal, batch, resource, attrs in resources(decoded):
        if attrs.get('service.name') != 'braid' or attrs.get('braid.run.id') != run_id:
            continue
        scopes_key, records_key, target = {
            'traces': ('scopeSpans', 'spans', 'spans'),
            'logs': ('scopeLogs', 'logRecords', 'logs'),
            'metrics': ('scopeMetrics', 'metrics', 'metrics'),
        }[signal]
        for scope in resource.get(scopes_key, []):
            for record in scope.get(records_key, []):
                if signal == 'logs' and record.get('eventName') == 'braid.evidence':
                    continue
                result[target].append({'batch': batch, 'resource': attrs,
                                       'scope': scope.get('scope'), 'record': record})
    # 同一个 span 在传输重试中可能重复；指标保留原始点，不跨 runtime 累加。
    spans = {}
    for item in result['spans']:
        record = item['record']
        spans[(record.get('traceId'), record.get('spanId'))] = item
    result['spans'] = sorted(spans.values(), key=lambda v: int(v['record'].get('startTimeUnixNano', 0)))
    return result


def invoke(braid, arguments, output, stem):
    with (output / f'{stem}.json').open('w', encoding='utf-8') as stdout, \
            (output / f'{stem}.stderr.log').open('w', encoding='utf-8') as stderr:
        process = subprocess.run([str(braid), 'telemetry', *arguments], stdout=stdout, stderr=stderr)
    return process.returncode


def render_prose(braid, output, evidence):
    texts = set()
    def collect(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in ('body', 'text', 'thinking', 'content', 'message') and isinstance(child, str):
                    texts.add(child)
                else:
                    collect(child)
        elif isinstance(item, list):
            for child in item:
                collect(child)
    collect(evidence)
    ordered = sorted(texts)
    with (output / 'markdown.stderr.log').open('w', encoding='utf-8') as stderr:
        result = subprocess.run([str(braid), 'telemetry', 'render-markdown'],
                                input=json.dumps(ordered), text=True, stdout=subprocess.PIPE, stderr=stderr)
    if result.returncode:
        raise RuntimeError(f'Markdown 渲染失败；见 {output / "markdown.stderr.log"}')
    rendered = json.loads(result.stdout)
    if len(rendered) != len(ordered):
        raise ValueError('Markdown 渲染结果数量不匹配')
    return dict(zip(ordered, rendered))


def generate(run, output, braid, braid_run_id):
    database = run / 'telemetry.sqlite'
    if not database.is_file():
        raise ValueError(f'实验 run 的 OTLP Backend 不存在：{database}')
    if not braid.is_file():
        raise ValueError(f'Braid 二进制不存在，请先构建或指定 --braid：{braid}')
    output.mkdir(parents=True, exist_ok=False)
    raw = output / 'otlp'
    raw.mkdir()
    # 固定批次列表，使持续写入的 Backend 有明确读取截止点。
    batches = list_batches(database)
    for batch in batches:
        signal, payload = read_batch(database, batch['id'])
        filename = f"{batch['id']:06d}-{signal}.pb"
        (raw / filename).write_bytes(payload)
        batch.update(file=f'otlp/{filename}', sha256=hashlib.sha256(payload).hexdigest())
    write_json(output / 'batches.json', batches)
    code = invoke(braid, ['decode', '--input', str(raw)], output, 'decoded')
    if code:
        raise RuntimeError(f'Braid OTLP 解码失败（退出码 {code}）；见 {output / "decoded.stderr.log"}')
    decoded = read_json(output / 'decoded.json')
    run_ids = sorted({attrs['braid.run.id'] for _, _, _, attrs in resources(decoded)
                      if attrs.get('service.name') == 'braid' and isinstance(attrs.get('braid.run.id'), str)})
    if not run_ids:
        raise ValueError(f'该 run 的 Backend 没有带 braid.run.id 的 Braid 数据；解码详情见 {output / "decoded.json"}')
    if braid_run_id is None:
        if len(run_ids) != 1:
            raise ValueError('该实验包含多个 Braid run，请指定 --braid-run-id：' + ', '.join(run_ids))
        braid_run_id = run_ids[0]
    if braid_run_id not in run_ids:
        raise ValueError(f'Backend 中不存在 Braid run {braid_run_id}；可选：{", ".join(run_ids)}')
    restored = output / 'evidence'
    code = invoke(braid, ['reconstruct', '--input', str(raw), '--output', str(restored),
                          '--run-id', braid_run_id], output, 'reconstruction')
    if code:
        manifest = {'run_id': braid_run_id, 'status': 'partial', 'artifacts': [],
                    'gaps': [f'证据重建失败（退出码 {code}）：' +
                             (output / 'reconstruction.stderr.log').read_text(encoding='utf-8')]}
    else:
        manifest = read_json(restored / 'manifest.json')
    sessions = {}
    objects, terminal = {}, None
    for artifact in manifest['artifacts']:
        path = restored / artifact['file']
        if not path.resolve().is_relative_to(restored.resolve()):
            raise ValueError('Braid 重建文件映射越过 evidence 目录')
        if artifact['logical_type'] == 'native_session':
            sessions[artifact['file']] = dict(artifact, entries=[])
        elif artifact['logical_type'] == 'objects':
            objects = read_json(path).get('tables', {})
        elif artifact['source'] == 'result.json':
            terminal = read_json(path)
    if sessions:
        with (restored / 'messages.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                message = json.loads(line)
                sessions[message['artifact']]['entries'].append(message)
    metadata = read_json(run / 'run.json') if (run / 'run.json').is_file() else {}
    # 页面只保留实验身份；command/env 等启动材料可能含凭据。
    metadata = {key: metadata[key] for key in ('run_id', 'variant', 'competition', 'task', 'phase') if key in metadata}
    data = {'experiment': metadata, 'braid_run_id': braid_run_id,
            'generated_at': datetime.now(timezone.utc).isoformat(), 'batches': batches,
            'signals': dict(Counter(b['signal'] for b in batches)), 'manifest': manifest,
            'sessions': list(sessions.values()), 'objects': objects, 'terminal': terminal,
            'diagnostics': diagnostics(decoded, braid_run_id)}
    data['markdown'] = render_prose(braid, output, [data['sessions'], objects])
    template = Path(__file__).with_suffix('.html').read_text(encoding='utf-8')
    # script[type=application/json] 也会被 HTML parser 的 </script> 提前结束。
    # ponytail: 单站数据嵌入 HTML；真实大型运行超过浏览器内存时改为按会话分页面。
    payload = json.dumps(browser_values(data), ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    payload = payload.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (output / 'index.html').write_text(template.replace('/*REPORT_DATA*/', payload), encoding='utf-8')
    return {'index': str(output / 'index.html'), 'braid_run_id': braid_run_id,
            'evidence_status': manifest['status'], 'sessions': len(sessions), 'batches': len(batches)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path, help='实验 run 目录；从其 OTLP Backend 查询 Braid 数据')
    parser.add_argument('--output', required=True, type=Path, help='尚不存在的静态网站目录')
    parser.add_argument('--braid', type=Path, default=ROOT / 'sources/braid/target/debug/braid')
    parser.add_argument('--braid-run-id', help='同一实验包含多个 Braid run 时明确选择')
    args = parser.parse_args()
    try:
        result = generate(args.run.resolve(), args.output.resolve(), args.braid.resolve(), args.braid_run_id)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f'生成失败：{error}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
