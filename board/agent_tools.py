"""Portable coordination, expiry and board edits for the assistant command entry."""
from datetime import datetime,timedelta
from pathlib import Path
import re,uuid
from . import storage,exchange,lifecycle,project

KINDS={'design':'design','budget':'budget','conclusion':'conclusion','external':'external','deletion':'deletion',
       '设计':'design','预算':'budget','结论':'conclusion','对外':'external','删除':'deletion'}

def stamp(now=None):return lifecycle.moment(now) or datetime.now().astimezone()
def records(root):return storage.lines(lifecycle.data_file(root,'attachments/coordination.jsonl'))
def record_value(who,kind,body,**extra):
    if who not in lifecycle.ROLES:raise ValueError('Choose Claude or GPT')
    if not isinstance(body,str) or not body.strip():raise ValueError('Provide concrete text')
    return dict(id=uuid.uuid4().hex[:8],by=who,kind=kind,body=body.strip(),at=stamp().isoformat(),**extra)
def record(root,who,kind,body,**extra):
    row=record_value(who,kind,body,**extra)
    with storage.locked(root):storage.append(lifecycle.data_file(root,'attachments/coordination.jsonl'),row)
    return row
def pending(root,who):
    rows=records(root);closed={r.get('ref') for r in rows if r['kind']=='answer'}
    return [r for r in rows if r['kind'] in ('ask','info') and r.get('peer')==who and r['id'] not in closed]
def ask(root,who,title,body,kind,options,lean=None):
    if kind not in KINDS:raise ValueError('ask requires --kind design|budget|conclusion|external|deletion')
    if not isinstance(title,str) or not title.strip() or any(c in title for c in '\r\n'):raise ValueError('Use a nonempty, single-line exchange title')
    if len(options)<2 or any(not isinstance(x,str) or not x.strip() for x in options):raise ValueError('ask requires two --option values')
    row=record(root,who,'ask',body,title=title,category=KINDS[kind],options=list(options),lean=lean,peer='Claude' if who=='GPT' else 'GPT')
    row['exchange_title']='['+row['id']+'] ['+row['category']+'] '+title
    row.update(exchange.write(root,who,row['exchange_title'],body,ask=True,options=options,lean=lean))
    return row
def info(root,who,body):return record(root,who,'info',body,peer='GPT' if who=='Claude' else 'Claude')
def answer(root,who,identifier,body):
    row=record_value(who,'answer',body,ref=identifier)
    with storage.locked(root):
        found=[r for r in pending(root,who) if r['id']==identifier]
        if len(found)!=1:raise ValueError('Choose one open question addressed to this assistant')
        q=found[0];storage.append(lifecycle.data_file(root,'attachments/coordination.jsonl'),row)
    if q['kind']=='ask':exchange.write(root,who,'['+q['id']+'] ['+q['category']+'] '+q['title'],body)
    return row
def decide(root,who,task,body,why):
    if not lifecycle.TASK.fullmatch(task) or not why.strip():raise ValueError('Provide a T-number and --why')
    return record(root,who,'decision',body,task=task,why=why)
def veto(root,who,identifier,body):
    if who!='Claude':raise ValueError('The lead (Claude) reviews and vetoes execution choices')
    if not any(r['id']==identifier and r['kind']=='decision' for r in records(root)):raise ValueError('Choose an existing decision ID')
    return record(root,who,'veto',body,ref=identifier)
def expiry(value):
    if value is None:return None
    at=lifecycle.moment(value)
    if at is None:raise ValueError('--until requires an ISO date and time')
    return at.isoformat()
def expire_due(root,*,now=None):
    at=stamp(now);changed=[]
    def update(d):
        for row in d.get('links',[]):
            until=lifecycle.moment(row.get('until'))
            if until and until<=at and not row.get('archived'):
                row.update(archived=True,archived_at=at.isoformat(),archive_reason='expired');changed.append(row.get('title'))
        keep=[]
        for row in d.get('todo',[]):
            until=lifecycle.moment(row.get('until'))
            if until and until<=at:
                d.setdefault('todo_done',[]).append(dict(row,done_at=at.isoformat(),reason='expired'));changed.append(row.get('what'))
            else:keep.append(row)
        if 'todo' in d:d['todo']=keep
        days=[]
        for day in d.get('schedule',[]):
            value=day.get('date','')
            # Month/day-only and relative demo schedules keep their original semantics.
            if re.fullmatch(r'\d{4}-\d\d-\d\d',value) and value<at.date().isoformat():
                d.setdefault('schedule_archive',[]).append(day);changed.append(value)
            else:days.append(day)
        if 'schedule' in d:d['schedule']=days
    storage.update_json(root,'overview.json',update);return dict(expired=changed)
def plan(root,date,time,what,kind):
    if not re.fullmatch(r'\d{4}-\d\d-\d\d',date) or lifecycle.moment(date+'T00:00:00') is None:raise ValueError('Use an ISO calendar date')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',time):raise ValueError('Use a 24-hour HH:MM time')
    if not what.strip():raise ValueError('Describe the scheduled action')
    def update(d):
        days=d.setdefault('schedule',[]);day=next((r for r in days if r.get('date')==date),None)
        if day is None:day=dict(date=date,items=[]);days.append(day)
        items=day.setdefault('items',[]);item=next((r for r in items if r.get('time')==time),None)
        if item is None:item={};items.append(item)
        item.update(time=time,what=what,kind=kind);items.sort(key=lambda r:r.get('time',''))
        days.sort(key=lambda r:r.get('date',''))
    storage.update_json(root,'overview.json',update);return dict(date=date,time=time,what=what)
def progress(root,line,text):
    if not line.strip() or not text.strip():raise ValueError('Provide a research line and current observation')
    def update(d):
        rows=d.setdefault('progress_lines',[]);row=next((r for r in rows if r.get('line')==line),None)
        if row is None:row=dict(line=line);rows.append(row)
        row.update(text=text,updated=stamp().isoformat())
    storage.update_json(root,'overview.json',update);return dict(line=line,text=text)
def tree(root,title,*,status=None,summary=None,task=None,result=None):
    if status is not None and status not in ('todo','doing','done'):raise ValueError('Use todo, doing or done')
    if task and not lifecycle.TASK.fullmatch(task):raise ValueError('Use a T-number')
    def update(d):
        found=[r for r in lifecycle.nodes(d) if r.get('title')==title]
        if len(found)!=1:raise ValueError('Choose one existing result-tree title')
        row=found[0]
        if status is not None:row['status']=status
        if summary is not None:row['summary']=summary
        for key,value in [('tasks',task),('results',result)]:
            if value and value not in row.setdefault(key,[]):row[key].append(value)
        row['updated']=stamp().isoformat()
    storage.update_json(root,'overview.json',update);return dict(node=title,status=status)
def finding(root,who,body,task=None):
    if who!='Claude':raise ValueError('The lead (Claude) records research conclusions')
    if task and not lifecycle.TASK.fullmatch(task):raise ValueError('Use a T-number')
    if not body.strip():raise ValueError('Write the conclusion')
    path=lifecycle.data_file(root,'findings.md')
    with storage.locked(root):
        raw=path.read_bytes() if path.exists() else b'# Findings\n'
        storage.write_bytes(path,lifecycle.append_text(raw,'\n## '+stamp().isoformat()+' '+(task or '')+'\n\n'+body.strip()+'\n'))
    return dict(path='findings.md',task=task)
def retitle(root,task,title):
    title=title.strip()
    if not title or len(title)>16 or any(c in title for c in '\r\n|'):raise ValueError('Task names use 1–16 characters on one line')
    path=lifecycle.data_file(root,'board.md');spec=lifecycle.task_spec(root,task)
    with storage.locked(root):
        raw=path.read_bytes();rows=[r for r in lifecycle.parse_board(raw.decode('utf-8-sig')) if r['task']==task]
        if len(rows)!=1:raise ValueError('Choose one live task')
        row=rows[0];lines=raw.decode('utf-8-sig').splitlines();cells=row['cells'][:]
        cells[1]='['+title+'](tasks/'+spec.name+')';lines[row['index']]='| '+' | '.join(cells)+' |'
        old=spec.read_bytes();text=re.sub(r'^# [^\r\n]*','# '+task+' '+title,old.decode('utf-8-sig'),count=1,flags=re.M)
        storage.write_bytes(spec,lifecycle.encode_like(text,old));storage.write_bytes(path,lifecycle.encode_like('\n'.join(lines)+'\n',raw))
    return dict(task=task,title=title)
def inbox(root,who):
    posts=[r for r in project.all_posts(root) if not r.get('deleted') and r.get('author')!=who and r.get('channel','main')=='main']
    replied={r.get('parent_id') for r in project.all_posts(root) if r.get('author')==who}
    path=lifecycle.data_file(root,'attachments/inbox/'+who+'.json')
    with storage.locked(root):
        seen=set(storage.read(path,{}).get('seen',[]));fresh=[]
        for p in posts:
            if p['id'] in seen:continue
            value=dict(id=p['id'],author=p.get('author'),body=p.get('body',''),at=p.get('created_at'),images=p.get('images',[]),image_paths=[])
            for asset in value['images']:
                name=asset if isinstance(asset,str) else asset.get('name','')
                if re.fullmatch(r'[a-f0-9]{32}\.(?:png|jpg|webp|gif)',name):value['image_paths'].append(str(lifecycle.data_file(root,'attachments/discussion/images/'+name).resolve()))
            fresh.append(value)
        storage.write(path,dict(seen=[p['id'] for p in posts][-5000:]))
    # Every owner message stays pending until this assistant replies or reacts; assistant @mentions of this assistant need a reply.
    from .message_controls import reaction_state
    reacted={mid for mid,actor,_ in reaction_state(storage.lines(lifecycle.data_file(root,'attachments/discussion/reactions.jsonl'))) if actor==who}
    pending_rows=[dict(id=p['id'],author=p['author'],body=p.get('body','')) for p in posts if p['id'] not in replied and (
        p.get('author')=='owner' and p['id'] not in reacted or p.get('author') in ('Claude','GPT') and (p.get('body') or '').lstrip().startswith('@'+who))]
    return dict(new_messages=fresh[-50:],pending_replies=pending_rows[-50:])
def react_owed(root,who):
    from .message_controls import reaction_state
    at=stamp();path=lifecycle.data_file(root,'attachments/discussion/reactions.jsonl');saved=[]
    with storage.locked(root):
        done={(actor,mid) for mid,actor,_ in reaction_state(storage.lines(path))}
        for p in project.all_posts(root):
            created=lifecycle.moment(p.get('created_at'))
            if p.get('deleted') or p.get('author')==who or not created or not 0<=(at-created).total_seconds()<=7200 or (who,p['id']) in done:continue
            storage.append(path,dict(actor=who,message_id=p['id'],emoji='👀',active=True));saved.append(p['id'])
    return dict(reacted=saved)
def efficiency(root,who,*,now=None):
    at=stamp(now);questions=pending(root,who);rows=storage.read(lifecycle.data_file(root,'attachments/gpu-observations.json'),{}).get('items',[])
    owned=[r for r in rows if r.get('owner')==who and type(r.get('idle_seconds')) in (int,float) and r['idle_seconds']>=0]
    idle=sum(r['idle_seconds'] for r in owned) if owned else None
    board=lifecycle.data_file(root,'board.md')
    tasks=lifecycle.parse_board(board.read_text('utf-8-sig')) if board.exists() else []
    tasks=[r for r in tasks if r['owner']==who]
    issues=stability_issues(root,at)
    value=dict(at=at.isoformat(),owner=who,open_questions=len(questions),oldest_question_hours=max([(at-lifecycle.moment(r['at'])).total_seconds()/3600 for r in questions],default=0),own_gpu_idle_seconds=idle,gpu_observation_count=len(owned),blocked_tasks=sum(lifecycle.state_of(r['status'])=='blocked' for r in tasks),returned_tasks=sum(lifecycle.state_of(r['status'])=='rejected' for r in tasks),stale_state_issues=sum('stale' in r.get('code','') for r in issues))
    storage.update_json(root,'overview.json',lambda d:d.setdefault('efficiency',{}).update({who:value}));return value
def stability_issues(root,at):
    from . import stability
    return stability.issues(root,at,storage.read(lifecycle.data_file(root,'overview.json'),{}))
def acknowledge(root,who,identifiers,result):
    path=lifecycle.data_file(root,'attachments/night-watch/events.json')
    with storage.locked(root):
        value=storage.read(path,{'events':[]});available={r['id'] for r in value['events']}
        if not identifiers or not set(identifiers)<=available:raise ValueError('Acknowledge existing exact event IDs')
        value['events']=[r for r in value['events'] if r['id'] not in set(identifiers)]
        storage.write(path,value)
        storage.append(lifecycle.data_file(root,'attachments/event-results.jsonl'),dict(by=who,at=stamp().isoformat(),ids=identifiers,result=result))
    return dict(acknowledged=identifiers,result=result)
