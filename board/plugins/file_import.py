"""Explicit directory observation, one bounded pass per caller invocation."""
from pathlib import Path
import math


def observe_once(config,state,importer,*,now):
    if config.get('enabled') is not True:return dict(status='disabled',collected=[])
    directory=Path(config['directory'])
    if not directory.is_absolute() or directory.is_symlink() or not directory.is_dir():raise ValueError('explicit_local_directory_required')
    settle=config.get('settle_seconds',2)
    if type(settle) not in (int,float) or not math.isfinite(settle) or settle<1:raise ValueError('positive_settle_interval')
    tracked=state.setdefault('files',{});ready=[]
    for source in directory.iterdir():
        if source.is_symlink() or not source.is_file():continue
        stat=source.stat()
        if getattr(stat,'st_file_attributes',0)&(0x400000|0x1000|0x40000) or stat.st_size>50*1024*1024:continue
        key=str(source);signature=[stat.st_size,stat.st_mtime_ns];old=tracked.get(key)
        if not old or old['signature']!=signature:
            tracked[key]=dict(signature=signature,since=now,imported=False);continue
        if not old['imported'] and now-old['since']>=settle:ready.append(source)
    result=importer(config['packet_root'],ready,apply=True) if ready else dict(collected=[])
    for row in result['collected']:
        original=row.get('original_path') or row.get('source')
        if original in tracked:tracked[original]['imported']=True
    current={str(path) for path in directory.iterdir()}
    state['files']={key:value for key,value in tracked.items() if key in current}
    return dict(status='observed',**result)
