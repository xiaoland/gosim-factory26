import json, pathlib, hashlib
ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/sheet')
OUT=ROOT/'cells/a/views';OUT.mkdir(exist_ok=True)
D=json.loads((ROOT/'coverage.json').read_text())
S=[x for x in D['sessions'] if x.get('cwd') and ('/issue-3/' in x['cwd'] or '/pr-8/' in x['cwd'])]
def first_time(x):
 try:return json.loads(next(open(ROOT/'evidence'/x['path'])))['timestamp']
 except:return ''
S.sort(key=lambda x:(first_time(x),x['id']))
seen={};index=[]
def lines_preserve(s,loc):
 if not isinstance(s,str): s=json.dumps(s,ensure_ascii=False,sort_keys=True)
 for n,line in enumerate(s.splitlines(keepends=True),1):
  if line in seen:
   yield f'    [EXACT REPEAT of {seen[line]}]'+('\n' if not line.endswith('\n') else '')
  else:
   seen[line]=f'{loc}:textline{n}'
   # long physical lines are split only for display, losslessly by character position
   for j in range(0,len(line),3000):
    part=line[j:j+3000]
    yield f'    [{n}:{j}-{j+len(part)}] '+part+('' if part.endswith('\n') else '\n')
for k,x in enumerate(S,1):
 alias=f'S{k:02d}';path=ROOT/'evidence'/x['path'];view=OUT/(alias+'.txt')
 with view.open('w') as out:
  out.write(f'{alias} source={x["id"]}\npath={x["path"]}\nlines={x["lines"]} bytes={x["bytes"]} cwd={x.get("cwd")} continuation_of={x.get("continuation_of")}\n\n')
  for i,line in enumerate(path.open(),1):
   d=json.loads(line);loc=f'{alias}:L{i}';m=d.get('message',{});role=m.get('role')
   out.write(f'===== {loc} {d.get("timestamp","")} type={d.get("type","legacy")} role={role or ""} =====\n')
   if m:
    for key in ('toolCallId','toolName','isError','stopReason','model','provider'):
     if key in m:out.write(f'{key}: {m[key]}\n')
    for cidx,c in enumerate(m.get('content',[]),1):
     typ=c.get('type');out.write(f'-- content {cidx} type={typ} --\n')
     if typ=='toolCall':
      out.write(f'name={c.get("name")} id={c.get("id")}\n')
      out.writelines(lines_preserve(json.dumps(c.get('arguments'),ensure_ascii=False,sort_keys=True),f'{loc}:C{cidx}:args'))
     elif typ=='thinking':out.writelines(lines_preserve(c.get('thinking',''),f'{loc}:C{cidx}:thinking'))
     elif typ=='text':out.writelines(lines_preserve(c.get('text',''),f'{loc}:C{cidx}:text'))
     else:
      out.write('    [non-text content placeholder] '+json.dumps({q:v for q,v in c.items() if q not in ('data','image_url')},ensure_ascii=False)[:500]+'\n')
    if 'details' in m:out.writelines(lines_preserve(json.dumps(m['details'],ensure_ascii=False,sort_keys=True),f'{loc}:details'))
    if 'usage' in m:out.write('usage='+json.dumps(m['usage'],ensure_ascii=False,sort_keys=True)+'\n')
   else:
    # Session headers, model changes, and custom_message including subagent supervisor content.
    for key,val in d.items():
     if key in ('id','parentId','timestamp','type'):continue
     out.write(f'-- {key} --\n')
     out.writelines(lines_preserve(val if isinstance(val,str) else json.dumps(val,ensure_ascii=False,sort_keys=True),f'{loc}:{key}'))
   out.write('\n')
 index.append({'alias':alias,'id':x['id'],'source':x['path'],'view':str(view),'view_bytes':view.stat().st_size,'lines':x['lines'],'first_time':first_time(x),'continuation_of':x.get('continuation_of')})
(OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(len(index),sum(x['view_bytes'] for x in index),len(seen))
