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
        s.append(f"<text x='{cx}' y='{y + 64 + i * 23}' text-anchor='middle' font-family=\"{SANS}\" font-size='18' fill='{INK}'>{line}</text>")
    s.append('</g>')
    s.append(tape(cx, y, color))
    return ''.join(s)


def avatar(cx, cy, file, r=24):
    """Small round character sticker (the real board avatars) embedded as PNG."""
    from PIL import Image
    im = Image.open(OUT / file).convert('RGBA').resize((192, 192), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"<image x='{cx - r}' y='{cy - r}' width='{2 * r}' height='{2 * r}' href='data:image/png;base64,{data}'/>"


def curve(x1, y1, x2, y2, bend=-18, label='', ly=None, lx=None, color=INK, dash=False, anchor='middle'):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
    d = " stroke-dasharray='6 5'" if dash else ''
    s = f"<path d='M{x1} {y1} Q {mx} {my} {x2} {y2}' fill='none' stroke='{color}' stroke-width='1.6' stroke-linecap='round' marker-end='url(#a)'{d}/>"
    if label:
        s += (f"<text x='{lx if lx is not None else mx}' y='{ly if ly is not None else my - 4}' text-anchor='{anchor}' "
              f"font-family=\"{HAND}\" font-size='22' fill='{MUTED}'>{label}</text>")
    return s


def band(x, y, w, h, color, title):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{NOTE[color]}' fill-opacity='.55' stroke='{color}' "
            f"stroke-width='1.4' stroke-dasharray='7 5'/>"
            f"<rect x='{x + 18}' y='{y + 14}' width='{len(title) * 10.8}' height='15' fill='{color}' opacity='.22'/>"
            f"<text x='{x + 20}' y='{y + 31}' font-family=\"{HAND}\" font-size='27' font-weight='700' fill='{color}'>{title}</text>")


def chip(x, y, w, color, text, sub=None):
    h = 64 if sub else 44
    s = (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='#fffdfb' stroke='{color}' stroke-width='1.1'/>"
         f"<text x='{x + w / 2}' y='{y + (26 if sub else 29)}' text-anchor='middle' font-family=\"{SANS}\" font-size='18' "
         f"font-weight='600' fill='{INK}'>{text}</text>")
    if sub:
        s += f"<text x='{x + w / 2}' y='{y + 51}' text-anchor='middle' font-family=\"{SANS}\" font-size='16' fill='{MUTED}'>{sub}</text>"
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
    style = ''  # Font contours are resolved before export.
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
    b = [note(20, 36, 240, 156, ROSE, 'Owner · Big Fish', ['sets direction and budget', 'approves external actions', 'and deletion'], rot=-1.2),
         note(330, 36, 240, 156, ORANGE, 'Lead · Miss', ['designs experiments,', 'decides, reviews', 'every delivery'], rot=0.8),
         note(640, 36, 240, 156, LAV, 'Executor · Dragon', ['runs jobs, builds pages,', 'reports results first'], rot=-0.8),
         avatar(24, 40, 'avatar-owner.png', 26), avatar(334, 40, 'avatar-lead.png', 26), avatar(644, 40, 'avatar-executor.png', 26),
         curve(264, 104, 326, 104, label='direction'),
         curve(326, 152, 264, 152, bend=18, label='conclusions', ly=192),
         curve(574, 104, 636, 104, label='orders'),
         curve(636, 152, 574, 152, bend=18, label='ask / deliver', ly=192),
         band(20, 240, 860, 116, SAND, 'Shared records: plain files')]
    for i, t in enumerate(['task board', 'exchange notes', 'decide / veto log', 'events', 'findings']):
        b.append(chip(32 + i * 168, 292, 158, SAND, t))
    b += [curve(450, 196, 450, 238, bend=0, label='read / write', lx=460, ly=222, anchor='start'),
          curve(760, 196, 760, 238, bend=0, label='read / write', lx=770, ly=222, anchor='start'),
          band(20, 410, 860, 138, TEAL, 'Plain programs: no model, no quota')]
    for i, (t, sub) in enumerate([('night watch', 'turns changes into events'), ('event bridge', 'wakes the right chat'),
                                  ('checks', 'flow, jobs, idle GPUs'), ('guardian', 'restarts local services')]):
        b.append(chip(32 + i * 211, 464, 203, TEAL, t, sub))
    b += [curve(450, 408, 450, 360, bend=0, label='watch', lx=460, ly=390, anchor='start'),
          f"<path d='M882 420 C 916 340, 916 210, 886 150' fill='none' stroke='{INK}' stroke-width='1.6' stroke-dasharray='6 5' marker-end='url(#a)'/>"
          f"<text x='910' y='300' font-family=\"{HAND}\" font-size='22' fill='{MUTED}' transform='rotate(-90 910 300)' text-anchor='middle'>wake</text>",
          doodles([('heart', 14, 222, ROSE), ('star', 612, 210, ORANGE), ('star', 900, 560, TEAL)])]
    return svg(930, 572, ''.join(b), 'Owner, Lead and Executor share plain-file records; plain programs watch the records and wake the Executor')


def wake_loop():
    steps = [('wake', TEAL, 'event or heartbeat'), ('1 · events', LAV, 'handle, acknowledge'), ('2 · idle GPUs', LAV, 'fill the queue'),
             ('3 · Lead orders', LAV, 'do each one'), ('4 · open tasks', LAV, 'move each a step'), ('only waiting?', ORANGE, 'patrol, then sleep')]
    rots = [-1.5, 1, -0.8, 1.2, -1, 0.8]
    b = []
    w, gap, h = 250, 45, 96
    pos = [(25 + (i % 3) * (w + gap), 44 + (i // 3) * 160) for i in range(6)]
    for i, (t, c, sub) in enumerate(steps):
        x, y = pos[i]
        b.append(note(x, y, w, h, c, t, [sub], rot=rots[i], title_size=26))
        if i % 3:
            px = pos[i - 1][0] + w
            b.append(curve(px + 3, y + 48, x - 3, y + 48, bend=-6))
    x2, y2 = pos[2]; x3, y3 = pos[3]
    b.append(f"<path d='M{x2 + w / 2} {y2 + h + 4} C {x2 + w / 2} {y2 + h + 40}, {x3 + w / 2} {y3 - 44}, {x3 + w / 2} {y3 - 6}' fill='none' stroke='{INK}' stroke-width='1.6' marker-end='url(#a)'/>")
    xe, ye = pos[1]
    xs = xe + w / 2 + 60; xt = pos[5][0] + w - 20
    b.append(f"<path d='M{xs} {ye + h + 4} C {xs + 60} {ye + h + 60}, {xt} {ye + h + 30}, {xt} {pos[5][1] - 6}' fill='none' stroke='{RED}' stroke-width='1.6' stroke-dasharray='6 5'/>"
             f"<g stroke='{RED}' stroke-width='2.4' stroke-linecap='round'><line x1='{xt - 70}' y1='{ye + h + 26}' x2='{xt - 54}' y2='{ye + h + 42}'/>"
             f"<line x1='{xt - 54}' y1='{ye + h + 26}' x2='{xt - 70}' y2='{ye + h + 42}'/></g>"
             f"<text x='450' y='{pos[5][1] + h + 44}' text-anchor='middle' font-family=\"{HAND}\" font-size='22' fill='{RED}'>"
             "old loop: slept right after the event while GPUs sat idle — the wake contract now refuses it</text>")
    b.append(doodles([('heart', 880, 30, ROSE), ('star', 14, 200, LAV)]))
    return svg(900, 400, ''.join(b), 'One wake: events, idle GPUs, Lead orders, open tasks; sleep only when everything left is waiting')


# The new diagrams reuse all existing notebook primitives and embedded fonts.
import textwrap
import json
import xml.etree.ElementTree as ET

NOTE[RED] = '#fff0ed'
AUDIT = {}


def ink_text(x, y, text, size=14, color=MUTED, anchor='middle', hand=False):
    return (f"<text x='{x}' y='{y}' text-anchor='{anchor}' font-family=\"{HAND if hand else SANS}\" "
            f"font-size='{size}' fill='{color}'>{text}</text>")


STICKY_TITLE = 21
CAPTION = (14, 18, 7.4)  # architecture diagrams; the README one uses a larger size


def caption(x, y, w, text, color=MUTED):
    size, step, per = CAPTION
    return ''.join(ink_text(x + w/2, y + i*step, line, size=size, color=color)
                   for i, line in enumerate(textwrap.wrap(text, max(16, int(w/per)))))


def sticky(key, x, y, w, color, title, detail, unit='', rot=0):
    lines = [unit] if unit else []
    assert len((' '.join([title, *lines])).split()) <= 6, title
    AUDIT.setdefault(key, []).append(dict(title=title, lines=lines, detail=detail))
    height = 84 if unit else 68
    return (note(x, y, w, height, color, title, lines, rot=rot, title_size=STICKY_TITLE)
            + caption(x, y + height + 21, w, detail))


def diagram_heading(title, subtitle):
    return ink_text(32, 43, title, 32, INK, 'start', True) + ink_text(34, 72, subtitle, 15, MUTED, 'start')


def elbow(points, color=INK, dash=False, label='', label_xy=None):
    parts = ['M'+str(points[0][0])+' '+str(points[0][1])]
    for x, y in points[1:]:parts.append('L'+str(x)+' '+str(y))
    stroke = " stroke-dasharray='7 5'" if dash else ''
    body = f"<path d='{' '.join(parts)}' fill='none' stroke='{color}' stroke-width='1.6' stroke-linejoin='round' marker-end='url(#a)'{stroke}/>"
    if label and label_xy:body += ink_text(*label_xy, label, 16, color, hand=True)
    return body


def question_life():
    key='question-life';AUDIT[key]=[]
    body=[diagram_heading("A question's life", 'Follow the numbered records through five roles; time grows from seconds to hours.')]
    lanes=[('Owner',ROSE),('Lead',ORANGE),('Executor',LAV),('Plain programs',TEAL),('Files',SAND)]
    for i,(title,color) in enumerate(lanes):body.append(band(18,94+i*174,1164,154,color,title))
    # Edges sit behind the notes, with separate return corridors between columns.
    body += [curve(203,255,203,818,bend=0),curve(274,860,309,686,bend=12),
             curve(454,686,489,686,bend=-8),elbow([(634,686),(650,686),(650,512),(634,512)]),
             curve(563,470,672,338,bend=-12),elbow([(814,338),(830,338),(830,512),(814,512)]),
             elbow([(672,512),(654,512),(654,608),(840,608),(840,686),(852,686)]),curve(994,686,1029,686,bend=-8),
             elbow([(1174,686),(1188,686),(1188,512),(1174,512)]),elbow([(1103,470),(1103,448),(1188,448),(1188,338),(1174,338)]),
             elbow([(1032,338),(1018,338),(1018,860),(994,860)]),
             elbow([(923,818),(923,790),(1008,790),(1008,164),(1032,164)]),
             elbow([(1032,364),(1000,364),(1000,432),(743,432),(743,470)],RED,True,'reject',(868,424))]
    data=[(132,122,ROSE,'Owner asks','Did tuning skip a model?','seconds',-1),
          (132,818,SAND,'Record message','Original message stays.','seconds',.7),
          (312,644,TEAL,'Night watch','Create an event from the message.','seconds',-.5),
          (492,644,TEAL,'Bridge wakes','Wake the Executor chat.','seconds',.8),
          (492,470,LAV,'ask #2884','Question kind: design.','minutes',-.8),
          (672,296,ORANGE,'answer #2884','Lead answers in exchange notes.','minutes',.7),
          (672,470,LAV,'Task + queue','Create contract; queue work.','minutes',-.6),
          (852,644,TEAL,'Dispatcher','Run on an available GPU.','hours',.7),
          (1032,644,TEAL,'Job done','Create the completion event.','hours',-.7),
          (1032,470,LAV,'Deliver: 3','First line is a number.','minutes',.6),
          (1032,296,ORANGE,'Review','Accept or send work back.','minutes',-.8),
          (852,818,SAND,'Write finding','Retain the accepted result.','seconds',.8),
          (1032,122,ROSE,'Result arrives','One result sentence in discussion.','seconds',-.6)]
    body += [sticky(key,x,y,142,color,title,detail,unit,rot) for x,y,color,title,detail,unit,rot in data]
    body += [ink_text(34,976,'A rejected delivery returns to Executor; the original question and evidence remain linked.',15,MUTED,'start'),
             doodles([('heart',1154,39,ROSE),('star',1133,969,TEAL)])]
    return svg(1200,1000,''.join(body),'Question life across Owner, Lead, Executor, programs and files')


def who_decides():
    key='who-decides';AUDIT[key]=[]
    body=[diagram_heading('Who decides what', 'Routine choices stay with Executor; consequential choices cross a recorded gate.'),
          band(28,104,350,558,SAND,'Three levels of authority'),
          band(432,290,290,280,ORANGE,'Five ask kinds'),
          band(790,104,380,266,ROSE,'Only Owner can act'),
          band(790,450,380,214,SAND,'Decision ledger')]
    body += [curve(200,280,200,306,bend=0),curve(200,440,200,466,bend=0),
             curve(338,490,429,490,label='ask',ly=464),
             elbow([(432,350),(400,350),(338,350)],ORANGE),
             elbow([(338,336),(398,336),(398,248),(790,248)],ROSE,False,'only-owner step',(590,235)),
             elbow([(338,510),(398,510),(398,630),(790,630)],SAND,False,'decide',(590,620)),
             elbow([(790,650),(700,650),(700,713),(356,713),(356,508),(338,508)],RED,True,'veto',(486,704))]
    body += [sticky(key,58,146,280,ROSE,'Owner','Pays, sends, deletes, consents.','Only-owner actions',-.7),
             sticky(key,58,306,280,ORANGE,'Lead','Budget, conclusions, research decisions.','Design + acceptance',.7),
             sticky(key,58,466,280,LAV,'Executor','Log routine choices with decide.','Everything else',-.6)]
    for i,(left,right) in enumerate([('design','budget'),('conclusions','external'),('deletion',None)]):
        y=342+i*67
        body.append(chip(452,y,118,ORANGE,left))
        if right:body.append(chip(584,y,118,ORANGE,right))
    for i,title in enumerate(['A license page','A rental extension','An external email']):
        body.append(chip(812,154+i*61,336,ROSE,title))
    body += [chip(812,502,336,SAND,'decide keeps the choice'),chip(812,558,336,ORANGE,'Lead audits; may veto'),
             ink_text(34,766,'Questions and overrides stay in the ledger, alongside their original choices.',16,MUTED,'start'),
             doodles([('heart',1152,42,ROSE),('star',753,390,ORANGE)])]
    return svg(1200,794,''.join(body),'Authority levels, five question kinds, decision records and only-owner escalation')


def gpu_job_life():
    key='gpu-job-life';AUDIT[key]=[]
    body=[diagram_heading("A GPU job's life", 'Completion, time limits and crashes take distinct paths through the deployment adapter.'),
          band(24,104,1152,472,TEAL,'Dispatch and outcomes'),band(24,606,710,246,LAV,'Idle watch'),
          band(24,900,1152,140,ROSE,'Before paying for a rental')]
    body += [curve(200,188,257,188),curve(420,188,477,188),curve(640,188,757,188),
             curve(640,198,757,328,bend=10),curve(640,208,757,488,bend=24),
             curve(920,188,997,188),elbow([(1160,180),(1176,180),(1176,342),(1160,342)]),
             elbow([(760,354),(716,354),(716,562),(28,562),(28,180),(40,180)],TEAL,False,'save + requeue',(386,550)),
             curve(920,488,997,488),
             elbow([(1080,454),(1080,432),(650,432),(650,180),(640,180)],RED,True,'retry',(682,422)),
             elbow([(1160,488),(1176,488),(1176,686),(1160,686)],RED,False,'after 3 retries',(1060,620)),
             elbow([(1160,350),(1188,350),(1188,822),(1160,822)]),
             curve(240,710,277,710),curve(458,710,495,710)]
    data=[(40,146,160,TEAL,'Queue','A ready job waits.'),
          (260,146,160,TEAL,'Dispatcher','GPU preference; flexible placement.'),
          (480,146,160,LAV,'Running','Retain the exact job identity.'),
          (760,146,160,TEAL,'Done','Completed work advances.'),
          (1000,146,160,TEAL,'Score','Official + independent evaluation.'),
          (1000,308,160,SAND,'Return locally','Verify file checksums.'),
          (760,312,160,TEAL,'Time limit','Save items; requeue; zero failures.'),
          (760,454,160,RED,'Crashed','Keep the failure receipt.'),
          (1000,454,160,RED,'Retry up to 3','A bounded recovery path.'),
          (1000,652,160,RED,'Failed','Retain all attempt records.'),
          (1000,790,160,ORANGE,'Lead review','Accept or return the result.'),
          (60,670,180,TEAL,'10-min average','Utilization below 10%.'),
          (278,670,180,LAV,'30 minutes','Executor investigates.'),
          (496,670,180,ORANGE,'60 minutes','Lead steps in.')]
    for index,(x,y,w,color,title,detail) in enumerate(data):body.append(sticky(key,x,y,w,color,title,detail,rot=(-.8 if index%2 else .7)))
    body.append(ink_text(378,827,'Memory allocation alone is a separate observation.',15,MUTED))
    for i,title in enumerate(['Queue ready','Dry run passed','Scorer has own GPU','Stop timer set']):
        body.append(chip(46+i*280,956,260,ROSE,title))
    body.append(doodles([('star',1154,40,TEAL),('heart',1150,1017,ROSE)]))
    return svg(1200,1060,''.join(body),'GPU job lifecycle with completion, time-limit requeue, bounded retries, idle watch and rental checklist')


def mistake_to_program():
    """Six flashcards in two staggered columns. Card color = kind of problem (tag top-right);
    red ✗ marks the mistake, green ✓ the rule now in code. Character stickers break the grid."""
    key = 'mistake-to-program'; AUDIT[key] = []
    pairs = [('One event, then sleep', 'GPUs sat idle.', 'Wake lists all work', 'Events, orders, tasks, idle cards.', 'wake', ROSE),
             ('GPU memory held', 'Computation stayed idle.', 'Watch utilization', 'Idle uses the 10-minute average.', 'GPUs', ORANGE),
             ('Time limit became failure', 'Finished items were discarded.', 'Save and requeue', 'Time limits retain completed items.', 'jobs', TEAL),
             ('Promises replaced results', 'The update was only a promise.', 'Check message content', 'Refuse promises; require concrete results.', 'reports', LAV),
             ('Model silently weakened', 'The chat used another model.', 'Owner chooses each model', 'Each chat uses the selected model.', 'models', ORANGE),
             ('Reports became cloud-only', 'Linked evidence left local storage.', 'Keep linked files local', 'Board-linked files retain readable bytes.', 'files', SAND)]
    W, w, h, top, gx, gy, stagger = 960, 446, 236, 112, 28, 34, 78
    rots = (-1.3, 1.1, 0.9, -1.2, -0.8, 1.3)
    cross = lambda x, y, c: (f"<path d='M{x - 7} {y - 7} L{x + 7} {y + 7} M{x + 7} {y - 7} L{x - 7} {y + 7}' stroke='{c}' "
                             f"stroke-width='3' stroke-linecap='round'/>")
    tick = lambda x, y, c: f"<path d='M{x - 8} {y} L{x - 2} {y + 7} L{x + 9} {y - 8}' fill='none' stroke='{c}' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'/>"
    GREEN = '#3f9a6a'
    b = [diagram_heading('Mistake → program', 'Repeated operational mistakes become executable checks.')]
    # 图例放在右列错开后留出的空白里
    lx = 20 + w + gx + 40; ly = top + 34
    b += [f"<rect x='{lx - 18}' y='{ly - 30}' width='{w - 44}' height='58' rx='29' fill='#fffdfb' stroke='{MUTED}' stroke-width='1' stroke-dasharray='5 4'/>",
          cross(lx + 4, ly, RED), ink_text(lx + 20, ly + 8, 'seen twice', 22, RED, 'start', True),
          f"<path d='M{lx + 150} {ly} L{lx + 205} {ly}' stroke='{INK}' stroke-width='1.6' marker-end='url(#a)'/>",
          tick(lx + 232, ly + 1, GREEN), ink_text(lx + 250, ly + 8, 'move into code', 22, GREEN, 'start', True)]
    stickers = {}
    for i, (old, old_detail, new, new_detail, tag, col) in enumerate(pairs):
        AUDIT[key] += [dict(title=old, lines=[], detail=old_detail), dict(title=new, lines=[], detail=new_detail)]
        c, r = i % 2, i // 2
        x = 20 + c * (w + gx); y = top + r * (h + gy) + (stagger if c else 0); cx = x + w / 2; rot = rots[i]
        half = 114; tint = NOTE[col]
        tw = len(tag) * 9 + 26
        b += [f"<g transform='rotate({rot} {cx} {y + h / 2})'>",
              f"<rect x='{x + 5}' y='{y + 6}' width='{w}' height='{h}' rx='10' fill='#000' opacity='.07'/>",
              f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='#fffdfb' stroke='{col}' stroke-width='1.4'/>",
              f"<path d='M{x} {y + 10} a10 10 0 0 1 10 -10 h{w - 20} a10 10 0 0 1 10 10 v{half - 10} h{-w}z' fill='{tint}'/>",
              f"<line x1='{x + 14}' x2='{x + w - 14}' y1='{y + half + 8}' y2='{y + half + 8}' stroke='{col}' stroke-width='1.2' stroke-dasharray='5 5' opacity='.6'/>",
              f"<circle cx='{x + 26}' cy='{y + 27}' r='16' fill='{col}'/>",
              ink_text(x + 26, y + 35, str(i + 1), 21, '#fffdfb', hand=True),
              f"<rect x='{x + w - tw - 16}' y='{y + 14}' width='{tw}' height='26' rx='13' fill='#fffdfb' stroke='{col}' stroke-width='1.2'/>",
              ink_text(x + w - 16 - tw / 2, y + 32, tag, 15, col),
              cross(x + 62, y + 60, RED), ink_text(x + 80, y + 68, old, 25, INK, 'start', True),
              ink_text(x + 80, y + 95, old_detail, 17, MUTED, 'start'),
              f"<circle cx='{cx}' cy='{y + half + 8}' r='15' fill='#fffdfb' stroke='{col}' stroke-width='1.5'/>",
              f"<path d='M{cx} {y + half} L{cx} {y + half + 14} M{cx - 6} {y + half + 8} L{cx} {y + half + 15} L{cx + 6} {y + half + 8}' "
              f"fill='none' stroke='{col}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>",
              tick(x + 62, y + half + 60, GREEN), ink_text(x + 80, y + half + 68, new, 25, col, 'start', True),
              ink_text(x + 80, y + half + 96, new_detail, 17, INK, 'start'),
              '</g>', tape(cx + (-40 if c else 40), y, col, w=78, rot=rot * 4)]
        if i in stickers:
            f, side = stickers[i]
            sx = x + w - 8 if side == 'right' else x + 8
            b += [f"<circle cx='{sx}' cy='{y + h - 6}' r='37' fill='#fffdfb' stroke='{col}' stroke-width='3'/>", avatar(sx, y + h - 6, f, r=34)]
    H = top + 3 * h + 2 * gy + stagger + 28
    b += [doodles([('star', 930, 80, ORANGE), ('star', 30, H - 40, LAV),
                   ('star', 470, top + h + 18, TEAL), ('heart', 488, top + 2 * h + gy + 50, LAV)])]
    return svg(W, H, ''.join(b), 'Six recurring mistakes become six executable safeguards')


def write_extended_diagrams():
    diagrams={'question-life':question_life,'who-decides':who_decides,
              'gpu-job-life':gpu_job_life,'mistake-to-program':mistake_to_program}
    audit={}
    for name,render in diagrams.items():
        raw=render();ET.fromstring(raw)
        (OUT/(name+'.svg')).write_text(outlined(raw,'en'),encoding='utf-8')
        if name=='mistake-to-program':
            (OUT/(name+'.zh-CN.svg')).write_text(outlined(raw,'zh-CN'),encoding='utf-8')
        texts=[node.text for node in ET.fromstring(raw).iter() if node.tag.endswith('}text')]
        audit[name]=dict(texts=texts,notes=AUDIT[name],min_body_px=14,title_px=32,width=1200)
    work=OUT.parents[1]/'work/t214-shots';work.mkdir(parents=True,exist_ok=True)
    (work/'diagram-text-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')



CAST = {
    'en': dict(title='Cast', label='Cast: Big Fish the owner, Miss the lead, Dragon the executor',
               people=[('Big Fish', 'Owner', ['Direction', 'Budget', 'Final say']),
                       ('Miss', 'Lead', ['Design', 'Decide', 'Review']),
                       ('Dragon', 'Executor', ['Run', 'Build', 'Report'])]),
    'zh-CN': dict(title='登场人物', label='登场人物：发起人大肥鱼、主线大小姐、执行龙娘',
                  people=[('大肥鱼', '发起人', ['方向', '预算', '最终拍板']),
                          ('大小姐', '主线', ['设计', '决定', '验收']),
                          ('龙娘', '执行', ['执行', '搭建', '汇报'])]),
}


def pill_width(text, zh):
    if zh:
        return len(text) * 19 + 26
    from diagram_labels import font, glyph
    f, _, _ = font('Nunito-Bold.ttf')
    return sum(glyph('Nunito-Bold.ttf', ch)[1] for ch in text) * 17 / f['head'].unitsPerEm + 28


def pill_rows(items, zh, limit):
    rows, row, used = [], [], 0
    for item in items:
        width = pill_width(item, zh) + (8 if row else 0)
        if row and used + width > limit:
            rows.append(row); row, used = [], 0; width -= 8
        row.append(item); used += width
    return rows + [row]


def cast_card(language):
    """README character cards: one taped note per role, avatar in a colored ring, name, role, three duty pills."""
    c = CAST[language]
    zh = language != 'en'
    colors = [ROSE, ORANGE, LAV]
    files = ['avatar-owner.png', 'avatar-lead.png', 'avatar-executor.png']
    rots = [-1.6, 1.2, -1.0]
    extra = max(len(pill_rows(d, zh, 240)) for _, _, d in c['people']) - 1
    W, H, w, h, top = 930, 420 + 42 * extra, 270, 312 + 42 * extra, 78
    b = [f"<rect x='28' y='22' width='{len(c['title']) * (30 if zh else 15) + 14}' height='18' fill='{ROSE}' opacity='.22'/>",
         f"<text x='34' y='44' font-family=\"{HAND}\" font-size='34' font-weight='700' fill='{ROSE}'>{c['title']}</text>"]
    for i, (name, role, duties) in enumerate(c['people']):
        x = 30 + i * (w + 30); cx = x + w / 2; col = colors[i]
        g = [f"<g transform='rotate({rots[i]} {cx} {top + h / 2})'>",
             f"<rect x='{x + 4}' y='{top + 5}' width='{w}' height='{h}' rx='8' fill='#000' opacity='.06'/>",
             f"<rect x='{x}' y='{top}' width='{w}' height='{h}' rx='8' fill='{NOTE[col]}' stroke='{col}' stroke-width='1.3'/>",
             f"<circle cx='{cx}' cy='{top + 100}' r='66' fill='#fff' stroke='{col}' stroke-width='4'/>",
             avatar(cx, top + 100, files[i], r=62),
             f"<text x='{cx}' y='{top + 206}' text-anchor='middle' font-family=\"{HAND}\" font-size='{34 if zh else 38}' font-weight='700' fill='{col}'>{name}</text>",
             f"<text x='{cx}' y='{top + 234}' text-anchor='middle' font-family=\"{HAND}\" font-size='{18 if zh else 22}' fill='{MUTED}'>{role}</text>"]
        for r, row in enumerate(pill_rows(duties, zh, w - 30)):
            widths = [pill_width(d, zh) for d in row]
            px = cx - (sum(widths) + 8 * (len(row) - 1)) / 2
            for d, pw in zip(row, widths):
                y = top + 252 + r * 42
                g.append(f"<rect x='{px}' y='{y}' width='{pw}' height='34' rx='17' fill='#fffdfb' stroke='{col}' stroke-width='1.2'/>"
                         f"<text x='{px + pw / 2}' y='{y + 23}' text-anchor='middle' font-family=\"{HAND}\" font-size='{17 if zh else 21}' font-weight='600' fill='{INK}'>{d}</text>")
                px += pw + 8
        g.append('</g>')
        b += g + [tape(cx, top, col, w=74, rot=rots[i] * 2)]
    b.append(doodles([('star', 905, 40, ORANGE), ('heart', 880, H - 22, ROSE), ('star', 18, H - 20, LAV)]))
    return svg(W, H, ''.join(b), c['label'])


if __name__ == '__main__':
    from diagram_labels import outlined
    for name, render in [('how-it-works', how_it_works), ('wake-loop', wake_loop)]:
        raw = render()
        for language in ['en', 'zh-CN']:
            suffix = '' if language == 'en' else '.zh-CN'
            (OUT / (name + suffix + '.svg')).write_text(outlined(raw, language), encoding='utf-8')
    from diagram_labels import ZH
    for language in ['en', 'zh-CN']:
        raw = cast_card(language)
        if language != 'en':  # 中文版直接用中文排版，outlined 只需原样映射
            ZH.update({s: s for s in re.findall(r">([^<>]+)</text>", raw)}); ZH[CAST[language]['label']] = CAST[language]['label']
        (OUT / ('cast' + ('' if language == 'en' else '.zh-CN') + '.svg')).write_text(outlined(raw, language), encoding='utf-8')
    print('four language-specific SVGs exported with accessible glyph outlines')
    write_extended_diagrams()
