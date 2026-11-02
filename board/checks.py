"""Due observations close a process issue after consecutive successful checks."""
from datetime import datetime, timedelta
import math
from . import lifecycle, storage, workflow_checks


def task_ready(root):
    config = storage.read(lifecycle.data_file(root, 'project.json'), {})
    roles = config.get('executor_roles', ['GPT'])
    if not isinstance(roles, list) or not roles or any(not isinstance(r, str) or not r for r in roles):
        roles = ['GPT']
    paused = config.get('paused_executor_roles', [])
    active = [role for role in roles if role not in paused]
    if not active:
        return dict(ok=None, detail='All execution roles are paused.')
    path = lifecycle.data_file(root, 'board.md')
    rows = lifecycle.parse_board(path.read_text('utf-8-sig')) if path.exists() else []
    missing = workflow_checks.idle_roles(root, rows)
    return dict(ok=not missing, detail='Roles awaiting actionable work: '+', '.join(missing)
                if missing else 'Each active execution role has actionable work.')


def _observation_time(now):
    at = lifecycle.moment(now if now is not None else datetime.now().astimezone())
    if at is None:raise ValueError('Use a valid observation time')
    return at


def patrols_on_time(root, *, now=None):
    """Audit recorded assistant patrols, with a forty-five-minute grace period."""
    from . import cadence
    at = _observation_time(now)
    rows = storage.read(lifecycle.data_file(root, 'overview.json'), {}).get('patrols', {})
    late, unknown = [], []
    for who in lifecycle.ROLES:
        row = rows.get(who, {})
        last = lifecycle.moment(row.get('at'))
        every = row.get('every_min', cadence.minutes(root, 'lead' if who=='Claude' else 'execution'))
        if (last is None or last > at or type(every) not in (int, float)
                or not math.isfinite(every) or every <= 0):
            unknown.append(who)
            continue
        due = lifecycle.moment(row.get('next_at')) if row.get('next_at') else last+timedelta(minutes=every)
        if due is None or due < last:
            unknown.append(who)
        elif at > due+timedelta(minutes=45):
            late.append(who)
    if late:return dict(ok=False, detail='Overdue assistant patrols: '+', '.join(late))
    if unknown:return dict(ok=None, detail='Patrol records awaited: '+', '.join(unknown))
    return dict(ok=True, detail='Both assistants have on-time patrol records.')


def owner_answered(root, *, now=None):
    """Find owner conversation messages waiting two to twenty-four hours."""
    from . import agent_tools, project
    at = _observation_time(now)
    posts = [p for p in project.all_posts(root) if not p.get('deleted')]
    replied = {p.get('parent_id') for p in posts if project.session_message(p)
               and (p.get('body') or '').strip()}
    enough = set().union(*(agent_tools.enough_messages(root, who) for who in lifecycle.ROLES))
    waiting, unknown = [], []
    for post in posts:
        if (post.get('author')!='owner' or post.get('channel', 'main')=='library'
                or post['id'] in replied or post['id'] in enough):continue
        created = lifecycle.moment(post.get('created_at'))
        if created is None or created > at:
            unknown.append(post['id'])
        elif timedelta(hours=2) <= at-created <= timedelta(hours=24):
            waiting.append(post['id'])
    if waiting:return dict(ok=False, detail='Owner messages awaiting a reply: '+', '.join(waiting[:5]))
    if unknown:return dict(ok=None, detail='Owner message times require review: '+', '.join(unknown[:5]))
    return dict(ok=True, detail='Owner messages have a reply or an explicit reaction decision within the audit window.')


CHECKS = {
    'task_ready': dict(title='Work for each execution role', target=10,
                      every_minutes=180, run=task_ready),
    'patrols_on_time': dict(title='Assistant patrols on time', target=10,
                          every_minutes=180, run=patrols_on_time, clocked=True),
    'owner_answered': dict(title='Owner messages answered within two hours', target=10,
                          every_minutes=180, run=owner_answered, clocked=True),
}


def run(root, *, show_only=False, now=None, registry=None):
    at = lifecycle.moment(now) if now is not None else lifecycle.moment(datetime.now().astimezone())
    if at is None:
        raise ValueError('Use a valid observation time')
    specs = CHECKS if registry is None else registry
    for name, spec in specs.items():
        if (not isinstance(name, str) or not name or not isinstance(spec.get('title'), str)
            or type(spec.get('target')) is not int or spec['target'] < 1
            or type(spec.get('every_minutes')) is not int or spec['every_minutes'] < 1
            or not callable(spec.get('run')) or type(spec.get('clocked', False)) is not bool):
            raise ValueError('Checks require a name, title, positive target and interval, and runner')
    path = lifecycle.data_file(root, 'attachments/checks.json')
    if show_only:
        return storage.read(path, {'checks': {}}).get('checks', {})
    results = {}
    with storage.locked(root):
        state = storage.read(path, {})
        rows = state.setdefault('checks', {})
        for name, spec in specs.items():
            row = rows.setdefault(name, dict(title=spec['title'], target=spec['target'],
                every_minutes=spec['every_minutes'], streak=0, solved=False, history=[]))
            if (row['target'], row.get('every_minutes')) != (spec['target'], spec['every_minutes']):
                row.update(target=spec['target'], every_minutes=spec['every_minutes'],
                           streak=0, solved=False, next_at=None)
                row.pop('solved_at', None)
            due = lifecycle.moment(row.get('next_at'))
            if row['solved'] or due and at < due:
                results[name] = dict(row)
                continue
            try:
                out = spec['run'](root, **({'now': at} if spec.get('clocked') else {}))
                if not isinstance(out, dict) or 'ok' not in out or not any(out.get('ok') is value for value in (True, False, None)):
                    raise ValueError('Return ok as true, false or null')
            except Exception as error:
                out = dict(ok=None, detail='Observation unavailable: '+str(error)[:160])
            if out['ok'] is True:
                row['streak'] += 1
            elif out['ok'] is False:
                row['streak'] = 0
            row.update(title=spec['title'], ok=out['ok'], detail=str(out.get('detail', '')),
                       last_at=at.isoformat(), next_at=(at+timedelta(minutes=spec['every_minutes'])).isoformat())
            row['history'].append(dict(at=at.isoformat(), ok=out['ok'], detail=row['detail']))
            row['history'] = row['history'][-60:]
            if row['streak'] >= row['target']:
                row.update(solved=True, solved_at=at.isoformat())
            results[name] = dict(row)
        storage.write(path, state)
    return results
