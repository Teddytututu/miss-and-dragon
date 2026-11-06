"""Move notes into dated plans and restore unfinished notes on rollover."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from . import storage,plan_checks

def today_date(stamp=None):
    return datetime.fromtimestamp(stamp).astimezone().date() if stamp is not None else datetime.now().astimezone().date()

def rollover(root,today=None):
    root=Path(root);today=today or today_date()
    with storage.locked(root):
        value=storage.read(root/'overview.json',{})
        state=storage.read(root/'attachments/plan-checks.json',{})
        projected=plan_checks.project(value.get('schedule',[]),state,today)
        returned=[];completed_indices=[];removed=0
        for day,checked_day in zip(value.get('schedule',[]),projected):
            kept=[]
            for item,checked in zip(day.get('items',[]),checked_day.get('items',[])):
                entry=item.get('scheduled_from_note')
                if not entry or entry['date']>=today.isoformat():
                    kept.append(item);continue
                removed+=1
                if checked.get('completed'):
                    completed_indices.append(entry['index'])
                    archive=value.setdefault('todo_done',[])
                    if not any(row.get('_schedule_check_id')==checked['check_id'] for row in archive):
                        archive.append(dict(entry['note'],note_id=entry['id'],_schedule_check_id=checked['check_id'],
                            done_at=state.get('items',{}).get(checked['check_id'],{}).get('updated_at') or entry['placed_at']))
                else:returned.append(entry)
            day['items']=kept
        for entry in sorted(returned,key=lambda row:row['index']):
            note=deepcopy(entry['note']);note['_returned_on']=today.isoformat()
            index=entry['index']-sum(i<entry['index'] for i in completed_indices)
            notes=value.setdefault('todo',[]);notes.insert(min(index,len(notes)),note)
        if removed:storage.write(root/'overview.json',value)
        return removed

def place(value, note_id, note, index, client_id, stamp):
    today = today_date(stamp)
    days = value.setdefault('schedule', [])
    prior_indices = sorted(item['scheduled_from_note']['index'] for day in days for item in day.get('items', []) if item.get('scheduled_from_note'))
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

