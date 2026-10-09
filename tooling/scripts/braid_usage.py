"""Price all saved Pi sessions in one explicit Braid scope of a project export."""
import argparse
from datetime import datetime
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import zipfile

from pi_usage import summarize, estimate


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def collect(project, scope, evidence):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', scope):
        raise ValueError('invalid native scope')
    project = Path(project).resolve(strict=True)
    evidence = Path(evidence).resolve()
    native = evidence / 'native'
    if native.exists():
        raise ValueError(f'使用新的证据目录，避免混入上次累计归档: {native}')
    files, skipped, identities = [], [], []
    archive = zipfile.ZipFile(project) if project.is_file() else None
    try:
        names = archive.namelist() if archive else [p.relative_to(project).as_posix()
            for p in project.rglob('*.jsonl') if p.is_file()]
        marker = f'{scope}/work/native-homes/'
        prefixes = {n[:n.index(marker)] + marker for n in names
                    if marker in n and (n.startswith(marker) or f'/{marker}' in n)}
        if project.name == scope and not archive:
            prefixes.add('work/native-homes/')
        prefixes = {p for p in prefixes if any(n.startswith(p) for n in names)}
        if len(prefixes) != 1:
            raise ValueError(f'必须唯一选中本轮 native-homes，发现 {sorted(prefixes)}')
        prefix = prefixes.pop()
        for name in sorted(set(names)):
            if not name.startswith(prefix) or not name.endswith('.jsonl'):
                continue
            relative = PurePosixPath(name[len(prefix):])
            if '..' in relative.parts or relative.is_absolute():
                raise ValueError(f'unsafe archive member: {name}')
            with archive.open(name) if archive else (project / name).open('rb') as stream:
                first = stream.readline()
                try:
                    header = json.loads(first)
                except (ValueError, UnicodeError) as exc:
                    skipped.append({'file': name, 'reason': str(exc)})
                    continue
                if not isinstance(header, dict) or header.get('type') != 'session':
                    skipped.append({'file': name, 'reason': 'not a native session header; transcript/event copy excluded'})
                    continue
                target = native / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('wb') as output:
                    output.write(first)
                    shutil.copyfileobj(stream, output)
                files.append({'member': name, 'file': str(relative), 'session_id': header.get('id'),
                              'sha256': sha256(target)})
        identity_name = prefix.removesuffix('work/native-homes/') + 'braid-state/sessions.json'
        if archive and identity_name in archive.namelist():
            identities = json.loads(archive.read(identity_name))
        elif not archive and (project / identity_name).is_file():
            identities = json.loads((project / identity_name).read_text())
        if not isinstance(identities, list):
            raise ValueError('braid-state/sessions.json must be an array')
        substitution_name = prefix.removesuffix('work/native-homes/') + 'native-model-substitution.json'
        substitution = None
        if archive and substitution_name in archive.namelist():
            substitution = json.loads(archive.read(substitution_name))
        elif not archive and (project / substitution_name).is_file():
            substitution = json.loads((project / substitution_name).read_text())
        return native, {'native_model_substitution': substitution,
                        'substitution_source': substitution_name if substitution else None,
                        'project': str(project), 'native_scope': scope, 'native_prefix': prefix,
                        'project_sha256': sha256(project)
                        if archive else None, 'files': files, 'excluded_copies': skipped,
                        'braid_identity_source': identity_name, 'braid_sessions': identities}
    finally:
        if archive:
            archive.close()


def apply_substitution(native, usage, receipt, since_ms=None):
    """Split saved responses at the adopted producer boundary, preserving aliases."""
    logical = receipt.get('logical_text_alias') or receipt.get('text_alias')
    actual = receipt.get('actual_text_model')
    # The native substitution contract leaves the independent visual provider
    # unchanged, even if its response records expose the same Flash model ID.
    text_provider = receipt.get('logical_text_provider', 'factory26')
    producer = receipt.get('producer_run')
    applied = receipt.get('applied_at')
    if not logical or not actual or not producer or not isinstance(applied, (int, float)) or isinstance(applied, bool) or not math.isfinite(applied) or applied <= 0:
        raise ValueError('model substitution requires producer_run/applied_at/logical_text_alias/actual_text_model')
    if logical == receipt.get('vision_alias'):
        raise ValueError('text substitution alias cannot also identify the preserved vision route')
    after_ms = max(applied * 1000, since_ms or 0)
    after = summarize(native, after_ms)
    after_items = {(r['session_id'], r['provider'], r['model']): r for r in after['items']}
    rows, mapped = [], 0
    for original in usage['items']:
        new = after_items.get((original['session_id'], original['provider'], original['model']))
        if original['provider'] != text_provider or original['model'] != logical or new is None:
            rows.append(original)
            continue
        before = {**original, 'messages': original['messages'] - new['messages'],
                  'tokens': {f: None if n is None else n - (new['tokens'].get(f) or 0)
                             for f, n in original['tokens'].items()},
                  'known_messages': dict(Counter(original['known_messages']) - Counter(new['known_messages'])),
                  'outcomes': dict(Counter(original['outcomes']) - Counter(new['outcomes'])),
                  'accounting_segment': 'before-substitution'}
        if before['messages']:
            rows.append(before)
        rows.append({**new, 'logical_model': logical, 'model': actual,
                     'accounting_segment': producer, 'applied_at': applied,
                     'accounting_model_source': 'frozen-native-model-substitution'})
        mapped += new['messages']
    models = {}
    for row in rows:
        model = models.setdefault((row['provider'], row['model']), {'provider': row['provider'],
            'model': row['model'], 'messages': 0, 'tokens': {f: None for f in row['tokens']},
            'known_messages': Counter()})
        model['messages'] += row['messages']
        for field, amount in row['tokens'].items():
            if amount is not None:
                if amount < 0:
                    raise ValueError('substitution segment exceeds saved original usage')
                model['tokens'][field] = (model['tokens'][field] or 0) + amount
            model['known_messages'][field] += row['known_messages'].get(field, 0)
    usage['items'], usage['models'] = rows, list(models.values())
    usage['model_substitution'] = {'receipt': receipt, 'mapped_responses': mapped,
        'response_boundary_ms': after_ms, 'logical_text_provider': text_provider,
        'note': 'Only matching text alias responses at/after applied_at are repriced; old histories and the independent vision alias retain their recorded model. This is an ARC price comparison, not token-plan payment.'}
    return usage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path, help='One saved project ZIP or extracted project directory')
    parser.add_argument('--scope', required=True, help='Current native scope; baseline histories are excluded')
    parser.add_argument('--evidence-dir', required=True, type=Path, help='New persistent evidence directory')
    parser.add_argument('--prices', required=True, type=Path, help='Frozen ARC-format prices JSON, no network requests')
    parser.add_argument('--model-substitution', type=Path, help='Explicit frozen producer/applied_at receipt; otherwise use the scope receipt')
    parser.add_argument('--since', help='Exclude inherited responses before this timezone-qualified ISO timestamp')
    args = parser.parse_args()
    since = datetime.fromisoformat(args.since.replace('Z', '+00:00')) if args.since else None
    if since and since.tzinfo is None:
        parser.error('--since 必须包含时区')
    native, evidence = collect(args.project, args.scope, args.evidence_dir)
    usage = summarize(native, since.timestamp()*1000 if since else None)
    substitution = json.loads(args.model_substitution.read_text()) if args.model_substitution else evidence.get('native_model_substitution')
    if substitution:
        usage = apply_substitution(native, usage, substitution, since.timestamp()*1000 if since else None)
        evidence['substitution_sha256'] = hashlib.sha256(json.dumps(substitution, sort_keys=True).encode()).hexdigest()
    if not usage['session_files']:
        parser.error('没有找到本轮原生 session 记录')
    identities = {s.get('native_session_id'): s for s in evidence.pop('braid_sessions')}
    recorded = {s['id'] for s in usage['sessions']}
    evidence['braid_sessions'] = [{k: s.get(k) for k in ('native_session_id', 'profile_id',
        'work_item_id', 'work_item_kind', 'assignment_generation', 'parent_native_session_id')} |
        {'native_record_saved': s.get('native_session_id') in recorded,
         'recorded_turns': len(s.get('turns') or [])} for s in identities.values()]
    for row in usage['items']:
        identity = identities.get(row['session_id'])
        row['session_kind'] = 'braid_member' if identity else 'pi_subagent_or_unindexed'
        if identity:
            row.update({k: identity.get(k) for k in ('profile_id', 'work_item_id', 'work_item_kind')})
    prices = json.loads(args.prices.read_text())
    usage['cost_estimate'] = estimate(usage, prices)
    usage['cost_estimate']['billing_basis'] = 'ARC-price-comparison-not-supplier-payment'
    if substitution:
        usage['cost_estimate']['note'] += ' Actual text model is resolved by producer/applied_at receipt; token-plan fees are not inferred.'
    usage['cost_by_model'] = [{**m, 'cost_estimate': estimate({'items': [m]}, prices)}
                              for m in usage['models']]
    usage['evidence'] = evidence
    usage['prices_sha256'] = hashlib.sha256(args.prices.read_bytes()).hexdigest()
    usage['scope_note'] = ('仅统计一份累计归档内本scope的全部原生session，包括嵌套子会话；'
        '不按根/Issue/PR/reviewer角色过滤，不叠加历史归档。错误响应中保存的usage也计入；'
        '未落盘/在途请求、失败重试未返回usage、已分配但无session文件均无法据此计费。')
    output = args.evidence_dir / 'usage.json'
    output.write_text(json.dumps(usage, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'usage': str(output.resolve()), 'sessions': len(usage['sessions']),
        'messages': usage['messages'], 'tokens': usage['tokens'], 'cost_estimate': usage['cost_estimate'],
        'warnings': usage['warnings']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
