"""Read Pi session trees, including child sessions, without counting event copies."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lab.analysis.native_profile import TOKENS, timestamp_ms
from lab.arc_bench.arc_spend import estimate

FIELDS = (*TOKENS, 'totalTokens')


def summarize(directory, since_ms=None):
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('输入必须是包含 Pi 原生 JSONL 的目录')
    groups, sessions, seen, warnings = {}, {}, {}, []
    scanned = duplicates = before_since = 0
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', 'node_modules', '.playwright', 'browser-cache'})
        for name in sorted(files):
            if not name.endswith('.jsonl'):
                continue
            path = Path(folder)/name
            relative = str(path.relative_to(root))
            with path.open(encoding='utf-8') as stream:
                try:
                    header = json.loads(next(stream, ''))
                except (ValueError, UnicodeError) as error:
                    warnings.append({'file': relative, 'line': 1, 'error': str(error)})
                    continue
                # Only native session logs are authoritative. events.jsonl and
                # timing streams contain copies and partial assistant updates.
                if not isinstance(header, dict) or header.get('type') != 'session':
                    continue
                scanned += 1
                session_id = header.get('id')
                if not session_id:
                    warnings.append({'file': relative, 'line': 1, 'error': 'session header has no id'})
                    continue
                session = sessions.setdefault(session_id, {'id': session_id, 'files': [],
                    'parent_session': header.get('parentSession'), 'messages': 0})
                session['files'].append(relative)
                for number, line in enumerate(stream, 2):
                    try:
                        entry = json.loads(line)
                        if not isinstance(entry, dict):
                            raise ValueError('record is not an object')
                        message = entry.get('message')
                        if entry.get('type') != 'message' or not isinstance(message, dict) or message.get('role') != 'assistant':
                            continue
                        at = message.get('timestamp') or entry.get('timestamp')
                        if since_ms is not None:
                            if timestamp_ms(at) < since_ms:
                                before_since += 1
                                continue
                        # Forks retain entry IDs and original message times. Count
                        # inherited history once even when the child has a new ID.
                        identity = [entry.get('id'), at, message.get('provider'), message.get('model')]
                        if not entry.get('id'):
                            identity.append(hashlib.sha256(json.dumps(message, sort_keys=True).encode()).hexdigest())
                        key = json.dumps(identity, sort_keys=True)
                        usage = message.get('usage')
                        fingerprint = json.dumps(usage, sort_keys=True)
                        values = usage if isinstance(usage, dict) else {}
                        for field in FIELDS:
                            amount = values.get(field)
                            if amount is not None and (not isinstance(amount, (int, float)) or isinstance(amount, bool)
                                    or not math.isfinite(amount) or amount < 0):
                                raise ValueError(f'invalid {field} token amount: {amount!r}')
                        if key in seen:
                            duplicates += 1
                            if seen[key] != fingerprint:
                                warnings.append({'file': relative, 'line': number, 'error': 'duplicate message has conflicting usage; first record retained'})
                            continue
                        seen[key] = fingerprint
                        provider, model = message.get('provider') or 'unknown', message.get('model') or 'unknown'
                        row = groups.setdefault((session_id, provider, model), {'session_id': session_id,
                            'provider': provider, 'model': model, 'messages': 0, 'outcomes': Counter(),
                            'tokens': {field: None for field in FIELDS}, 'known_messages': Counter()})
                        row['messages'] += 1
                        session['messages'] += 1
                        row['outcomes'][message.get('stopReason') or 'unknown'] += 1
                        usage = usage if isinstance(usage, dict) else {}
                        for field in FIELDS:
                            amount = usage.get(field)
                            if amount is None:
                                continue
                            row['tokens'][field] = (row['tokens'][field] or 0) + amount
                            row['known_messages'][field] += 1
                    except (ValueError, TypeError, OverflowError) as error:
                        warnings.append({'file': relative, 'line': number, 'error': str(error)})
    items = list(groups.values())
    models = {}
    for row in items:
        model = models.setdefault((row['provider'], row['model']), {'provider': row['provider'],
            'model': row['model'], 'messages': 0, 'tokens': {field: None for field in FIELDS}, 'known_messages': Counter()})
        model['messages'] += row['messages']
        for field in FIELDS:
            if row['tokens'][field] is not None:
                model['tokens'][field] = (model['tokens'][field] or 0) + row['tokens'][field]
            model['known_messages'][field] += row['known_messages'][field]
    totals = {field: sum(row['tokens'][field] or 0 for row in items)
              if any(row['tokens'][field] is not None for row in items) else None for field in FIELDS}
    return {'directory': str(root), 'as_of': datetime.now(timezone.utc).isoformat(),
        'tokens': totals,
        'since_ms': since_ms, 'status': 'partial', 'session_files': scanned,
        'sessions': list(sessions.values()), 'duplicate_messages_excluded': duplicates,
        'records_before_since': before_since, 'messages': sum(row['messages'] for row in items),
        'models': list(models.values()), 'items': items, 'warnings': warnings,
        'note': '仅统计已保存的原生模型响应，不代表 HTTP 尝试数或供应商账单；进行中和未落盘用量未知。'
                'reasoning 已计入 output，不重复相加。镜像与 fork 历史去重；'
                '选择单次运行目录或用 --since 排除其它旧运行。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Pi run evidence root containing main and child session logs')
    parser.add_argument('--since', help='Only responses at/after this ISO timestamp (include timezone)')
    parser.add_argument('--prices', type=Path, help='Optional explicit ARC-format price JSON; no network requests')
    parser.add_argument('--json', action='store_true', help='Print per-session, per-model usage and evidence gaps as JSON')
    args = parser.parse_args()
    since = datetime.fromisoformat(args.since.replace('Z', '+00:00')) if args.since else None
    if since is not None and since.tzinfo is None:
        parser.error('--since 必须包含时区，例如 2026-10-07T22:59:00+08:00')
    result = summarize(args.directory, since.timestamp()*1000 if since else None)
    if args.prices:
        result['cost_estimate'] = estimate(result, json.loads(args.prices.read_text()))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"会话 {len(result['sessions'])} / 文件 {result['session_files']} / 模型响应 {result['messages']} / 去重 {result['duplicate_messages_excluded']}")
        print('模型\t响应\tinput\toutput\tcacheRead\tcacheWrite\treasoning\ttotalTokens')
        for row in result['models']:
            values = ['unknown' if row['tokens'][f] is None else f"{row['tokens'][f]:,}" for f in FIELDS]
            print('\t'.join([row['provider']+'/'+row['model'], str(row['messages']), *values]))
        if args.prices:
            cost = result['cost_estimate']; print(f"已定价用量小计: {cost['value']} {cost['currency']} ({cost['coverage']})")
        print(result['note'])
        for warning in result['warnings']:
            print(f"WARNING {warning['file']}:{warning['line']}: {warning['error']}", file=sys.stderr)
    if not result['session_files']:
        parser.exit(1, '没有找到带 session 头的 Pi 原生会话文件。\n')


if __name__ == '__main__':
    main()
