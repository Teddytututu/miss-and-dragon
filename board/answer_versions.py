"""Version projection shared by manual packet UI and CLI; reading keeps disk unchanged."""
from pathlib import Path
import hashlib


def versions(folder, meta):
    folder = Path(folder)
    recorded = meta.get('answer_versions', [])
    if not isinstance(recorded, list):
        raise ValueError('Answer version metadata must be a list')
    rows = []
    for row in recorded:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or not isinstance(row.get('answer'), str)
                or not isinstance(row.get('files', []), list)
                or any(not isinstance(name, str) for name in row.get('files', []))
                or ('review' in row and not isinstance(row['review'], dict))):
            raise ValueError('Answer version metadata needs id, answer and a file list')
        rows.append(dict(row, files=list(row.get('files', []))))
    known = {row['answer'] for row in rows}
    attachments = {name for row in rows for name in row['files']}
    inputs = meta.get('attachments', [])
    if not isinstance(inputs, list):
        raise ValueError('Answer version attachment metadata must be a list')
    for item in inputs:
        name = item.get('file') if isinstance(item, dict) else item
        if isinstance(name, str):
            attachments.add(name)
    for path in sorted(set(folder.glob('回答-*.md')) | set(folder.glob('answer-*.md'))):
        if path.name not in known and path.name not in attachments:
            rows.append({'id': hashlib.sha256(path.name.encode()).hexdigest()[:16],
                         'answer': path.name, 'files': [], 'legacy': True})
    return rows


def add_version(folder, meta, version_id, answer, files, saved_at):
    record = {'id': version_id, 'answer': answer, 'files': list(dict.fromkeys(files)),
              'saved_at': saved_at, 'legacy': False}
    recorded = meta.get('answer_versions', [])
    if not isinstance(recorded, list):
        raise ValueError('Answer version metadata must be a list')
    # Make newly pasted files explicit before discovering legacy answer names.
    existing = versions(folder, dict(meta, answer_versions=recorded + [record]))
    rows = [row for row in existing if row['answer'] != answer or not row.get('legacy')]
    rows = list({row['id']: row for row in rows}.values())
    meta['answer_versions'] = rows
    meta['answer_files'] = list(dict.fromkeys(list(meta.get('answer_files', [])) + [answer] + files))
    return next(row for row in rows if row['id'] == version_id)


def attach_files(meta, version_id, files):
    for row in meta.get('answer_versions', []):
        if row['id'] == version_id:
            row['files'] = list(dict.fromkeys(row.get('files', []) + files))
            meta['answer_files'] = list(dict.fromkeys(meta.get('answer_files', []) + files))
            return
    raise ValueError('Answer version was not found')


def review(folder, meta, version_id, decision, note, *, task='', reviewer='Claude'):
    if decision not in {'accepted', 'partial', 'rejected'}:
        raise ValueError('Choose accepted, partial or rejected')
    rows = versions(folder, meta)
    row = next((row for row in rows if row['id'] == version_id), None)
    if row is None:
        raise ValueError('Answer version was not found')
    row['review'] = {'decision': decision, 'note': note, 'task': task, 'by': reviewer}
    meta['answer_versions'] = rows
    if decision in {'accepted', 'partial'}:
        meta['adopted_answer'] = version_id
    elif meta.get('adopted_answer') == version_id:
        meta.pop('adopted_answer')
    return row
