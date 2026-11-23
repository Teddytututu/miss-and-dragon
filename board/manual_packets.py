"""Local manual research packets. Models and browsers remain human operated."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import zipfile
from . import answer_versions, storage


def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _put(folder, name, raw):
    name = Path(name).name
    if name in {'', '.', '..', 'meta.json', 'ask.md', 'materials.zip'} or name.startswith('.'):
        raise ValueError('Choose an ordinary result filename')
    target = folder / name
    stem = Path(name).stem + '-' + hashlib.sha256(raw).hexdigest()[:16]
    suffix = Path(name).suffix
    number = 1
    while True:
        if target.is_symlink():
            raise ValueError('Use packet-local regular files')
        if not target.exists():
            storage.write_bytes(target, raw)
            return target.name
        if not target.is_file():
            raise ValueError('Use packet-local regular files')
        if target.read_bytes() == raw:
            return target.name
        target = folder / (stem + ('' if number == 1 else '-'+str(number)) + suffix)
        number += 1


def create(folder, title, question, sources=(), *, task='', owner='Claude'):
    folder = Path(folder)
    with storage.locked(folder):
        if (folder/'meta.json').exists():
            raise ValueError('Choose a new packet directory')
        paths = [Path(source) for source in sources]
        if len({path.name for path in paths}) != len(paths):
            raise ValueError('Give input files distinct names')
        if sum(path.stat().st_size for path in paths) > 50*1024*1024:
            raise ValueError('Keep packet inputs within 50 MB')
        storage.write_bytes(folder/'ask.md', question.encode('utf-8'))
        with zipfile.ZipFile(folder/'materials.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                archive.write(path, path.name)
        storage.write(folder/'meta.json', {'title':title,'task':task,'owner':owner,'status':'ready',
                                         'created_at':_stamp(),'attachments':['ask.md','materials.zip']})
    return snapshot(folder)


def paste(folder, answer, files=()):
    folder = Path(folder)
    if not answer.strip():
        raise ValueError('Paste the answer text')
    decoded = [(Path(path).name, Path(path).read_bytes()) for path in files]
    if sum(len(raw) for _, raw in decoded) > 50*1024*1024:
        raise ValueError('Keep returned files within 50 MB')
    raw = (answer.strip()+'\n').encode('utf-8')
    digest = hashlib.sha256(raw)
    for name, data in sorted(decoded):
        digest.update(name.encode()+b'\0'+hashlib.sha256(data).digest())
    key = digest.hexdigest()[:16]
    with storage.locked(folder):
        meta = storage.read(folder/'meta.json')
        if not isinstance(meta, dict):
            raise ValueError('Create this packet first')
        if any(row['id'] == key for row in answer_versions.versions(folder, meta)):
            return snapshot(folder)
        answer_name = _put(folder, 'answer-'+key+'.md', raw)
        names = [_put(folder,name,data) for name,data in decoded]
        answer_versions.add_version(folder,meta,key,answer_name,names,_stamp())
        meta['status'] = 'returned'
        storage.write(folder/'meta.json',meta)
    return snapshot(folder)


def review(folder, version_id, decision, note, *, task='', reviewer='Claude'):
    folder = Path(folder)
    with storage.locked(folder):
        meta = storage.read(folder/'meta.json')
        if not isinstance(meta, dict):
            raise ValueError('Create this packet first')
        answer_versions.review(folder,meta,version_id,decision,note,task=task,reviewer=reviewer)
        meta['status'] = 'reviewed'
        storage.write(folder/'meta.json',meta)
    return snapshot(folder)


def snapshot(folder):
    folder = Path(folder)
    meta = storage.read(folder/'meta.json')
    if not isinstance(meta, dict):
        raise ValueError('Create this packet first')
    return dict(meta,answer_versions=answer_versions.versions(folder,meta))
