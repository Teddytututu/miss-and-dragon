"""One source for patrol defaults and small, locked user overrides."""
from datetime import datetime, timedelta, timezone
import copy, re, time
from pathlib import Path
from . import storage

# id, Chinese name, English name, actor, kind, minutes, description, rationale
DEFAULTS = [
 ('night_watch','守夜人','Night watch','program','program',10,'看任务、空卡与截止的变化','程序巡检省额度，十分钟内发现空卡'),
 ('service_guard','服务卫士','Service guard','program','program',5,'服务停止时重新启动','服务可用时所有人才能看到看板'),
 ('event_cooldown','事件叫醒','Event wake','program → Dragon','program',5,'事件立即处理，同会话按此间隔合并叫醒','合并连续事件，减少重复叫醒'),
 ('execution','龙娘 · 执行','Dragon · execution','GPT','model',60,'实验与资源兜底巡检','空转代价高，按额度调整'),
 ('front','龙娘 · 前台','Dragon · front desk','GPT','model',60,'接消息与分派的兜底巡检','消息由事件叫醒，定时补漏'),
 ('lead','大小姐巡检','Miss patrol','Claude','model',120,'验收、回答问题与定方向','按额度分配，提及时优先回应'),
 ('chores','龙娘 · 杂活','Dragon · chores','GPT','model',120,'界面、文档与清理的兜底巡检','按额度调整日常维护频率'),
 ('stall','任务卡住判定','Progress stall','program','program',60,'进度停止多久后提醒','一小时无进展时检查原因'),
 ('eta_overdue','预计完成过期提醒','ETA overdue','program','program',30,'预计完成时间过后多久提醒','给短时波动留出半小时'),
 ('patrol_overdue','巡检逾期提醒','Patrol overdue','program','program',15,'预定巡检时间过后多久提醒','超过一刻钟时提醒负责会话'),
 ('efficiency','额度与效率核对','Quota and efficiency','Claude','daily',None,'每天核对花费与成果','每天看一次哪类工作最费额度'),
 ('weekly_tidy','报告收纳整理','Weekly report tidy','Claude → GPT','weekly',None,'每个发现保留一张主卡，数据挂在下面','每周整理当前结论与入门材料'),
 ('weekly_rules','规则复盘','Weekly rule review','Claude','weekly',None,'把重复两次的错误写进程序','报告整理完成后复盘协作规则'),
]
IDS=[r[0] for r in DEFAULTS]
EN = {
 'night_watch':('Watch task, capacity and deadline changes','Cheap checks discover idle capacity within ten minutes'),
 'service_guard':('Restart a stopped local service','Keep the shared board available'),
 'event_cooldown':('Handle events immediately; coalesce wakes per session','Combine bursts into one wake'),
 'execution':('Fallback patrol for experiments and resources','Idle resources cost money; adjust to quota'),
 'front':('Fallback patrol for messages and routing','Events handle messages; patrol catches missed work'),
 'lead':('Review results, answer questions and choose direction','Budget quota; prioritize mentions'),
 'chores':('Fallback patrol for interface, documents and cleanup','Adjust routine maintenance to quota'),
 'stall':('Remind after progress stops for this long','Check the cause after an hour without progress'),
 'eta_overdue':('Grace period after the estimated finish','Allow thirty minutes for short fluctuations'),
 'patrol_overdue':('Grace period after a promised patrol','Remind the responsible session after fifteen minutes'),
 'efficiency':('Compare quota spending and useful results daily','Review the most expensive work once a day'),
 'weekly_tidy':('One main card per finding, with supporting file links','Keep current conclusions and newcomer reading together'),
 'weekly_rules':('Turn repeated mistakes into program checks','Review rules after the report tidy is acknowledged'),
}

def read(root):
    return storage.read(Path(root)/'attachments/cadence.json',{'overrides':{},'order':IDS[:]})

def _clock(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',value):raise ValueError('Time must be HH:MM')
    return value

def validate(payload,current=None):
    if not isinstance(payload,dict) or set(payload)-{'overrides','order'}:raise ValueError('Use overrides and order')
    value=copy.deepcopy(current or {'overrides':{},'order':IDS[:]})
    overrides=payload.get('overrides',{})
    if not isinstance(overrides,dict):raise ValueError('Overrides must be an object')
    for key,setting in overrides.items():
        if key not in IDS:raise ValueError('Choose a cadence item')
        if setting is None:value.setdefault('overrides',{}).pop(key,None);continue
        if not isinstance(setting,dict):raise ValueError('Cadence setting must be an object')
        kind=next(r[4] for r in DEFAULTS if r[0]==key)
        if kind in ('model','program'):
            n=setting.get('minutes');lo,hi=(20,1440) if kind=='model' else (1,60)
            if set(setting)!={'minutes'} or isinstance(n,bool) or not isinstance(n,int) or not lo<=n<=hi:raise ValueError(f'Minutes must be an integer from {lo} to {hi}')
        else:
            if set(setting)-{'weekday','time','after'}:raise ValueError('Use weekday, time and after')
            if 'time' in setting:_clock(setting['time'])
            day=setting.get('weekday',6)
            if isinstance(day,bool) or not isinstance(day,int) or not 0<=day<=6:raise ValueError('Weekday must be 0 through 6')
            if 'after' in setting and (key!='weekly_rules' or setting['after'] not in (None,'weekly_tidy')):raise ValueError('Rule review can follow weekly_tidy')
            if not setting:raise ValueError('Provide a time')
        value.setdefault('overrides',{})[key]=dict(setting)
    if 'order' in payload:
        order=payload['order']
        if not isinstance(order,list) or len(order)!=len(IDS) or set(order)!=set(IDS):raise ValueError('Order must include each item once')
        value['order']=order[:]
    return value

def configure(root,payload):
    root=Path(root)
    with storage.locked(root):storage.write(root/'attachments/cadence.json',validate(payload,read(root)))
    from . import scheduler
    scheduler.refresh(root)
    return view(root)

def configure_plans(root,plans):
    if not isinstance(plans,dict) or set(plans)-{'Claude','GPT'}:raise ValueError('Choose Claude and GPT plans')
    for p in plans.values():
        if not isinstance(p,dict) or set(p)!={'subscriptions','tier'} or isinstance(p['subscriptions'],bool) or not isinstance(p['subscriptions'],int) or not 0<=p['subscriptions']<=100 or p['tier'] not in ('free','normal','highest'):raise ValueError('Plans use subscriptions (0–100) and tier (free, normal, highest)')
    def update(v):v.setdefault('plans',{}).update(plans)
    storage.update_json(Path(root),'attachments/onboarding.json',update)
    return view(root)

def minutes(root,key):
    default=next(r[5] for r in DEFAULTS if r[0]==key)
    return read(root).get('overrides',{}).get(key,{}).get('minutes',default)

def timing(config,key):
    base={'time':'20:00','weekday':6}
    if key=='efficiency':base={'time':'19:00'}
    if key=='weekly_rules':base['after']='weekly_tidy'
    return dict(base,**config.get('overrides',{}).get(key,{}))

def due(config,key,at):
    """Latest local calendar occurrence; weekly rules can follow tidy acknowledgement."""
    spec=timing(config,key);local=datetime.fromtimestamp(at,timezone.utc).astimezone()
    hour,minute=map(int,spec['time'].split(':'))
    point=local.replace(hour=hour,minute=minute,second=0,microsecond=0)
    if key!='efficiency':point-=timedelta(days=(point.weekday()-spec['weekday'])%7)
    if point.timestamp()>at:point-=timedelta(days=1 if key=='efficiency' else 7)
    return point.timestamp(),point.strftime('%Y-%m-%d')

def view(root,now=None):
    root=Path(root);at=time.time() if now is None else now;config=read(root)
    plans=storage.read(root/'attachments/onboarding.json',{}).get('plans',{})
    schedule=storage.read(root/'attachments/schedule.json',{});items=[]
    for key,zh,en,actor,kind,base,desc,why in DEFAULTS:
        setting=config.get('overrides',{}).get(key,{});plan=plans.get(actor,{})
        suggested=base
        if kind=='model':suggested=20 if plan.get('subscriptions',0)>1 or plan.get('tier')=='highest' else 240 if plan.get('tier')=='free' else base
        row=dict(id=key,name=zh,name_en=en,actor=actor,kind=kind,description=desc,reason=why,description_en=EN[key][0],reason_en=EN[key][1],default_minutes=base,suggested_minutes=suggested,override=setting or None)
        if kind in ('program','model'):
            row['minutes']=setting.get('minutes',base)
            session=schedule.get('sessions',{}).get(key,{})
            last=storage.read(root/'attachments/night-watch/timer.json',{}).get('last_patrol') if key=='night_watch' else None
            row['next_wake']=session.get('next_wake') if kind=='model' else last+row['minutes']*60 if last else None
        else:
            row.update(timing(config,key));latest,_=due(config,key,at);row['next_wake']=latest+(86400 if kind=='daily' else 604800)
            if row.get('after'):row['next_wake']=None
        items.append(row)
    order=config.get('order',IDS)
    return dict(items=sorted(items,key=lambda r:order.index(r['id'])),order=order,default_order=IDS[:],plans=plans)
