"""Versioned stage delivery, explicit review and dependency invalidation."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import re
from . import storage

PATH='attachments/delivery.json'


def stamp():return datetime.now(timezone.utc).isoformat()
def read(root):return storage.read(Path(root)/PATH,dict(stages={},events=[]))


def key(task,stage):
    if not re.fullmatch(r'T\d+',task) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',stage):raise ValueError('Task and stage identifiers required')
    return task+':'+stage


def binding(root,name):
    path=storage.relative_file(Path(root),name)
    if not path.is_file() or path.stat().st_size==0:raise ValueError('Nonempty project artifact required')
    return dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def configure(root,task,stage,dependencies=(),executor='GPT',reviewer='Claude'):
    identity=key(task,stage)
    if executor not in {'GPT','Claude'} or reviewer not in {'GPT','Claude'} or reviewer==executor:raise ValueError('Separate executor and reviewer required')
    dependencies=[key(task,name) for name in dependencies]
    with storage.locked(root):
        data=read(root)
        if identity in data['stages']:raise ValueError('Stage already configured')
        if identity in dependencies or any(dep not in data['stages'] for dep in dependencies):raise ValueError('Configure upstream stages first')
        row=dict(task=task,stage=stage,state='ready',executor=executor,reviewer=reviewer,dependencies=dependencies,version=None,artifacts=[])
        data['stages'][identity]=row;storage.write(Path(root)/PATH,data)
        return row


def submit(root,task,stage,artifacts,*,actor):
    identity=key(task,stage)
    with storage.locked(root):
        data=read(root);row=data['stages'][identity]
        if actor!=row['executor']:raise PermissionError('Stage executor required')
        if any(data['stages'][dep]['state']!='accepted' or not current(root,data['stages'][dep]) for dep in row['dependencies']):raise ValueError('Accepted current upstream artifacts required')
        if not artifacts or len(set(artifacts))!=len(artifacts):raise ValueError('Distinct artifacts required')
        bound=sorted((binding(root,name) for name in artifacts),key=lambda a:a['path'])
        upstream={dep:data['stages'][dep]['version'] for dep in row['dependencies']}
        version=hashlib.sha256(json.dumps(dict(artifacts=bound,upstream=upstream),sort_keys=True).encode()).hexdigest()
        if row['version']==version and row['state'] in {'delivered','accepted'}:return row
        changed={identity}
        while True:
            extra={k for k,r in data['stages'].items() if k not in changed and set(r['dependencies'])&changed}
            if not extra:break
            changed.update(extra)
        for k in changed-{identity}:data['stages'][k]['state']='invalidated'
        row.update(state='delivered',version=version,artifacts=bound,upstream=upstream,delivered_at=stamp(),review=None)
        data['events'].append(dict(stage=identity,action='deliver',version=version,actor=actor,at=stamp()))
        storage.write(Path(root)/PATH,data);return row


def current(root,row):
    data=read(root)
    def check(stage,seen):
        identity=key(stage['task'],stage['stage'])
        if identity in seen:return False
        seen=seen|{identity}
        return (bool(stage['artifacts']) and all(binding(root,a['path'])==a for a in stage['artifacts'])
                and all(data['stages'][dep]['state']=='accepted' and data['stages'][dep]['version']==version
                        and check(data['stages'][dep],seen) for dep,version in stage.get('upstream',{}).items()))
    try:return check(row,set())
    except (OSError,ValueError,KeyError):return False


def review(root,task,stage,version,*,actor,accept,note=''):
    with storage.locked(root):
        data=read(root);row=data['stages'][key(task,stage)]
        if actor!=row['reviewer']:raise PermissionError('Stage reviewer required')
        if type(accept) is not bool:raise ValueError('Explicit review decision required')
        if row['version']!=version or row['state'] not in {'delivered','accepted','rejected'} or not current(root,row):raise ValueError('Current delivered artifact version required')
        if any(data['stages'][dep]['state']!='accepted' or data['stages'][dep]['version']!=v or not current(root,data['stages'][dep]) for dep,v in row.get('upstream',{}).items()):raise ValueError('Current accepted upstream version required')
        row.update(state='accepted' if accept else 'rejected',review=dict(actor=actor,version=version,accept=accept,note=note,at=stamp()))
        data['events'].append(dict(stage=key(task,stage),action='review',version=version,actor=actor,accept=accept,at=stamp()))
        storage.write(Path(root)/PATH,data);return row
