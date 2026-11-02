"""Project report references projected to scoped read-only URLs.

Only existing files explicitly reached from the selected report are eligible.
The caller retains the board's loopback and HTTP-method checks.
"""
from html import escape,unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote,unquote,urlsplit
import hashlib,re

READABLE={'.html','.htm','.md','.txt','.csv','.pdf','.png','.jpg','.jpeg','.webp','.svg','.gif','.mp4','.webm','.css','.js','.woff','.woff2','.zip'}

def target_file(value,document,eligible=lambda p: True):
    value=unescape(value).strip()
    if not value or value.startswith('#'):return None
    u=urlsplit(value)
    if re.match(r'^[A-Za-z]:[/\\]',value):path=re.split(r'[?#]',value,1)[0]
    elif u.scheme=='file' and u.netloc in {'','localhost'}:
        path=u.path
        if re.match(r'^/[A-Za-z]:/',path):path=path[1:]
    elif u.scheme or u.netloc or u.path.startswith(('/', '\\')):return None
    else:path=u.path
    p=Path(unquote(path));p=p if p.is_absolute() else document.parent/p
    if not eligible(p):return None
    p=p.resolve()
    return p if p.is_file() and p.suffix.lower() in READABLE else None

class References(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        self.urls.extend(v for k,v in attrs if k in {'src','href','poster'} and v)
    handle_startendtag=handle_starttag

def references(document):
    if document.suffix.lower() not in {'.html','.htm','.css','.md'} or document.stat().st_size>16*2**20:return []
    text=document.read_text(encoding='utf-8-sig',errors='replace');urls=[]
    if document.suffix.lower() in {'.html','.htm'}:
        parser=References();parser.feed(text);urls.extend(parser.urls)
    if document.suffix.lower()=='.css':urls+=re.findall(r'url\(\s*[\"\']?([^\"\')]+)',text)
    if document.suffix.lower()=='.md':urls+=re.findall(r'\]\(<?([^\n)]+?)>?\)',text)
    return urls

def closure(report,stops=(),eligible=lambda p: True):
    allowed={report};todo=[report]
    while todo and len(allowed)<1500:
        document=todo.pop()
        for value in references(document):
            target=target_file(value,document,eligible)
            if target is not None and eligible(target) and target not in allowed and len(allowed)<1500:
                allowed.add(target)
                if target not in stops:todo.append(target)
    return allowed

def asset_key(path):return hashlib.sha256(str(path).encode()).hexdigest()[:24]

def asset_url(prefix,path):return prefix+'_asset/'+asset_key(path)+'/'+quote(path.name,safe='')

def resolve_asset(allowed,name):
    match=re.fullmatch(r'_asset/([a-f0-9]{24})/([^/\\\x00]+)',name)
    if not match:return None
    return next((p for p in allowed if asset_key(p)==match[1] and p.name==match[2]),None)

def routed_url(value,document,prefix,allowed,routes=None):
    target=target_file(value,document)
    if target not in allowed:return value
    suffix='';match=re.search(r'[?#]',unescape(value))
    if match:suffix=unescape(value)[match.start():]
    return ((routes or {}).get(target) or asset_url(prefix,target))+suffix

def rewrite_html(text,document,prefix,allowed,routes=None):
    # Edit attribute spans, retaining all document text, whitespace and scripts.
    starts=[0]
    starts.extend(m.end() for m in re.finditer('\n',text));edits=[]
    attr=re.compile(r'(?P<name>[^\s=/>]+)\s*=\s*(?:(?P<quote>[\"\'])(?P<url>.*?)(?P=quote)|(?P<bare>[^\s>]+))',re.S)
    class Rewriter(HTMLParser):
        def handle_starttag(self,tag,attrs):
            line,column=self.getpos();start=starts[line-1]+column
            for match in attr.finditer(self.get_starttag_text()):
                if match['name'].lower() not in {'src','href','poster'}:continue
                group='url' if match['url'] is not None else 'bare'
                value=match[group];new=routed_url(value,document,prefix,allowed,routes)
                if new!=value:edits.append((start+match.start(group),start+match.end(group),escape(new,quote=True)))
        handle_startendtag=handle_starttag
    parser=Rewriter(convert_charrefs=False);parser.feed(text)
    for start,end,value in reversed(edits):text=text[:start]+value+text[end:]
    return text

def rewrite_css(text,document,prefix,allowed,routes=None):
    def replace(match):
        value=match[2];new=routed_url(value,document,prefix,allowed,routes)
        return match[0] if new==value else 'url('+match[1]+new+match[1]+')'
    return re.sub(r'url\(\s*([\"\']?)([^\"\')]+)\1\s*\)',replace,text)
