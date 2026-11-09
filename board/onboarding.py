"""Observable assistant setup, distinct from a running HTTP service."""
from pathlib import Path
from . import storage, provider_bridge, scheduler, project, assets
import shutil, subprocess, uuid
NAMES=('avatar','calm','surprised','wink','smile','shy','teary')
EMOTE_PROMPT='要不要下载 B 站表情包（约 225 个，只存在你本机）'
VOICE_PROMPT='要不要开启语音朗读（需要 NVIDIA 显卡、显存至少 6 GiB、磁盘余量至少 10 GiB）'
NIGHT_WATCH_PROMPT='要不要装守夜人（每 10 分钟查一次，可随时关）'
VOICE_PROJECT_URL='https://github.com/FunAudioLLM/CosyVoice'
VOICE_INSTALL_URL='https://github.com/FunAudioLLM/CosyVoice#installation'
VOICE_LICENSE='Apache-2.0'
VOICE_MIN_GPU_GIB=6
VOICE_MIN_DISK_GIB=10
PREFERENCES='attachments/onboarding.json'


class ImageDependencyError(ValueError):
    """Pixel inspection requires the optional image dependency."""


def pillow_image():
    """Load image support only when an operation needs to inspect pixels."""
    try:
        from PIL import Image
    except ModuleNotFoundError as error:
        if error.name not in ['PIL', 'PIL.Image']:
            raise
        raise ImageDependencyError('Image features require Pillow. Install project dependencies: python -m pip install -r requirements.txt') from None
    return Image


def emote_preferences(root):
    saved=storage.read(storage.relative_file(root,PREFERENCES),{}).get('emotes',{})
    choice=saved.get('choice') if saved.get('choice') in ['download','unicode'] else None
    return dict(saved,choice=choice,mode='download' if choice=='download' and saved.get('mode')=='download' else 'unicode',
                decision_required=choice is None,prompt=EMOTE_PROMPT)


def configure_emotes(root,choice=None,*,installer=None):
    """Only an explicit recorded answer enables the optional downloader; never read stdin."""
    if choice not in [None,'download','unicode']:raise ValueError('Choose download or unicode')
    root=Path(root);token=uuid.uuid4().hex
    with storage.locked(root):
        path=storage.relative_file(root,PREFERENCES);settings=storage.read(path,{})
        saved=settings.setdefault('emotes',{});show_prompt=choice is None and not saved.get('prompt_shown') and not saved.get('choice')
        saved['prompt_shown']=True
        if choice is not None:saved.update(choice=choice,source='explicit-cli')
        download=saved.get('choice')=='download'
        saved.update(mode='unicode',status='installing' if download else 'selected' if saved.get('choice') else 'awaiting-answer',attempt=token)
        saved.pop('error',None)
        storage.write(path,settings)
    if download:
        try:
            if installer is None:
                pillow_image()
                from scripts.install_emotes import install
                installer=install
            report=installer(root)
            if not isinstance(report,dict) or any(type(report.get(k)) is not int or report[k]<0 for k in ['downloaded','reused','failed']):
                raise ValueError('Emote installer returned an invalid report')
            success=report['failed']==0 and report['downloaded']+report['reused']>0
            update=dict(report=report,mode='download' if success else 'unicode',status='ready' if success else 'fallback')
        except (OSError,ValueError,subprocess.SubprocessError) as error:
            update=dict(mode='unicode',status='fallback',error=str(error))
        with storage.locked(root):
            settings=storage.read(path,{});saved=settings.get('emotes',{})
            if saved.get('attempt')==token:saved.update(update);storage.write(path,settings)
    return dict(emote_preferences(root),show_prompt=show_prompt)


def _nvidia_memory_mib():
    """Return the memory reported by each NVIDIA GPU, keeping setup offline-safe."""
    executable=shutil.which('nvidia-smi')
    if not executable:return []
    try:
        result=subprocess.run(
            [executable,'--query-gpu=memory.total','--format=csv,noheader,nounits'],
            capture_output=True,text=True,encoding='utf-8',timeout=5,
        )
    except (OSError,ValueError,AssertionError,subprocess.SubprocessError):
        return []
    values=[]
    for line in (result.stdout or '').splitlines():
        token=line.strip().split()[0] if line.strip() else ''
        try:
            value=float(token)
        except ValueError:
            continue
        if value>0:values.append(value)
    return values


def _free_disk_bytes(root):
    path=Path(root).resolve()
    while not path.exists() and path != path.parent:path=path.parent
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return 0


def voice_hardware(root,*,gpu_probe=None,disk_probe=None):
    """Describe the local prerequisites for the optional voice reader."""
    memories=list((gpu_probe or _nvidia_memory_mib)())
    free_bytes=(disk_probe or _free_disk_bytes)(root)
    largest=max(memories,default=0)/1024
    free_gib=free_bytes/(1024**3)
    eligible=bool(memories) and largest>=VOICE_MIN_GPU_GIB and free_gib>=VOICE_MIN_DISK_GIB
    return dict(
        has_nvidia=bool(memories),gpu_count=len(memories),gpu_memory_gib=round(largest,2),
        disk_free_gib=round(free_gib,2),min_gpu_gib=VOICE_MIN_GPU_GIB,
        min_disk_gib=VOICE_MIN_DISK_GIB,eligible=eligible,
    )


def voice_preferences(root,*,hardware=None,detect_hardware=True):
    saved=storage.read(storage.relative_file(root,PREFERENCES),{}).get('voice',{})
    if hardware is None and not detect_hardware:
        hardware=saved.get('eligibility') or dict(
            has_nvidia=False,gpu_count=0,gpu_memory_gib=0,disk_free_gib=0,
            min_gpu_gib=VOICE_MIN_GPU_GIB,min_disk_gib=VOICE_MIN_DISK_GIB,
            eligible=False,checked=False,
        )
        choice=saved.get('choice') if saved.get('choice') in ['enable','disable'] else None
        return dict(
            saved,choice=choice,mode=saved.get('mode','disabled'),
            decision_required=False,prompt=VOICE_PROMPT,hardware=hardware,
            project_url=VOICE_PROJECT_URL,install_url=VOICE_INSTALL_URL,
            license=VOICE_LICENSE,
        )
    hardware=hardware or voice_hardware(root)
    choice=saved.get('choice') if saved.get('choice') in ['enable','disable'] else None
    if not hardware['eligible']:
        choice='disable'
    return dict(
        saved,choice=choice,mode='enabled' if choice=='enable' and hardware['eligible'] else 'disabled',
        decision_required=bool(hardware['eligible'] and choice is None),
        prompt=VOICE_PROMPT,hardware=hardware,project_url=VOICE_PROJECT_URL,
        install_url=VOICE_INSTALL_URL,license=VOICE_LICENSE,
    )


def configure_voice(root,choice=None,*,gpu_probe=None,disk_probe=None):
    """Record an explicit voice choice, or default to disabled on unsupported hardware."""
    if choice not in [None,'enable','disable']:raise ValueError('Choose enable or disable')
    root=Path(root);hardware=voice_hardware(root,gpu_probe=gpu_probe,disk_probe=disk_probe)
    with storage.locked(root):
        path=storage.relative_file(root,PREFERENCES);settings=storage.read(path,{})
        saved=settings.setdefault('voice',{})
        prior=saved.get('choice') if saved.get('choice') in ['enable','disable'] else None
        show_prompt=bool(hardware['eligible'] and choice is None and prior is None)
        if choice is not None:
            saved.update(choice=choice,source='explicit-cli')
        elif not hardware['eligible']:
            saved.update(choice='disable',source='hardware-default')
        saved.update(
            mode='enabled' if saved.get('choice')=='enable' and hardware['eligible'] else 'disabled',
            status='selected' if saved.get('choice') else 'awaiting-answer',
            eligibility=hardware,
        )
        storage.write(path,settings)
    result=voice_preferences(root,hardware=hardware)
    result['show_prompt']=show_prompt
    return result


def night_watch_preferences(root):
    saved=storage.read(storage.relative_file(root,PREFERENCES),{}).get('night_watch',{})
    choice=saved.get('choice') if saved.get('choice') in ['install','disable'] else None
    return dict(saved,choice=choice,decision_required=choice is None,prompt=NIGHT_WATCH_PROMPT)


def configure_night_watch(root,choice=None):
    """Record the optional watcher choice; the installer runs only after consent."""
    if choice not in [None,'install','disable']:raise ValueError('Choose install or disable')
    root=Path(root)
    with storage.locked(root):
        path=storage.relative_file(root,PREFERENCES);settings=storage.read(path,{})
        saved=settings.setdefault('night_watch',{})
        prior=saved.get('choice') if saved.get('choice') in ['install','disable'] else None
        show_prompt=choice is None and prior is None and not saved.get('prompt_shown')
        saved['prompt_shown']=True
        if choice is not None:
            saved.update(choice=choice,source='explicit-cli')
        elif prior is None:
            saved.update(choice='disable',source='default')
        if saved.get('choice')=='disable' and saved.get('status') not in ['installed','registered','manual','preview']:
            saved['status']='disabled'
        storage.write(path,settings)
    result=night_watch_preferences(root);result['show_prompt']=show_prompt
    return result


def bundled_artwork():
    """Packaged PNGs satisfy the normal setup; custom generation stays optional."""
    try:
        Image=pillow_image()
    except ImageDependencyError as error:
        Image=None;dependency_reason=str(error)
    rows=[]
    for role in ['Claude','GPT']:
        name=assets.avatars().get(role,{}).get('file','');path=assets.ROOT/'board/art'/name;valid=False;reason='bundled character PNG'
        if Image is None:
            reason=dependency_reason
        else:
            try:
                with Image.open(path) as image:
                    valid=image.format=='PNG' and min(image.size)>0
                    image.verify()
            except (OSError,ValueError):pass
        rows.append(dict(role=role,file='board/art/'+name,valid=valid,reason=reason))
    return dict(mode='bundled',expected=len(rows),valid=sum(row['valid'] for row in rows),files=rows)

def artwork(root,agent):
    import xml.etree.ElementTree as ET
    expected=[(role,name,'png') for role in ['Claude','GPT'] for name in NAMES] if agent=='GPT' else [('Claude',name,'svg') for name in NAMES]
    rows=[]
    for role,name,extension in expected:
        path=Path(root)/'attachments/generated'/role/(name+'.'+extension);valid=False;reason='optional replacement output'
        if path.is_file():
            try:
                if extension=='png':
                    Image=pillow_image()
                    with Image.open(path) as im:
                        alpha=im.getchannel('A').getextrema() if 'A' in im.getbands() else (255,255)
                        valid=im.format=='PNG' and min(im.size)>=256 and alpha[0]<255 and alpha[1]>0
                        reason='transparent PNG' if valid else 'use a transparent PNG at least 256 pixels square'
                else:
                    tree=ET.fromstring(path.read_bytes())
                    valid=tree.tag.rsplit('}',1)[-1]=='svg' and len(list(tree))>0
                    reason='original SVG output' if valid else 'use an SVG drawing'
            except ImageDependencyError as error:reason=str(error)
            except (OSError,ValueError,ET.ParseError):reason='readable image required'
        rows.append(dict(file=str(path.relative_to(root)),valid=valid,reason=reason))
    return dict(mode='optional-custom',required=False,expected=len(rows),valid=sum(row['valid'] for row in rows),files=rows)

def status(root,agent):
    if agent not in ['GPT','Claude']:raise ValueError('Choose GPT or Claude')
    art=bundled_artwork();quota=storage.read(Path(root)/'attachments/agents.json',{}).get(agent,{})
    native=provider_bridge.controls(root).get(agent,{})
    all_posts=project.all_posts(root);posts=[p for p in all_posts if p['author']==agent and project.session_message(p)]
    counterpart='Claude' if agent=='GPT' else 'GPT'
    targets={p['id'] for p in all_posts if p['author']==counterpart and project.session_message(p)}
    reactions=storage.lines(Path(root)/'attachments/discussion/reactions.jsonl')
    goal=native.get('goal',{});patrol=native.get('patrol',{})
    valid_goal=bool(goal.get('thread_id') and goal.get('status') in ['active','complete'])
    valid_patrol=bool(patrol.get('id') and patrol.get('status') in ['active','scheduled-session','running-session'])
    active=set()
    for row in reactions:
        key=(row.get('message_id'),row.get('actor'),row.get('emoji'))
        if row.get('active'):active.add(key)
        else:active.discard(key)
    checks=dict(artwork=art['expected']==art['valid'],quota=bool(quota.get('updated_at') and quota.get('source')),
                native_control=valid_goal or agent=='Claude' and valid_patrol,
                patrol=valid_patrol,
                opening=bool(posts),reply=any(p.get('parent_id') in targets for p in posts),
                reaction=any(mid in targets and actor==agent for mid,actor,emoji in active))
    return dict(agent=agent,artwork=art,generated_artwork=artwork(root,agent),emotes=emote_preferences(root),quota_reported=checks['quota'],native_control=checks['native_control'],
                checks=checks,pending=[k for k,v in checks.items() if not v],complete=all(checks.values()),
                local_ready=all(value for name,value in checks.items() if name not in ['reply','reaction']),
                waiting_on=counterpart if not targets else None,
                next=('Finish independent setup, then await '+counterpart+' actual session message for reply and reaction' if not targets else 'Complete pending setup steps using actual session messages and native controls'))

def prepare(root,agent):
    scheduler.report(root,agent,**provider_bridge.quota(root,agent))
    result=status(root,agent)
    storage.update_json(root,'attachments/state.json',lambda s:s.setdefault('assistant_setup',{}).update({agent:result}))
    return result
