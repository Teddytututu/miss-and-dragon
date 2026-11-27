"""Local manual research packets. Models and browsers remain human operated."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import zipfile
from . import answer_versions, storage


def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _result_name(name):
    name = Path(name).name
    if name in {'', '.', '..', 'meta.json', 'ask.md', 'materials.zip'} or name.startswith('.'):
        raise ValueError('Choose an ordinary result filename')
    return name


def _metadata(folder):
    path = Path(folder)/'meta.json'
    try:
        meta = storage.read(path)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError('Cannot read packet metadata at %s: %s; repair this file or restore a history copy' % (path, error)) from error
    if not isinstance(meta, dict):
        raise ValueError('Create this packet first: %s' % path)
    files = meta.get('answer_files', [])
    if not isinstance(files, list) or any(not isinstance(name, str) for name in files):
        raise ValueError('Packet answer_files must be a filename list: %s' % path)
    return meta


def _put(folder, name, raw):
    name = _result_name(name)
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
        if any(path.name != '.write.lock' for path in folder.iterdir()):
            raise ValueError('Choose an empty packet directory; existing files were kept')
        paths = [Path(source) for source in sources]
        if any(not path.is_file() for path in paths):
            raise ValueError('Packet inputs must be existing files')
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
    # Reject every reserved filename before creating an answer or result file.
    paths = [Path(path) for path in files]
    names = [_result_name(path.name) for path in paths]
    decoded = [(name, path.read_bytes()) for name, path in zip(names, paths)]
    if sum(len(raw) for _, raw in decoded) > 50*1024*1024:
        raise ValueError('Keep returned files within 50 MB')
    raw = (answer.strip()+'\n').encode('utf-8')
    digest = hashlib.sha256(raw)
    for name, data in sorted(decoded):
        digest.update(name.encode()+b'\0'+hashlib.sha256(data).digest())
    key = digest.hexdigest()[:16]
    with storage.locked(folder):
        meta = _metadata(folder)
        if any(row['id'] == key for row in answer_versions.versions(folder, meta)):
            return snapshot(folder)
        answer_name = _put(folder, 'answer-'+key+'.md', raw)
        names = [_put(folder,name,data) for name,data in decoded]
        answer_versions.add_version(folder,meta,key,answer_name,names,_stamp())
        meta['status'] = 'returned'
        storage.write(folder/'meta.json',meta)
    return snapshot(folder)


def review(folder, version_id, decision, note, *, task='', reviewer='Claude', adopted_files=None):
    folder = Path(folder)
    with storage.locked(folder):
        meta = _metadata(folder)
        candidate = next((row for row in answer_versions.versions(folder,meta)
                          if row['id'] == version_id), None)
        if candidate is None:
            raise ValueError('Answer version was not found')
        previous = candidate.get('review', {})
        # A rejection changes the decision, not the bytes identified by a version.
        bindings = previous.get('artifacts')
        inputs = previous.get('inputs')
        selected_files = None
        if adopted_files is not None and decision not in {'accepted', 'partial'}:
            raise ValueError('Adopted files require an accepted or partial review')
        if decision in {'accepted', 'partial'}:
            if adopted_files is not None:
                if (not isinstance(adopted_files, (list, tuple))
                        or any(not isinstance(name, str) or name not in candidate['files']
                               for name in adopted_files)):
                    raise ValueError('Choose adopted files from this answer version\'s registered file list')
                selected_files = list(dict.fromkeys(adopted_files))
            bindings = _bindings(folder,candidate)
            if 'artifacts' in previous and previous['artifacts'] != bindings:
                raise ValueError('Saved reviewed files changed; paste and review a new answer version')
            inputs = _input_bindings(folder,meta)
            if 'inputs' in previous and previous['inputs'] != inputs:
                raise ValueError('Original packet inputs changed; create a new packet or paste and review a new answer after checking the new inputs')
        row = answer_versions.review(folder,meta,version_id,decision,note,task=task,reviewer=reviewer)
        if bindings is not None or 'artifacts' in previous:
            row['review']['artifacts'] = bindings
        if inputs is not None or 'inputs' in previous:
            row['review']['inputs'] = inputs
        if selected_files is not None:
            row['review']['adopted_files'] = selected_files
        meta['status'] = 'reviewed'
        storage.write(folder/'meta.json',meta)
    return snapshot(folder)


def snapshot(folder):
    folder = Path(folder)
    meta = _metadata(folder)
    return dict(meta,answer_versions=answer_versions.versions(folder,meta))


def _bindings(folder, row):
    result = []
    for name in dict.fromkeys([row['answer'], *row['files']]):
        path = storage.relative_file(folder, name)
        if not path.is_file():
            raise ValueError('Answer version file is missing: %s; restore it before review or reporting' % path)
        result.append(dict(file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return result


def _input_bindings(folder, meta):
    result = {}
    for item in meta.get('attachments', []):
        name = item.get('file') if isinstance(item, dict) else item
        if not isinstance(name, str):
            continue
        path = storage.relative_file(folder, name)
        if not path.is_file():
            raise ValueError('Packet input file is missing: %s; restore the original input or create a new packet' % path)
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def adopted(folder):
    """Read the selected, reviewed answer and require its files to be available.

    This projection writes nothing and leaves older packets unchanged. Reports
    use it instead of guessing that the latest returned answer was adopted.
    """
    folder = Path(folder)
    meta = snapshot(folder)
    identifier = meta.get('adopted_answer')
    if not identifier:
        raise ValueError('No adopted answer; review a version as accepted or partial first')
    matches = [row for row in meta['answer_versions'] if row['id'] == identifier]
    if len(matches) != 1:
        raise ValueError('The adopted answer must identify one registered version')
    row = matches[0]
    review = row.get('review', {})
    if review.get('decision') not in {'accepted', 'partial'}:
        raise ValueError('The adopted answer needs an accepted or partial review')
    bindings = _bindings(folder,row)
    if 'artifacts' in review and review['artifacts'] != bindings:
        raise ValueError('Saved reviewed files changed; paste and review a new answer version')
    if 'inputs' in review and review['inputs'] != _input_bindings(folder,meta):
        raise ValueError('Original packet inputs changed; create a new packet or paste and review a new answer after checking the new inputs')
    copied_review = dict(review)
    if 'artifacts' in review:
        copied_review['artifacts'] = [dict(item) for item in review['artifacts']]
    if 'inputs' in review:
        copied_review['inputs'] = dict(review['inputs'])
    if 'adopted_files' in review:
        selected_files = review['adopted_files']
        if (not isinstance(selected_files, list)
                or any(not isinstance(name, str) or name not in row['files'] for name in selected_files)):
            raise ValueError('The adopted file list must refer to this answer version\'s registered files')
        copied_review['adopted_files'] = list(selected_files)
    return dict(row, files=list(row['files']), review=copied_review)
