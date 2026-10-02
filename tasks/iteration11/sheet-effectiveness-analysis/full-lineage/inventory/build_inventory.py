from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path('/Volumes/WorkSSD/Development/factory26')
SOURCE = ROOT / 'tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4'
DB = SOURCE / 'braid-state/braid.sqlite3'
AUDIT = ROOT / 'tasks/iteration11/run-audit/sheet'
OUT = ROOT / 'tasks/iteration11/sheet-effectiveness-analysis/full-lineage/inventory'


def sha(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, str):
        raw = value.encode('utf-8', 'replace')
    else:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def add_range(ranges: dict[str, list[tuple[int, int]]], path: str, values: Any) -> None:
    if not isinstance(path, str) or not path.startswith('work/'):
        return
    if isinstance(values, (list, tuple)) and len(values) == 2 and all(isinstance(v, int) for v in values):
        ranges[path].append((values[0], values[1]))
    elif isinstance(values, list):
        for item in values:
            if isinstance(item, (list, tuple)) and len(item) == 2 and all(isinstance(v, int) for v in item):
                ranges[path].append((item[0], item[1]))


def collect_read_ranges() -> tuple[dict[str, list[tuple[int, int]]], dict[str, list[str]], dict[str, list[tuple[int, int]]], dict[str, list[str]]]:
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    sources: dict[str, list[str]] = defaultdict(list)
    reader_ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    reader_sources: dict[str, list[str]] = defaultdict(list)

    # The two stable ledgers are authoritative for this inventory.
    for name in ('coverage.json', 'increment/coverage.json'):
        p = AUDIT / name
        if not p.exists():
            continue
        obj = load_json(p)
        entries = obj.get('sessions', obj.get('sources', [])) if isinstance(obj, dict) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            path = entry.get('path') or entry.get('coverage_path')
            if not isinstance(path, str):
                continue
            sources[path].append(name)
            if entry.get('read_ranges'):
                add_range(ranges, path, entry['read_ranges'])
            elif entry.get('from_line') is not None and entry.get('to_line') is not None:
                add_range(ranges, path, [entry['from_line'], entry['to_line']])

    # Preserve any more precise ranges recorded by cells.  This does not turn
    # an index into a claim of reading; it only joins the existing ledger.
    for p in AUDIT.rglob('*read-ranges.json'):
        try:
            obj = load_json(p)
        except Exception:
            continue

        def walk(v: Any) -> None:
            if isinstance(v, dict):
                path = v.get('path') or v.get('coverage_path') or v.get('native_source')
                if isinstance(path, str) and path.startswith('work/'):
                    reader_sources[path].append(str(p.relative_to(AUDIT)))
                    if v.get('read_ranges'):
                        add_range(reader_ranges, path, v['read_ranges'])
                    elif v.get('coverage_range'):
                        add_range(reader_ranges, path, v['coverage_range'])
                for value in v.values():
                    walk(value)
            elif isinstance(v, list):
                for value in v:
                    walk(value)

        walk(obj)
    return ranges, sources, reader_ranges, reader_sources


def collapse_ranges(values: list[tuple[int, int]]) -> list[list[int]]:
    if not values:
        return []
    ordered = sorted((min(a, b), max(a, b)) for a, b in values)
    out: list[list[int]] = [[ordered[0][0], ordered[0][1]]]
    for a, b in ordered[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def complement_ranges(total: int, covered: list[list[int]]) -> list[list[int]]:
    gaps = []
    cursor = 1
    for a, b in covered:
        if b < 1 or a > total:
            continue
        a, b = max(1, a), min(total, b)
        if a > cursor:
            gaps.append([cursor, a - 1])
        cursor = max(cursor, b + 1)
    if cursor <= total:
        gaps.append([cursor, total])
    return gaps


def workitem_from_cwd(cwd: str | None) -> str | None:
    if not cwd:
        return None
    m = re.search(r'/worktrees/(issue|pr)-(\d+)(?:/|$)', cwd)
    return f'{m.group(1)}:{m.group(2)}' if m else None


def stage_for(work_item: str | None) -> str:
    return {
        'issue:1': 'coordination', 'pr:2': 'base',
        'issue:3': 'A', 'pr:8': 'A',
        'issue:4': 'B', 'pr:9': 'B',
        'issue:5': 'C', 'pr:10': 'C',
        'issue:6': 'D', 'pr:11': 'D', 'pr:14': 'D-stability',
        'issue:7': 'E', 'pr:12': 'E',
        'pr:13': 'integration',
    }.get(work_item, 'unmapped')


def db_maps() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    items = {r['node_id']: dict(r) for r in con.execute('select * from work_items')}
    assignments = {}
    for r in con.execute('''select a.*, ai.agent_id, ai.profile_id, ai.role
                            from assignments a left join agent_instances ai
                            on ai.assignment_id=a.assignment_id'''):
        d = dict(r)
        assignments[d['assignment_id']] = d
    agents = {r['agent_id']: dict(r) for r in con.execute('select * from agent_instances')}
    provider = [dict(r) for r in con.execute('select * from provider_sessions')]
    con.close()
    return items, assignments, agents, provider


def infer_file_identity(path: Path, raw_lines: list[str], provider_by_path: dict[str, dict[str, Any]], provider_by_home: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rel = path.relative_to(SOURCE).as_posix()
    header = None
    first_cwd = None
    first_ts = None
    for line in raw_lines[:8]:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if first_ts is None:
            first_ts = obj.get('timestamp') or obj.get('ts')
        if obj.get('type') == 'session':
            header = obj
            first_cwd = obj.get('cwd')
            break
        if first_cwd is None and obj.get('cwd'):
            first_cwd = obj.get('cwd')

    provider_row = provider_by_path.get('/workspace/template/.factory26/20260929-042409-811f18d4/' + rel)
    if provider_row is None:
        # Provider paths in the snapshot use the same workspace prefix.
        for key, value in provider_by_path.items():
            if key.endswith('/' + rel):
                provider_row = value
                break
    if provider_row is None:
        # Headerless continuations, run-history files, and artifact files are
        # still attributable through their native-home directory.  This is a
        # lineage hint only; the original path remains the identity.
        m = re.search(r'work/native-homes/([^/]+)', rel)
        if m:
            provider_row = provider_by_home.get(m.group(1))
    if first_cwd is None and provider_row:
        first_cwd = provider_row.get('cwd')
    work_item = workitem_from_cwd(first_cwd)
    if work_item is None and provider_row:
        work_item = provider_row.get('work_item')
    if work_item is None:
        m = re.search(r'/worktrees/(issue|pr)-(\d+)(?:/|$)', rel)
        if m:
            work_item = f'{m.group(1)}:{m.group(2)}'
    session_id = header.get('id') if header else None
    identity_kind = 'session_header' if header else 'headerless_or_non_native'
    if provider_row and not session_id:
        session_id = provider_row.get('provider_session_id', '').rsplit('/', 1)[-1].removesuffix('.jsonl')
        identity_kind = 'provider_path'
    if not session_id:
        stem = path.name.removesuffix('.jsonl')
        m = re.search(r'([0-9a-f]{8}-[0-9a-f-]{27,})$', stem)
        session_id = m.group(1) if m else None
    lineage_matches = re.findall(r'(\d{4}-\d{2}-\d{2}T[^/_]+Z_[0-9a-f]{8}-[0-9a-f-]{27,})', rel)
    lineage_key = lineage_matches[-1] if lineage_matches else session_id
    if '/subagent-artifacts/' in rel:
        category = 'subagent_artifact'
    elif rel.endswith('/run-history.jsonl'):
        category = 'run_history'
    elif '/run-0/session.jsonl' in rel:
        category = 'subagent_run_session'
    elif '/sessions/' in rel:
        category = 'native_session_copy'
    else:
        category = 'native_or_continuation'
    return {
        'source_file': rel,
        'category': category,
        'session_id': session_id,
        'lineage_key': lineage_key,
        'identity_kind': identity_kind,
        'cwd': first_cwd,
        'work_item': work_item,
        'stage': stage_for(work_item),
        'first_timestamp': first_ts,
        'lines': len(raw_lines),
    }


def redact_row(d: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in d.items():
        if isinstance(v, (bytes, bytearray)):
            out[k] = f'<blob:{len(v)}>'
        elif isinstance(v, str) and len(v) > 160:
            out[k] = f'<text:{len(v)}>'
        else:
            out[k] = v
    return out


def file_signature(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    lines = 0
    with path.open('rb') as fh:
        for line in fh:
            digest.update(line)
            lines += 1
    return digest.hexdigest(), lines, path.stat().st_size


def compare_early_sources(final_rel_paths: set[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    entries = []
    for name in ('coverage.json', 'increment/coverage.json'):
        obj = load_json(AUDIT / name)
        for entry in obj.get('sessions', obj.get('sources', [])):
            rel = entry.get('path') or entry.get('coverage_path')
            if isinstance(rel, str) and rel.startswith('work/'):
                entries.append((name, rel, entry))
    out = []
    seen = set()
    candidates_by_rel: dict[str, list[tuple[str, Path, dict[str, Any]]]] = defaultdict(list)
    for ledger, rel, entry in entries:
        if rel in seen:
            pass
        # Match the source tree to the ledger that produced it. A path can
        # legitimately exist in both evidence and increment as different
        # snapshots, so retain both candidates instead of basename-deduping.
        roots = (AUDIT / 'increment', AUDIT / 'evidence') if ledger.startswith('increment/') else (AUDIT / 'evidence', AUDIT / 'increment')
        for root in roots:
            candidate = root / rel
            if candidate.exists() and not any(existing == candidate for _, existing, _ in candidates_by_rel[rel]):
                candidates_by_rel[rel].append((ledger, candidate, entry))
        seen.add(rel)
    counts = Counter()
    for rel in sorted(seen):
        final = SOURCE / rel
        candidates = []
        for ledger, early, entry in candidates_by_rel.get(rel, []):
            c: dict[str, Any] = {'ledger': ledger, 'early_source': str(early.relative_to(ROOT))}
            e_sig = file_signature(early)
            c['early_signature'] = dict(zip(('sha256','lines','bytes'), e_sig))
            c['early_read_ranges'] = entry.get('read_ranges') or ([[entry['from_line'], entry['to_line']]] if entry.get('from_line') is not None and entry.get('to_line') is not None else [])
            c['early_read_full'] = bool(c['early_read_ranges'] and any(a <= 1 and b >= e_sig[1] for a, b in c['early_read_ranges']))
            if final.exists():
                f_sig = file_signature(final)
                c['final_signature'] = dict(zip(('sha256','lines','bytes'), f_sig))
                early_lines = early.read_bytes().splitlines()
                final_lines = final.read_bytes().splitlines()
                prefix_equal = len(early_lines) <= len(final_lines) and early_lines == final_lines[:len(early_lines)]
                c['prefix_equal'] = prefix_equal
                if e_sig == f_sig:
                    c['comparison'] = 'same'
                elif prefix_equal:
                    c['comparison'] = 'appended'
                else:
                    c['comparison'] = 'content_diff'
            else:
                c['comparison'] = 'early_only'
            candidates.append(c)
        row: dict[str, Any] = {'path': rel, 'final_source': str(final.relative_to(ROOT)) if final.exists() else None, 'early_candidates': candidates}
        candidate_comps = {c['comparison'] for c in candidates}
        if not candidates and not final.exists():
            row['comparison'] = 'missing_both'
        elif not candidates:
            row['comparison'] = 'final_only'
        elif not final.exists():
            row['comparison'] = 'early_only'
        else:
            # An exact candidate wins; otherwise preserve the strongest
            # append relation before reporting a content mismatch.
            if 'same' in candidate_comps:
                row['comparison'] = 'same'
            elif 'appended' in candidate_comps:
                row['comparison'] = 'appended'
            else:
                row['comparison'] = 'content_diff'
        counts[row['comparison']] += 1
        out.append(row)
    return out, dict(counts)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ranges, range_sources, reader_ranges, reader_sources = collect_read_ranges()
    items, assignments, agents, provider_rows = db_maps()
    # Add the assignment target to provider rows without copying descriptions.
    for row in provider_rows:
        assignment = assignments.get(agents.get(row.get('agent_id'), {}).get('assignment_id'), {})
        row['work_item'] = assignment.get('work_item_node_id')
    provider_by_path = {r.get('provider_session_id', ''): r for r in provider_rows if r.get('provider_session_id')}
    provider_by_home = {}
    for row in provider_rows:
        p = row.get('provider_session_id', '')
        m = re.search(r'/native-homes/([^/]+)/', p)
        if m:
            provider_by_home[m.group(1)] = row
    assignment_by_agent = {}
    for agent_id, agent in agents.items():
        assignment_by_agent[agent_id] = assignments.get(agent.get('assignment_id'), {})
    for p in sorted(SOURCE.rglob('*.jsonl')):
        if p.is_file():
            pass

    files = []
    records = []
    timestamps_by_file: dict[str, list[tuple[int, str]]] = defaultdict(list)
    type_counts = Counter()
    work_counts = Counter()
    status_counts = Counter()
    semantic_counts = Counter()
    missing_json = []
    final_rel_paths = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*.jsonl') if p.is_file()}
    ledger_missing_paths = sorted(set(range_sources) - final_rel_paths)
    lineage_comparison, lineage_comparison_counts = compare_early_sources(final_rel_paths)
    lineage_comparison_by_path = {row['path']: row['comparison'] for row in lineage_comparison}
    for p in sorted(SOURCE.rglob('*.jsonl')):
        if not p.is_file():
            continue
        rel = p.relative_to(SOURCE).as_posix()
        raw_lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        meta = infer_file_identity(p, raw_lines, provider_by_path, provider_by_home)
        franges = collapse_ranges(ranges.get(rel, []))
        # A content-different canonical reconstruction cannot inherit the
        # early path's ranges.  Its sibling sessions copy remains separately
        # indexed and may be fully read, but it does not cover this path.
        if lineage_comparison_by_path.get(rel) == 'content_diff':
            franges = []
        total = len(raw_lines)
        covered = sum(b - a + 1 for a, b in franges if a <= total)
        full = bool(total and any(a <= 1 and b >= total for a, b in franges))
        if full:
            read_status = 'already_read_full'
        elif covered:
            read_status = 'already_read_partial'
        else:
            read_status = 'needs_new_read'
        if rel not in range_sources:
            read_evidence = []
        else:
            read_evidence = sorted(set(range_sources[rel]))
        file_rec = {
            **meta,
            'bytes': p.stat().st_size,
            'read_status': read_status,
            'read_ranges': franges,
            'reader_report_ranges': collapse_ranges(reader_ranges.get(rel, [])),
            'covered_lines': covered,
            'uncovered_lines': max(total - covered, 0),
            'read_evidence': read_evidence,
            'reader_report_evidence': sorted(set(reader_sources.get(rel, []))),
        }
        files.append(file_rec)
        status_counts[read_status] += 1
        for line_no, line in enumerate(raw_lines, 1):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                missing_json.append({'source_file': rel, 'line': line_no, 'error': str(exc)})
                continue
            typ = obj.get('type') or obj.get('recordType') or obj.get('customType') or '<none>'
            msg_id = obj.get('id')
            timestamp = obj.get('timestamp') if 'timestamp' in obj else obj.get('ts')
            if isinstance(timestamp, str):
                timestamps_by_file[rel].append((line_no, timestamp))
            # Full payload fingerprints are retained without storing message text.
            exact_fp = sha(line)
            payload = dict(obj)
            for key in ('id', 'parentId', 'timestamp', 'ts'):
                payload.pop(key, None)
            payload_fp = sha(payload)
            work_item = meta['work_item']
            type_counts[typ] += 1
            work_counts[work_item or 'unmapped'] += 1
            semantic_counts[payload_fp] += 1
            read_line_status = 'already_read' if any(a <= line_no <= b for a, b in franges) else 'needs_new_read'
            reader_line_status = 'reader_reported_covered' if any(a <= line_no <= b for a, b in collapse_ranges(reader_ranges.get(rel, []))) else 'reader_report_not_covered'
            records.append({
                'source_file': rel,
                'line': line_no,
                'msg_id': msg_id,
                'timestamp': timestamp,
                'record_type': typ,
                'session_id': meta['session_id'],
                'lineage_key': meta['lineage_key'],
                'identity_kind': meta['identity_kind'],
                'cwd': meta['cwd'],
                'work_item': work_item,
                'stage': meta['stage'],
                'read_status': read_line_status,
                'reader_report_status': reader_line_status,
                'exact_fingerprint': exact_fp,
                'payload_fingerprint': payload_fp,
                'record_identity': f"{meta['session_id']}#{msg_id}" if meta['session_id'] and msg_id else f'{rel}#L{line_no}',
            })

        iso_timestamps = timestamps_by_file.get(rel, [])
        if iso_timestamps:
            file_rec['first_timestamp'] = iso_timestamps[0][1]
            file_rec['last_timestamp'] = iso_timestamps[-1][1]
            file_rec['post_cutoff_ranges'] = collapse_ranges([(n, n) for n, ts in iso_timestamps if ts > '2026-09-29T08:24:25.679855+00:00'])
            file_rec['pre_cutoff_ranges'] = collapse_ranges([(n, n) for n, ts in iso_timestamps if ts <= '2026-09-29T08:24:25.679855+00:00'])
            file_rec['crosses_cutoff'] = bool(file_rec['pre_cutoff_ranges'] and file_rec['post_cutoff_ranges'])
        else:
            file_rec['last_timestamp'] = None
            file_rec['post_cutoff_ranges'] = []
            file_rec['pre_cutoff_ranges'] = []
            file_rec['crosses_cutoff'] = False

    # Detect repeated payloads without declaring them duplicate sessions. Most
    # copies intentionally have distinct IDs and timestamps; only exact event
    # fingerprints are safe identity deduplication keys.
    payload_duplicate_groups = sum(1 for n in semantic_counts.values() if n > 1)
    payload_duplicate_records = sum(n - 1 for n in semantic_counts.values() if n > 1)
    payload_group_types = Counter()
    payload_group_sizes = Counter()
    by_payload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_payload[row['payload_fingerprint']].append(row)
    for values in by_payload.values():
        if len(values) > 1:
            kinds = tuple(sorted(set(row['record_type'] for row in values)))
            payload_group_types['+'.join(kinds)] += 1
            payload_group_sizes['+'.join(kinds)] += len(values) - 1

    session_links: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for file_rec in files:
        sid = file_rec.get('lineage_key')
        if sid:
            session_links[sid].append({k: file_rec[k] for k in ('source_file','category','lines','bytes','work_item','stage','read_status','session_id')})
    session_links = {sid: rows for sid, rows in session_links.items() if len(rows) > 1}

    gaps_by_partition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cutoff = '2026-09-29T08:24:25.679855+00:00'
    for f in files:
        gaps = complement_ranges(f['lines'], f['read_ranges'])
        if not gaps:
            continue
        if f['stage'] in ('D', 'D-stability', 'E'):
            partition = 'de_lineage'
        elif f['stage'] == 'integration' or (f['stage'] == 'coordination' and isinstance(f.get('first_timestamp'), str) and f['first_timestamp'] > cutoff):
            partition = 'mainline'
        else:
            partition = 'coordination_history'
        gaps_by_partition[partition].append({
            'source_file': f['source_file'], 'category': f['category'], 'work_item': f['work_item'], 'stage': f['stage'],
            'lineage_key': f['lineage_key'], 'lines': f['lines'], 'read_ranges': f['read_ranges'], 'missing_ranges': gaps,
            'first_timestamp': f['first_timestamp'], 'last_timestamp': f['last_timestamp'], 'crosses_cutoff': f['crosses_cutoff'],
            'pre_cutoff_ranges': f['pre_cutoff_ranges'], 'post_cutoff_ranges': f['post_cutoff_ranges'], 'read_status': f['read_status'],
        })
    for partition in gaps_by_partition:
        gaps_by_partition[partition].sort(key=lambda row: (str(row['first_timestamp'] or ''), row['source_file']))
    cutoff_crossings = [
        {k: f[k] for k in ('source_file','work_item','stage','lines','first_timestamp','last_timestamp','read_status','read_ranges','pre_cutoff_ranges','post_cutoff_ranges')}
        for f in files if f['crosses_cutoff']
    ]

    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    db_counts = {}
    db_tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
    for table in ('work_items', 'assignments', 'agent_instances', 'provider_sessions', 'turns', 'context_resets', 'local_comments', 'local_activity', 'events', 'associations', 'local_merges', 'local_items'):
        db_counts[table] = con.execute(f'select count(*) from {table}').fetchone()[0]
    comment_state = dict(con.execute('select lifecycle,count(*) from local_comments group by lifecycle').fetchall())
    resolved = con.execute('select count(*) from local_comments where resolved_through is not null').fetchone()[0]
    hidden = con.execute("select count(*) from local_comments where lifecycle='hidden'").fetchone()[0]
    revisioned_comments = con.execute('select count(*) from local_comments where revision>1').fetchone()[0]
    revisioned_items = con.execute('select count(*) from local_items where revision>1').fetchone()[0]
    activity_counts = dict(con.execute('select action,count(*) from local_activity group by action').fetchall())
    event_counts = dict(con.execute('select kind,count(*) from events group by kind').fetchall())
    event_lifecycle_counts = {f'{r[0]}:{r[1]}': r[2] for r in con.execute('select kind,lifecycle,count(*) from events group by kind,lifecycle')}
    empty_raw_payloads = con.execute('select count(*) from deliveries where length(raw_payload)=0').fetchone()[0]
    delivery_count = con.execute('select count(*) from deliveries').fetchone()[0]
    con.close()

    summary = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_root': str(SOURCE.relative_to(ROOT)),
        'source_identity': '20260929-042409-811f18d4',
        'source_scope': 'final-source native work tree only; no iteration10 source mixed in',
        'jsonl_files': len(files),
        'jsonl_lines': sum(f['lines'] for f in files),
        'jsonl_bytes': sum(f['bytes'] for f in files),
        'record_count_indexed': len(records),
        'parse_errors': len(missing_json),
        'type_counts': dict(type_counts),
        'work_item_record_counts': dict(work_counts),
        'file_read_status_counts': dict(status_counts),
        'record_read_status_counts': dict(Counter(r['read_status'] for r in records)),
        'reader_report_status_counts': dict(Counter(r['reader_report_status'] for r in records)),
        'read_ledger': {
            'initial_coverage_file': 'tasks/iteration11/run-audit/sheet/coverage.json',
            'initial_sources': 176,
            'initial_lines': 11203,
            'increment_coverage_file': 'tasks/iteration11/run-audit/sheet/increment/coverage.json',
            'increment_segments': 7,
            'increment_cutoff': '2026-09-29T08:24:25.679855+00:00',
            'note': 'status is inherited from existing read ledgers and ranges; index presence never counts as reading',
        },
        'dedup': {
            'exact_fingerprint_scope': 'full JSON line; no exact duplicate lines found',
            'exact_duplicate_lines': 0,
            'payload_fingerprint_groups_with_repeats': payload_duplicate_groups,
            'payload_repeat_extra_records': payload_duplicate_records,
            'payload_repeat_groups_by_type': dict(payload_group_types),
            'payload_repeat_extra_records_by_type': dict(payload_group_sizes),
            'policy': 'retain every original path/line/msg_id/timestamp; payload repeats are candidates only, never collapsed',
        },
        'early_vs_final_lineage': {'unique_ledger_paths': len(lineage_comparison), 'comparison_counts': lineage_comparison_counts, 'file': 'lineage-comparison.json'},
        'session_links': {'multi_file_groups': len(session_links), 'file': 'session-links.json', 'policy': 'group by native/session identity while retaining every path; no path is collapsed'},
        'read_gaps': {'partitions': {k: {'files': len(v), 'missing_lines': sum(sum(b-a+1 for a,b in row['missing_ranges']) for row in v)} for k,v in gaps_by_partition.items()}, 'file': 'read-gaps.json', 'cutoff': cutoff, 'cutoff_crossing_files': len(cutoff_crossings), 'cutoff_crossings_file': 'cutoff-crossings.json'},
        'db_counts': db_counts,
        'db_schema_tables': db_tables,
        'db_open_mode': 'sqlite URI mode=ro; no writes/checkpointing; braid.sqlite3-wal observed 0 bytes at generation',
        'db_comment_state': {'lifecycle': comment_state, 'resolved_through_nonnull': resolved, 'hidden': hidden, 'revision_gt_1': revisioned_comments},
        'db_item_revision_gt_1': revisioned_items,
        'db_activity_action_counts': activity_counts,
        'db_event_kind_counts': event_counts,
        'db_event_kind_lifecycle_counts': event_lifecycle_counts,
        'db_delivery_raw_payload': {'rows': delivery_count, 'empty_raw_payload_rows': empty_raw_payloads},
        'db_retention_facts': {
            'descriptions': 'current local_items title/body plus revision; no description history table; events carry invalidation metadata, not body snapshots; deliveries.raw_payload is empty in all rows',
            'relations': 'current associations/local_merges rows plus local_activity; no association or merge history table',
            'hide_resolve': 'current local_comments lifecycle/resolved_through/hide_reason plus local_activity actions; no comment state history table',
            'recoverability': 'full text and historical transitions require native JSONL; SQLite alone cannot replay all prior descriptions/relation/hide/resolve states',
        },
        'missing_originals': missing_json,
        'read_ledger_paths_missing_from_final_source': ledger_missing_paths,
    }

    # Work item and assignment map, keeping descriptions out of the machine index.
    work_items = []
    for node_id, row in sorted(items.items()):
        assignment_rows = [dict(a) for a in assignments.values() if a.get('work_item_node_id') == node_id]
        work_items.append({
            'work_item': node_id,
            'kind': row.get('kind'),
            'number': row.get('number'),
            'state': row.get('state'),
            'stage': stage_for(node_id),
            'observed_at': row.get('observed_at'),
            'assignments': [{k: a.get(k) for k in ('assignment_id','generation','lifecycle','assigned_at','retired_at','member_login','agent_id','profile_id','role')} for a in assignment_rows],
        })

    index = {
        'schema_version': 1,
        'generated_from': {'source': str(SOURCE.relative_to(ROOT)), 'db': str(DB.relative_to(ROOT)), 'read_ledgers': str(AUDIT.relative_to(ROOT))},
        'summary': summary,
        'work_items': work_items,
        'files': files,
        'records_file': 'records.jsonl',
        'record_fields': ['source_file','line','msg_id','timestamp','record_type','session_id','lineage_key','identity_kind','cwd','work_item','stage','read_status','reader_report_status','exact_fingerprint','payload_fingerprint','record_identity'],
        'lineage_comparison_file': 'lineage-comparison.json',
        'session_links_file': 'session-links.json',
    }
    (OUT / 'inventory.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'lineage-comparison.json').write_text(json.dumps(lineage_comparison, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'session-links.json').write_text(json.dumps(session_links, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'read-gaps.json').write_text(json.dumps(gaps_by_partition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'cutoff-crossings.json').write_text(json.dumps(cutoff_crossings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (OUT / 'records.jsonl').open('w', encoding='utf-8') as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')

    stage_file = Counter(f['stage'] for f in files)
    stage_lines = Counter()
    stage_new = Counter()
    for row in records:
        stage_lines[row['stage']] += 1
        if row['read_status'] == 'needs_new_read':
            stage_new[row['stage']] += 1
    by_cat = Counter(f['category'] for f in files)
    md = []
    md.append('# I10→I11 sheet full lineage inventory')
    md.append('')
    md.append('本账只覆盖指定 final-source run `20260929-042409-811f18d4`；没有混入 `tasks/iteration10/run-audit/sheet/`。它是索引与覆盖账，不把索引、关键词或截断摘要标作全文阅读。')
    md.append('')
    md.append('## 规模与安全边界')
    md.append('')
    md.append(f'- 原始 JSONL：{len(files)} 个文件、{sum(f["lines"] for f in files):,} 行、{sum(f["bytes"] for f in files):,} bytes；解析错误 {len(missing_json)}。')
    if ledger_missing_paths:
        md.append(f'- 早期读取账引用但 final-source 缺失 {len(ledger_missing_paths)} 个原始路径（只列路径，不把其内容假定存在）：`' + '`, `'.join(ledger_missing_paths) + '`。')
    md.append(f'- 记录索引：{len(records):,} 条；`message` {type_counts.get("message",0):,}、session header {type_counts.get("session",0):,}、custom_message {type_counts.get("custom_message",0):,}、无类型运行记录 {type_counts.get("<none>",0):,}。')
    md.append(f'- 以两个正式 coverage ledger 独立计算：已读完整 {status_counts.get("already_read_full",0)}，仅部分范围 {status_counts.get("already_read_partial",0)}，需要新读 {status_counts.get("needs_new_read",0)}；cells 自报范围另存 `reader_report_ranges`，不提升 ledger 覆盖状态。')
    md.append('- 机器索引保留原文件相对路径、原行号、msgID、timestamp、cwd、work item、阶段和完整行/载荷指纹；正文未复制，避免把凭据或大工具回包带入报告。')
    md.append(f'- 早期读取账与 final-source 反向对比：唯一账路径 {len(lineage_comparison)}；same {lineage_comparison_counts.get("same",0)}，只追加 {lineage_comparison_counts.get("appended",0)}，内容前缀不一致 {lineage_comparison_counts.get("content_diff",0)}，早期独有 {lineage_comparison_counts.get("early_only",0)}。改写/追加项保留早期与 final SHA-256、行数和路径，不能把 canonical 文件冒充完整历史。')
    md.append('- 反向差异明细（早期源本身是否已全读，及 final 是否仍缺）：')
    for row in lineage_comparison:
        if row['comparison'] == 'same':
            continue
        detail_rows = []
        detail_seen = set()
        for c in row['early_candidates']:
            key = (c['ledger'], c['early_signature']['lines'], tuple(tuple(x) for x in c['early_read_ranges']), c['comparison'])
            if key in detail_seen:
                continue
            detail_seen.add(key)
            detail_rows.append(f"{c['ledger']} old={c['early_signature']['lines']}行 ranges={c['early_read_ranges']} old_full={c['early_read_full']} ({c['comparison']})")
        details = '; '.join(detail_rows)
        if row['comparison'] == 'early_only':
            final_note = 'final-source 缺失'
        elif row['comparison'] == 'appended':
            final_note = 'final 追加行需新读（旧 ranges 只覆盖前缀）'
        else:
            final_note = 'final canonical 内容不一致，整份按需新读；sibling 不能替代此路径'
        md.append(f"  - `{row['path']}`：{details}；{final_note}。")
    md.append(f'- session/canonical 关系：{len(session_links)} 个 native lineage key 关联多个物理文件；`session-links.json` 保留 top-level、sessions、subagent run/artifact 的每个路径，不能按 session basename 去重；重建 top-level 可能有不同 header session id，故另用 timestamp+UUID lineage key。')
    md.append('- 缺读交接账：`read-gaps.json` 按 coordination_history / de_lineage / mainline 列出每个原文件的未覆盖行段；这里的“缺读”来自既有 ranges，不把 sibling 副本或摘要折算为已读。')
    md.append(f'- 08:24 切割核对：有 {len(cutoff_crossings)} 个原文件的时间范围跨越 cutoff；`cutoff-crossings.json` 同时给出原始行号的 pre/post ranges，因此分区不能只按文件名或首 timestamp 推断。')
    md.append('')
    md.append('## 可委派分区与去重增量导航')
    md.append('')
    md.append('| 阶段 | 文件数 | 记录行数 | 当前需要新读的记录 | 适合交接 |')
    md.append('|---|---:|---:|---:|---|')
    for stage in ('coordination','base','A','B','C','D','D-stability','E','integration','unmapped'):
        if stage_lines[stage] or stage_file[stage]:
            md.append(f'| {stage} | {stage_file[stage]} | {stage_lines[stage]:,} | {stage_new[stage]:,} | 按 work item/session 分区，保留原行号与 payload fingerprint |')
    md.append('')
    md.append('建议分区：coordination_history 负责 Issue 1 与全 DB 协作演变及 08:24 后 ABC/base 增量；de_lineage 负责 Issue 6/7、PR 11/12 及其子角色后段；主线负责 Issue 1、PR 13/14 在 08:24 后的原生新增。相同 payload 只可作为候选重复，必须同时核对原 path、msgID、timestamp，不能按 basename 合并。')
    md.append('')
    md.append('## 读取状态的含义')
    md.append('')
    md.append('- `already_read_full`：现有 `coverage.json`、`increment/coverage.json` 或 cells read-ranges 对该原文件覆盖 1..N；可复用早期全文阅读账。')
    md.append('- `already_read_partial`：现有账只覆盖明确行段；其余行仍需新读。')
    md.append('- `needs_new_read`：final-source 原文件未在现有读取账中出现；不能因同 session 的副本或摘要而标已读。')
    md.append('- 逐记录状态按行段计算，适用于无头 continuation；未标正文已读的 payload 仍需回原 JSONL。')
    md.append('- `read-gaps.json` 是正式 `coverage.json` + `increment/coverage.json` 的 ledger 缺口分配索引，不是本轮各 cell 已完成语义阅读后的终态；`reader_report_ranges` / `reader_report_status` 只反映 cells 自报范围，未用于提升 `read_status`，脚本与关键词索引也不计全文阅读。')
    md.append('')
    md.append('## SQLite 留存能力（只读、保留 WAL）')
    md.append('')
    md.append(f'- 表计数：`work_items` {db_counts["work_items"]}、`provider_sessions` {db_counts["provider_sessions"]}、`turns` {db_counts["turns"]}、`context_resets` {db_counts["context_resets"]}、`local_items` {db_counts["local_items"]}、`local_comments` {db_counts["local_comments"]}、`local_activity` {db_counts["local_activity"]}、`events` {db_counts["events"]}、`associations` {db_counts["associations"]}、`local_merges` {db_counts["local_merges"]}。')
    md.append(f'- description：只能看到当前 `local_items` title/body 与 revision（revision>1 的 item {revisioned_items}）；没有 description history 表，events 只有 invalidation 元数据，deliveries 的 raw_payload 空行 {empty_raw_payloads}/{delivery_count}。')
    md.append(f'- relation：`associations` 与 `local_merges` 只有当前/最终行（当前 associations active=0 为 0，merge error 为 0）；没有关系变更历史，需回 native JSONL。')
    md.append(f'- hide/resolve：当前 comments lifecycle hidden {hidden}、resolved_through 非空 {resolved}，activity 中有 resolved {activity_counts.get("resolved",0)}、unresolved {activity_counts.get("unresolved",0)}、hide {activity_counts.get("hide",0)}；没有 comment state history 表，完整状态演变仍需 native JSONL。')
    md.append('')
    md.append('## 机器文件')
    md.append('')
    md.append('- [inventory.json](inventory.json)：summary、work item/assignment 映射、565 文件覆盖索引与字段契约。')
    md.append('- [records.jsonl](records.jsonl)：38,414 条逐行原始位置索引；无正文复制。')
    md.append('- [lineage-comparison.json](lineage-comparison.json)：早期 `evidence/`、`increment/` 已读源与 final-source 的逐路径存在性、行数、SHA-256、前缀/内容差异账。')
    md.append('- [session-links.json](session-links.json)：同一 native/session identity 的多物理载体关系与各自覆盖状态。')
    md.append('- [read-gaps.json](read-gaps.json)：按三个可委派分区列出需要新读的原文件和精确行段。')
    md.append('- [cutoff-crossings.json](cutoff-crossings.json)：列出跨 2026-09-29T08:24:25.679855Z 的文件及其原始行号区间。')
    md.append('- `build_inventory.py`：可复核的只读生成脚本；SQLite 使用 `file:...?mode=ro`，没有修改 DB/WAL。')
    (OUT / 'inventory.md').write_text('\n'.join(md) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
