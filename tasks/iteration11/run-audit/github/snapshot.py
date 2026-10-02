import pathlib, sqlite3, zipfile, sys, datetime, hashlib, json
root=pathlib.Path('/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--github-7fe42a1248f9d8/workspace/official-generation/template/.factory26/20260929-042409-1202e245')
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
files=list((root/'work/native-homes').rglob('*.jsonl'))+list((root/'braid-state/turns').glob('*.md'))
files += [p for p in root.iterdir() if p.is_file() and (p.suffix in ['.json','.txt','.log'] or p.name=='pi-timing.jsonl')]
manifest=[]
with zipfile.ZipFile(sys.stdout.buffer,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:
  data=p.read_bytes(); name=str(p.relative_to(root)); z.writestr(name,data)
  manifest.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),lines=data.count(b'\n')))
 db=sqlite3.connect('file:'+str(root/'braid-state/braid.sqlite3')+'?mode=ro',uri=True); mem=sqlite3.connect(':memory:'); db.backup(mem); z.writestr('braid.sqlite3',mem.serialize()); db.close()
 z.writestr('manifest.json',json.dumps(dict(source=str(root),capture_start=start,capture_end=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest),indent=2))
