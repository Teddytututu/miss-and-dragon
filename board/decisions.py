"""Owner decision cards with version-bound execution and artifact confirmation."""
import json, math, re, secrets, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from . import storage,delivery


def _rejected():
    from .plugins.accounts import Rejected
    return Rejected


def stamp(now=None):
    return datetime.fromtimestamp(time.time() if now is None else now, None).isoformat(timespec='minutes')


def policy(value):
    """Local defaults remain stable; deployments can configure trusted identities."""
    custom = value.get('decision_policy', {})
    if not isinstance(custom, dict) or set(custom) - {'creators', 'chooser', 'executors'}:
        raise ValueError('决策角色配置需要creators、chooser和executors字段。')
    result = dict(creators=['Claude'], chooser='owner', executors={'Claude': ['*'], 'GPT': ['*']})
    result.update(custom)
    valid_name = lambda name: isinstance(name, str) and bool(name.strip()) and len(name) <= 80
    if (not isinstance(result['creators'], list) or not result['creators'] or
            not all(valid_name(name) for name in result['creators']) or not valid_name(result['chooser']) or
            not isinstance(result['executors'], dict) or not result['executors'] or
            not all(valid_name(name) and isinstance(roles, list) and roles and all(valid_name(role) for role in roles)
                    for name, roles in result['executors'].items())):
        raise ValueError('决策角色配置需要有效身份和执行角色。')
    return result


def authorize(value, actor, operation, role=None):
    roles = policy(value)
    if operation == 'add':
        allowed = actor in roles['creators']
    else:
        assigned = roles['executors'].get(actor, [])
        allowed = '*' in assigned or role in assigned
    if not allowed:
        raise ValueError('请使用决策配置指定的身份和角色执行此操作。')


def add(value, title, why, options, *, detail='', recommend=None, task=None, page=None, now=None, actor='Claude'):
    """Claude 出一张。value 是 总览.json 的内容（调用方负责加锁写回）。"""
    authorize(value, actor, 'add')
    title, why = str(title or '').strip(), str(why or '').strip()
    options = [str(o).strip() for o in options or [] if str(o).strip()]
    if not title or len(title) > 40:
        raise ValueError('决策标题要有，最多 40 字：写成一个问句，例如“下一阶段明天开吗”')
    if not 2 <= len(options) <= 4 or any(len(o) > 30 for o in options):
        raise ValueError('选项 2–4 个，每个最多 30 字')
    if recommend is not None and not (type(recommend) is int and 0 <= recommend < len(options)):
        raise ValueError('推荐项要是选项的序号（从 0 数）')
    row = dict(id=secrets.token_hex(4), title=title, why=why[:200], detail=str(detail or '')[:2000], options=options,
               recommend=recommend, task=task, page=page, by=actor, created_at=stamp(now), chosen=None, chosen_at=None, note='', acked_at=None)
    value.setdefault('decisions', []).append(row)
    return row


def pending(value):
    """project owner 还没选的（看板最上面那张从这里挑）。"""
    return [d for d in value.get('decisions', []) if d.get('by') in policy(value)['creators'] and d.get('chosen') is None and not d.get('acked_at')]


def answered(value):
    """project owner 选了、Claude 还没处理的（Claude 醒来要读）。"""
    return [d for d in value.get('decisions', []) if d.get('chosen') is not None and not d.get('acked_at')]


def choose(root, actor, payload, *, now=None):
    Rejected = _rejected()
    if not isinstance(payload, dict) or set(payload) - {'id', 'option', 'note'}:
        raise Rejected('请选一个选项。', 400)
    did, option, note = payload.get('id'), payload.get('option'), payload.get('note') or ''
    if not isinstance(did, str) or not re.fullmatch(r'[a-f0-9]{8}', did) or type(option) is not int:
        raise Rejected('请选一个选项。', 400)
    if not isinstance(note, str) or len(note.strip()) > 80:
        raise Rejected('补充一句，最多 80 字。', 400)
    if now is not None and (type(now) not in (int, float) or not math.isfinite(now)):
        raise ValueError('Use a finite clock')
    path = Path(root) / 'overview.json'
    with storage.locked(root):
        value = json.loads(path.read_bytes())
        roles = policy(value)
        if actor != roles['chooser']:
            raise Rejected('请使用决策配置指定的选择人身份。', 403)
        row = next((d for d in value.get('decisions', []) if d.get('id') == did), None)
        if row is None:
            raise Rejected('这张决策卡已经不在了。', 404)
        if row.get('by') not in roles['creators']:
            raise Rejected('请选择配置中的出题人提交的决策。', 403)
        if row.get('acked_at'):
            raise Rejected('Claude 已经照这个选择办了，改主意直接在讨论室说。', 409)
        if not 0 <= option < len(row.get('options', [])):
            raise Rejected('请选卡上的选项。', 400)
        if row.get('chosen') == option and row.get('note', '') == note.strip():
            return dict(ok=True, decision=row)
        fields = dict(chosen=option, chosen_at=stamp(now), note=note.strip(),
                      selection_revision=row.get('selection_revision', 0) + 1)
        def apply(current):
            for d in current.get('decisions', []):
                if d.get('id') == did:
                    d.update(fields)
        apply(value)
        storage.write(path,value)
        row.update(fields)
    return dict(ok=True, decision=row)


def selection_key(row):
    import hashlib
    return hashlib.sha256(json.dumps([row['id'],row.get('selection_revision',0),row['chosen'],row.get('note','')],ensure_ascii=False).encode()).hexdigest()


def claim(root,identifier,actor,next_action,*,role=None,now=None):
    clock=time.time() if now is None else now
    if not isinstance(next_action,str) or not next_action.strip():raise ValueError('Concrete next action required')
    with storage.locked(root):
        path=Path(root)/'overview.json';value=storage.read(path);authorize(value,actor,'claim',role)
        row=next(d for d in value['decisions'] if d['id']==identifier)
        if row.get('chosen') is None or row.get('acked_at'):raise ValueError('Open selected decision required')
        identity=selection_key(row);old=row.get('execution',{})
        if old.get('selection_key')==identity:
            if (old['by'],old.get('role'))!=(actor,role) and old['expected_unix']>clock:raise ValueError('Current execution claim is active')
            if (old['by'],old.get('role'))==(actor,role):return old
        row['execution']=dict(by=actor,role=role,selection_key=identity,next_action=next_action,claimed_at=stamp(clock),expected_unix=clock+1200)
        storage.write(path,value);return row['execution']


def finish(root,identifier,actor,artifact,*,role=None):
    with storage.locked(root):
        path=Path(root)/'overview.json';value=storage.read(path);authorize(value,actor,'ack',role)
        row=next(d for d in value['decisions'] if d['id']==identifier);old=row.get('execution',{})
        if old.get('selection_key')!=selection_key(row) or (old.get('by'),old.get('role'))!=(actor,role):raise ValueError('Claim the current selection as its executor')
        evidence=delivery.binding(Path(root),artifact)
        if row.get('acked_at'):
            if row.get('ack_evidence')!=evidence:raise ValueError('Completed decision evidence is frozen')
            return row
        row.update(acked_at=stamp(),acked_by=actor,ack_evidence=evidence,acked_selection_key=selection_key(row));storage.write(path,value);return row
