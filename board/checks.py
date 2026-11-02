"""Due observations close a process issue after consecutive successful checks."""
from datetime import datetime, timedelta
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


CHECKS = {'task_ready': dict(title='Work for each execution role', target=10,
                           every_minutes=180, run=task_ready)}


def run(root, *, show_only=False, now=None, registry=None):
    at = lifecycle.moment(now) if now is not None else lifecycle.moment(datetime.now().astimezone())
    if at is None:
        raise ValueError('Use a valid observation time')
    specs = CHECKS if registry is None else registry
    for name, spec in specs.items():
        if (not isinstance(name, str) or not name or not isinstance(spec.get('title'), str)
            or type(spec.get('target')) is not int or spec['target'] < 1
            or type(spec.get('every_minutes')) is not int or spec['every_minutes'] < 1
            or not callable(spec.get('run'))):
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
                out = spec['run'](root)
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
