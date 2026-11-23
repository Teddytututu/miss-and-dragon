"""Explicit version-scoped file import; source files remain in place."""
from pathlib import Path
import hashlib
import re
from . import manual_packets,research_view,storage


def attach(root,packet,files,*,version_id=None):
    folder=research_view.packet_folder(root,packet)
    sources=[]
    for source in map(Path,files):
        stat=source.stat()
        if source.is_symlink() or not source.is_file() or stat.st_size>50*1024*1024 or getattr(stat,'st_file_attributes',0)&(0x400000|0x1000|0x40000):raise ValueError('Bounded local regular files required')
        sources.append((source,source.read_bytes()))
    if sum(len(raw) for _,raw in sources)>50*1024*1024:raise ValueError('Keep total imports within 50 MB')
    with storage.locked(folder):
        meta=storage.read(folder/'meta.json');versions=manual_packets.snapshot(folder)['answer_versions']
        if version_id is None:
            if len(versions)!=1:raise ValueError('Choose the answer version')
            version_id=versions[0]['id']
        version=next((row for row in meta.get('answer_versions',[]) if row['id']==version_id),None)
        if version is None:raise ValueError('Registered answer version required')
        result=[]
        for source,raw in sources:
            name=manual_packets._put(folder,source.name,raw)
            if name not in version['files']:version['files'].append(name)
            result.append(dict(source=str(source),file=name,sha256=hashlib.sha256(raw).hexdigest(),version_id=version_id))
        storage.write(folder/'meta.json',meta);return result
