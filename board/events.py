"""Durable single-flight host delivery, separated from consumer acknowledgements."""
from pathlib import Path
import hashlib
import json
import uuid
from . import continuity,delivery,lifecycle,storage
from .workers import archived_task

PATH='attachments/host-events.json'


def read(root):return storage.read(Path(root)/PATH,{})


def enqueue(root,actor,task,stage,version,body,*,authorization):
    if actor not in {'GPT','Claude'}:raise ValueError('Explicit target assistant required')
    delivery.key(task,stage)
    if not all(isinstance(v,str) and v.strip() for v in (version,body,authorization)):raise ValueError('Current version, concrete instruction and authorization required')
    identity=hashlib.sha256(json.dumps([actor,task,stage,version,body],ensure_ascii=False).encode()).hexdigest()[:24]
    with storage.locked(root):
        rows=read(root)
        if identity not in rows:
            rows[identity]=dict(id=identity,actor=actor,task=task,stage=stage,version=version,body=body,authorization=authorization,state='ready',at=delivery.stamp())
            storage.write(Path(root)/PATH,rows)
        return rows[identity]


def claim(root,identifier):
    with storage.locked(root):
        rows=read(root);row=rows[identifier]
        if archived_task(root,row['task']):return None
        state=storage.read(Path(root)/'attachments/state.json',{}).get('tasks',{}).get(row['task'],{}).get('status')
        if state is None:
            file=Path(root)/'board.md'
            state=next((r['status'] for r in lifecycle.parse_board(file.read_text('utf-8-sig')) if r['task']==row['task']),None) if file.exists() else None
        if row['state']!='ready' or state and (lifecycle.state_of(state) in {'accepted','stopped','delivered'} or str(state).startswith(('paused','暂停'))):return None
        row.update(state='sending',claim=uuid.uuid4().hex,claimed_at=delivery.stamp());storage.write(Path(root)/PATH,rows);return dict(row)


def settle(root,identifier,claim_id,*,sent,receipt=None):
    if type(sent) is not bool:raise ValueError('Explicit transport outcome required')
    with storage.locked(root):
        rows=read(root);row=rows[identifier]
        if row['state']!='sending' or row.get('claim')!=claim_id:raise ValueError('Current in-flight claim required')
        row.update(state='sent' if sent else 'ready',receipt=receipt,settled_at=delivery.stamp());storage.write(Path(root)/PATH,rows);return row


def consume(root,consumer,identifier):
    if identifier not in read(root):raise ValueError('Registered event required')
    return continuity.consume(root,consumer,identifier)
