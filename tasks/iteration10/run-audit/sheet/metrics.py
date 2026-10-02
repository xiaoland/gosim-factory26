import json,pathlib,collections,datetime
B=pathlib.Path(__file__).parent; E=B/'evidence'
rows=[json.loads(x) for x in (E/'pi-timing.jsonl').read_text().splitlines()]
requests={}; tools={}; response={}; duplicates=0
for n,r in enumerate(rows,1):
 if r['kind'] in ('request_start','response_headers','first_update','message_end'):
  d=requests.setdefault(r['request_id'],{});d[r['kind']]=(n,r)
 if r['kind']=='message_end':
  key=(r.get('provider'),r.get('response_id')) if r.get('response_id') else ('request',r['request_id'])
  if key in response:duplicates+=1
  response[key]=(n,r)
 if r['kind'] in ('tool_start','tool_end'):
  tools.setdefault((r['session_id'],r['tool_call_id']),{})[r['kind']]=(n,r)
def union(intervals):
 result=[]
 for a,b in sorted(intervals):
  if result and a<=result[-1][1]:result[-1][1]=max(result[-1][1],b)
  else:result.append([a,b])
 return sum(b-a for a,b in result)/1000
usage=collections.Counter();by_model=collections.defaultdict(collections.Counter);by_session=collections.defaultdict(collections.Counter)
for n,r in response.values():
 for k,v in r.get('usage',{}).items():
  if isinstance(v,(int,float)):
   usage[k]+=v;by_model[r.get('model')][k]+=v;by_session[r.get('session_id')][k]+=v
mi=[];ti=[]; latency=[];unmatched=collections.Counter()
for key,d in requests.items():
 if 'request_start' in d and 'message_end' in d:
  a=d['request_start'][1]['at_ms'];b=d['message_end'][1]['at_ms'];mi.append((a,b))
  if 'first_update' in d:latency.append((d['first_update'][1]['at_ms']-a)/1000)
 else:unmatched['requests']+=1
for key,d in tools.items():
 if 'tool_start' in d and 'tool_end' in d:ti.append((d['tool_start'][1]['at_ms'],d['tool_end'][1]['at_ms']))
 else:unmatched['tools']+=1
def percentile(x,p):return sorted(x)[min(len(x)-1,int(len(x)*p))]
out={'basis':'Only main retained pi-timing; early unique snapshots not reconciled; no gateway/native double counting','events':len(rows),'requests':len(requests),'responses_unique':len(response),'duplicate_responses':duplicates,'usage':dict(usage),'by_model':by_model,'by_session':by_session,'unmatched':dict(unmatched),'span_seconds':(max(r['at_ms'] for r in rows)-min(r['at_ms'] for r in rows))/1000,'model_interval_sum_seconds':sum(b-a for a,b in mi)/1000,'model_interval_union_seconds':union(mi),'tool_interval_sum_seconds':sum(b-a for a,b in ti)/1000,'tool_interval_union_seconds':union(ti),'model_or_tool_union_seconds':union(mi+ti),'first_update_seconds':{'n':len(latency),'p50':percentile(latency,.5),'p90':percentile(latency,.9),'p99':percentile(latency,.99)}}
(B/'metrics.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('by_session',)},indent=2))
