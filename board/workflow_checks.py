"""Portable, read-only checks for work allocation and collaboration habits."""
import re
from . import storage

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
