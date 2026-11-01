"""Date-bound task check identities; scheduling remains owned by the planner."""
import copy
import hashlib
import json
import re
from datetime import date, timedelta

PASSIVE={'休息','用餐','吃饭','早餐','午餐','晚餐','餐饮','通勤','交通','出行',
         '健康','运动','课','上课','考试','会议','睡眠','生活'}


def actionable(item):
    if type(item.get('checkable')) is bool:
        return item['checkable']
    return bool(str(item.get('what','')).strip()) and str(item.get('kind','')).strip() not in PASSIVE


def day_key(day, today):
    if type(day.get('relative_day')) is int:
        return (today+timedelta(days=day['relative_day'])).isoformat()
    label=str(day.get('date','')).strip()
    full=re.match(r'^(\d{4})-(\d{2})-(\d{2})(?:\D|$)',label)
    if full:return date(*map(int,full.groups())).isoformat()
    short=re.match(r'^(\d{2})-(\d{2})(?:\D|$)',label)
    if short:
        choices=[]
        for year in (today.year-1,today.year,today.year+1):
            try:choices.append(date(year,*map(int,short.groups())))
            except ValueError:pass
        return min(choices,key=lambda d:abs((d-today).days)).isoformat() if choices else label
    return str(today.year)+':'+label


def project(days, state=None, today=None):
    today=today or date.today()
    result=copy.deepcopy(days or [])
    checks=(state or {}).get('items',{})
    def identity(day,item):
        content=['id',str(item['id'])] if item.get('id') else ['text',str(item.get('what','')).strip(),str(item.get('kind','')).strip()]
        return json.dumps([day_key(day,today),content],ensure_ascii=False,separators=(',',':'))
    counts={}
    for day in result:
        for item in day.get('items',[]):
            if actionable(item):
                key=identity(day,item);counts[key]=counts.get(key,0)+1
    seen={}
    for day in result:
        for item in day.get('items',[]):
            item.pop('check_id',None)
            if not actionable(item):continue
            raw=identity(day,item)
            if counts[raw]>1:raw+=':'+str(item.get('time','')).strip()
            occurrence=seen.get(raw,0);seen[raw]=occurrence+1
            key=hashlib.sha256((raw+':'+str(occurrence)).encode()).hexdigest()
            item['check_id']=key
            item['completed']=checks.get(key,{}).get('completed',item.get('completed') is True) is True
    return result


def validate(days, payload, today=None):
    if (not isinstance(payload,dict) or set(payload)!={'id','completed'} or
            not isinstance(payload['id'],str) or type(payload['completed']) is not bool):
        raise ValueError('请使用时间表上的任务勾选框。')
    for day in project(days,today=today):
        for item in day.get('items',[]):
            if item.get('check_id')==payload['id']:
                return dict(id=payload['id'],completed=payload['completed'])
    raise ValueError('安排已更新，请刷新后选择当前任务。')


def summary(root,today=None):
    """Expose the same dated completion facts to the project's assistants."""
    from pathlib import Path
    from . import storage
    root=Path(root);today=today or date.today()
    with storage.locked(root):
        days=storage.read(root/'overview.json',{}).get('schedule',[])
        state=storage.read(root/'attachments/plan-checks.json',{})
        days=project(days,state,today)
    rows=[];people={}
    for day in days:
        for item in day.get('items',[]):
            if not item.get('check_id'):continue
            person=item.get('who') or item.get('owner') or item.get('assignee') or 'owner'
            row=dict(id=item['check_id'],date=day_key(day,today),time=item.get('time',''),what=item.get('what',''),person=person,completed=item['completed'])
            rows.append(row);counts=people.setdefault(person,dict(completed=0,pending=0));counts['completed' if row['completed'] else 'pending']+=1
    return dict(items=rows,people=people,completed=sum(r['completed'] for r in rows),pending=sum(not r['completed'] for r in rows))
