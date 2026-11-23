"""Dated sticky-note placement, planner assignment and reversible day rollover."""
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import json
import re
from . import storage,plan_checks

TZ = datetime.now().astimezone().tzinfo


def today_date(stamp=None):
    if isinstance(stamp, datetime):
        return stamp.astimezone(TZ).date() if stamp.tzinfo else stamp.replace(tzinfo=TZ).date()
    if isinstance(stamp, date):
        return stamp
    return datetime.fromtimestamp(stamp).astimezone().date() if stamp is not None else datetime.now().astimezone().date()


def origin(item):
    """Read both existing metadata versions while preserving stored item IDs."""
    if item.get('scheduled_from_note'):
        return item['scheduled_from_note']
    old = item.get('_board_note')
    if old:
        return dict(id=old['note_id'], date=old['scheduled_on'], index=old['index'],
                    note=old['row'], placed_at=old.get('placed_at'))
    return None


def restore(value, entries, returned_on=None):
    notes = value.setdefault('todo', [])
    for entry in sorted(entries, key=lambda entry:entry['index']):
        note = deepcopy(entry['note'])
        if returned_on:
            note['_returned_on'] = returned_on
        notes.insert(min(entry['index'], len(notes)), note)


def restore_today_completed(value, today):
    """Recover same-day rows archived by the previous completion handler."""
    recovered = []
    for archived in value.get('todo_done', []):
        check_id = archived.get('_schedule_check_id')
        done_at = archived.get('done_at', '')
        if not check_id or done_at[:10] != today.isoformat():
            continue
        client = next((key for key, note_id in value.get('note_schedule_operations', {}).items()
                       if note_id == archived.get('note_id')), None)
        if client is None:
            continue
        note = {key:deepcopy(item) for key, item in archived.items()
                if key not in {'assigned_by', 'done_at', 'note_id', '_schedule_check_id'}}
        note['by'] = archived.get('assigned_by', 'Claude')
        entry = dict(id=archived['note_id'], date=today.isoformat(), placed_at=done_at,
                     index=len(value.get('todo', [])), client_id=client, note=note)
        item = dict(id='note:' + client, time='', what=note['what'], kind=note.get('kind') or '事务',
                    checkable=True, completed=True, scheduled_from_note=entry)
        candidate = dict(date=today.isoformat(), items=[item])
        if plan_checks.project([candidate], today=today)[0]['items'][0]['check_id'] != check_id:
            continue
        day = next((day for day in value.get('schedule', [])
                    if plan_checks.day_key(day, today) == today.isoformat()), None)
        if day is None:
            day = dict(date=today.isoformat(), items=[])
            value.setdefault('schedule', []).append(day)
        if not any(row.get('id') == item['id'] for row in day.get('items', [])):
            day.setdefault('items', []).append(item)
        recovered.append(archived)
    for archived in recovered:
        value['todo_done'].remove(archived)
    return len(recovered)


def rollover(root, today=None):
    today = today_date(today)
    path = Path(root) / 'overview.json'
    if not path.exists():
        return 0
    with storage.locked(root):
        value = json.loads(path.read_bytes())
        recovered = restore_today_completed(value, today)
        checks = Path(root) / 'attachments/plan-checks.json'
        state = json.loads(checks.read_bytes()) if checks.exists() else {}
        projected = plan_checks.project(value.get('schedule', []), state, today)
        expired = []
        completed_indices = []
        removed = 0
        for day, checked_day in zip(value.get('schedule', []), projected):
            kept = []
            for item, checked in zip(day.get('items', []), checked_day.get('items', [])):
                entry = origin(item)
                if entry and entry['date'] < today.isoformat():
                    removed += 1
                    if checked.get('completed'):
                        completed_indices.append(entry['index'])
                        archive = value.setdefault('todo_done', [])
                        if not any(row.get('_schedule_check_id') == checked['check_id'] for row in archive):
                            note = entry['note']
                            archive.append(dict(note, assigned_by=note.get('by') or 'Claude', by='owner',
                                done_at=state.get('items', {}).get(checked['check_id'], {}).get('updated_at')
                                        or entry.get('placed_at') or datetime.combine(today, datetime.min.time(), TZ).isoformat(),
                                note_id=entry['id'], _schedule_check_id=checked['check_id']))
                    else:
                        expired.append(entry)
                else:
                    kept.append(item)
            had_notes = any(origin(item) for item in day.get('items', []))
            day['items'] = kept
            if had_notes and not kept:
                day['_empty_after_notes'] = True
        if expired:
            expired = [dict(entry, index=entry['index'] - sum(index < entry['index'] for index in completed_indices))
                       for entry in expired]
            restore(value, expired, today.isoformat())
        if removed or recovered:
            value['schedule'] = [day for day in value['schedule'] if not day.pop('_empty_after_notes', False)]
            storage.write(path,value)
        return removed


def place(value, note_id, note, index, client_id, stamp):
    today = today_date(stamp)
    days = value.setdefault('schedule', [])
    prior_indices = sorted(origin(item)['index'] for day in days for item in day.get('items', []) if origin(item))
    original_index = index
    for occupied in prior_indices:
        if occupied <= original_index:
            original_index += 1
    target = next((day for day in days if plan_checks.day_key(day, today) == today.isoformat()), None)
    if target is None:
        target = dict(date=today.isoformat(), items=[])
        days.append(target)
    metadata = dict(id=note_id, placed_at=datetime.fromtimestamp(stamp).astimezone().isoformat(),
                    date=today.isoformat(), index=original_index, client_id=client_id, note=deepcopy(note))
    target.setdefault('items', []).append(dict(id='note:' + client_id, time='', what=note['what'], kind=note.get('kind') or '事务',
                                              checkable=True, scheduled_from_note=metadata))
    value.setdefault('note_schedule_operations', {})[client_id] = note_id
    value['todo'].pop(index)


def assign(root, note_id, period, today=None):
    today = today_date(today)
    if not isinstance(period, str) or not re.fullmatch(r'白天|晚上|(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*[–—-]\s*(?:[01]?\d|2[0-3]):[0-5]\d)?', period):
        raise ValueError('时段用白天、晚上、HH:MM或HH:MM–HH:MM。')
    rollover(root, today)
    path = Path(root) / 'overview.json'
    with storage.locked(root):
        value = json.loads(path.read_bytes())
        matches = [(day, item) for day in value.get('schedule', []) for item in day.get('items', [])
                   if origin(item) and origin(item)['id'] == note_id
                   and origin(item)['date'] == today.isoformat()]
        if len(matches) != 1:
            raise ValueError('请选择今天唯一的待排便利贴。')
        day, item = matches[0]
        item['time'] = period
        metadata = item.get('scheduled_from_note') or item['_board_note']
        metadata['assigned_at'] = datetime.now().astimezone().isoformat()
        def order(row):
            time = row.get('time', '')
            match = re.match(r'(\d{1,2}):(\d{2})', time)
            if match:
                return int(match[1]) * 60 + int(match[2])
            return {'白天':9 * 60, '晚上':18 * 60}.get(time, 24 * 60)
        day['items'].sort(key=order)
        storage.write(path,value)
        return dict(note_id=note_id, date=today.isoformat(), time=period, what=item['what'])


def pending_events(root, stamp=None):
    """Observe aged unassigned notes through the existing completion projection."""
    stamp = datetime.now().astimezone().timestamp() if stamp is None else stamp
    today = today_date(stamp)
    root = Path(root)
    overview = root/'overview.json'
    with storage.locked(root):
        value = json.loads(overview.read_bytes())
        checks = root/'attachments/plan-checks.json'
        state = json.loads(checks.read_bytes()) if checks.exists() else {}
        days = plan_checks.project(value.get('schedule', []), state, today)
    events = []
    for day in days:
        if plan_checks.day_key(day, today) != today.isoformat():
            continue
        for row in day.get('items', []):
            metadata = origin(row) or {}
            note_id = metadata.get('id')
            if row.get('time') or row.get('completed') or not isinstance(note_id, str) or not note_id or metadata.get('date') != today.isoformat():
                continue
            try:
                placed = datetime.fromisoformat(metadata['placed_at'])
                if placed.tzinfo is None:
                    placed = placed.replace(tzinfo=TZ)
                age = stamp-placed.timestamp()
            except (KeyError, TypeError, ValueError):
                continue
            if age >= 30*60:
                events.append(dict(id='pending_note_30min:'+today.isoformat()+':'+note_id,
                                   type='pending_note_30min', at=stamp,
                                   title='今日便利贴已待排30分钟', note_id=note_id,
                                   date=today.isoformat(), placed_at=metadata['placed_at'],
                                   what=row.get('what', ''), waited_seconds=age))
    return events
