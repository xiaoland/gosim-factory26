"""Estimate observed self-funded usage from the existing Pi callback stream."""
import json
from pathlib import Path
import time
from zipfile import ZipFile

from lab.arc_bench.hosted_monitor import download
from lab.arc_bench.playground import TERMINAL


TIMING_PATH = 'template/.factory26/pi-minimal/pi-timing.jsonl'
USAGE_FIELDS = ('input', 'output', 'cacheRead', 'cacheWrite')


def _price_key(provider, model):
    return f'{provider}/{model}' if provider and model else None


def _valid_usage(usage):
    return all(type(usage.get(key)) in (int, float) and usage[key] >= 0
               for key in USAGE_FIELDS)


def snapshot_cost(archive, prices, cache_write_at_input_rate=False):
    with ZipFile(archive) as bundle:
        try:
            raw = bundle.read(TIMING_PATH)
        except KeyError:
            return {
                'cost_cny': 0,
                'cost_status': 'unknown',
                'models': {},
                'gaps': [f'Missing {TIMING_PATH}'],
                'open_requests': None,
            }
    seen, opened, totals = set(), {}, {}
    gaps = []
    for number, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
        except ValueError:
            gaps.append(f'Incomplete callback record at line {number}')
            continue
        request = row.get('request_id')
        if row.get('kind') == 'request_start' and request:
            opened[request] = {
                'provider': row.get('provider'),
                'model': row.get('model'),
            }
        if row.get('kind') != 'message_end':
            continue
        if not request:
            gaps.append(f'Missing request identity at line {number}')
            continue
        if request in seen:
            continue
        seen.add(request)
        request_meta = opened.pop(request, {})
        provider = row.get('provider') or request_meta.get('provider')
        model = row.get('model') or request_meta.get('model')
        usage = row.get('usage') or {}
        key = _price_key(provider, model)
        price = (prices.get(key) if key else None) or (prices.get(model) if model else None)
        group_key = key or (model if model and prices.get(model) else None)
        if not group_key:
            gaps.append(f'Missing provider/model for request {request}')
        if not _valid_usage(usage):
            gaps.append(f'Incomplete usage for {group_key or "unknown"}, request {request}')
        price_complete = (isinstance(price, dict)
                          and all(price.get(field) is not None
                                  for field in ('input', 'output', 'cache_hit')))
        if not price_complete:
            gaps.append(f'Unknown provider price for {group_key or "unknown"}, request {request}')
        if not group_key or not _valid_usage(usage):
            continue
        total = totals.setdefault(group_key, dict.fromkeys(USAGE_FIELDS, 0) | {
            'provider': provider, 'model': model, 'messages': 0, 'cost_cny': 0,
        })
        total['messages'] += 1
        for field in USAGE_FIELDS:
            total[field] += usage[field]
        if not price_complete:
            total['cost_cny'] = None
            continue
        cache_write_price = price.get('cache_write')
        if cache_write_price is None:
            if cache_write_at_input_rate:
                cache_write_price = price['input']
            elif usage['cacheWrite']:
                total['cost_cny'] = None
                gaps.append(f'Unknown cache-write price for {group_key}, request {request}')
                continue
            else:
                cache_write_price = 0
        if total['cost_cny'] is not None:
            total['cost_cny'] += (
                usage['input'] * price['input']
                + usage['output'] * price['output']
                + usage['cacheRead'] * price['cache_hit']
                + usage['cacheWrite'] * cache_write_price
            ) / 1_000_000
    if not seen:
        gaps.append('No completed model requests in snapshot')
    known = [v['cost_cny'] for v in totals.values() if v['cost_cny'] is not None]
    status = 'unknown' if gaps or any(v['cost_cny'] is None for v in totals.values()) else 'known'
    return {'cost_cny': sum(known), 'cost_status': status, 'models': totals,
            'gaps': gaps, 'open_requests': len(opened)}


def active_cost(journal, client, tariff_name='arc-prices.json', include_terminal=False):
    state_file = journal / 'state.json'
    if not state_file.exists():
        return {'cost_cny': 0, 'runs': []}
    state = json.loads(state_file.read_text())
    tariff = json.loads(Path(__file__).with_name(tariff_name).read_text())
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
        if status['status'] in TERMINAL and not include_terminal:
            continue
        row = {'run_id': rid, 'task': task, 'started_at': time.time()}
        try:
            archive = folder / (rid + '.zip')
            terminal_receipt = folder / (rid + '.terminal.json')
            if not (include_terminal and status['status'] in TERMINAL
                    and terminal_receipt.is_file() and archive.is_file()):
                download('/runs/' + rid + '/workspace/template-bundle', archive)
            row.update(snapshot_cost(
                archive,
                tariff['models'],
                cache_write_at_input_rate=(tariff_name == 'arc-prices.json'),
            ))
            if include_terminal and status['status'] in TERMINAL:
                terminal_receipt.write_text(json.dumps({'run_id': rid, 'status': status['status']})+'\n')
        except Exception as exc:
            row.update(cost_cny=0, gaps=[str(exc)], open_requests=None)
        # Official mode treats a run that settles during download as already
        # billed by the platform. Self-funded observation keeps the final
        # archive because no competition balance is being decremented.
        if client.request('/runs/' + rid)['status'] in TERMINAL and not include_terminal:
            row.update(cost_cny=0, settled_during_download=True)
        row['finished_at'] = time.time()
        rows.append(row)
    return {'cost_cny': sum(row['cost_cny'] for row in rows), 'runs': rows,
            'prices_observed_at': tariff['observed_at'],
            'incomplete': any(row.get('gaps') or row.get('cost_status') != 'known' for row in rows),
            'cost_status': 'unknown' if any(row.get('gaps') or row.get('cost_status') != 'known'
                                           for row in rows) else 'known'}
