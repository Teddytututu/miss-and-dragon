"""Portable, read-only checks for work allocation and collaboration habits."""
import re
from . import storage

JARGON=('identity boundary','admission gate','byte contract','field lock','canonical projection',
        '原字节','字段锁','完整身份','沿原','准入','现役')

def prompt_readability_issues(root):
    from . import lifecycle as life
    out=[]
    archive=life.data_file(root,'tasks/archive.md')
    done={r['task'] for r in life.parse_board(archive.read_text('utf-8-sig'))} if archive.exists() else set()
    for name in ('instructions.md','当前指令.md'):
        path=life.data_file(root,name)
        if not path.exists():continue
        text=path.read_text('utf-8-sig');stale=sorted(set(re.findall(r'\bT\d+\b',text))&done)
        hits=[word for word in JARGON if word.lower() in text.lower()]
        if len(text)>4500 or len(hits)>=3 or stale:
            out.append(f'{name}: {len(text)} characters; repeated jargon {len(hits)}; archived tasks '+', '.join(stale))
    texts=storage.read(life.data_file(root,'attachments/wake-prompts.json'),{})
    if isinstance(texts,dict):
        for role,text in texts.items():
            if isinstance(text,str) and (len(text)>1200 or sum(w.lower() in text.lower() for w in JARGON)>=2):
                out.append(f'{role} wake prompt requires plain, concise steps ({len(text)} characters)')
    return out

def idle_roles(root,rows):
    from . import lifecycle as life
    config=storage.read(life.data_file(root,'project.json'),{})
    roles=config.get('executor_roles',['GPT'])
    if not isinstance(roles,list) or any(not isinstance(r,str) or not r for r in roles):roles=['GPT']
    paused=config.get('paused_executor_roles',[])
    out=[]
    for role in roles:
        if role in paused:continue
        mine=[]
        for row in rows:
            if row.get('owner')!='GPT':continue
            assigned='GPT'
            try:
                text=life.task_spec(root,row['task']).read_text('utf-8-sig')
                match=re.search(r'^Execution role:\s*(\S+)\s*$',text,re.M)
                if match:assigned=match[1]
            except (OSError,ValueError):pass
            if assigned==role:mine.append(row)
        if not any(life.state_of(r['status'])=='running' or life.state_of(r['status'])=='rejected' or
                   life.state_of(r['status'])=='queued' and re.search(r'ready now|now|现在可开工|立即',r['status'],re.I) for r in mine):
            out.append(role)
    return out
