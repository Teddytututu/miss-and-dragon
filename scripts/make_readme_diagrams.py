"""Generate the README flowcharts in the notebook (手账) style of the board:
dot-grid paper, sticky notes with washi tape, highlighter titles and inked curved arrows.
Role colors match the avatars: Owner rose, Lead orange, Executor lavender, programs teal, records sand."""
import base64, io, re
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'images'
ROSE, ORANGE, LAV, TEAL, SAND, INK, MUTED, RED = '#d9668f', '#e0843a', '#8f6fd0', '#3f9a96', '#b8925c', '#3b2f36', '#7d6f76', '#c8524a'
NOTE = {ROSE: '#ffe4ee', ORANGE: '#ffecd9', LAV: '#efe6ff', TEAL: '#ddf3f0', SAND: '#fbf1e1'}
# Fonts are embedded as subsets (SIL OFL 1.1, licenses in scripts/fonts/): Caveat for handwriting, Nunito for text.
HAND = "'MD Hand','Segoe Print',cursive"
SANS = "'MD Sans','Segoe UI',Helvetica,Arial,sans-serif"


def tape(cx, y, color, w=58, rot=-4):
    return (f"<g transform='rotate({rot} {cx} {y})'><rect x='{cx - w / 2}' y='{y - 8}' width='{w}' height='16' rx='2' "
            f"fill='{color}' opacity='.38'/><rect x='{cx - w / 2}' y='{y - 8}' width='{w}' height='16' rx='2' fill='url(#stripe)' opacity='.5'/></g>")


def note(x, y, w, h, color, title, lines=(), rot=0, title_size=27):
    cx = x + w / 2
    s = [f"<g transform='rotate({rot} {cx} {y + h / 2})'>",
         f"<rect x='{x + 3}' y='{y + 4}' width='{w}' height='{h}' rx='6' fill='#000' opacity='.06'/>",
         f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='{NOTE[color]}' stroke='{color}' stroke-width='1.3'/>",
         f"<text x='{cx}' y='{y + 35}' text-anchor='middle' font-family=\"{HAND}\" font-size='{title_size}' font-weight='700' fill='{color}'>{title}</text>"]
    for i, line in enumerate(lines):
        s.append(f"<text x='{cx}' y='{y + 60 + i * 20}' text-anchor='middle' font-family=\"{SANS}\" font-size='15' fill='{INK}'>{line}</text>")
    s.append('</g>')
    s.append(tape(cx, y, color))
    return ''.join(s)


def curve(x1, y1, x2, y2, bend=-18, label='', ly=None, lx=None, color=INK, dash=False, anchor='middle'):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
    d = " stroke-dasharray='6 5'" if dash else ''
    s = f"<path d='M{x1} {y1} Q {mx} {my} {x2} {y2}' fill='none' stroke='{color}' stroke-width='1.6' stroke-linecap='round' marker-end='url(#a)'{d}/>"
    if label:
        s += (f"<text x='{lx if lx is not None else mx}' y='{ly if ly is not None else my - 4}' text-anchor='{anchor}' "
              f"font-family=\"{HAND}\" font-size='19' fill='{MUTED}'>{label}</text>")
    return s


def band(x, y, w, h, color, title):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{NOTE[color]}' fill-opacity='.55' stroke='{color}' "
            f"stroke-width='1.4' stroke-dasharray='7 5'/>"
            f"<rect x='{x + 18}' y='{y + 14}' width='{len(title) * 9.6}' height='14' fill='{color}' opacity='.22'/>"
            f"<text x='{x + 20}' y='{y + 30}' font-family=\"{HAND}\" font-size='24' font-weight='700' fill='{color}'>{title}</text>")


def chip(x, y, w, color, text, sub=None):
    h = 54 if sub else 38
    s = (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='#fffdfb' stroke='{color}' stroke-width='1.1'/>"
         f"<text x='{x + w / 2}' y='{y + (23 if sub else 25)}' text-anchor='middle' font-family=\"{SANS}\" font-size='15' "
         f"font-weight='600' fill='{INK}'>{text}</text>")
    if sub:
        s += f"<text x='{x + w / 2}' y='{y + 44}' text-anchor='middle' font-family=\"{SANS}\" font-size='13.5' fill='{MUTED}'>{sub}</text>"
    return s


def doodles(items):
    out = []
    for kind, x, y, c in items:
        if kind == 'heart':
            out.append(f"<path d='M{x} {y + 4} c -6 -8 -16 -2 -8 6 l 8 7 l 8 -7 c 8 -8 -2 -14 -8 -6z' fill='{c}' opacity='.7'/>")
        else:
            out.append(f"<path d='M{x} {y - 7} L{x + 2} {y - 2} L{x + 7} {y} L{x + 2} {y + 2} L{x} {y + 7} L{x - 2} {y + 2} L{x - 7} {y} L{x - 2} {y - 2}z' fill='{c}' opacity='.75'/>")
    return ''.join(out)


FONTS = Path(__file__).resolve().parent / 'fonts'


def font_face(family, file, weight, chars):
    font = TTFont(FONTS / file)
    sub = subset.Subsetter(subset.Options(flavor='woff2', layout_features=['kern', 'liga']))
    sub.populate(text=chars)
    sub.subset(font)
    font.flavor = 'woff2'
    buf = io.BytesIO(); font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}"


def svg(w, h, body, label):
    chars = ''.join(re.findall(r'>([^<]+)</text>', body)) + ' '
    style = ('<style>' + font_face('MD Hand', 'Caveat-Bold.ttf', 700, chars) + font_face('MD Sans', 'Nunito-Medium.ttf', 500, chars)
             + font_face('MD Sans', 'Nunito-Bold.ttf', 700, chars) + '</style>')
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' role='img' aria-label='{label}'>"
            "<defs>" + style +
            f"<marker id='a' viewBox='0 0 10 10' refX='8' refY='5' markerWidth='8' markerHeight='8' orient='auto-start-reverse'>"
            f"<path d='M1,1 L9,5 L1,9' fill='none' stroke='{INK}' stroke-width='1.6' stroke-linecap='round'/></marker>"
            "<pattern id='dots' width='18' height='18' patternUnits='userSpaceOnUse'><circle cx='9' cy='9' r='1.1' fill='#e8c9d6'/></pattern>"
            "<pattern id='stripe' width='8' height='8' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
            "<rect width='4' height='8' fill='#fff'/></pattern>"
            "</defs>"
            f"<rect width='{w}' height='{h}' rx='16' fill='#fffdfb'/><rect width='{w}' height='{h}' rx='16' fill='url(#dots)'/>"
            + body + '</svg>')


def how_it_works():
    b = [note(30, 36, 236, 132, ROSE, 'Owner', ['sets direction and budget', 'approves external actions', 'and deletion'], rot=-1.2),
         note(362, 36, 236, 132, ORANGE, 'Lead', ['designs experiments,', 'decides, reviews', 'every delivery'], rot=0.8),
         note(694, 36, 236, 132, LAV, 'Executor', ['runs jobs, builds pages,', 'reports results first'], rot=-0.8),
         curve(270, 78, 358, 78, label='direction'),
         curve(358, 128, 270, 128, bend=18, label='conclusions', ly=160),
         curve(602, 78, 690, 78, label='orders'),
         curve(690, 128, 602, 128, bend=18, label='asks, deliveries', ly=160),
         band(30, 214, 900, 104, SAND, 'Shared records: plain files')]
    for i, t in enumerate(['task board', 'exchange notes', 'decide / veto log', 'events', 'findings']):
        b.append(chip(50 + i * 176, 260, 160, SAND, t))
    b += [curve(480, 172, 480, 212, bend=0, label='read / write', lx=490, ly=196, anchor='start'),
          curve(812, 172, 812, 212, bend=0, label='read / write', lx=822, ly=196, anchor='start'),
          band(30, 362, 900, 118, TEAL, 'Plain programs: no model, no quota')]
    for i, (t, sub) in enumerate([('night watch', 'turns changes into events'), ('event bridge', 'wakes the right chat'),
                                  ('checks', 'flow, idle GPUs, model'), ('guardian', 'restarts local services')]):
        b.append(chip(50 + i * 220, 410, 204, TEAL, t, sub))
    b += [curve(480, 360, 480, 322, bend=0, label='watch', lx=490, ly=346, anchor='start'),
          f"<path d='M928 372 C 970 290, 970 190, 936 150' fill='none' stroke='{INK}' stroke-width='1.6' stroke-dasharray='6 5' marker-end='url(#a)'/>"
          f"<text x='962' y='270' font-family=\"{HAND}\" font-size='19' fill='{MUTED}' transform='rotate(-90 962 270)' text-anchor='middle'>wake</text>",
          doodles([('heart', 22, 30, ROSE), ('star', 652, 180, ORANGE), ('star', 918, 340, TEAL)])]
    return svg(990, 498, ''.join(b), 'Owner, Lead and Executor share plain-file records; plain programs watch the records and wake the Executor')


def wake_loop():
    steps = [('wake', TEAL, 'event or heartbeat'), ('1 · events', LAV, 'handle, acknowledge'), ('2 · idle GPUs', LAV, 'fill the queue'),
             ('3 · Lead orders', LAV, 'do each one'), ('4 · open tasks', LAV, 'move each a step'), ('only waiting?', ORANGE, 'patrol, then sleep')]
    rots = [-1.5, 1, -0.8, 1.2, -1, 0.8]
    b = []
    w, gap, y = 150, 18, 44
    for i, (t, c, sub) in enumerate(steps):
        x = 24 + i * (w + gap)
        b.append(note(x, y, w, 86, c, t, [sub], rot=rots[i], title_size=22))
        if i:
            b.append(curve(x - gap + 2, y + 44, x - 3, y + 44, bend=-8))
    x1 = 24 + (w + gap) + w / 2
    xe = 24 + 5 * (w + gap) + 30
    b.append(f"<path d='M{x1} 134 C {x1 + 10} 180, {xe - 40} 184, {xe} 138' fill='none' stroke='{RED}' stroke-width='1.6' stroke-dasharray='6 5'/>"
             f"<g stroke='{RED}' stroke-width='2.4' stroke-linecap='round'><line x1='{(x1 + xe) / 2 - 8}' y1='{168}' x2='{(x1 + xe) / 2 + 8}' y2='{184}'/>"
             f"<line x1='{(x1 + xe) / 2 + 8}' y1='{168}' x2='{(x1 + xe) / 2 - 8}' y2='{184}'/></g>"
             f"<text x='{(x1 + xe) / 2}' y='212' text-anchor='middle' font-family=\"{HAND}\" font-size='20' fill='{RED}'>"
             "old loop: slept right after the event while GPUs sat idle — the wake contract now refuses it</text>")
    b.append(doodles([('heart', 1000, 30, ROSE), ('star', 18, 150, LAV)]))
    return svg(1040, 232, ''.join(b), 'One wake: events, idle GPUs, Lead orders, open tasks; sleep only when everything left is waiting')


(OUT / 'how-it-works.svg').write_text(how_it_works(), encoding='utf-8')
(OUT / 'wake-loop.svg').write_text(wake_loop(), encoding='utf-8')
print('ok')
