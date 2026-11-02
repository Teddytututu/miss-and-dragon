"""Print local clock context for an optional Claude UserPromptSubmit hook."""
from datetime import datetime
import argparse


def context(now=None, language='en'):
    now = now or datetime.now().astimezone()
    if now.tzinfo is None:
        now = now.astimezone()
    date = now.strftime('%Y-%m-%d %H:%M')
    offset = now.strftime('%z')
    if language == 'zh-CN':
        day = ('周一', '周二', '周三', '周四', '周五', '周六', '周日')[now.weekday()]
        return f'现在是 {date} {day}（UTC{offset}）。'
    if language != 'en':
        raise ValueError('Choose en or zh-CN')
    day = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')[now.weekday()]
    return f'Current local time: {date} {day} (UTC{offset}).'


if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # Windows consoles default to a local code page
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=('en', 'zh-CN'), default='en')
    print(context(language=parser.parse_args().language))
