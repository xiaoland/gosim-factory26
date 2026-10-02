import pathlib,re,json
root=pathlib.Path(__file__).parent
for idx in (56,59,60,61):
    s=(root/f'session-{idx:03}.md').read_text()
    blocks=re.split(r'(?=\n## )',s)
    out=[]; flags=[]
    for block in blocks:
        if not block.strip(): continue
        header=block.splitlines()[1] if block.startswith('\n') else block.splitlines()[0]
        if ' custom_message ' in header:
            try:
                j=json.loads(block.split('\n',2)[2])
                d=j.get('details',{})
                body=d.get('body','')
                command=d.get('command','')
                if len(body)>1800:
                    flags.append((header,'custom_body',len(body)))
                    body=body[:700]+'\n[... MECHANICAL BACKGROUND BODY OMITTED '+str(len(body)-1400)+' CHARS ...]\n'+body[-700:]
                out.append(header+'\nBACKGROUND '+str(d.get('jobId'))+' '+str(d.get('outcome'))+' exit='+str(d.get('exitCode'))+' command='+command+'\n'+body)
            except Exception:
                flags.append((header,'custom_parse',len(block)))
                out.append(header+'\n[CUSTOM PARSE REVIEW NEEDED]')
            continue
        m=re.search(r'\ntext: ',block)
        if 'ROLE toolResult' in block and m:
            pre=block[:m.end()]; body=block[m.end():]
            if len(body)>2800:
                flags.append((header,'tool_result',len(body)))
                body=body[:1000]+'\n[... TOOL RESULT OMITTED '+str(len(body)-2000)+' CHARS ...]\n'+body[-1000:]
            out.append(pre+body)
        else:
            out.append(block)
    (root/f'session-{idx:03}-compact.md').write_text('\n'.join(out))
    (root/f'session-{idx:03}-compact-flags.json').write_text(json.dumps(flags,ensure_ascii=False,indent=2))
    print(idx,len(s),len('\n'.join(out)),len(flags))
