"""Portable job tickets and pure resource admission; transport is explicit."""
import math
import inspect
from pathlib import PurePosixPath
import re
import shlex

IDENTIFIER=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')


def identifier(value):
    if not isinstance(value,str) or not IDENTIFIER.fullmatch(value):
        raise ValueError('作业和任务编号使用字母、数字、点、横线或下划线，并以字母或数字开头。')
    return value


def positive(value,name,zero=False):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0 or (value==0 and not zero):
        raise ValueError(name+' 使用有限的'+('非负数。' if zero else '正数。'))
    return value


def cards(value):
    if not isinstance(value,list) or not value or any(type(c) is not int or c<0 or c>=128 for c in value) or len(set(value))!=len(value):
        raise ValueError('允许卡列表填写互异的 0–127 整数，至少指定一张。')
    return list(value)


def posix_path(value):
    if not isinstance(value,str) or not value.startswith('/') or value.startswith('//') or any(c in value for c in '\x00\r\n') or '..' in PurePosixPath(value).parts:
        raise ValueError('服务器目录填写绝对 POSIX 路径。')
    return value


def ticket(value):
    if not isinstance(value,dict):raise ValueError('作业参数使用对象。')
    row=dict(value)
    for key in ('id','task','job_group'):identifier(row.get(key))
    row['cwd']=posix_path(row.get('cwd'))
    for key in ('cmd','next'):
        if not isinstance(row.get(key),str) or not row[key].strip() or '\x00' in row[key]:
            raise ValueError(key+' 填写具体内容。')
    if re.search(r'(?<![\w/])[A-Za-z]:[\\/]',row['cmd']):raise ValueError('作业命令使用服务器路径。')
    for key in ('vram_gb','mem_gb','max_seconds'):positive(row.get(key),key)
    if type(row.get('priority')) is not int or row['priority']<0:raise ValueError('优先级填写非负整数。')
    row['allowed_cards']=cards(row.get('allowed_cards'))
    return row


def admission(job,policy,sample,*,now,phase='loading'):
    """New loads use measured free resources; running guards keep their own checks."""
    positive(now,'now',zero=True)
    if phase=='running':return dict(eligible=[],reasons=[],continue_run=True,**{'continue':True})
    if phase!='loading':raise ValueError('phase 使用 loading 或 running。')
    pool=set(cards(policy.get('cards')))&set(cards(job.get('allowed_cards')))
    need=positive(job.get('vram_gb'),'vram_gb')
    ram=positive(job.get('mem_gb'),'mem_gb')
    disk=positive(job.get('disk_gb',0),'disk_gb',zero=True)
    reserve=positive(policy.get('disk_reserve_gb',0),'disk_reserve_gb',zero=True)
    loading=positive(policy.get('loading_reserve_gb',0),'loading_reserve_gb',zero=True)
    max_age=positive(policy.get('max_age_seconds',120),'max_age_seconds')
    limit=policy.get('max_cards',len(pool))
    if type(limit) is not int or limit<0:raise ValueError('max_cards 填写非负整数。')
    at=sample.get('at');reasons=[]
    if type(at) not in (int,float) or not math.isfinite(at) or not 0<=now-at<=max_age:reasons.append('刷新资源采样')
    def enough(key,minimum):
        value=sample.get(key)
        return type(value) in (int,float) and math.isfinite(value) and value>=minimum
    if not enough('ram_free_gb',ram):reasons.append('等待可用内存')
    if not enough('disk_free_gb',disk+reserve):reasons.append('等待磁盘余量')
    running=sample.get('running_cards',[])
    if not isinstance(running,list) or any(type(c) is not int or c<0 for c in running):raise ValueError('running_cards 填写实际卡号。')
    if len(set(running))>=limit:reasons.append('等待并发名额')
    eligible=[]
    if not reasons:
        for gpu in sample.get('gpus',[]):
            free=gpu.get('free_gb');card=gpu.get('card')
            if type(card) is int and card in pool and card not in running and type(free) in (int,float) and math.isfinite(free) and free>=need+loading:
                eligible.append(card)
    if not eligible and not reasons:reasons.append('等待允许卡达到显存要求')
    return dict(eligible=sorted(set(eligible)),reasons=reasons,continue_run=None)


def remote_python():
    """Self-contained atomic publisher; a shared submission lock serializes clients."""
    validators='\n\n'.join(inspect.getsource(fn) for fn in (identifier,positive,cards,posix_path,ticket))
    return 'import math\nfrom pathlib import PurePosixPath\nimport re\nIDENTIFIER=re.compile('+repr(IDENTIFIER.pattern)+')\n'+validators+'''\nimport json,os,re,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]).resolve(strict=True);job=sys.argv[2]
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',job):raise SystemExit(5)
try:value=ticket(json.loads(sys.stdin.read(1048576)))
except (ValueError,TypeError):raise SystemExit(5)
if not isinstance(value,dict) or value.get('id')!=job:raise SystemExit(5)
if not all((root/name).is_dir() for name in ('pending','running','done')):raise SystemExit(5)
with (root/'.submission.lock').open('a+b') as lock:
 if os.name=='nt':
  import msvcrt
  lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
  msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
 else:
  import fcntl
  fcntl.flock(lock,fcntl.LOCK_EX)
 if any((root/name/(job+'.json')).exists() for name in ('pending','running','done','failed')):
  print('已有同名作业：'+job);raise SystemExit(3)
 # A ticket whose command is identical to one already pending or running is a duplicate; retry a failed ticket under a new id.
 for name in ('pending','running'):
  for other in (root/name).glob('*.json'):
   try:same=json.loads(other.read_text(encoding='utf-8')).get('cmd')==value.get('cmd')
   except (OSError,ValueError):same=False
   if same:print('同一条命令已在排：'+name+'/'+other.name);raise SystemExit(3)
 temporary=None
 try:
  fd,temporary=tempfile.mkstemp(prefix='.'+job+'-',suffix='.tmp',dir=root/'pending')
  with os.fdopen(fd,'w',encoding='utf-8') as stream:
   json.dump(value,stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
  os.replace(temporary,root/'pending'/(job+'.json'));temporary=None
 finally:
  if temporary:Path(temporary).unlink(missing_ok=True)
 print('已入队 '+job)
'''


def remote_command(queue_root,job_id):
    # Login shells differ (tcsh rejects a multi-line quoted program), so ship the program as one base64 line and exec it remotely; sys.argv stays (root, job).
    import base64
    packed=base64.b64encode(remote_python().encode('utf-8')).decode('ascii')
    return ' '.join(['python3','-c','"import base64;exec(base64.b64decode(\'%s\').decode(\'utf-8\'))"'%packed,
                     shlex.quote(posix_path(queue_root)),shlex.quote(identifier(job_id))])
