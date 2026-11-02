"""Escaped Markdown report rendering with a caller-supplied URL policy."""
import html
import re

CSS = """body{margin:0;background:#f7f1f3;color:#3b2f36;font:16px/1.8 'Segoe UI','Microsoft YaHei',sans-serif}
main{max-width:860px;margin:28px auto;padding:30px 36px;background:#fffdfb;border:1px solid #ecdbe2;border-radius:14px}
h1{font-size:28px;line-height:1.4;margin:.2em 0 .6em}h2{font-size:22px;margin:1.6em 0 .5em;padding-bottom:.2em;border-bottom:1px dashed #e3c7d3}
h3{font-size:18px;margin:1.3em 0 .4em}h4,h5,h6{font-size:16px;margin:1.1em 0 .3em}
p{margin:.5em 0}ul,ol{margin:.4em 0 .8em;padding-left:1.6em}li{margin:.25em 0}
a{color:#b8466f;text-decoration:none;border-bottom:1px solid #f0c3d5}a:hover{border-bottom-color:#b8466f}
code{font:14px Consolas,monospace;background:#f6eef1;padding:.1em .35em;border-radius:5px}
pre{background:#f6eef1;padding:12px 14px;border-radius:8px;overflow:auto}pre code{background:none;padding:0}
blockquote{margin:.8em 0;padding:.3em 1em;border-left:4px solid #e7a9c1;background:#fff6f9;color:#5b4651}
table{border-collapse:collapse;margin:.8em 0;width:100%;font-size:15px}th,td{border:1px solid #ecdbe2;padding:6px 10px;text-align:left;vertical-align:top}
th{background:#fbeff3}tr:nth-child(even) td{background:#fffafc}hr{border:0;border-top:1px dashed #e3c7d3;margin:1.6em 0}
img{max-width:100%;border-radius:8px}
@media(max-width:700px){main{margin:0;border-radius:0;padding:18px 16px}}"""


def inline(text, link):
    out = html.escape(text, quote=True)
    out = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', out)
    out = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', lambda m: f'<img alt="{m.group(1)}" src="{html.escape(link(html.unescape(m.group(2))))}">', out)
    out = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{html.escape(link(html.unescape(m.group(2))))}">{m.group(1)}</a>', out)
    out = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', out)
    out = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<i>\1</i>', out)
    return out


def render(text, title, link=lambda u: u):
    lines = text.replace('\r\n', '\n').split('\n')
    out, i = [], 0
    def is_table(k):
        return k + 1 < len(lines) and lines[k].strip().startswith('|') and re.match(r'^\s*\|?\s*:?-{2,}', lines[k + 1])
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1; continue
        if s.startswith('```'):
            j = i + 1; block = []
            while j < len(lines) and not lines[j].strip().startswith('```'):
                block.append(lines[j]); j += 1
            out.append('<pre><code>' + html.escape('\n'.join(block)) + '</code></pre>'); i = j + 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            n = len(m.group(1)); out.append(f'<h{n}>{inline(m.group(2), link)}</h{n}>'); i += 1; continue
        if re.match(r'^(-{3,}|\*{3,})$', s):
            out.append('<hr>'); i += 1; continue
        if is_table(i):
            cells = lambda row: [c.strip() for c in row.strip().strip('|').split('|')]
            head = cells(lines[i]); body = []; j = i + 2
            while j < len(lines) and lines[j].strip().startswith('|'):
                body.append(cells(lines[j])); j += 1
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c, link)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c, link)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table>')
            i = j; continue
        if s.startswith('>'):
            block = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                block.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote>' + '<br>'.join(inline(b, link) for b in block) + '</blockquote>'); continue
        if re.match(r'^\s*([-*+]|\d+[.)])\s+', line):
            items = []
            while i < len(lines) and (re.match(r'^\s*([-*+]|\d+[.)])\s+', lines[i]) or (lines[i].startswith('  ') and lines[i].strip() and items)):
                cur = lines[i]
                mm = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$', cur)
                if mm:
                    items.append([len(mm.group(1).expandtabs()), mm.group(2)[0].isdigit(), mm.group(3)])
                else:
                    items[-1][2] += ' ' + cur.strip()
                i += 1
            base = min(x[0] for x in items)
            html_parts, open_sub = [], False
            tag = 'ol' if items[0][1] else 'ul'
            html_parts.append(f'<{tag}>')
            for indent, ordered, body in items:
                if indent > base and not open_sub:
                    html_parts[-1] = html_parts[-1][:-5] if html_parts[-1].endswith('</li>') else html_parts[-1]
                    html_parts.append('<ul>'); open_sub = True
                elif indent <= base and open_sub:
                    html_parts.append('</ul></li>'); open_sub = False
                html_parts.append(f'<li>{inline(body, link)}' + ('' if indent > base else '</li>') if indent <= base else f'<li>{inline(body, link)}</li>')
            if open_sub:
                html_parts.append('</ul></li>')
            html_parts.append(f'</{tag}>')
            out.append(''.join(html_parts)); continue
        para = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6}\s|```|>|\s*([-*+]|\d+[.)])\s+|\|)', lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append('<p>' + '<br>'.join(inline(p, link) for p in para) + '</p>')
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>' + '\n'.join(out) + '</main></body></html>')
