"""Read-only per-card view of GPU observations and current queue jobs.

The collector is the runtime authority. Queue metadata supplies a job and ETA
only when its task signature or PID agrees with an observed own-account process.
No GPU history or queue mutation is produced here.
"""
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import time
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler, Request

TZ = timezone.utc
MAX_BYTES = 4 * 1024 * 1024
QUEUE_MAX_AGE = 20 * 60
def default_profile():return {}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _stamp(value):
    if _number(value):
        return float(value)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return (dt if dt.tzinfo else dt.replace(tzinfo=TZ)).timestamp()
        except ValueError:
            pass
    return None


def _iso(value):
    return datetime.fromtimestamp(value, TZ).isoformat() if value is not None else None


def _fresh(value, now, age):
    at = _stamp(value)
    return at is not None and -60 <= now-at <= age


def _card(value):
    if isinstance(value, bool):
        return None
    try:
        card = int(value)
        return card if 0 <= card < 128 and str(card) == str(value) else None
    except (TypeError, ValueError):
        return None


def _ours(process):
    return process.get('relation') in {'same_login', 'inferred_same_login'}


def _task(command, profile):
    resolver=profile.get('task_resolver')
    if resolver:return resolver(command)
    match=re.search(r'(?<![A-Za-z0-9])T(\d{3})(?:R)?(?=[^0-9]|$)',str(command or ''),re.I)
    return 'T'+match[1] if match else None


def _detail(task, command, job_id, profile):
    resolver=profile.get('detail_resolver')
    if resolver:return resolver(task,command,job_id)
    return profile.get('titles',{}).get(task,task or '进程运行中')


def project(queue, gpu_status, now=None, task_titles=None, profile=None):
    """Pure projection; inputs are untouched and timestamps use independent freshness."""
    now = time.time() if now is None else now
    queue = queue if isinstance(queue, dict) else {}
    gpu_status = gpu_status if isinstance(gpu_status, dict) else {}
    profile = default_profile() if profile is None else dict(profile)
    titles = dict(profile.get('titles', {}), **(task_titles or {}))
    profile['titles'] = titles
    host_name = profile.get('host', '')
    host = next((h for h in gpu_status.get('hosts', []) if isinstance(h, dict) and h.get('name') == host_name), {})
    observed = _stamp(host.get('last_success'))
    max_age = gpu_status.get('stale_after_seconds', 125)
    max_age = max_age if _number(max_age) and max_age > 0 else 125
    live = bool(host) and host.get('status') == 'ok' and not host.get('stale') and _fresh(observed, now, max_age)
    queue_at = queue.get('observed_at') or queue.get('at')
    queue_live = (_fresh(queue_at, now, QUEUE_MAX_AGE) and not queue.get('error')
                  and not queue.get('queue_support_error') and queue.get('admission_fresh') is not False
                  and queue.get('runtime_verified') is not False)
    config = queue.get('cards') or {}
    config = config.get('configured', []) if isinstance(config, dict) else config
    configured = {card for value in config if (card := _card(value)) is not None} if isinstance(config, list) else set()
    samples = {card: g for g in host.get('gpus', []) if isinstance(g, dict) and (card := _card(g.get('index'))) is not None}
    own_cards = {c for c, g in samples.items() if any(_ours(p) for p in g.get('processes', []) if isinstance(p, dict))}
    forecasts = [j for j in queue.get('job_forecasts', []) if isinstance(j, dict) and j.get('state') == 'running'] if queue_live else []
    card_details = {item.get('card'): item for item in queue.get('card_status', []) if isinstance(item, dict)} if queue_live else {}
    
    # 改成：同类作业（id 里数字当通配）已经跑完的实测时长中位数，开始时间加上它；同类还没跑完过才退回上限。
    import re as _re, statistics as _st
    _fam = {}
    for j in queue.get('job_forecasts', []) if queue_live else []:
        if isinstance(j, dict) and j.get('state') == 'succeeded' and _number(j.get('started')) and _number(j.get('ended')) and j['ended'] > j['started']:
            _fam.setdefault(_re.sub(r'\d+', '#', str(j.get('id') or '')), []).append(j['ended'] - j['started'])
    family_seconds = {k: _st.median(v) for k, v in _fam.items() if v}
    rows = []
    for card in sorted(configured | own_cards | set(samples)):
        sample = samples.get(card)
        current = live and isinstance(sample, dict)
        processes = [p for p in (sample or {}).get('processes', []) if isinstance(p, dict)]
        own = [p for p in processes if _ours(p)] if current else []
        others = [p for p in processes if p.get('relation') == 'other' and p.get('username') not in profile.get('ignored_accounts', []) and not (_number(p.get('memory_mib')) and p['memory_mib'] < profile.get('other_memory_floor_mib', 0))] if current else []
        row = dict(card=card, configured=card in configured, outside_config=card not in configured,
                   state='stale' if host and sample else 'unavailable', state_label='采样更新中',
                   task=None, title='采样更新中', job=None, detail='等待最新显卡采样',
                   utilization_pct=None, memory_used_mib=None, memory_total_mib=None,
                   finish=None, finish_window=None, finish_label='随作业更新',
                   process_ids=[p.get('pid') for p in own], other_process_count=len(others),
                   queue_mismatch=False, observed_at=_iso(observed), queue_at=queue_at,
                   jobs=[], tasks=[], memory_free_mib=None, allowed_jobs=[], execution_profile=None, method=None, question=None)
        if not current:
            rows.append(row)
            continue
        for key in ('utilization_pct', 'memory_used_mib', 'memory_total_mib'):
            value = sample.get(key)
            row[key] = value if _number(value) else None
        if row['memory_total_mib'] is not None and row['memory_used_mib'] is not None:
            row['memory_free_mib'] = max(0, row['memory_total_mib'] - row['memory_used_mib'])
        row['allowed_jobs'] = card_details.get(card, {}).get('allowed', [])
        if own:
            detected = {_task(p.get('cmd'), profile) for p in own} - {None}
            own_pids = {str(p.get('pid')) for p in own if p.get('pid') is not None}
            candidates = [j for j in forecasts if _card(j.get('card')) == card]
            matched = [j for j in candidates if j.get('pid') is not None and
                       str(j['pid']) in own_pids and (not detected or j.get('task') in detected)]
            matched += [j for j in candidates if j.get('pid') is None and j.get('task') in detected]
            tasks = detected | {j.get('task') for j in matched if j.get('task')}
            row.update(state='mixed' if others else 'running', state_label='与其他账号共用' if others else '运行中',
                       task=next(iter(tasks)) if len(tasks) == 1 else None,
                       tasks=sorted(tasks), jobs=[j.get('id') for j in matched if j.get('id')],
                       queue_mismatch=bool(candidates and not matched),
                       title=' / '.join(titles.get(t, '实验 '+t) for t in sorted(tasks)) or '我方进程运行')
            command = ' '.join(str(p.get('cmd') or '') for p in own)
            job_id = matched[0].get('id') if len(matched) == 1 else None
            row.update(job=job_id, detail='；'.join(_detail(t, command, job_id, profile) for t in sorted(tasks)) or _detail(None, command, None, profile))
            if len(matched) == 1:
                details = matched[0]
                row.update(method=details.get('method'), question=details.get('question'), execution_profile=details.get('execution_profile'))
                readable = [text for text in (details.get('method'), details.get('question')) if text]
                if readable:
                    row['detail'] = ' · '.join(readable)
                if 'offload' in str(details.get('execution_profile') or ''):
                    row['detail'] += ' · 单Transformer块CPU offload'
                estimate = matched[0].get('finish')
                started = _stamp(matched[0].get('started_at') or matched[0].get('started'))
                median = family_seconds.get(_re.sub(r'\d+', '#', str(matched[0].get('id') or '')))
                if median and started and started + median >= now:
                    estimate = _iso(started + median)
                    row['finish_basis'] = '同类作业实测中位数 %d 分钟' % round(median / 60)
                end = _stamp(estimate)
                if end is not None and end >= now:
                    row.update(finish=estimate, finish_window=matched[0].get('finish_window'),
                               finish_label=datetime.fromtimestamp(end, TZ).strftime('%m月%d日 %H:%M'))
                elif end is not None:
                    row.update(finish=None, finish_label='已超过原估计，按新实测更新', estimate_overdue=True)
                else:
                    component = details.get('component_forecast') or {}
                    window = component.get('generation_window')
                    if isinstance(window, dict) and all(_number(window.get(k)) for k in ('low','high')) and window['high'] >= window['low']:
                        row['finish_label'] = '生成 ' + '—'.join(datetime.fromtimestamp(window[k], TZ).strftime('%H:%M') for k in ('low','high')) + '；导出/判分另计'
                        row['generation_window'] = {k: _iso(window[k]) for k in ('low','high')}
                    else:
                        row['finish_label'] = '首批完整导出后更新'
                    row['eta_conditions'] = component.get('unknowns', [])
            else:
                row['finish_label'] = '作业信息同步后更新'
        elif others:
            row.update(state='other', state_label='其他账号占用', title='其他账号占用',
                       detail='其他账号进程使用此卡', finish_label='由占用方释放')
        elif sample.get('process_status') != 'ok':
            row.update(state='unavailable', state_label='进程信息刷新中', title='进程信息刷新中',
                       detail='利用率与显存按最新采样显示')
        elif processes or (row['memory_used_mib'] or 0) > 16 or (row['utilization_pct'] or 0) > 0:
            row.update(state='occupied', state_label='占用归属同步中', title='占用归属同步中',
                       detail='显卡存在占用，任务归属正在同步')
        else:
            row.update(state='idle', state_label='空闲', title='空闲', detail='等待作业调度', finish_label='可安排作业')
        rows.append(row)
    return dict(rows=rows, observed_at=_iso(observed), queue_at=queue_at,
                generated_at=_iso(now), stale=not live, queue_stale=not queue_live,
                configured_cards=sorted(configured), host=host_name,
                running_count=sum(r['state'] in {'running', 'mixed'} for r in rows),
                refresh_seconds=gpu_status.get('interval_seconds', 60))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _clock(value):
    stamp = _stamp(value)
    return datetime.fromtimestamp(stamp, TZ).strftime('%H:%M') if stamp is not None else None


def ours_only(data, plan_stages=()):
    """Project own-account and idle cards; summarize other observations separately."""
    import re
    rows = []
    for row in data.get('rows', []):
        if row.get('state') not in ('running', 'mixed', 'idle'):
            continue
        row = dict(row)
        title = str(row.get('title') or '')
        parts = [s.strip() for s in str(row.get('detail') or '').split('·')]
        keep = [s for s in parts if re.search(r'[一-鿿]', s) and not re.search(r'T\d{3}|prompt-|offload|[A-Za-z]{3,}', s)
                and s[:4] != title[:4]]
        row['sub'] = keep[0] if keep and row.get('state') != 'idle' else ''
        window = row.get('generation_window') or {}
        now = _stamp(data.get('generated_at')) or 0
        end = _stamp(row.get('finish')) or _stamp(window.get('high'))
        row['eta_short'] = _clock(end) if end and end >= now else None
        
        # 一个作业只有几分钟，几点跑完没意义；改成它所在这一批的整批预计结束（四卡计划里该批阶段的 estimated_finish），跨天写“明天 / 月-日”
        job_ids = row.get('jobs') or ([row['job']] if row.get('job') else [])
        if job_ids:
            parts = str(job_ids[0]).split('-')
            if len(parts) > 2:
                stage_id = (row.get('task') or parts[0]) + '.batch_' + '-'.join(parts[:2]).split('-', 1)[1]
                stage = next((x for x in plan_stages if x.get('id') == stage_id and x.get('status') in ('scheduled', 'running') and x.get('estimated_finish')), None)
                batch_end = _stamp(stage.get('estimated_finish')) if stage else None
                if batch_end and batch_end >= now:
                    day = (datetime.fromtimestamp(batch_end, TZ).date() - datetime.fromtimestamp(now, TZ).date()).days
                    clock = _clock(batch_end)
                    row['eta_short'] = clock if day == 0 else ('明天 ' + clock if day == 1 else datetime.fromtimestamp(batch_end, TZ).strftime('%m-%d ') + clock)
                    row['finish_basis'] = '整批预计结束（四卡计划）'
                    row['batch_end_ms'] = int(batch_end * 1000)   
        row['wrapping_up'] = bool(_stamp(window.get('high')) and _stamp(window['high']) < now)
        row['estimate_overdue'] = bool(row.get('estimate_overdue') or (end and end < now and not row['wrapping_up']))
        rows.append(row)
    hidden = sum(r.get('state') == 'other' for r in data.get('rows', []))
    unknown = sum(r.get('state') in ('occupied', 'unavailable', 'stale') for r in data.get('rows', []))
    return dict(data, rows=rows, others_count=hidden, unknown_count=unknown)
