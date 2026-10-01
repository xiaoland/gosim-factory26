import json,pathlib,re,sys
B=pathlib.Path(__file__).parent; m=json.load(open(B/'manifest.json'));ix=json.load(open(B/'record-sources.json'));done=json.load(open(B/'semantic-coverage-index.json'))['decision_read_session_indices'];sids={m[i]['sid'] for i in done};seen={};cache={}
def remember(t,loc):
 for p in re.split(r'\n\s*\n',t):
  if len(p)>150:seen.setdefault(p,loc)
for e in ix:
 if e['key'][0] not in sids:continue
 f,n=e['sources'][0]
 if f not in cache:cache[f]=[json.loads(l) for l in (B/'evidence'/f).read_text().splitlines()]
 r=cache[f][n-1];msg=r.get('message',{})
 for c in msg.get('content',[]):
  if c.get('type') in ['text','thinking']:remember(c.get(c['type'],''),f+':L'+str(n))
 if r.get('type')=='custom_message':remember(str(r.get('content','')),f+':L'+str(n))
for fn in ['local_items.json','local_comments.json']:
 for v in json.load(open(B/'evidence'/fn)):remember(v.get('body') or '',fn+':'+str(v.get('node_id',v.get('comment_id'))))
idx=int(sys.argv[1]);f=B/f'session-{idx:03}-decisions.md';text=f.read_text();out=[];refs=[]
for n,p in enumerate(re.split(r'(\n\s*\n)',text)):
 if p in seen:
  out.append('[EXACT PREVIOUSLY READ PARAGRAPH; see session-'+f'{idx:03}'+'-known-refs.json entry '+str(len(refs))+']');refs.append({'render_block':n,'source':seen[p],'chars':len(p),'text':p})
 else:out.append(p)
(B/f'session-{idx:03}-known-read.md').write_text(''.join(out));(B/f'session-{idx:03}-known-refs.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2));print('chars',len(''.join(out)),'lines',len(''.join(out).splitlines()),'reused',len(refs))
