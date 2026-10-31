"""Generate the README flowcharts in the notebook (手账) style of the board:
dot-grid paper, sticky notes with washi tape, highlighter titles and inked curved arrows.
Role colors match the avatars: Owner rose, Lead orange, Executor lavender, programs teal, records sand."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'images'
ROSE, ORANGE, LAV, TEAL, SAND, INK, MUTED, RED = '#d9668f', '#e0843a', '#8f6fd0', '#3f9a96', '#b8925c', '#3b2f36', '#7d6f76', '#c8524a'
NOTE = {ROSE: '#ffe4ee', ORANGE: '#ffecd9', LAV: '#efe6ff', TEAL: '#ddf3f0', SAND: '#fbf1e1'}
HAND = "'Segoe Print','Bradley Hand','Comic Sans MS','Chalkboard SE',cursive"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


def tape(cx, y, color, w=58, rot=-4):
    return (f"<g transform='rotate({rot} {cx} {y})'><rect x='{cx - w / 2}' y='{y - 8}' width='{w}' height='16' rx='2' "
            f"fill='{color}' opacity='.38'/><rect x='{cx - w / 2}' y='{y - 8}' width='{w}' height='16' rx='2' fill='url(#stripe)' opacity='.5'/></g>")


def note(x, y, w, h, color, title, lines=(), rot=0, title_size=19):
    cx = x + w / 2
    s = [f"<g transform='rotate({rot} {cx} {y + h / 2})'>",
         f"<rect x='{x + 3}' y='{y + 4}' width='{w}' height='{h}' rx='6' fill='#000' opacity='.06'/>",
         f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='{NOTE[color]}' stroke='{color}' stroke-width='1.3'/>",
         f"<text x='{cx}' y='{y + 32}' text-anchor='middle' font-family=\"{HAND}\" font-size='{title_size}' font-weight='700' fill='{color}'>{title}</text>"]
    for i, line in enumerate(lines):
        s.append(f"<text x='{cx}' y='{y + 54 + i * 18}' text-anchor='middle' font-family=\"{SANS}\" font-size='12.5' fill='{INK}'>{line}</text>")
    s.append('</g>')
    s.append(tape(cx, y, color))
    return ''.join(s)


def curve(x1, y1, x2, y2, bend=-18, label='', ly=None, lx=None, color=INK, dash=False, anchor='middle'):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
    d = " stroke-dasharray='6 5'" if dash else ''
    s = f"<path d='M{x1} {y1} Q {mx} {my} {x2} {y2}' fill='none' stroke='{color}' stroke-width='1.6' stroke-linecap='round' marker-end='url(#a)'{d}/>"
    if label:
        s += (f"<text x='{lx if lx is not None else mx}' y='{ly if ly is not None else my - 4}' text-anchor='{anchor}' "
              f"font-family=\"{HAND}\" font-size='13' fill='{MUTED}'>{label}</text>")
    return s


def band(x, y, w, h, color, title):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{NOTE[color]}' fill-opacity='.55' stroke='{color}' "
            f"stroke-width='1.4' stroke-dasharray='7 5'/>"
            f"<rect x='{x + 18}' y='{y + 14}' width='{len(title) * 8.6}' height='11' fill='{color}' opacity='.22'/>"
            f"<text x='{x + 20}' y='{y + 24}' font-family=\"{HAND}\" font-size='16' font-weight='700' fill='{color}'>{title}</text>")


def chip(x, y, w, color, text, sub=None):
    h = 46 if sub else 32
    s = (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='#fffdfb' stroke='{color}' stroke-width='1.1'/>"
         f"<text x='{x + w / 2}' y='{y + (19 if sub else 21)}' text-anchor='middle' font-family=\"{SANS}\" font-size='13' "
         f"font-weight='600' fill='{INK}'>{text}</text>")
    if sub:
        s += f"<text x='{x + w / 2}' y='{y + 37}' text-anchor='middle' font-family=\"{SANS}\" font-size='11.5' fill='{MUTED}'>{sub}</text>"
    return s


def doodles(items):
    out = []
    for kind, x, y, c in items:
        if kind == 'heart':
            out.append(f"<path d='M{x} {y + 4} c -6 -8 -16 -2 -8 6 l 8 7 l 8 -7 c 8 -8 -2 -14 -8 -6z' fill='{c}' opacity='.7'/>")
        else:
            out.append(f"<path d='M{x} {y - 7} L{x + 2} {y - 2} L{x + 7} {y} L{x + 2} {y + 2} L{x} {y + 7} L{x - 2} {y + 2} L{x - 7} {y} L{x - 2} {y - 2}z' fill='{c}' opacity='.75'/>")
    return ''.join(out)


def svg(w, h, body, label):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' role='img' aria-label='{label}'>"
            "<defs>"
            f"<marker id='a' viewBox='0 0 10 10' refX='8' refY='5' markerWidth='8' markerHeight='8' orient='auto-start-reverse'>"
            f"<path d='M1,1 L9,5 L1,9' fill='none' stroke='{INK}' stroke-width='1.6' stroke-linecap='round'/></marker>"
            "<pattern id='dots' width='18' height='18' patternUnits='userSpaceOnUse'><circle cx='9' cy='9' r='1.1' fill='#e8c9d6'/></pattern>"
            "<pattern id='stripe' width='8' height='8' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
            "<rect width='4' height='8' fill='#fff'/></pattern>"
            "</defs>"
            f"<rect width='{w}' height='{h}' rx='16' fill='#fffdfb'/><rect width='{w}' height='{h}' rx='16' fill='url(#dots)'/>"
            + body + '</svg>')


def how_it_works():
    b = [note(30, 36, 236, 104, ROSE, 'Owner', ['sets direction and budget', 'approves external actions, deletion'], rot=-1.2),
         note(362, 36, 236, 104, ORANGE, 'Lead', ['designs experiments, decides,', 'reviews every delivery'], rot=0.8),
         note(694, 36, 236, 104, LAV, 'Executor', ['runs jobs, builds pages,', 'reports results first'], rot=-0.8),
         curve(270, 70, 358, 70, label='direction'),
         curve(358, 112, 270, 112, bend=18, label='conclusions', ly=140),
         curve(602, 70, 690, 70, label='orders'),
         curve(690, 112, 602, 112, bend=18, label='asks · deliveries', ly=140),
         band(30, 186, 900, 88, SAND, 'Shared records — plain files')]
    for i, t in enumerate(['task board', 'exchange notes', 'decide / veto ledger', 'events', 'findings']):
        b.append(chip(50 + i * 176, 228, 160, SAND, t))
    b += [curve(480, 144, 480, 184, bend=0, label='read / write', lx=490, ly=168, anchor='start'),
          curve(812, 144, 812, 184, bend=0, label='read / write', lx=822, ly=168, anchor='start'),
          band(30, 320, 900, 104, TEAL, 'Plain programs — no model, no quota')]
    for i, (t, sub) in enumerate([('night watch', 'turns changes into events'), ('event bridge', 'wakes the right chat'),
                                  ('checks', 'flow, idle GPUs, model'), ('guardian', 'restarts local services')]):
        b.append(chip(50 + i * 220, 362, 204, TEAL, t, sub))
    b += [curve(480, 318, 480, 278, bend=0, label='watch', lx=490, ly=302, anchor='start'),
          f"<path d='M928 330 C 968 260, 968 170, 936 136' fill='none' stroke='{INK}' stroke-width='1.6' stroke-dasharray='6 5' marker-end='url(#a)'/>"
          f"<text x='958' y='238' font-family=\"{HAND}\" font-size='13' fill='{MUTED}' transform='rotate(-90 958 238)' text-anchor='middle'>wake</text>",
          doodles([('heart', 22, 30, ROSE), ('star', 652, 162, ORANGE), ('star', 918, 300, TEAL)])]
    return svg(980, 446, ''.join(b), 'Owner, Lead and Executor share plain-file records; plain programs watch the records and wake the Executor')


def wake_loop():
    steps = [('wake', TEAL, 'event or heartbeat'), ('1 · events', LAV, 'handle, acknowledge'), ('2 · idle GPUs', LAV, 'fill the queue'),
             ('3 · Lead orders', LAV, 'do each one'), ('4 · open tasks', LAV, 'move each a step'), ('only waiting?', ORANGE, 'patrol, then sleep')]
    rots = [-1.5, 1, -0.8, 1.2, -1, 0.8]
    b = []
    w, gap, y = 136, 20, 44
    for i, (t, c, sub) in enumerate(steps):
        x = 24 + i * (w + gap)
        b.append(note(x, y, w, 74, c, t, [sub], rot=rots[i], title_size=15))
        if i:
            b.append(curve(x - gap + 2, y + 40, x - 3, y + 40, bend=-8))
    x1 = 24 + (w + gap) + w / 2
    xe = 24 + 5 * (w + gap) + 30
    b.append(f"<path d='M{x1} 122 C {x1 + 10} 168, {xe - 40} 172, {xe} 126' fill='none' stroke='{RED}' stroke-width='1.6' stroke-dasharray='6 5'/>"
             f"<g stroke='{RED}' stroke-width='2.4' stroke-linecap='round'><line x1='{(x1 + xe) / 2 - 8}' y1='{156}' x2='{(x1 + xe) / 2 + 8}' y2='{172}'/>"
             f"<line x1='{(x1 + xe) / 2 + 8}' y1='{156}' x2='{(x1 + xe) / 2 - 8}' y2='{172}'/></g>"
             f"<text x='{(x1 + xe) / 2}' y='196' text-anchor='middle' font-family=\"{HAND}\" font-size='13.5' fill='{RED}'>"
             "old loop: slept right after the event while GPUs sat idle — the wake contract now refuses it</text>")
    b.append(doodles([('heart', 930, 30, ROSE), ('star', 18, 140, LAV)]))
    return svg(960, 214, ''.join(b), 'One wake: events, idle GPUs, Lead orders, open tasks; sleep only when everything left is waiting')


(OUT / 'how-it-works.svg').write_text(how_it_works(), encoding='utf-8')
(OUT / 'wake-loop.svg').write_text(wake_loop(), encoding='utf-8')
print('ok')
