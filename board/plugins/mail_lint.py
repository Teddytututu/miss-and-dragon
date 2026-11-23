"""Rule-level feedback for a named English email draft."""
import re
import argparse
import json
from html.parser import HTMLParser
import sys
from pathlib import Path

RULES = [
    (r"\bglad to\b|\bhappy to\b", "glad/happy to 像在答应对方的请求；改成 grateful for the chance"),
    (r"\bI plan to\b|\bI will apply\b|\bI am going to\b", "陈述自己的计划像通知；改成 I hope to …"),
    (r"\bI understand (that )?(the|your)\b", "替老师说出她的决定；删掉"),
    (r"\bI fully respect\b", "“我尊重您的决定”是居高临下的姿态；删掉"),
    (r"\bI would like you to\b|\byou can come to know\b", "在安排对方做事；改成请求或删掉"),
    (r"\bfar too much\b|\btoo abrupt\b", "替对方总结感受；改成具体说自己哪里做错"),
    (r"\bcontinue as\b|\bin your group\b.*\bresearch assistant\b", "默认自己已是组员"),
    (r"\bThe most important lesson\b|\bpart of the gain\b", "汇报研究发现，道歉信里不是重点"),
    (r"\bCompute\.|\bVideo\.|^\s*\*\*", "一词小标题或加粗，像进度报告"),
    (r"\bcould I have\b|\bthis weekend or next week\b", "第一次接触就要时间"),
    (r"\brecommendation letter\b", "推荐信要等老师真的了解后当面提"),
]


class BodyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.hidden=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style'}:self.hidden+=1
        if tag in {'div','p','br','h1','h2'} and not self.hidden:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in {'script','style'}:self.hidden=max(0,self.hidden-1)
    def handle_data(self,text):
        if not self.hidden:self.parts.append(text)


def text_of(p: Path) -> str:
    text=p.read_text(encoding='utf-8-sig')
    if p.suffix.lower() in {'.html','.htm'}:
        parser=BodyParser();parser.feed(text);text=''.join(parser.parts)
    return text


def check(text, rules=None, max_you=3, max_apologies=1):
    hits=[]
    for index,(pattern,message) in enumerate(RULES if rules is None else rules,1):
        for match in re.finditer(pattern,text,re.I|re.M):
            hits.append(dict(id=f'rule-{index:02d}',message=message,start=match.start(),end=match.end(),
                             excerpt=text[max(0,match.start()-40):match.end()+40].replace('\n',' ')))
    for identifier,pattern,limit,message in [
        ('you-count',r'\byou(r|rs)?\b',max_you,'you/your 次数'),
        ('apology-count',r'\bsorry\b|\bapolog',max_apologies,'道歉词次数')]:
        count=len(re.findall(pattern,text,re.I))
        if count>limit:hits.append(dict(id=identifier,message=f'{message} {count}，参考上限 {limit}',count=count))
    return hits


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('file',type=Path)
    parser.add_argument('--json',action='store_true');args=parser.parse_args(argv)
    hits=check(text_of(args.file))
    if args.json:print(json.dumps(dict(hits=hits,count=len(hits)),ensure_ascii=False))
    else:
        for hit in hits:print('[改] '+hit['message']+'：'+hit.get('excerpt',''))
        print(f'命中 {len(hits)} 处')
    return 1 if hits else 0


if __name__=='__main__':raise SystemExit(main())
