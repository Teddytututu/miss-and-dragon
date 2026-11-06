"""Portable, read-only checks for work allocation and collaboration habits."""
import re
from datetime import datetime
from . import storage

JARGON=('identity boundary','admission gate','byte contract','field lock','canonical projection',
        '原字节','字段锁','完整身份','沿原','准入','现役')

def timestamp_issues(root,at,overview):
    """Compare recent authored timestamps with file modification time."""
    from . import lifecycle as life
    out=[]
    pattern=re.compile(r'Claude[^\n（）()]{0,16}?(?:(\d{4})-)?(?:(\d{1,2})-(\d{1,2}) )?(\d{1,2}):(\d{2})')
    candidates=[]
    for folder in ('tasks','experiment-design'):
        candidates.extend((p,False) for p in life.data_file(root,folder).glob('*.md'))
    for link in overview.get('links',[]):
        relative=link.get('path','')
        if link.get('archived') or not isinstance(relative,str) or not relative.lower().endswith('.html'):
            continue
        try:path=life.data_file(root,relative)
        except ValueError:continue
        candidates.append((path,True))
    seen=set()
    for path,html in candidates:
        try:
            path=life.data_file(root,path.relative_to(root))
            if path in seen or not path.is_file():continue
            seen.add(path)
            modified=datetime.fromtimestamp(path.stat().st_mtime,life.TAIPEI)
            if (at-modified).total_seconds()>48*3600:continue
            with path.open(encoding='utf-8-sig') as stream:
                text=stream.read(4000) if html else stream.read()
        except (OSError,ValueError):continue
        for line in text.splitlines():
            if re.match(r'\s*- \d{4}-\d\d-\d\d \d\d:\d\d HKT · ',line):continue
            matches=(re.finditer(r'Claude (\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})',line)
                     if html else pattern.finditer(line))
            found=False
            for match in matches:
                if not html and re.search(r'截止|约|预计|之前|以前|前交|ETA|做好|·|due|before|expected',match[0],re.I):continue
                year,month,day,hour,minute=match.groups()
                try:
                    stamp=modified.replace(year=int(year or modified.year),month=int(month or modified.month),
                                           day=int(day or modified.day),hour=int(hour),minute=int(minute),second=0,microsecond=0)
                except ValueError:continue
                gap=(stamp-modified).total_seconds()
                if gap>(300 if html else 180) and (html or month or gap<3600):
                    task=re.search(r'T\d+',path.stem)
                    out.append(dict(owner='Claude',task=task[0] if task else '-',code='future_timestamp',
                                    what='Authored timestamp is ahead of file modification time: '+path.relative_to(root).as_posix(),
                                    fix='Correct the authored timestamp to the actual completion time'))
                    found=True
                    break
            if found:break
    return out

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
        from .wake_prompt import build
        texts=dict(texts,**{'built-in GPT':build('GPT')})
    if isinstance(texts,dict):
        for role,text in texts.items():
            if isinstance(text,str) and (len(text)>1200 or sum(w.lower() in text.lower() for w in JARGON)>=2):
                out.append(f'{role} wake prompt requires plain, concise steps ({len(text)} characters)')
    return out

def lead_review_issues(root,at):
    from . import lifecycle as life
    local=at.astimezone(life.TAIPEI)
    if (local.hour,local.minute)<(22,30):return []
    path=life.data_file(root,'lead-review.md')
    text=path.read_text('utf-8-sig') if path.exists() else ''
    return [] if re.search(r'^#{2,3}\s+'+local.strftime('%Y-%m-%d')+r'\s*$',text,re.M) else ['Write today’s four-line lead review and update the error log']

def task_todo_issues(todos,rows):
    from . import lifecycle as life
    states={row['task']:life.state_of(row['status']) for row in rows}
    return [dict(task=todo['task'],what=str(todo.get('what',''))[:80]) for todo in todos
            if todo.get('task') and states.get(todo['task']) not in {'blocked','queued'}]

def oss_sync_issues(root,at):
    from . import lifecycle as life
    config=storage.read(life.data_file(root,'project.json'),{}).get('open_source_sync',{})
    if not isinstance(config,dict) or config.get('enabled') is not True:return []
    folder=life.data_file(root,'attachments/open-source-sync');out=[]
    for path in sorted(folder.glob('????-??-??.md')):
        lines=path.read_text('utf-8-sig').lstrip().splitlines()
        head=lines[0] if lines else ''
        if head.startswith(('Review: pending Claude','审核：待 Claude')):
            out.append(dict(owner='Claude',task='-',code='oss_sync_review',what='Open-source changes await review: '+path.stem,fix='Review the commits and validation, then record the decision'))
        elif head.startswith(('Review: returned','审核：退回')):
            out.append(dict(owner='GPT',task='-',code='oss_sync_returned',what='Open-source changes returned: '+path.stem,fix='Apply the review and mark the report pending Claude'))
    local=at.astimezone(life.TAIPEI)
    if local.hour>=22 and not life.data_file(root,f'attachments/open-source-sync/{local:%Y-%m-%d}.md').exists():
        out.append(dict(owner='GPT',task='-',code='oss_sync_missing',what='Today’s open-source review report is due',fix='Prepare the batch or record why this day has no suitable changes'))
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
