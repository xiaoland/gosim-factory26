"""Summarize saved V8 memory/GC and sampled allocation evidence, without live attachment."""
import argparse
import json
from pathlib import Path


def summarize(folder):
    metrics = folder/'memory.jsonl'
    rows = [json.loads(line) for line in metrics.read_text().splitlines() if line.strip()]
    memory = [row for row in rows if row.get('kind') == 'v8_memory']
    gc = [row for row in rows if row.get('kind') == 'v8_gc']
    result = {'directory': str(folder), 'identity': {key: rows[0].get(key) for key in
              ('pid', 'starttime', 'execution_id', 'node_version')} if rows else {},
              'memory_samples': len(memory),
              'memory_first': memory[0] if memory else None,
              'memory_last': memory[-1] if memory else None,
              'max_bytes': {key: max(row[key] for row in memory) for key in
                            ('rss', 'heapTotal', 'heapUsed', 'external', 'arrayBuffers')} if memory else {},
              'gc_events': len(gc), 'gc_duration_ms': sum(row['duration_ms'] for row in gc),
              'profile_events': [row for row in rows if row.get('kind', '').startswith('v8_profile_')],
              'limits': ['arrayBuffers is included in external; do not add them',
                         'sampled allocation sizes are estimates, not process RSS or retained ownership',
                         'SIGKILL may prevent final profile saving']}
    profile = folder/'allocation.heapprofile'
    if profile.is_file():
        value = json.loads(profile.read_text())
        stacks = []
        pending = [(value['head'], [])]
        while pending:
            node, ancestors = pending.pop()
            frame = node['callFrame']
            stack = [*ancestors, {key: frame.get(key) for key in ('functionName', 'url', 'lineNumber', 'columnNumber')}]
            if node.get('selfSize', 0):
                stacks.append({'estimated_bytes': node['selfSize'], 'stack': stack})
            pending.extend((child, stack) for child in node.get('children', []))
        result['estimated_sampled_bytes'] = sum(row['estimated_bytes'] for row in stacks)
        result['top_allocation_stacks'] = sorted(stacks, key=lambda row: row['estimated_bytes'], reverse=True)[:20]
    else:
        result['profile_missing'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Saved v8 directory or an execution archive root')
    args = parser.parse_args()
    if not args.path.is_dir():
        parser.error('path must be an existing evidence directory')
    folders = [args.path] if (args.path/'memory.jsonl').is_file() else sorted(
        {file.parent for file in args.path.rglob('memory.jsonl') if file.parent.name == 'v8'})
    print(json.dumps({'executions': [summarize(folder) for folder in folders]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
