import json,pathlib
ROOT=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/sheet');OUT=ROOT/'cells/a/views_unique';OUT.mkdir(exist_ok=True)
IDX=json.loads((ROOT/'cells/a/views/index.json').read_text());seen={};mapping={}
def emit(s,loc,f):
 lines=s.splitlines(keepends=True);refs=[];new=0
 for n,ln in enumerate(lines,1):
  if ln in seen:refs.append([n,seen[ln]])
  else:
   seen[ln]=f'{loc}:textline{n}';f.write(ln if ln.endswith('\n') else ln+'\n');new+=1
 if refs:
  mapping[loc]={'total_lines':len(lines),'new_lines':new,'duplicates':refs}
  f.write(f'[DUPLICATES: {len(refs)} exact source lines omitted; precise per-line source map in duplicate-lines.json at {loc}]\n')
for x in IDX:
 p=ROOT/'evidence'/x['source'];v=OUT/(x['alias']+'.txt')
 with v.open('w') as f:
  f.write(f'{x["alias"]} {x["id"]}\nsource={x["source"]}\n')
  for i,line in enumerate(p.open(),1):
   d=json.loads(line);m=d.get('message',{});role=m.get('role');loc=f'{x["alias"]}:L{i}';f.write(f'## {loc} {d.get("timestamp","")} {d.get("type","legacy")} {role or ""}\n')
   if m:
    if 'toolName' in m:f.write('toolResult '+str(m['toolName'])+' '+str(m.get('isError'))+'\n')
    for j,c in enumerate(m.get('content',[]),1):
     typ=c.get('type');cloc=f'{loc}:C{j}';f.write(f'[{typ}]')
     if typ=='toolCall':f.write(f' {c.get("name")} {c.get("id")}\n');emit(json.dumps(c.get('arguments'),ensure_ascii=False,sort_keys=True),cloc,f)
     elif typ in ('thinking','text'):f.write('\n');emit(c.get('thinking' if typ=='thinking' else 'text',''),cloc,f)
     else:f.write(' [nontext '+json.dumps({k:v for k,v in c.items() if k not in ('data','image_url')},ensure_ascii=False)[:300]+']\n')
    if 'details' in m and m['details']:f.write('[details]\n');emit(json.dumps(m['details'],ensure_ascii=False,sort_keys=True),loc+':details',f)
   else:
    for k,vv in d.items():
     if k in ('type','id','parentId','timestamp'):continue
     if k in ('details','display') and not vv:continue
     f.write(f'[{k}]\n');emit(vv if isinstance(vv,str) else json.dumps(vv,ensure_ascii=False,sort_keys=True),loc+':'+k,f)
   f.write('\n')
 x['unique_view']=str(v);x['unique_bytes']=v.stat().st_size
(OUT/'index.json').write_text(json.dumps(IDX,ensure_ascii=False,indent=2)+'\n')
(OUT/'duplicate-lines.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=0)+'\n')
print(sum(x['unique_bytes'] for x in IDX),len(seen),len(mapping))
