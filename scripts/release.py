"""Build a clean source archive from the explicit allowlist and project version."""
from pathlib import Path
import hashlib,json,re,zipfile,sys,uuid,shutil,getpass,socket,tomllib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_eol import check_eol
VERSION=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']

def write_report(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if path.exists():
        before=path.read_bytes()
        if before==raw:return
        history=path.parent/'history';history.mkdir(exist_ok=True)
        saved=history/(path.name+'.'+hashlib.sha256(before).hexdigest()+'.before')
        if not saved.exists():saved.write_bytes(before)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.partial')
    temp.write_bytes(raw);temp.replace(path)

def files():
    names=['.gitattributes','.gitignore','LICENSE','README.md','README.zh-CN.md','当前指令.md','AGENTS.md','CLAUDE.md','pyproject.toml','requirements.txt','发言.py']
    names += ['board/motion.css', 'board/motion.js']
    names += ['templates/report-kit/report_kit.py', 'templates/report-kit/check_report.py', 'templates/report-kit/example_build.py', 'templates/report-kit/example.html', 'templates/report-kit/README.md', 'templates/report-kit/FORMAT.md', 'templates/report-kit/FORMAT.zh-CN.md', 'docs/writing-reports.md', 'docs/writing-reports.zh-CN.md']
    names += ['tests/room-sizing.test.cjs']
    names+=['board/'+n for n in ['__init__.py','__main__.py','app.py','contacts.py','project.py','maintenance.py','scheduler.py','provider_bridge.py','onboarding.py','artwork.py','assets.py','environment.py','storage.py','workers.py','task_eta.py','eta-view.js','eta-view.css','fanart.css','index.html','identity.js','identity.css','discussion.js','discussion.css','room-extras.js','room-markdown.js','room-features.css','v02.js','v02.css','room-collection.js','mood.js','room-collection.css','help.html']]
    names+=['scripts/'+n for n in ['bootstrap.py','install_emotes.py','install_deps.py','verify.py','onboarding.py','provider_bridge.py','artwork.py','maintenance.py','task_number.py','workers.py','post_message.py','update_state.py','patrol.py','react.py','install-startup.ps1','watchdog.ps1','release.py','night_watch.py','run_queue.py','install_night_watch.py','install-night-watch.ps1']]
    names+=['docs/'+n for n in ['assets.md','agent-schedules.md','provider-bridge.md','patrol.md','quota.md','quota-scenarios.md','customization.md','private-repository.md','validation.md','third-party-notices.md','night-watch.md']]
    names+=['demo/overview.json','demo/board.md']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob('test_v0*.py')]
    names += ['board/visual.css','board/favicon-32.png','board/apple-touch-icon.png']
    names += ['board/agent_tools.py','board/notebook.css','board/XiaolaiSC-subset.woff2','board/Xiaolai-OFL.txt','CHANGELOG.md','CHANGELOG.zh-CN.md','docs/optional-event-bridge.md','docs/optional-resource-guard.md','docs/system-map.svg','docs/system-map-captions.md','docs/v04-pink.png','docs/v04-blue.png']
    names += ['board/i18n.js','board/i18n.css','board/help.en.html','tests/i18n.test.cjs','docs/languages.md','docs/languages.zh-CN.md']
    names += ['docs/images/'+name+'.svg' for name in ['question-life','who-decides','gpu-job-life','mistake-to-program']]
    names += ['scripts/make_readme_diagrams.py','docs/images/how-it-works.svg','docs/images/wake-loop.svg',
              'docs/images/avatar-lead.png','docs/images/avatar-executor.png','docs/images/avatar-owner.png',*[f'docs/images/screen-{theme}.{lang}.png' for theme in ['pink','blue'] for lang in ['en','zh-CN']]]
    names += ['scripts/diagram_labels.py','docs/images/mistake-to-program.zh-CN.svg','docs/images/how-it-works.zh-CN.svg','docs/images/wake-loop.zh-CN.svg','docs/images/cast.svg','docs/images/cast.zh-CN.svg']
    names += ['scripts/fonts/'+name for name in ['Caveat-Bold.ttf','Nunito-Bold.ttf','Nunito-Medium.ttf','OFL-Caveat.txt','OFL-Nunito.txt','Xiaolai-Diagrams.ttf','OFL-Xiaolai.txt']]
    names += ['board/notebook.js','board/message_controls.py','tests/discussion-actions.test.cjs','tests/mobile-layers.browser.cjs']
    names += ['board/lifecycle.py','board/watch_rules.py','board/writing.py','board/lifecycle-view.js','board/lifecycle-view.css']
    names += ['scripts/task_flow.py','scripts/flow_check.py','scripts/patrol_log.py']
    names += ['tests/forecast.test.cjs','tests/file-groups.test.cjs']
    names += ['tests/lifecycle-view.test.cjs','tests/mobile-layers-optional-runtime.test.cjs']
    names += ['tests/room-collection.test.cjs','tests/eta-view.test.cjs','tests/identity-refresh.test.cjs','tests/quota-truth.test.cjs']
    names += ['board/index-tabs.css', 'board/index-tabs.js']
    names += ['board/private_notes.py','board/private-notes.css','board/private-notes.js','scripts/private_chat.py','docs/private-chat.md','tests/private-chat.browser.cjs']
    names += ['scripts/agent.py','docs/agent-commands.md','docs/optional-gpu-dispatcher.md','skills/board-agent/SKILL.md']
    names += ['docs/ARCHITECTURE.md','docs/architecture/index.html']
    names += ['docs/images/'+name for name in ['readme-hero.png','social-preview.png','wake-cycle.png','human-in-the-loop.png','mistakes-to-programs.png','alternatives/readme-hero-a.png','alternatives/readme-hero-b.png']]
    names += ['docs/badges/license.svg','docs/badges/python.svg']
    names += ['docs/install-with-agent.md','docs/install-with-agent.zh-CN.md']
    names += ['docs/architecture/'+name+'.svg' for name in ['01-overview','02-channels','03-question','04-cadence','05-authority','06-wake-loop']]
    names += ['docs/architecture/'+name+'.zh-CN.svg' for name in ['01-overview','02-channels','03-question','04-cadence','05-authority','06-wake-loop']]
    names += ['docs/ARCHITECTURE.zh-CN.md','docs/architecture/index.zh-CN.html','docs/optional-gpu-dispatcher.zh-CN.md','assets/README.zh-CN.md','scripts/make_architecture_diagrams.py']
    names += ['board/exchange.py','board/stability.py','board/workflow_checks.py','scripts/check_eol.py']
    names += ['docs/prompt-writing.md','docs/prompt-writing.zh-CN.md']
    names += ['docs/plain-notes.md','docs/plain-notes.zh-CN.md']
    names += ['docs/task-notes.md','docs/task-notes.zh-CN.md']
    names += ['docs/open-source-sync.md','docs/open-source-sync.zh-CN.md']
    names += ['scripts/citation_chain.py','docs/literature-search.md','docs/literature-search.zh-CN.md']
    for folder in ['personas','protocol','templates']:
        names += [p.relative_to(ROOT).as_posix() for p in (ROOT/folder).glob('*') if p.suffix in ['.md','.json']]
    names += ['skills/research-report-writing/'+name for name in [
        'SKILL.md','README.md','references/writing.zh-CN.md','templates/report_helpers.py']]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'board/art').glob('*.svg') if p.name.startswith(('avatar-user','avatar-claude','avatar-gpt','claude-','gpt-','user-'))]
    names += ['assets/README.md','assets/public-emotes.json','board/art/fanart.json']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'board/art').glob('*.png') if p.name in {'avatar-claude-full.png','avatar-claude.png','avatar-gpt.png','avatar-user.png','cell-01.png','cell-02.png','cell-03.png','cell-04.png','cell-05.png','cell-06.png','cell-07.png','cell-08.png','cell-09.png','cell-10.png','cell-11.png','cell-12.png','claude-calm.png','claude-cheer.png','claude-confused.png','claude-happy.png','claude-heart.png','claude-panic.png','claude-pout.png','claude-proud.png','claude-reading.png','claude-shy.png','claude-sleepy.png','claude-surprised.png','claude-teary.png','claude-thinking.png','claude-wink.png','emotion-atlas.png','trio-atlas.png'}]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'board/reactions').glob('*.svg')]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').glob('v02-*.png')]
    names += ['board/plan_checks.py','board/plan-checks.js','board/plan-checks.css','tests/test_v031_plan_checks.py','tests/plan-checks.test.cjs']
    names += ['board/cadence.py','board/cadence.js','board/cadence.css','tests/test_v043_cadence.py','docs/report-tidy.md','docs/report-tidy.zh-CN.md','demo/cache-findings.html','demo/cache-results.csv','demo/cache-notes.md']
    return sorted(set(names))

def scan(blob,name=''):
    if blob.startswith((b'\x89PNG',b'wOF2')):return []
    text=blob.decode('utf-8',errors='replace');rules={
        'private_absolute_path':r'(?i)[A-Z]:[/\\](?:Users|科研工作)[/\\]|/(?:home|localdata|var/tmp)/[a-z0-9_-]+',
        'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'literal_credential':r'''(?i)(?:api[_-]?key|password|secret)\s*[:=]\s*["'][A-Za-z0-9+/=]{24,}["']''',
        'email':r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}',
        'private_media_reference':r'/chat-img/[a-f0-9]{32}\.',
    }
    problems=[k for k,p in rules.items() if re.search(p,text)]
    # The local user's machine identity is computed at release time, never embedded in source.
    for value in [getpass.getuser(),socket.gethostname()]:
        if len(value)>3 and re.search(r'(?<![A-Za-z0-9_])'+re.escape(value)+r'(?![A-Za-z0-9_])',text,re.I):problems.append('local_machine_identity')
    return problems

def main():
    if check_eol(ROOT):raise SystemExit(1)
    out=ROOT/'work/releases';out.mkdir(parents=True,exist_ok=True);manifest=[];problems=[];scanned=[]
    for name in files():
        path=ROOT/name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):raise ValueError('Source boundary')
        raw=path.read_bytes();manifest.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        problems.extend(dict(path=name,rule=r) for r in scan(raw,name))
        scanned.append((name,raw))
    report=dict(version=VERSION,files=len(manifest),findings=problems,manifest=manifest)
    write_report(out/'privacy-scan.json',report)
    if problems:raise SystemExit('Review work/releases/privacy-scan.json')
    archive=out/('research-collab-board-'+VERSION+'.zip');temp=out/(archive.name+'.'+uuid.uuid4().hex+'.partial')
    with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for name,raw in scanned:z.writestr('research-collab-board/'+name,raw)
    if archive.exists():
        history=out/'history';history.mkdir(exist_ok=True);digest=hashlib.sha256(archive.read_bytes()).hexdigest();saved=history/(digest+'.zip')
        if not saved.exists():shutil.copy2(archive,saved)
    temp.replace(archive)
    value=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,source_files=len(manifest),privacy_findings=0)
    write_report(out/'release.json',value);print(json.dumps(value))

if __name__=='__main__':main()
