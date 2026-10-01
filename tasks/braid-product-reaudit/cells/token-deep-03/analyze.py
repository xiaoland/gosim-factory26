import collections, gzip, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from lab.analysis.native_profile import union_ms

base = Path(__file__).parent
with gzip.open(base/'snapshot.json.gz', 'rt') as source:
    data = json.load(source)
result = {'since': data['since'], 'capture_started': data['captured'], 'runs': {}}
fields = ('input', 'output', 'cacheRead', 'cacheWrite', 'reasoning')
def text(message):
    content = message.get('content', [])
    return content if isinstance(content, str) else '\n'.join(b.get('text', '') for b in content)
def usage_add(target, usage):
    target['responses'] += 1
    for field in fields: target[field] += usage.get(field, 0)
def poll(command):
    return (bool(re.search(r'\bpbb (status|tail|list)\b|\bsleep \d|\b(tail|grep).*\.log', command))
            and not re.search(r'\b(npm|npx|node|python3?|git|curl|braid|pkill|kill|mkdir|rm|cp|tsc|setsid)\b|\bcat\s*>|\becho.*>>', command))
for label, run in data['runs'].items():
    sessions = {s['native_session_id']: s for s in run['sessions']}
    by_session = collections.defaultdict(collections.Counter)
    by_model = collections.defaultdict(collections.Counter)
    tools = []; output_hashes = collections.defaultdict(list); user_inputs = []
    poll_rows = []; comment_reads = []; max_outputs = []; commands = {}
    for row in run['messages']:
        message = row['message']; usage = message.get('usage', {}); sid = row['session']
        blocks = message.get('content', [])
        blocks = blocks if isinstance(blocks,list) else []
        calls = [b for b in blocks if b.get('type') == 'toolCall']
        locator = {k:row[k] for k in ('session','path','line','timestamp')}
        if 'input' in usage:
            usage_add(by_session[sid], usage); usage_add(by_model[message.get('model')], usage)
            if calls and all(c['name']=='bash' and poll(c['arguments'].get('command','')) for c in calls):
                poll_rows.append({**locator, 'usage': usage, 'commands': [c['arguments']['command'] for c in calls]})
        for call in calls:
            command = call.get('arguments',{}).get('command','')
            commands[call['id']] = command
            tools.append({**locator,'name':call['name'],'id':call['id'],'command':command})
            for match in re.finditer(r'braid\s+(comment view\s+(\d+)|(issue|pr) view\s+(\d+))',command):
                comment_reads.append({**locator,'target':match.group(0),'command':command})
        body = text(message)
        if message['role']=='toolResult':
            item = {**locator,'chars':len(body),'command':commands.get(message.get('toolCallId'),'')}
            max_outputs.append(item)
            if len(body)>500:output_hashes[hashlib.sha256(body.encode()).hexdigest()].append(item)
        if message['role']=='user':user_inputs.append({**locator,'chars':len(body),'tail':body[-600:]})
    session_rows=[]
    for sid, counts in by_session.items():
        s=sessions.get(sid,{})
        session_rows.append({'session':sid,**{k:s.get(k) for k in ('work_item_kind','work_item_id','profile_id','status','context_revision','parent_native_session_id')},'first_trigger':s.get('turns',[{}])[0].get('trigger_kind'),**counts})
    timing=collections.Counter(x['kind'] for x in run['timing'])
    starts={x['request_id']:x for x in run['timing'] if x['kind']=='request_start'}
    ends={x['request_id']:x for x in run['timing'] if x['kind']=='message_end'}
    intervals=[(x['at_ms'],ends[k]['at_ms']) for k,x in starts.items() if k in ends]
    polls=collections.Counter()
    for row in poll_rows:usage_add(polls,row['usage'])
    prefixes = collections.defaultdict(list)
    for row in run['messages']:
        body = text(row['message'])
        if row['message']['role'] == 'user' and '# Local ' in body[:150]:
            prefix = body.split('请处理')[0]
            key = (row['session'], hashlib.sha256(prefix.encode()).hexdigest())
            prefixes[key].append({**{k:row[k] for k in ('session','path','line','timestamp')}, 'chars':len(prefix)})
    repeated_prefixes = [rows for rows in prefixes.values() if len(rows)>1]
    scenarios = []
    if label == 'sheet':
        for sid, assumed_tokens in [('01a0e750-f3de-71e1-9c6d-a7d4aac8f334',20000),
                                    ('01a0e750-f3cb-7190-89fd-06143726d5b6',7000)]:
            seen_prefixes = set(); duplicate_count = 0; weighted_copies = 0
            for row in sorted((r for r in run['messages'] if r['session']==sid),key=lambda r:r['line']):
                message = row['message']; body = text(message)
                if message['role']=='user' and body.startswith('# Local'):
                    digest = hashlib.sha256(body.split('请处理')[0].encode()).hexdigest()
                    if digest in seen_prefixes: duplicate_count += 1
                    seen_prefixes.add(digest)
                if 'input' in message.get('usage',{}): weighted_copies += duplicate_count
            scenarios.append({'session':sid,'assumed_tokens_per_duplicate':assumed_tokens,
                'duplicate_count':duplicate_count,'duplicate_copies_carried_by_later_requests':weighted_copies,
                'scenario_avoided_prompt_processing_tokens':assumed_tokens*weighted_copies})
    result['runs'][label]={'models':by_model,'sessions':sorted(session_rows,key=lambda x:-x['cacheRead']),
        'duplicate_context_scenarios_not_bill_savings':scenarios,
        'repeated_context_prefixes': repeated_prefixes,
        'repeated_context_count':sum(len(rows)-1 for rows in repeated_prefixes),
        'repeated_context_chars':sum((len(rows)-1)*rows[0]['chars'] for rows in repeated_prefixes),
        'tools':dict(collections.Counter(x['name'] for x in tools)), 'tool_calls':tools,
        'poll_candidate_totals':polls,'poll_candidates':poll_rows,'comment_reads':comment_reads,
        'largest_outputs':sorted(max_outputs,key=lambda x:-x['chars'])[:25],
        'repeated_outputs':[v for v in output_hashes.values() if len(v)>1], 'user_inputs':user_inputs,
        'timing_kinds':timing, 'request_sum_ms':sum(b-a for a,b in intervals),
        'request_wall_union_ms':union_ms(intervals)}
(base/'aggregate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for label,run in result['runs'].items():
    print(label,run['models'],'poll',run['poll_candidate_totals'])
    print('largest',json.dumps(run['largest_outputs'][:5],ensure_ascii=False))
    print('repeated',sum(len(rows)-1 for rows in run['repeated_outputs']),sum(sum(r['chars'] for r in rows[1:]) for rows in run['repeated_outputs']))
    print('timing',run['timing_kinds'],run['request_sum_ms'],run['request_wall_union_ms'])
