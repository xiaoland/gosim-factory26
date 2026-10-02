"""Read-only exact-content reconciliation of the declared Sheet native roots."""
import hashlib
import json
import pathlib
import subprocess

B = pathlib.Path(__file__).parent
index = json.loads((B / "record-sources.json").read_text())
cache = {}
known = []
for item in index:
    path, line = item["sources"][0]
    if path not in cache:
        cache[path] = [json.loads(s) for s in (B / "evidence" / path).read_text().splitlines()]
    record = cache[path][line - 1]
    digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    known.append([item["key"], digest])
roots = [r["root"] for r in json.loads((B / "early-reconciliation.json").read_text())["roots"]]
remote = r'''
import hashlib,json,pathlib,re,collections
known={tuple(k):h for k,h in KNOWN}
results=[]
for root in ROOTS:
    b=pathlib.Path(root)
    ss=json.loads((b/'braid-state/sessions.json').read_text())
    mapping={pathlib.Path(s.get('native_session_path','')).name:s.get('native_session_id') for s in ss}
    dirs=[b/'native',b/'work/native-homes']+list(b.glob('*native*'))
    files=sorted(set(p for d in dirs if d.is_dir() for p in d.glob('**/*.jsonl')))
    mismatch=[];unmapped=[];unique=set();matched=0
    for p in files:
        rows=[(n,json.loads(s)) for n,s in enumerate(p.read_text(errors='replace').splitlines(),1)]
        sid=next((v.get('id') for _,v in rows if v.get('type')=='session'),None) or mapping.get(p.name)
        if not sid:
            match=re.search(r'_([0-9a-f-]{36})\.jsonl$',p.name)
            sid=match.group(1) if match else None
        if not sid:
            unmapped.append({'path':str(p.relative_to(b)),'records':len(rows),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'types':dict(collections.Counter(str(v.get('type')) for _,v in rows))})
            continue
        for n,v in rows:
            digest=hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
            key=(sid,v.get('id') or digest,v.get('timestamp'))
            unique.add((key,digest))
            if known.get(key)==digest:matched+=1
            else:mismatch.append({'key':key,'digest':digest,'source':str(p.relative_to(b))+':L'+str(n),'record':v})
    results.append({'root':root,'files':len(files),'matched_copies':matched,'unique_key_content_pairs':len(unique),'mismatches':mismatch,'unmapped':unmapped})
print(json.dumps(results,ensure_ascii=False))
'''.replace("KNOWN", repr(known)).replace("ROOTS", repr(roots))
result = subprocess.run(["ssh", "wsl.win-ws.localhost", "python3", "-"], input=remote, text=True, capture_output=True, check=True)
data = json.loads(result.stdout)
(B / "early-content-reconciliation.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(json.dumps([{**r, "mismatches": len(r["mismatches"])} for r in data], ensure_ascii=False, indent=2))
