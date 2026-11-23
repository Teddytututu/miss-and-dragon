"""Explicit reply completion with voice preferences and separate local receipts."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import re
from . import storage
from .plugins.voice_backend import command_speech,speech_lock


def speech_text(text):
    text=re.sub(r'```[\s\S]*?```','',text)
    text=re.sub(r'!?\[([^\]]*)\]\([^)]*\)',r'\1',text)
    return re.sub(r'\s+',' ',re.sub(r'(?m)^#+\s*|[*`_]','',text)).strip()


def finish(root,actor,text_file,*,config=None,now=None):
    root=Path(root);text=Path(text_file).read_text('utf-8-sig');now=now or datetime.now(timezone.utc)
    config=storage.read(root/'attachments/voice.json',{}) if config is None else config
    if actor not in {'Claude','GPT'} or not text.strip():raise ValueError('Assistant identity and reply text required')
    result=dict(engine='disabled',playback='disabled_by_preference')
    if config.get('enabled') is True:
        until=config.get('mute_until',{}).get(actor)
        until=datetime.fromisoformat(until) if until else None
        if until is not None and until.tzinfo is None:raise ValueError('Timezone-aware mute deadline required')
        if until and now<until:result=dict(engine='muted',playback='muted_by_preference')
        else:
            with speech_lock(root/'attachments/voice.lock'):result=command_speech(actor,speech_text(text),config)
    receipt=dict(actor=actor,text_sha256=hashlib.sha256(text.encode()).hexdigest(),at=now.isoformat(),**result)
    with storage.locked(root):storage.append(root/'attachments/reply-results.jsonl',receipt)
    return receipt
