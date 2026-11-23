"""Explicit current assignments, task-scoped work records and per-consumer receipts."""
from pathlib import Path
import hashlib
import re
from . import storage,delivery


def role(value):
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,40}',value):raise ValueError('Role identifier required')
    return value


def set_current(root,who,task,action,artifact,*,authorization):
    role(who);delivery.key(task,'current')
    if not authorization or not action.strip():raise ValueError('Current authorization and concrete action required')
    storage.relative_file(Path(root),artifact)
    with storage.locked(root):
        path=Path(root)/'attachments/current-assignments.json';data=storage.read(path,{})
        data[who]=dict(task=task,action=action,artifact=artifact,authorization=authorization,at=delivery.stamp())
        storage.write(path,data);return data[who]


def current(root,who):return storage.read(Path(root)/'attachments/current-assignments.json',{}).get(role(who))


def record(root,who,task,stage,turn,state):
    role(who);delivery.key(task,stage)
    if state not in {'running','waiting','delivered','done','paused'}:raise ValueError('Work state required')
    identity=hashlib.sha256((who+'\0'+task+'\0'+stage+'\0'+turn).encode()).hexdigest()[:24]
    with storage.locked(root):
        path=Path(root)/'attachments/work-records.json';data=storage.read(path,{})
        data[identity]=dict(id=identity,role=who,task=task,stage=stage,turn=turn,state=state,at=delivery.stamp())
        storage.write(path,data);return data[identity]


def consume(root,consumer,event_id):
    role(consumer)
    with storage.locked(root):
        path=Path(root)/'attachments/consumers'/f'{consumer}.json';seen=storage.read(path,{})
        if event_id in seen:return False
        seen[event_id]=dict(at=delivery.stamp());storage.write(path,seen);return True
