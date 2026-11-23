"""Optional local speech transport; explicit argv and playback confirmation."""
import json
import subprocess
import os
from contextlib import contextmanager


@contextmanager
def speech_lock(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0);stream.write(b'0');stream.flush();stream.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX)
        try:yield
        finally:
            if os.name=='nt':
                stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream,fcntl.LOCK_UN)


def command_speech(who,text,config):
    command=config.get('backend_command')
    if not isinstance(command,list) or not command or any(not isinstance(v,str) or not v or '\x00' in v for v in command):
        return dict(engine='failed',playback='invalid_backend')
    timeout=config.get('backend_timeout',120)
    if type(timeout) not in (int,float) or not 0<timeout<=600:
        return dict(engine='failed',playback='invalid_timeout')
    try:
        result=subprocess.run(command,input=json.dumps(dict(who=who,text=text),ensure_ascii=False),text=True,
                              encoding='utf-8',capture_output=True,timeout=timeout,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        response=json.loads(result.stdout) if result.returncode==0 else {}
        if isinstance(response,dict) and response.get('played') is True:
            return dict(engine='command',playback='completed')
        return dict(engine='failed',playback='confirmation_required')
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return dict(engine='failed',playback='backend_error')
