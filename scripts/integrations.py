"""Explicit local integrations; importing the package activates no plugin."""
from pathlib import Path
import argparse
import getpass
import json
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from board import storage,continuity,delivery,publication,imports,note_schedule


def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,default=ROOT/'data')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('current');s.add_argument('--actor',required=True);s.add_argument('--task');s.add_argument('--stage',default='implementation');s.add_argument('--artifact',default='board.md');s.add_argument('--authorization',default='Explicit CLI assignment')
    s=sub.add_parser('stage');s.add_argument('action',choices=['configure','submit','review']);s.add_argument('--task',required=True);s.add_argument('--stage',required=True);s.add_argument('--actor',default='GPT');s.add_argument('--reviewer',default='Claude');s.add_argument('--depends',nargs='*',default=[]);s.add_argument('--files',nargs='*',default=[]);s.add_argument('--version');s.add_argument('--decision',choices=['accept','reject']);s.add_argument('--note',default='')
    s=sub.add_parser('publish');s.add_argument('--task',required=True);s.add_argument('--stage',required=True);s.add_argument('--file',required=True);s.add_argument('--title',required=True)
    s=sub.add_parser('import');s.add_argument('--packet',required=True);s.add_argument('--version');s.add_argument('files',type=Path,nargs='+')
    s=sub.add_parser('watch');s.add_argument('--config',type=Path)
    s=sub.add_parser('schedule');s.add_argument('--note',required=True);s.add_argument('--period',required=True)
    s=sub.add_parser('decision');s.add_argument('action',choices=['list','add','claim','ack']);s.add_argument('--actor',default='Claude');s.add_argument('--id');s.add_argument('--title');s.add_argument('--why',default='');s.add_argument('--option',action='append',default=[]);s.add_argument('--next');s.add_argument('--evidence')
    s=sub.add_parser('budget');s.add_argument('--input',type=Path,required=True)
    s=sub.add_parser('queue');s.add_argument('--input',type=Path,required=True);s.add_argument('--host');s.add_argument('--queue-root');s.add_argument('--submit',action='store_true')
    s=sub.add_parser('gpu');s.add_argument('--input',type=Path,required=True)
    s=sub.add_parser('services');s.add_argument('--config',type=Path)
    s=sub.add_parser('voice');s.add_argument('--config',type=Path,required=True);s.add_argument('--actor',default='GPT');s.add_argument('--text',required=True)
    s=sub.add_parser('reply');s.add_argument('--config',type=Path);s.add_argument('--actor',default='GPT');s.add_argument('--text-file',type=Path,required=True)
    s=sub.add_parser('event');s.add_argument('action',choices=['list','enqueue','claim','settle','consume']);s.add_argument('--actor',default='GPT');s.add_argument('--task');s.add_argument('--stage');s.add_argument('--version');s.add_argument('--body');s.add_argument('--authorization');s.add_argument('--id');s.add_argument('--claim');s.add_argument('--outcome',choices=['sent','failed']);s.add_argument('--consumer')
    s=sub.add_parser('mail');s.add_argument('file',type=Path)
    s=sub.add_parser('accounts');s.add_argument('action',choices=['init','password','revoke']);s.add_argument('--person',default='owner')
    a=p.parse_args(argv);root=a.data_dir.resolve()
    if a.command=='current':
        return continuity.set_current(root,a.actor,a.task,a.stage,a.artifact,authorization=a.authorization) if a.task else continuity.current(root,a.actor)
    if a.command=='stage':
        if a.action=='configure':return delivery.configure(root,a.task,a.stage,executor=a.actor,reviewer=a.reviewer,dependencies=a.depends)
        if a.action=='submit':return delivery.submit(root,a.task,a.stage,a.files,actor=a.actor)
        if a.decision is None or a.version is None:p.error('review requires --decision and --version')
        return delivery.review(root,a.task,a.stage,a.version,actor=a.actor,accept=a.decision=='accept',note=a.note)
    if a.command=='publish':return publication.publish(root,a.task,a.stage,a.file,a.title)
    if a.command=='import':return dict(collected=imports.attach(root,a.packet,a.files,version_id=a.version))
    if a.command=='watch':
        from board.plugins import file_import
        config=load(a.config) if a.config else {}
        if config.get('enabled') is not True:return dict(status='disabled',collected=[])
        # Separate observations for each directory, packet and answer version.
        import hashlib
        identity=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
        with storage.locked(root):
            path=root/'attachments/import-observers'/f'{identity}.json';state=storage.read(path,{})
            def importer(packet,files,apply):return dict(collected=imports.attach(root,packet,files,version_id=config.get('version_id')))
            result=file_import.observe_once(dict(config,packet_root=config['packet']),state,importer,now=time.time());storage.write(path,state);return result
    if a.command=='schedule':return note_schedule.assign(root,a.note,a.period)
    if a.command=='decision':
        from board import decisions
        if a.action=='claim':return decisions.claim(root,a.id,a.actor,a.next)
        if a.action=='ack':return decisions.finish(root,a.id,a.actor,a.evidence)
        with storage.locked(root):
            path=root/'overview.json';value=storage.read(path,{})
            if a.action=='list':return dict(pending=decisions.pending(value),answered=decisions.answered(value))
            row=decisions.add(value,a.title,a.why,a.option,actor=a.actor);storage.write(path,value);return row
    if a.command=='queue':
        from board.plugins.queue_protocol import ticket,admission,remote_command
        value=load(a.input);job=ticket(value['ticket'])
        result=dict(ticket=job,admission=admission(job,value['policy'],value['sample'],now=value.get('now',time.time())))
        if a.submit:
            import subprocess,re
            if not a.host or not a.queue_root or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.@-]{0,253}',a.host):p.error('Submission requires an SSH host and absolute queue root')
            if not result['admission']['eligible']:raise ValueError('Refresh resources or wait for admission before submitting')
            sent=subprocess.run(['ssh','-o','BatchMode=yes',a.host,remote_command(a.queue_root,job['id'])],input=json.dumps(job),text=True,capture_output=True,timeout=30)
            result['submission']=dict(exit_code=sent.returncode,message=sent.stdout.strip(),error=sent.stderr.strip())
            if sent.returncode:raise ValueError('Queue submission returned '+str(sent.returncode)+': '+sent.stderr.strip())
        return result
    if a.command=='gpu':
        from board.plugins.gpu_observer import project
        value=load(a.input);return project(value.get('queue',{}),value.get('gpu_status',{}),now=value.get('now'),profile=value.get('profile',{}))
    if a.command=='budget':
        from board.plugins.budget import decide
        from datetime import datetime,timezone
        value=load(a.input);state=value['state'];now=datetime.fromisoformat(value['now']) if isinstance(value.get('now'),str) else datetime.fromtimestamp(value.get('now',time.time()),timezone.utc)
        return dict(decision=decide(state,value['sample'],value['policy'],now,value.get('direct',False)),state=state)
    if a.command=='services':
        from board.plugins.services import snapshot
        return snapshot(force=True,config=a.config)
    if a.command=='voice':
        from board.plugins.voice_backend import command_speech,speech_lock
        with speech_lock(root/'attachments/voice.lock'):return command_speech(a.actor,a.text,load(a.config))
    if a.command=='reply':
        from board import reply
        return reply.finish(root,a.actor,a.text_file,config=load(a.config) if a.config else None)
    if a.command=='event':
        from board import events
        if a.action=='list':return events.read(root)
        if a.action=='enqueue':return events.enqueue(root,a.actor,a.task,a.stage,a.version,a.body,authorization=a.authorization)
        if a.action=='claim':return events.claim(root,a.id)
        if a.action=='settle':
            if a.outcome is None:p.error('Explicit transport --outcome required')
            return events.settle(root,a.id,a.claim,sent=a.outcome=='sent')
        return dict(consumed=events.consume(root,a.consumer,a.id))
    if a.command=='mail':
        from board.plugins.mail_lint import check,text_of
        return dict(issues=check(text_of(a.file)))
    if a.command=='accounts':
        from board.plugins import accounts
        path=root/'attachments/accounts.json'
        if a.action=='init':
            with storage.locked(root):
                if path.exists():raise ValueError('Account configuration already exists')
                accounts.atomic_json(path,accounts.initial_config())
            return dict(initialized=True,people=['owner','visitor'])
        store=accounts.Store(path)
        with storage.locked(root):
            if a.action=='password':store.set_password(a.person,getpass.getpass('New account password: '))
            else:
                def revoke(value):value['accounts'][a.person]['session_version']+=1
                store.update(revoke)
        return dict(updated=a.person,action=a.action)


if __name__=='__main__':
    try:print(json.dumps(main(),ensure_ascii=False,allow_nan=False))
    except (ValueError,KeyError,OSError,PermissionError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
