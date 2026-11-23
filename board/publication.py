"""Freeze accepted report bytes; registration, opening and speech retry separately."""
from pathlib import Path
import hashlib
import os
from . import delivery,reader_assets,report_reader,storage


def publish(root,task,stage,artifact,title,*,open_report=None,speak=None):
    root=Path(root);identity=delivery.key(task,stage)
    with storage.locked(root):
        row=delivery.read(root)['stages'][identity]
        if row['state']!='accepted' or not delivery.current(root,row):raise ValueError('Accepted current report required')
        source=storage.relative_file(root,artifact)
        if source.suffix.lower() not in {'.html','.htm','.md','.pdf'}:raise ValueError('Readable report required')
        bindings={a['path']:a['sha256'] for a in row['artifacts']}
        closure=reader_assets.closure(source,eligible=lambda p:report_reader.eligible(root,p))
        if any(p.relative_to(root).as_posix() not in bindings for p in closure):raise ValueError('Review every report dependency')
        request=hashlib.sha256((identity+':'+row['version']+':'+artifact).encode()).hexdigest()[:24]
        common=Path(os.path.commonpath([p.parent for p in closure]));folder=root/'attachments/published'/request
        for path in closure:
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=bindings[path.relative_to(root).as_posix()]:raise ValueError('Artifact changed during publication')
            destination=storage.relative_file(folder,path.relative_to(common))
            if destination.exists() and destination.read_bytes()!=raw:raise ValueError('Frozen artifact integrity required')
            if not destination.exists():storage.write_bytes(destination,raw)
        relative=(folder/source.relative_to(common)).relative_to(root).as_posix()
        overview=storage.read(root/'overview.json',{})
        links=overview.setdefault('links',[])
        if not any(link.get('publication_id')==request for link in links):
            links.append(dict(title=title,path=relative,publication_id=request,task=task,stage=stage,version=row['version']))
            storage.write(root/'overview.json',overview)
        receipts=storage.read(root/'attachments/publications.json',{})
        receipt=receipts.setdefault(request,dict(id=request,path=relative,registration='completed',opening='pending',speech='pending'))
        url=report_reader.report_url(relative)
    for field,callback in [('opening',open_report),('speech',speak)]:
        if callback:
            # The claim makes retries from another caller observe the in-flight step.
            with storage.locked(root):
                receipts=storage.read(root/'attachments/publications.json',{});saved=receipts.get(request,receipt)
                if saved[field] in {'completed','sending'}:continue
                saved[field]='sending';receipts[request]=saved;storage.write(root/'attachments/publications.json',receipts)
            try:
                outcome=callback(url if field=='opening' else title)
                state='completed' if outcome is not False else 'failed'
            except Exception:state='failed'
            with storage.locked(root):
                receipts=storage.read(root/'attachments/publications.json',{});receipts[request][field]=state
                storage.write(root/'attachments/publications.json',receipts)
    with storage.locked(root):
        receipts=storage.read(root/'attachments/publications.json',{})
        receipts.setdefault(request,receipt);storage.write(root/'attachments/publications.json',receipts)
        return dict(receipts[request])
