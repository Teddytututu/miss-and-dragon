"""Opt-in host hooks with explicit workspace, session IDs and rule configuration."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import os


def context(event,text):
    return dict(hookSpecificOutput=dict(hookEventName=event,additionalContext=text))


def handle(event,config):
    kind=event.get('hook_event_name')
    root=Path(config['workspace']).resolve(strict=True)
    if kind=='SessionStart' and event.get('source')=='compact' and event.get('session_id') in config.get('sessions',[]):
        pointer=(root/config['pointer']).resolve()
        if not pointer.is_relative_to(root):raise ValueError('pointer_scope')
        if not pointer.is_file():raise ValueError('pointer_required')
        return context(kind,'先处理最新明确指令或暂停。接续时先读 '+str(pointer)+' 和它指向的任务卡，从磁盘成果对应的下一步继续。历史消息和已交付事项作为资料。'),0
    if kind=='UserPromptSubmit':
        return context(kind,'当前时间 '+datetime.now().astimezone().isoformat(timespec='seconds')),0
    if kind=='Stop':
        text=str(event.get('last_assistant_message') or '')
        hits=[rule['id'] for rule in config.get('reply_rules',[]) if re.search(rule['pattern'],text)]
        return dict(violations=hits),0
    if kind=='PreToolUse':
        tool=event.get('tool_name');data=event.get('tool_input') or {}
        for raw in config.get('protected_roots',[]):
            protected=Path(raw).resolve()
            if tool=='Grep':
                target=Path(data.get('path') or root).resolve()
                if target.is_relative_to(protected) and not target.is_file() and not target.suffix:
                    raise ValueError('recursive_read_scope')
            elif tool in {'Bash','PowerShell','exec_command'}:
                command=str(data.get('command') or data.get('cmd') or '')
                if str(protected).replace('\\','/').lower() in command.replace('\\','/').lower() and re.search(r'\brg\b|\bgrep\b.*-[a-zA-Z]*[rR]|-Recurse|findstr.*?/s',command,re.I):
                    raise ValueError('recursive_read_scope')
    return None,0


def templates(config_file,host):
    args=[sys.executable,str(Path(__file__).resolve()),'--config',str(Path(config_file).resolve())]
    command=subprocess.list2cmdline(args) if os.name=='nt' else shlex.join(args)
    events=['SessionStart','Stop'] if host=='codex' else ['UserPromptSubmit','PreToolUse','Stop']
    return dict(hooks={name:[dict(hooks=[dict(type='command',command=command)])] for name in events})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--template',choices=['claude','codex']);args=parser.parse_args()
    try:
        if args.template:result=templates(args.config,args.template);code=0
        else:result,code=handle(json.load(sys.stdin),json.loads(args.config.read_text('utf-8')))
        if result is not None:print(json.dumps(result,ensure_ascii=True))
        return code
    except (ValueError,KeyError,OSError,re.error) as error:
        print(str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
