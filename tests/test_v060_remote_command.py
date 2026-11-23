"""The queue submission command is one shell-safe line that carries the full program."""
import base64
import re

from board.plugins import queue_protocol


def test_remote_command_is_one_line_and_carries_the_program():
    command = queue_protocol.remote_command('/srv/queue', 'job-1')
    assert '\n' not in command
    packed = re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)", command).group(1)
    assert base64.b64decode(packed).decode('utf-8') == queue_protocol.remote_python()
    assert command.endswith("/srv/queue job-1")


def test_remote_program_rejects_identical_pending_command():
    program = queue_protocol.remote_python()
    assert "for name in ('pending','running')" in program
    assert "get('cmd')==value.get('cmd')" in program
