import json,pathlib
R=pathlib.Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/sheet/cells/a/views_unique');O=R/'chunks';O.mkdir(exist_ok=True)
idx=json.loads((R/'index.json').read_text());chunks=[]
for x in idx:
 s=pathlib.Path(x['unique_view']).read_text();size=24000
 for j in range(0,len(s),size):
  chunk=s[j:j+size];name=f'{x["alias"]}-{j//size+1:02d}.txt';(O/name).write_text(chunk)
  chunks.append({'chunk':name,'alias':x['alias'],'start_char':j,'end_char':j+len(chunk),'bytes':len(chunk.encode())})
(O/'index.json').write_text(json.dumps(chunks,ensure_ascii=False,indent=2)+'\n')
print(len(chunks))
