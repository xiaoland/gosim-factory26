"""Estimate unbilled CNY from the existing Pi callback stream in ARC snapshots."""
import json
from pathlib import Path
import time
from zipfile import ZipFile

from lab.arc_bench.hosted_monitor import download
from lab.arc_bench.playground import TERMINAL


def snapshot_cost(archive, prices):
    with ZipFile(archive) as bundle:
        raw = bundle.read('template/.factory26/pi-minimal/pi-timing.jsonl')
    seen, opened, totals = set(), set(), {}
    gaps = []
    for number, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
        except ValueError:
            gaps.append(f'Incomplete callback record at line {number}')
            continue
        request = row.get('request_id')
        if row.get('kind') == 'request_start' and request:
            opened.add(request)
        if row.get('kind') != 'message_end':
            continue
        if not request:
            gaps.append(f'Missing request identity at line {number}')
            continue
        opened.discard(request)
        if request in seen:
            continue
        seen.add(request)
        model, usage = row.get('model'), row.get('usage') or {}
        price = prices.get(model)
        fields = ('input', 'output', 'cacheRead', 'cacheWrite')
        if price is None or any(type(usage.get(k)) not in (int, float) or usage[k] < 0 for k in fields):
            gaps.append(f'Incomplete usage or price for {model}, request {request}')
            continue
        total = totals.setdefault(model, dict.fromkeys(fields, 0) | {'messages': 0, 'cny': 0})
        total['messages'] += 1
        for key in fields:
            total[key] += usage[key]
        # Pi input excludes cache tokens; output already includes reasoning.
        # ARC lists no separate cache-write tariff, so charge those as input.
        total['cny'] += ((usage['input'] + usage['cacheWrite']) * price['input']
                         + usage['output'] * price['output']
                         + usage['cacheRead'] * price['cache_hit']) / 1_000_000
    if not seen:
        gaps.append('No completed model requests in snapshot')
    return {'cost_cny': sum(v['cny'] for v in totals.values()), 'models': totals,
            'gaps': gaps, 'open_requests': len(opened)}


def active_cost(journal, client):
    state_file = journal / 'state.json'
    if not state_file.exists():
        return {'cost_cny': 0, 'runs': []}
    state = json.loads(state_file.read_text())
    tariff = json.loads(Path(__file__).with_name('arc-prices.json').read_text())
    folder = journal / 'usage-snapshots'
    folder.mkdir(exist_ok=True)
    rows = []
    for task, item in state['tasks'].items():
        rid = item.get('run_id')
        if not rid:
            continue
        status = client.request('/runs/' + rid)
        if status.get('submission_id') != state['submission_id']:
            raise ValueError(f'Budget run identity mismatch: {rid}')
        if status['status'] in TERMINAL:
            continue
        row = {'run_id': rid, 'task': task, 'started_at': time.time()}
        try:
            archive = folder / (rid + '.zip')
            download('/runs/' + rid + '/workspace/template-bundle', archive)
            row.update(snapshot_cost(archive, tariff['models']))
        except Exception as exc:
            row.update(cost_cny=0, gaps=[str(exc)], open_requests=None)
        # Read balance only after this check so newly settled runs are not
        # deducted again. The platform's terminal amount is authoritative.
        if client.request('/runs/' + rid)['status'] in TERMINAL:
            row.update(cost_cny=0, settled_during_download=True)
        row['finished_at'] = time.time()
        rows.append(row)
    return {'cost_cny': sum(row['cost_cny'] for row in rows), 'runs': rows,
            'prices_observed_at': tariff['observed_at'],
            'incomplete': any(row.get('gaps') for row in rows)}
