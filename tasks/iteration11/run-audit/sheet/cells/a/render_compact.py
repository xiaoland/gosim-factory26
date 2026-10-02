import json,pathlib,re
ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/sheet');O=ROOT/'cells/a/views_compact';O.mkdir(exist_ok=True)
IDX=json.loads((ROOT/'cells/a/views/index.json').read_text());seen={}
def blocks(s,loc):
 lines=s.splitlines(keepends=True)
 i=0
 while i<len(lines):
  ln=lines[i]
  if ln not in seen:
   seen[ln]=(loc,i+1)
   yield ln if ln.endswith('\n') else ln+'\n'
   i+=1;continue
  ref=seen[ln];start=i+1;j=i+1;prev=ref[1]
  while j<len(lines) and lines[j] in seen and seen[lines[j]][0]==ref[0] and seen[lines[j]][1]==prev+1:
   prev+=1;j+=1
  if j-i>1:yield f'↪ exact duplicate {ref[0]} lines {ref[1]}-{prev}\n'
  else:yield f'↪ exact duplicate {ref[0]} line {ref[1]}\n'
  i=j
for x in IDX:
 p=ROOT/'evidence'/x['source'];out=O/(x['alias']+'.txt')
 with out.open('w') as f:
  f.write(f'{x["alias"]} {x["id"]} {x["source"]}\n')
  for i,line in enumerate(p.open(),1):
   d=json.loads(line);m=d.get('message',{});role=m.get('role');loc=f'{x["alias"]}:L{i}';f.write(f'## {loc} {d.get("timestamp","")} {d.get("type","legacy")} {role or ""}\n')
   if m:
    if 'toolName' in m:f.write('toolResult '+str(m['toolName'])+' '+str(m.get('isError'))+'\n')
    for j,c in enumerate(m.get('content',[]),1):
     typ=c.get('type');cloc=f'{loc}:C{j}';f.write(f'[{typ}]')
     if typ=='toolCall':
      f.write(f' {c.get("name")} {c.get("id")}\n')
      f.writelines(blocks(json.dumps(c.get('arguments'),ensure_ascii=False,sort_keys=True),cloc))
     elif typ in ('thinking','text'):
      f.write('\n');f.writelines(blocks(c.get(typ if typ=='text' else 'thinking',''),cloc))
     else:f.write(' [nontext '+json.dumps({k:v for k,v in c.items() if k not in ('data','image_url')},ensure_ascii=False)[:300]+']\n')
    if 'details' in m and m['details']:
     f.write('[details]\n');f.writelines(blocks(json.dumps(m['details'],ensure_ascii=False,sort_keys=True),loc+':details'))
   else:
    for k,v in d.items():
     if k in ('type','id','parentId','timestamp'):continue
     if k in ('details','display') and not v:continue
     f.write(f'[{k}]\n');f.writelines(blocks(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True),loc+':'+k))
   f.write('\n')
 x['compact_view']=str(out);x['compact_bytes']=out.stat().st_size
(O/'index.json').write_text(json.dumps(IDX,ensure_ascii=False,indent=2)+'\n')
print(sum(x['compact_bytes'] for x in IDX))
