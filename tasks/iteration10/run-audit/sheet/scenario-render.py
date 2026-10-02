import pathlib,re,hashlib
B=pathlib.Path(__file__).parent;ls=(B/'evidence/input/requirements.yaml').read_text().splitlines();out=[];seen={};i=0
while i<len(ls):
 line=ls[i]
 if re.match(r'\s*- name:',line):out.append(f'L{i+1} '+line.strip())
 if re.match(r'\s*- keyword:',line):
  j=i+1
  while j<len(ls) and not re.match(r'\s*(?:- keyword:|- name:|- id:)',ls[j]):
   if re.match(r'\s*(?:name:|type:|dependencies:|description:|children:)',ls[j]):break
   j+=1
  val=' '.join(l.strip() for l in ls[i:j]).strip();h=hashlib.sha256(val.encode()).hexdigest()
  if h in seen:out.append(f'L{i+1}–{j} EXACT REPEAT L{seen[h]} (whitespace folded only)')
  else:seen[h]=i+1;out.append(f'L{i+1}–{j} '+val)
  i=j;continue
 i+=1
(B/'scenario-unique.md').write_text('\n'.join(out));print(len(out),'entries',len(seen),'unique steps',len('\n'.join(out)),'chars')
