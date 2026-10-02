import json,hashlib
from pathlib import Path
R=Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github/cells/root-full/read-receipts.json')
base=Path('/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github')
d=json.loads(R.read_text())
# Keep every substantive scalar recursively. Only omit pure record wrappers/usage and opaque image blobs.
wrapper_leaf={'id','parentId','timestamp','cwd','sessionId','sessionKey','instanceId','pbbCursor','toolCallId','thinkingSignature'}
subleaf={'text','thinking','command','content','body','patch','diff','errorMessage','outcome','newText','oldText','path','name','toolName','agent','model','modelId','provider','stopReason','rawStopReason','role','api','type','status','sourceEventType','recordType','customType','isError','outputTruncated','truncated','mode','action','description','objective','recommendation','missingFacts','counterexamples','extraNotes','value','key','url','branch','commit','sha','head','base','title','message','prompt','answer','question','summary','reason','reasoning','result','output','details','arguments','custom','globalJobId','startedAt','finishedAt','createdAt','updatedAt','error','stderr','stdout'}
items=[]; seen={}
for idx,ent in enumerate(d['source_materials']):
  if not 15<=idx<=24: continue
  p=base/ent['view']; lines=p.read_text().splitlines();i=0
  while i<len(lines):
    if not lines[i].startswith('## Record '):i+=1;continue
    rec=int(lines[i].split()[2]); src=lines[i+1][8:];j=i+2;buf=[]
    while j<len(lines) and not lines[j].startswith('## Record '):
      if lines[j].strip():buf.append(lines[j])
      j+=1
    try:o=json.loads('\n'.join(buf))
    except:i=j;continue
    def walk(x,path):
      if isinstance(x,dict):
        for k,v in x.items():walk(v,path+'/'+k)
      elif isinstance(x,list):
        for n,v in enumerate(x):walk(v,path+'/'+str(n))
      else:
        if not isinstance(x,str): return
        low=path.lower(); leaf=path.split('/')[-1]
        if '/usage' in low or '/cache' in low or 'signature' in low: return
        if x.startswith('[binary omitted ') or len(x)>60000: return
        # Any scalar in message details/content, arguments, custom is substantive; elsewhere retain known semantic leaves.
        is_sem = any(q in low for q in ('/message/content/','/message/details/','/arguments/','/custom/','/details/'))
        if not is_sem and leaf in wrapper_leaf: return
        if not is_sem and leaf not in subleaf: return
        key=(path,x)
        if key in seen:
          seen[key].append((ent['view'],rec,src))
          return
        seen[key]=[(ent['view'],rec,src)]
        items.append((ent['view'],rec,src,path,x))
    walk(o,'');i=j
out=[]
for n,(v,r,s,p,x) in enumerate(items,1):
 out.append(f'ITEM {n}\nVIEW {v}\nRECORD {r}\nSOURCE {s}\nFIELD {p}\nVALUE {json.dumps(x,ensure_ascii=False)}\n')
 # add duplicate locs only when duplicates exist; exact values remain represented by first occurrence
 if len(seen[(p,x)])>1:
  out.append('DUPLICATE_LOCATIONS '+json.dumps(seen[(p,x)][1:],ensure_ascii=False)+'\n')
path=Path('/tmp/root_readstream_15_24_full.txt');path.write_text(''.join(out))
meta={'items':len(items),'chars':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scalars_collapsed_exact_path_value':sum(len(v)-1 for v in seen.values()),'skipped':['pure top-level wrapper id/parentId/timestamp/cwd/session ids','usage/cache/signatures','opaque image placeholders','strings over 60000']}
Path('/tmp/root_readstream_15_24_full.meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(meta,ensure_ascii=False))
