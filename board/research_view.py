"""Read-only views of measured resource plans and manual research packets."""
from pathlib import Path
from . import storage, manual_packets, ticket_schedule


def packet_folder(root, name):
    if not name or name in {'.', '..'} or Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError('Choose a packet name')
    return storage.relative_file(Path(root), 'attachments/manual-packets/' + name)


def _attachment_names(meta):
    """Project legacy {file: name} inputs without changing saved metadata."""
    names = []
    for item in meta.get('attachments', []):
        name = item.get('file') if isinstance(item, dict) else item
        if isinstance(name, str):
            names.append(name)
    return names


def packets(root, issues=None):
    base = Path(root) / 'attachments/manual-packets'
    result = []
    if not base.is_dir():
        return result
    for item in sorted(base.iterdir()):
        if not item.is_dir() or item.is_symlink() or not (item/'meta.json').is_file():
            continue
        try:
            folder = packet_folder(root, item.name)
            row = manual_packets.snapshot(folder)
            row['attachments'] = _attachment_names(row)
            row['name'] = item.name
            row['question'] = storage.relative_file(folder, 'ask.md').read_text('utf-8')
            result.append(row)
        except (ValueError, OSError, KeyError, TypeError):
            if issues is not None:
                issues.append(dict(section='manual_packets', name=item.name,
                                   message='Check the saved packet metadata'))
            continue
    return result


def packet_file(root, name, filename):
    folder = packet_folder(root, name)
    meta = manual_packets.snapshot(folder)
    allowed = set(_attachment_names(meta))
    for row in meta['answer_versions']:
        allowed.add(row['answer'])
        allowed.update(row.get('files', []))
    if filename not in allowed:
        raise ValueError('Choose a registered packet file')
    return storage.relative_file(folder, filename)


def view(root):
    issues=[]
    plan=None
    try:
        path = storage.relative_file(Path(root), 'attachments/resource-plan.json')
        plan = ticket_schedule.from_file(path)
        if plan:
            plan['observed_at'] = path.stat().st_mtime
            plan['input_jobs'] = storage.read(path, {}).get('jobs', [])
    except (ValueError, OSError, KeyError, TypeError):
        plan=None
        issues.append(dict(section='resource_plan',message='Check the resource plan jobs and measured units'))
    from . import delivery
    stages=list(delivery.read(root)['stages'].values())
    return dict(delivery_stages=stages,resource_plan=plan, manual_packets=packets(root,issues), research_issues=issues)
