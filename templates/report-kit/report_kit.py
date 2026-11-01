"""Reusable offline report components. See example_build.py and check_report.py."""
from pathlib import Path
import base64, html, io

esc = lambda s: html.escape(str(s), quote=True)

# ---------- 颜色是身份：一个名字一个颜色，全页不变 ----------
INK, MUTED, GRID = '#493641', '#7a6170', '#ead9e0'
PALETTE = ['#c2477a', '#3a6ea5', '#3f8f8a', '#d9905a', '#8a6bb3', '#7b9e5a', '#d0603f', '#6f8496']
BASELINE = '#bdb3b9'   # “什么都不做”的基线固定用灰


class Colors:
    """identity = Colors({'早筛': '#c2477a', '画完四张再挑': '#6f8496'})；没登记的名字按顺序自动发色。
    同一个颜色发给两个名字会直接报错。"""
    def __init__(self, fixed=None):
        self.map = {}
        for k, v in (fixed or {}).items():
            self.set(k, v)

    def set(self, name, color):
        other = next((k for k, v in self.map.items() if v == color and k != name), None)
        if other:
            raise ValueError(f'颜色 {color} 已经代表“{other}”，不能再给“{name}”')
        self.map[name] = color

    def __call__(self, name):
        if name not in self.map:
            free = [c for c in PALETTE if c not in self.map.values()]
            if not free:
                raise ValueError('颜色用完了：一张页面里要区分的东西太多，先合并或拆页')
            self.map[name] = free[0]
        return self.map[name]


# ---------- 页面骨架 ----------
CSS = """
:root{--bg:#f6f1ee;--paper:#fffdfb;--ink:#493641;--muted:#7a6170;--line:#e6d6dc;--accent:#c2477a;--wash:#f6e3ea}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.85 'Segoe UI','Microsoft YaHei',sans-serif}
main{max-width:960px;margin:auto;padding:36px 32px 70px}
header.top{margin:0 0 22px}h1{font:700 32px/1.4 'KaiTi','STKaiti',Georgia,serif;margin:6px 0 6px}.sub{color:var(--muted);margin:0}
section{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:24px 28px;margin:0 0 20px}
h2{font:700 22px/1.5 'KaiTi','STKaiti','Microsoft YaHei',serif;margin:0 0 10px}h3{font-size:17px;margin:20px 0 4px}
p{margin:6px 0 12px}p.claim{font-size:18px}p.claim b{color:var(--ink)}
figure{margin:8px 0 14px}figure svg,figure img{width:100%;height:auto;display:block;border-radius:6px}
figcaption{font-size:13.5px;color:var(--muted);margin-top:4px}.ft{font-weight:700;margin:16px 0 2px}
table{border-collapse:collapse;width:100%;font-size:14.5px;margin:6px 0 14px}th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600}tbody tr:nth-child(odd){background:#faf3f5}td small{display:block;color:var(--muted)}
dl.terms{display:grid;grid-template-columns:8em 1fr;gap:6px 14px;margin:8px 0}dl.terms dt{font-weight:700;color:var(--accent)}dl.terms dd{margin:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.next{border-left:4px solid var(--accent);padding:2px 0 2px 16px;margin:14px 0}
details{margin:10px 0}summary{cursor:pointer;color:var(--accent);font-weight:600}
@media(max-width:720px){main{padding:18px 12px 50px}section{padding:18px 16px}.two{grid-template-columns:1fr}dl.terms{grid-template-columns:1fr}h1{font-size:26px}}
"""


def page(title, sub, sections, lang='zh-CN', extra_css=''):
    """title 是一句结论（“错误什么时候定下来，额外的算力就该什么时候花”），不是“XX报告”。
    sub 一行：给谁、什么时候整理的。sections 是 section() 的结果列表。"""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>'
            f'<style>{CSS}{extra_css}</style></head><body><main>'
            f'<header class="top"><h1>{esc(title)}</h1><p class="sub">{esc(sub)}</p></header>'
            + ''.join(sections) + '</main></body></html>')


def section(heading, claim_bold, claim_rest, *parts):
    """一节 = 标题（说清这节讲什么）+ 结论段（一句加粗论断 + 两三句带数字和出处）+ 证据（图、表、例子）。"""
    return (f'<section><h2>{esc(heading)}</h2>{claim(claim_bold, claim_rest)}' + ''.join(parts) + '</section>')


def claim(bold, rest=''):
    return f'<p class="claim"><b>{esc(bold)}</b>{esc(rest)}</p>'


def para(text):
    return f'<p>{esc(text)}</p>'


def raw(html_text):
    """已经排好的 HTML（MathML 公式、链接）。只放可信内容。"""
    return html_text


def figure(svg_or_img, title='', caption=''):
    """title：图上方一行粗体，写“这张图比什么”（图 1　同样约 160 次计算，两种花法）。
    caption 只在图本身画不出来的信息时才写（数据来源、样本数），不写“红色表示……”。"""
    t = f'<div class="ft">{esc(title)}</div>' if title else ''
    c = f'<figcaption>{esc(caption)}</figcaption>' if caption else ''
    return f'<figure>{t}{svg_or_img}{c}</figure>'


def table(head, rows, small=None):
    """一格一事。rows 里的格子可以是 (主文字, 小字) 两元组，小字显示在下一行（会议·年份）。"""
    def cell(v, tag):
        if isinstance(v, tuple):
            return f'<{tag}>{esc(v[0])}<small>{esc(v[1])}</small></{tag}>'
        return f'<{tag}>{esc(v)}</{tag}>'
    for r in rows:
        for v in r:
            s = v[0] if isinstance(v, tuple) else str(v)
            if s.count('/') >= 2 or s.count('；') >= 1:
                raise ValueError(f'一格只放一件事：“{s}”')
    h = ''.join(cell(x, 'th') for x in head)
    b = ''.join('<tr>' + ''.join(cell(x, 'td') for x in r) + '</tr>' for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def terms(pairs):
    """术语表：只解释读者不认识的词，每条一句白话。"""
    return '<dl class="terms">' + ''.join(f'<dt>{esc(a)}</dt><dd>{esc(b)}</dd>' for a, b in pairs) + '</dl>'


def next_steps(items):
    """下一步：每条写“回答什么问题、怎么做、预期什么”。"""
    return ''.join(f'<div class="next"><b>{esc(q)}</b><br>{esc(how)}</div>' for q, how in items)


def photo(path, alt, max_w=1100, quality=78):
    """照片压成 JPEG 内嵌，页面单文件可发微信。"""
    from PIL import Image
    im = Image.open(path).convert('RGB')
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=quality, optimize=True)
    return f'<img alt="{esc(alt)}" src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}">'


# ---------- 图 ----------
def bars(rows, colors, unit='', aria='', W=760, label_w=150, cost=None):
    """横条比较图。rows = [(名字, 数值, 是否加粗)]，大的在上。
    cost = {名字: '约 160 次计算'}：结论里有“省”就必须给，花了多少直接写在条后面。
    基线（什么都不做）请用 colors.set('直接画一张', BASELINE)。"""
    maxv = max(v for _, v, _ in rows)
    bh, gap = 24, 12
    span = W - label_w - (200 if cost else 80)
    H = len(rows) * (bh + gap) + 6
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(aria)}">']
    for i, (name, v, bold) in enumerate(rows):
        y, col, w = 4 + i * (bh + gap), colors(name), span * v / maxv
        s.append(f'<text x="{label_w-10}" y="{y+17}" text-anchor="end" font-size="14" font-weight="{700 if bold else 500}" fill="{INK}">{esc(name)}</text>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bh}" rx="4" fill="{col}"/>')
        s.append(f'<text x="{label_w+w+8:.1f}" y="{y+17}" font-size="14" font-weight="700" fill="{col}">{v}{esc(unit)}</text>')
        if cost and name in cost:
            s.append(f'<text x="{label_w+w+60:.1f}" y="{y+17}" font-size="12.5" fill="{MUTED}">{esc(cost[name])}</text>')
    s.append('</svg>')
    return ''.join(s)


def diverging(rows, left, right, colors, aria='', W=760, unit_px=30):
    """差值图：谁赢、赢多少，一张图说完。rows = [(类别, 左边赢几个, 右边赢几个)]；left/right 是两种做法的名字。"""
    mid, H = W / 2, len(rows) * 40 + 34
    lc, rc = colors(left), colors(right)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(aria)}">',
         f'<line x1="{mid}" x2="{mid}" y1="4" y2="{H-28}" stroke="{MUTED}"/>']
    for i, (n, l, r) in enumerate(rows):
        y = 8 + i * 40
        s.append(f'<text x="110" y="{y+17}" text-anchor="end" font-size="14" font-weight="600" fill="{INK}">{esc(n)}</text>')
        s.append(f'<rect x="{mid-l*unit_px}" y="{y}" width="{l*unit_px}" height="24" rx="4" fill="{lc}"/>')
        s.append(f'<text x="{mid-l*unit_px-8}" y="{y+17}" text-anchor="end" font-size="13" font-weight="700" fill="{lc}">{l}</text>')
        s.append(f'<rect x="{mid}" y="{y}" width="{r*unit_px}" height="24" rx="4" fill="{rc}"/>')
        s.append(f'<text x="{mid+r*unit_px+8}" y="{y+17}" font-size="13" font-weight="700" fill="{rc}">{r}</text>')
    s.append(f'<text x="{mid-10}" y="{H-6}" text-anchor="end" font-size="13" fill="{lc}">← {esc(left)}赢的</text>')
    s.append(f'<text x="{mid+10}" y="{H-6}" font-size="13" fill="{rc}">{esc(right)}赢的 →</text></svg>')
    return ''.join(s)


def lines(series, colors, xlabel, ylabel='', aria='', W=760, H=290, ymax=None, marks=()):
    """曲线图。series = {名字: [(x, y), ...]}。marks = [(x, 文字, 名字)] 在某个 x 画竖虚线并标注（定型、可读）。
    曲线末端直接写名字，不用图例。"""
    xs = [x for pts in series.values() for x, _ in pts]
    ys = [y for pts in series.values() for _, y in pts]
    x0, x1, y1 = min(xs), max(xs), ymax or max(ys)
    L, R, T, B = 56, 150, 16, 44
    fx = lambda x: L + (x - x0) / ((x1 - x0) or 1) * (W - L - R)
    fy = lambda y: T + (1 - y / (y1 or 1)) * (H - T - B)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(aria)}">']
    for k in range(5):
        v = y1 * k / 4
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{fy(v):.1f}" y2="{fy(v):.1f}" stroke="{GRID}"/>'
                 f'<text x="{L-8}" y="{fy(v)+4:.1f}" text-anchor="end" font-size="11.5" fill="{MUTED}">{v:g}</text>')
    for x in sorted(set(xs)):
        s.append(f'<text x="{fx(x):.1f}" y="{H-B+18}" text-anchor="middle" font-size="11.5" fill="{MUTED}">{x:g}</text>')
    s.append(f'<text x="{(L+W-R)/2}" y="{H-6}" text-anchor="middle" font-size="12.5" fill="{MUTED}">{esc(xlabel)}</text>')
    if ylabel:
        s.append(f'<text x="14" y="{(T+H-B)/2}" font-size="12.5" fill="{MUTED}" transform="rotate(-90 14 {(T+H-B)/2})" text-anchor="middle">{esc(ylabel)}</text>')
    for i, (x, text, name) in enumerate(marks):   # 标注错开行，靠得近也不重叠
        c = colors(name)
        s.append(f'<line x1="{fx(x):.1f}" x2="{fx(x):.1f}" y1="{T}" y2="{H-B}" stroke="{c}" stroke-dasharray="4 4"/>'
                 f'<text x="{fx(x)+5:.1f}" y="{T+12+i*16}" font-size="12" fill="{c}" stroke="#fffdfb" stroke-width="3" paint-order="stroke">{esc(text)}</text>')
    for name, pts in series.items():
        c, pts = colors(name), sorted(pts)
        s.append('<polyline fill="none" stroke-width="2.6" stroke="%s" points="%s"/>' % (c, ' '.join(f'{fx(x):.1f},{fy(y):.1f}' for x, y in pts)))
        lx, ly = pts[-1]
        s.append(f'<text x="{fx(lx)+8:.1f}" y="{fy(ly)+4:.1f}" font-size="13" font-weight="700" fill="{c}">{esc(name)}</text>')
    s.append('</svg>')
    return ''.join(s)


def write(path, html_text):
    Path(path).write_text(html_text, encoding='utf-8')
    return path
