"""Shared result-tree read markers. Each mutation updates one node under lock."""
import json
from pathlib import Path
from .plugins.accounts import Rejected
from . import storage

def state_path(root):
    return Path(root)/'attachments/tree-reads.json'

def snapshot(root):
    path=state_path(root)
    with storage.locked(root):
        return json.loads(path.read_bytes()) if path.exists() else {'revision':0,'versions':{}}

def project(root,value):
    overview=value.get('overview')
    if isinstance(overview,dict):overview['tree_reads']=snapshot(root)
    return value

def node_key(node):
    if node.get('id'):return 'id:'+str(node['id'])
    main=(node.get('reports') or [None])[0] or node.get('page')
    path=main.get('path') if isinstance(main,dict) else main
    return 'report:'+path if isinstance(path,str) and path else 'title:'+str(node.get('title',''))

def choose(root,actor,payload):
    if not isinstance(payload,dict) or set(payload) not in ({'title','version','read'},{'title','key','version','read'}):
        raise Rejected('请选择结果树上的已读按钮。',400)
    title,version,read=payload['title'],payload['version'],payload['read']
    if not isinstance(title,str) or not isinstance(version,str) or len(version)>20000 or type(read) is not bool:
        raise Rejected('请提交有效的结果版本。',400)
    overview=json.loads((Path(root)/'overview.json').read_text(encoding='utf-8-sig'))
    def nodes_in(nodes):
        for node in nodes:
            yield node
            yield from nodes_in(node.get('children',[]))
    nodes=list(nodes_in(overview.get('tree',[])))
    key=payload.get('key')
    if key is not None and (not isinstance(key,str) or len(key)>20000):
        raise Rejected('请提交有效的结果标识。',400)
    matches=[node for node in nodes if node_key(node)==key] if key is not None else [node for node in nodes if node.get('title')==title]
    if not matches:
        raise Rejected('请选择现有结果。',404)
    if key is None and len(matches)!=1:
        raise Rejected('同名结果请刷新后分别选择。',409)
    result={}
    def mutate(state):
        versions=state.setdefault('versions',{})
        versions[key if key is not None else node_key(matches[0])]=version if read else None
        if key is None:
            if read:versions[title]=version
            else:versions.pop(title,None)
        state['revision']=state.get('revision',0)+1
        state['actor']=actor
        result.update(state)
    storage.update_json(root,'attachments/tree-reads.json',mutate)
    return result
