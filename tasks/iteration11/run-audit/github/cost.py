import json,pathlib,collections,datetime
p=pathlib.Path(__file__).parent; rs=json.loads((p/'response-index.json').read_text()); rows=[json.loads(l) for l in (p/'snapshot-01/pi-timing.jsonl').read_text().splitlines()]; cap=int(datetime.datetime.fromisoformat('2026-09-29T08:04:30.462358+00:00').timestamp()*1000)
rows=[r for r in rows if r['at_ms']<=cap]; starts={r['request_id']:r for r in rows if r['kind']=='request_start'}; ends={r['request_id']:r for r in rows if r['kind']=='message_end'}
spans=[(starts[k]['at_ms'],r['at_ms']) for k,r in ends.items() if k in starts]; spans.sort(); merged=[]
for a,b in spans:
 if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
 else: merged.append([a,b])
print('request starts',len(starts),'complete',len(ends),'unmatched',len(starts.keys()-ends.keys()),'HTTP',collections.Counter(r['status'] for r in rows if r['kind']=='response_headers'))
print('model wall union seconds',sum(b-a for a,b in merged)/1000,'model cumulative sec',sum(b-a for a,b in spans)/1000)
coverage=json.loads((p/'coverage.json').read_text());home={pathlib.Path(s).parts[2]:u['owner'] for u in coverage['units'] for s in u['sources']}; agg=collections.defaultdict(collections.Counter)
for rid,r in rs.items():
 source=r['sources'][0];owner=home[pathlib.Path(source).parts[3]]
 agg[owner]['responses']+=1
 for k,v in r['usage'].items():
  if isinstance(v,(int,float)):agg[owner][k]+=v
out=dict(cutoff='2026-09-29T08:04:30.462358Z',unique_responses=len(rs),request_starts=len(starts),complete_timing_requests=len(ends),requests_without_message_end=len(starts.keys()-ends.keys()),http_status_counts=dict(collections.Counter(r['status'] for r in rows if r['kind']=='response_headers')),model_wall_union_seconds=sum(b-a for a,b in merged)/1000,model_cumulative_seconds=sum(b-a for a,b in spans)/1000,by_owner={k:dict(v) for k,v in agg.items()},timing_tail_excluded='采集窗口后段有一条08:04:31.554 message_end，无首轮native正文，按逻辑截点排除。')
(p/'cost-summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out['by_owner'],ensure_ascii=False,indent=2))
