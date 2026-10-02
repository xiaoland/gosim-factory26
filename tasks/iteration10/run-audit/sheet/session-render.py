import json,pathlib,sys,collections
B=pathlib.Path(__file__).parent;M=json.loads((B/'manifest.json').read_text());IX=json.loads((B/'record-sources.json').read_text());idx=int(sys.argv[1]);sid=M[idx]['sid'];rr=[];ca={};known=[]
for fn in ['local_items.json','local_comments.json']:
 for z in json.loads((B/'evidence'/fn).read_text()):
  t=z.get('body') or ''
  if len(t)>80:known.append((t,z.get('node_id','comment:'+str(z.get('comment_id')))))
known.sort(key=lambda z:-len(z[0]))
def scrub(t):
 for val,label in known:t=t.replace(val,f'[EXACT ALREADY READ items.md {label}; {len(val)} chars]')
 return t
out=[];omit=[]
for x in sorted([x for x in IX if x['key'][0]==sid],key=lambda x:str(x['key'][2])):
 p,n=x['sources'][0]
 if p not in ca:ca[p]=[json.loads(z) for z in (B/'evidence'/p).read_text().splitlines()]
 r=ca[p][n-1];loc=p+':L'+str(n);out.append(f'\n### {r.get("timestamp")} {r.get("type")} SOURCE {loc}')
 if r.get('type')!='message':out.append(scrub(json.dumps(r,ensure_ascii=False)));continue
 msg=r['message'];out.append('ROLE '+msg.get('role','')+' '+msg.get('toolName',''))
 for j,c in enumerate(msg.get('content',[])):
  typ=c.get('type')
  if typ in ['text','thinking']:
   t=c.get(typ,'')
   if idx==6 and n==18:t='[原requirements提取工具结果，正文已完整读取；此消息尚未逐字匹配]';omit.append([loc,j,'需求读取结果未逐字匹配'])
   out.append(typ+': '+scrub(t))
  elif typ=='image':out.append('IMAGE BINARY OMITTED '+str(len(c.get('data',''))))
  elif typ=='toolCall':
   args=c.get('arguments',{}).copy();path=args.get('path','')
   if c.get('name') in ['write','edit'] and path.endswith(('.ts','.tsx','.js','.mjs')):
    for k in ['content','oldText','newText']:
     if k in args:omit.append([loc,j,path,k,len(args[k]),'机械源码写入；本轮不逐字读，不据此判代码正确']);args[k]='[MECHANICAL CODE OMITTED; see omission registry]'
   out.append('toolCall '+c.get('name','')+' '+json.dumps(args,ensure_ascii=False))
  else:out.append(scrub(json.dumps(c,ensure_ascii=False)))
 for k in ['stopReason','isError','errorMessage']:
  if k in msg:out.append(k+': '+str(msg[k]))
(B/f'session-{idx:03}-decisions.md').write_text('\n'.join(out));(B/f'session-{idx:03}-omissions.json').write_text(json.dumps(omit,ensure_ascii=False,indent=2));print(len('\n'.join(out)),len('\n'.join(out).splitlines()))
