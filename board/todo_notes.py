"""Owner sticky-note replies using the existing workspace transaction lock."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import hashlib,json,re,time
from . import storage,project,note_schedule

def active_rows(value):
    counts={};rows=[]
    for row in value.get('todo',[]):
        identity={key:item for key,item in row.items() if key not in ('note_id','note_replies','_returned_on')}
        key=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]
        ordinal=counts.get(key,0);counts[key]=ordinal+1
        rows.append((row.get('note_id') or key+'-'+str(ordinal),row))
    return rows

def view(value):
    return dict(todo=[dict({k:deepcopy(v) for k,v in row.items() if not k.startswith('_')},note_id=key,returned_yesterday=row.get('_returned_on')==note_schedule.today_date().isoformat()) for key,row in active_rows(value)],todo_done=deepcopy(value.get('todo_done',[])))

def choose(root,actor,payload):
    if actor!='owner':raise ValueError('Use the project owner for note replies')
    if not isinstance(payload,dict) or payload.get('op') not in ('reply','schedule'):raise ValueError('Choose a note action')
    scheduling=payload['op']=='schedule'
    expected={'op','id','client_id'} if scheduling else {'op','id','text','client_id'}
    if set(payload)!=expected:raise ValueError('Use the selected note action')
    client=payload.get('client_id');text=payload.get('text')
    if not isinstance(client,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{16,80}',client):raise ValueError('Provide a reply identifier')
    if not scheduling and (not isinstance(text,str) or not 1<=len(text.strip())<=40):raise ValueError('Write up to 40 characters')
    text=text.strip() if isinstance(text,str) else '';root=Path(root)
    if scheduling:note_schedule.rollover(root)
    with storage.locked(root):
        value=storage.read(root/'overview.json',{})
        if scheduling and client in value.get('note_schedule_operations',{}):
            if value['note_schedule_operations'][client]!=payload['id']:raise ValueError('Retry must select the same note')
            return view(value)
        rows=active_rows(value)
        for key,row in rows:row['note_id']=key
        selected=next((row for key,row in rows if key==payload['id']),None)
        if selected is None:raise ValueError('Refresh to choose a current note')
        if scheduling:
            index=next(i for i,(key,row) in enumerate(rows) if key==payload['id'])
            note_schedule.place(value,payload['id'],selected,index,client,time.time())
            storage.write(root/'overview.json',value)
            return view(value)
        replies=selected.setdefault('note_replies',[])
        prior=next((reply for reply in replies if reply['client_id']==client),None)
        if prior and prior['text']!=text:raise ValueError('Retry content must match')
        if not prior:
            recipient=next((selected.get(k) for k in ('assigned_by','by','author') if selected.get(k) in ('Claude','GPT')),'Claude')
            post=project._post(root,'owner','@'+recipient+' 便利贴「'+str(selected.get('what',''))+'」\n'+text,
                parent_id=selected.get('message_id'),client_id=client)
            replies.append(dict(text=text,at=post['created_at'],message_id=post['id'],client_id=client,to=recipient))
        storage.write(root/'overview.json',value)
        return view(value)
