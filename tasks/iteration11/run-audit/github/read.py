import json,pathlib,sys
b=pathlib.Path(__file__).parent;c=json.loads((b/'coverage.json').read_text()); u=next(u for u in c['units'] if sys.argv[1] in u['id']); rec={}
for s in u['sources']:
 for i,l in enumerate((b/'snapshot-01'/s).read_text().splitlines(),1):
  r=json.loads(l);key=r.get('id') or l
  if key not in rec:rec[key]=(r,s,i)
rows=sorted(rec.values(),key=lambda a:a[0].get('timestamp',''))
for ix,(r,s,i) in enumerate(rows,1):
 if not int(sys.argv[2])<=ix<=int(sys.argv[3]):continue
 m=r.get('message',r); print('\nRECORD',ix,r.get('timestamp'),m.get('role',r.get('type')),'SOURCE',s+':'+str(i))
 for block in m.get('content',[]) if isinstance(m.get('content'),list) else []:
  typ=block.get('type');
  if typ in ['text','thinking']:print(typ+': '+block.get(typ,''))
  elif typ=='image': print('[image binary; retained in source]')
  else: print(json.dumps(block,ensure_ascii=False))
 if isinstance(m.get('content'),str): print(m['content'])
 if 'content' not in m: print(json.dumps(m,ensure_ascii=False))
 if m.get('details'):
  details=m['details'].copy()
  if isinstance(details.get('truncation'),dict):
   details['truncation']=details['truncation'].copy()
   t=details['truncation'].get('content')
   if t and any(t in x.get('text','') for x in m.get('content',[]) if isinstance(x,dict)): details['truncation']['content']='[exact duplicate of content above]'
  print('DETAILS',json.dumps(details,ensure_ascii=False))
 if m.get('errorMessage'): print('ERROR',m['errorMessage'])
