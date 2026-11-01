"""Architecture-guide diagrams in the README notebook style, with role names You / Claude / GPT.

Four figures reuse the README and extended generators and are relabelled; two are drawn here:
communication channels and what wakes the assistants. Run: python scripts/make_architecture_diagrams.py
Outputs docs/architecture/0N-*.svg and .zh-CN.svg (glyph-outlined, no font dependency).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_readme_diagrams as M
from make_readme_diagrams import (ROSE, ORANGE, LAV, TEAL, SAND, INK, MUTED, NOTE, HAND, SANS, RED,
                                  avatar, curve, doodles, ink_text, svg, tape)
from diagram_labels import ZH, outlined

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'architecture'

# ---------- relabelling of the reused figures ----------
FIX = {'You · Big Fish': 'You', 'Claude · Miss': 'Claude · Lead', 'GPT · Dragon': 'GPT · Executor',
       'You asks': 'You ask', 'Only You can act': 'Only you can act', 'only-owner step': 'your call',
       'Only-owner actions': 'Only you',
       'You, Claude and GPT share plain-file records; plain programs watch the records and wake the GPT':
           'You, Claude and GPT share plain-file records; plain programs watch them and wake GPT',
       'Authority levels, five question kinds, decision records and only-owner escalation':
           'Authority levels, five question kinds, decision records and what only you decide',
       '1 · events': '1 · messages, events', 'handle, acknowledge': 'read, handle, ack',
       '4 · open tasks': '4 · open + returned', 'move each a step': 'move each a step',
       'Question life across You, Claude, GPT, programs and files':
           'A question travels through you, Claude, GPT, programs and files'}


def relabel(raw):
    def one(s):
        s = re.sub(r'\bOwner\b', 'You', re.sub(r'\bLead\b', 'Claude', re.sub(r'\bExecutor\b', 'GPT', s)))
        return FIX.get(s, s)
    raw = re.sub(r'>([^<>]+)</text>', lambda m: '>' + one(m.group(1)) + '</text>', raw)
    return re.sub(r"aria-label='([^']*)'", lambda m: "aria-label='" + one(m.group(1)) + "'", raw)


ZH_ARCH = {
    # how it works
    'You': '你', 'Claude · Lead': 'Claude · 主线', 'GPT · Executor': 'GPT · 执行',
    'sets direction and budget': '定方向与预算', 'approves external actions': '批准对外行动', 'and deletion': '与删除范围',
    'designs experiments,': '设计实验', 'decides, reviews': '拍板与审阅', 'every delivery': '验收每份成果',
    'runs jobs, builds pages,': '跑作业、搭页面', 'reports results first': '先汇报具体结果',
    'direction': '方向', 'conclusions': '结论', 'orders': '指令', 'ask / deliver': '提问交付',
    'Shared records: plain files': '共享记录：普通文件', 'task board': '任务看板', 'exchange notes': '交流板',
    'decide / veto log': '决定与否决记录', 'events': '事件', 'findings': '研究发现', 'read / write': '读写',
    'Plain programs: no model, no quota': '普通程序：不用模型、不花额度', 'night watch': '守夜人',
    'turns changes into events': '把变化变成事件', 'event bridge': '事件桥', 'wakes the right chat': '叫醒对应会话',
    'checks': '检查', 'flow, jobs, idle GPUs': '流程、作业与空卡', 'guardian': '卫士', 'restarts local services': '服务挂了就拉起来',
    'watch': '观察', 'wake': '叫醒',
    'You, Claude and GPT share plain-file records; plain programs watch them and wake GPT':
        '你、Claude 和 GPT 共用文件记录；普通程序看着记录并叫醒 GPT',
    # wake loop
    'event or heartbeat': '事件或兜底心跳', '1 · events': '1 · 事件', 'handle, acknowledge': '处理并登记',
    '1 · messages, events': '1 · 消息与事件', 'read, handle, ack': '读、处理、登记', '4 · open + returned': '4 · 进行中与退回的活',
    '2 · idle GPUs': '2 · 空卡', 'fill the queue': '补满队列', '3 · Claude orders': '3 · Claude 的指令', 'do each one': '逐条做完',
    '4 · open tasks': '4 · 进行中的任务', 'move each a step': '每项推进一步', 'only waiting?': '只剩等待？',
    'patrol, then sleep': '登记巡检再休息',
    'old loop: slept right after the event while GPUs sat idle — the wake contract now refuses it':
        '旧做法：处理完事件就睡，空卡一直闲着——现在的醒来约定不允许这样',
    'One wake: events, idle GPUs, Claude orders, open tasks; sleep only when everything left is waiting':
        '一轮醒来：事件、空卡、Claude 的指令、进行中任务，只剩等待时才休息',
    # question life
    "A question's life": '一个问题的一生', 'Follow the numbered records through five roles; time grows from seconds to hours.':
        '顺着编号走过五条泳道；时间从几秒长到几小时。',
    'Claude': 'Claude', 'GPT': 'GPT', 'Plain programs': '普通程序', 'Files': '文件', 'reject': '退回',
    'You ask': '你提问', 'seconds': '几秒', 'minutes': '几分钟', 'hours': '几小时',
    'Did tuning skip a': '调参时是不是', 'model?': '漏了一个模型？',
    'Record message': '记下消息', 'Original message': '原话原样', 'stays.': '保留。',
    'Night watch': '守夜人', 'Create an event': '从这条消息', 'from the message.': '生成一个事件。',
    'Bridge wakes': '事件桥叫醒', 'Wake the GPT': '叫醒 GPT', 'chat.': '会话。',
    'ask #2884': '提问 #2884', 'Question kind:': '提问类别：', 'design.': '设计。',
    'answer #2884': '回答 #2884', 'Claude answers in': 'Claude 在交流板', 'exchange notes.': '上作答。',
    'Task + queue': '建任务、排队', 'Create contract;': '写清交付要求，', 'queue work.': '排进队列。',
    'Dispatcher': '调度器', 'Run on an available': '在有空的显卡', 'GPU.': '上运行。',
    'Job done': '作业完成', 'Create the': '生成', 'completion event.': '完成事件。',
    'Deliver: 3': '交付：3', 'First line is a': '第一句', 'number.': '就是数字。',
    'Review': '验收', 'Accept or send work': '通过，或退回', 'back.': '重做。',
    'Write finding': '写进研究发现', 'Retain the accepted': '保留验收过的', 'result.': '结果。',
    'Result arrives': '结果送达', 'One result sentence': '在讨论室用', 'in discussion.': '一句话说结果。',
    'A rejected delivery returns to GPT; the original question and evidence remain linked.':
        '退回的交付回到 GPT 手里，原问题和证据始终连在一起。',
    'A question travels through you, Claude, GPT, programs and files': '一个问题走过你、Claude、GPT、程序和文件',
    # who decides
    'Who decides what': '谁来决定什么', 'Routine choices stay with GPT; consequential choices cross a recorded gate.':
        '日常选择由 GPT 自己定；要紧的选择要过一道留记录的关口。',
    'Three levels of authority': '三层决定权', 'Five ask kinds': '五类提问', 'Only you can act': '只有你能做的',
    'Decision ledger': '决定记录', 'ask': '提问', 'your call': '交给你', 'decide': '自定', 'veto': '否决',
    'Only you': '只有你', 'Pays, sends, deletes, consents.': '付钱、发出、删除、同意条款。',
    'Design + acceptance': '设计与验收', 'Budget, conclusions, research': '预算、结论与研究', 'decisions.': '上的决定。',
    'Everything else': '其余一切', 'Log routine choices with decide.': '日常选择用“自定”记一笔。',
    'design': '设计', 'budget': '预算', 'external': '对外', 'deletion': '删除',
    'A license page': '一份许可协议', 'A rental extension': '一次续租', 'An external email': '一封对外邮件',
    'decide keeps the choice': '“自定”留下选择', 'Claude audits; may veto': 'Claude 抽查，可以否决',
    'Questions and overrides stay in the ledger, alongside their original choices.': '提问和否决都留在记录里，和原来的选择放在一起。',
    'Authority levels, five question kinds, decision records and what only you decide': '三层决定权、五类提问、决定记录，以及只有你能定的事',
}

# ---------- two new figures ----------
TEXT = {
    'en': dict(
        ch_title='Where conversations live', ch_sub='Four places, each with its own people and purpose.',
        room='Discussion room', room1='You, Claude and GPT', room2='Results in one sentence;', room3='your questions and asks.',
        priv='Private chats', priv1='You with Claude, you with GPT', priv2='One-to-one and kept apart;', priv3='never mixed into the room.',
        exch='Exchange notes', exch1='Claude and GPT', exch2='ask · answer · decide · veto;', exch3='every question has a number.',
        ev='Events', ev1='Programs to the right chat', ev2='Task changes become events;', ev3='an optional bridge wakes a chat.',
        ch_label='Discussion room, private chats, exchange notes and events, each with its participants',
        ca_title='What wakes the assistants', ca_sub='Programs watch all the time; the model chats work when there is something to do.',
        progs='Plain programs: no model', chats='Model chats',
        nw='Night watch', nw1='every 10 min', gd='Guardian', gd1='every 5 min; restarts the board', br='Event bridge', br1='on each event',
        sc='Quota scheduler', sc1='after each patrol',
        gpt='GPT chats', gpt1='woken by events or mentions;', gpt2='fallback 60–120 min',
        cl='Claude', cl1='patrol about every 2 h;', cl2='sooner when mentioned',
        e1='events', e2='wake', e3='next interval', e4='restarts the board',
        ca_label='Programs watch continuously and wake the GPT and Claude chats on events or by quota-based intervals'),
    'zh-CN': dict(
        ch_title='对话放在哪里', ch_sub='四个地方，各有各的人和用处。',
        room='讨论室', room1='你、Claude、GPT', room2='一句话说结果；', room3='你的提问和要求。',
        priv='私聊', priv1='你和 Claude，你和 GPT', priv2='一对一，各自分开；', priv3='不混进讨论室。',
        exch='交流板', exch1='Claude 和 GPT', exch2='提问 · 回答 · 自定 · 否决；', exch3='每个问题都有编号。',
        ev='事件', ev1='程序发给对应会话', ev2='任务变化写成事件；', ev3='可选的事件桥叫醒会话。',
        ch_label='讨论室、私聊、交流板和事件，各自的参与者和用处',
        ca_title='谁来叫醒助手', ca_sub='程序一直盯着；模型会话有事才干活。',
        progs='普通程序：不用模型', chats='模型会话',
        nw='守夜人', nw1='每 10 分钟', gd='卫士', gd1='每 5 分钟，看板挂了就拉起', br='事件桥', br1='每个事件立即', sc='额度调度', sc1='每次巡检后',
        gpt='GPT 会话', gpt1='有事件、被点名就叫醒；', gpt2='兜底 60–120 分钟',
        cl='Claude', cl1='约每 2 小时巡检；', cl2='被点名就提前',
        e1='事件', e2='叫醒', e3='下次间隔', e4='拉起看板',
        ca_label='程序持续观察，按事件或按额度算出的间隔叫醒 GPT 和 Claude 会话'),
}
FACES = {'you': 'avatar-owner.png', 'claude': 'avatar-lead.png', 'gpt': 'avatar-executor.png'}


def face(cx, cy, who, color, r=24):
    return (f"<circle cx='{cx}' cy='{cy}' r='{r + 3}' fill='#fffdfb' stroke='{color}' stroke-width='2.5'/>"
            + avatar(cx, cy, FACES[who], r=r))


def gear(cx, cy, color, r=22):
    teeth = ''.join(f"<rect x='{cx - 4}' y='{cy - r - 5}' width='8' height='10' rx='2' fill='{color}' transform='rotate({a} {cx} {cy})'/>"
                    for a in range(0, 360, 45))
    return teeth + f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{color}'/><circle cx='{cx}' cy='{cy}' r='{r * .42}' fill='#fffdfb'/>"


def card(x, y, w, h, color, title, lines, rot):
    cx = x + w / 2
    s = [f"<g transform='rotate({rot} {cx} {y + h / 2})'>",
         f"<rect x='{x + 4}' y='{y + 5}' width='{w}' height='{h}' rx='10' fill='#000' opacity='.06'/>",
         f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{NOTE[color]}' stroke='{color}' stroke-width='1.4'/>",
         ink_text(x + 24, y + 44, title, 30, color, 'start', True)]
    for i, (text, size, ink) in enumerate(lines):
        s.append(ink_text(x + 24, y + 82 + i * 28, text, size, ink, 'start'))
    s.append('</g>')
    return ''.join(s) + tape(x + w - 70, y, color, w=72, rot=rot * 3)


def channels(lang):
    t = TEXT[lang]
    W, w, h = 960, 440, 196
    pos = [(28, 104), (492, 104), (28, 336), (492, 336)]
    rots = [-1.0, 0.9, 0.8, -0.9]
    spec = [(ROSE, t['room'], t['room1'], t['room2'], t['room3'], ['you', 'claude', 'gpt']),
            (LAV, t['priv'], t['priv1'], t['priv2'], t['priv3'], ['you', 'claude', 'you', 'gpt']),
            (ORANGE, t['exch'], t['exch1'], t['exch2'], t['exch3'], ['claude', 'gpt']),
            (TEAL, t['ev'], t['ev1'], t['ev2'], t['ev3'], ['gear', 'gpt'])]
    colors = {'you': ROSE, 'claude': ORANGE, 'gpt': LAV}
    b = [ink_text(32, 46, t['ch_title'], 34, INK, 'start', True), ink_text(34, 76, t['ch_sub'], 17, MUTED, 'start')]
    for (x, y), rot, (col, title, who, l2, l3, people) in zip(pos, rots, spec):
        b.append(card(x, y, w, h, col, title, [(who, 18, INK), (l2, 17, MUTED), (l3, 17, MUTED)], rot))
        # 参与者头像排在卡片右下；私聊两对各用一个胶囊底框起来；事件是“程序 → GPT”
        fx, cy = x + w - 34, y + h - 40
        if col == LAV:
            for k, pair in enumerate((('you', 'gpt'), ('you', 'claude'))):
                right = fx - k * 136
                b.append(f"<rect x='{right - 84}' y='{cy - 30}' width='112' height='60' rx='30' fill='#fffdfb' stroke='{col}' stroke-width='1.4' stroke-dasharray='4 3'/>")
                b += [face(right, cy, pair[1], colors[pair[1]], 22), face(right - 56, cy, pair[0], colors[pair[0]], 22)]
        elif col == TEAL:
            b += [gear(fx - 110, cy, TEAL, 18), curve(fx - 82, cy, fx - 32, cy, bend=-10), face(fx, cy, 'gpt', LAV, 22)]
        else:
            for i, p in enumerate(reversed(people)):
                b.append(face(fx - i * 58, cy, p, colors[p], 22))
    b.append(doodles([('star', 930, 40, ORANGE), ('heart', 40, 548, ROSE), ('star', 470, 330, TEAL)]))
    return svg(W, 572, ''.join(b), t['ch_label'])


def cadence(lang):
    t = TEXT[lang]
    W = 960
    b = [ink_text(32, 46, t['ca_title'], 34, INK, 'start', True), ink_text(34, 76, t['ca_sub'], 17, MUTED, 'start'),
         f"<rect x='22' y='100' width='420' height='452' rx='12' fill='{NOTE[TEAL]}' fill-opacity='.5' stroke='{TEAL}' stroke-width='1.4' stroke-dasharray='7 5'/>",
         ink_text(42, 134, t['progs'], 24, TEAL, 'start', True),
         f"<rect x='520' y='100' width='418' height='452' rx='12' fill='#fffdfb' stroke='{MUTED}' stroke-width='1.2' stroke-dasharray='7 5'/>",
         ink_text(540, 134, t['chats'], 24, INK, 'start', True)]
    rows = [(t['nw'], t['nw1'], 160), (t['br'], t['br1'], 256), (t['sc'], t['sc1'], 352), (t['gd'], t['gd1'], 448)]
    for i, (name, every, y) in enumerate(rows):
        rot = (-0.8, 0.7, -0.6, 0.8)[i]
        b += [f"<g transform='rotate({rot} 232 {y + 34})'>",
              f"<rect x='44' y='{y}' width='376' height='72' rx='9' fill='#fffdfb' stroke='{TEAL}' stroke-width='1.3'/>",
              gear(84, y + 36, TEAL, 16), ink_text(118, y + 32, name, 22, INK, 'start', True),
              ink_text(118, y + 58, every, 17, MUTED, 'start'), '</g>']
    # 右边两个会话
    b += [f"<g transform='rotate(0.9 728 236)'><rect x='540' y='160' width='378' height='150' rx='10' fill='{NOTE[LAV]}' stroke='{LAV}' stroke-width='1.4'/>",
          ink_text(640, 206, t['gpt'], 28, LAV, 'start', True), ink_text(640, 240, t['gpt1'], 18, INK, 'start'),
          ink_text(640, 268, t['gpt2'], 18, INK, 'start'), '</g>', face(588, 220, 'gpt', LAV, 30), tape(860, 160, LAV, w=70, rot=3),
          f"<g transform='rotate(-0.9 728 456)'><rect x='540' y='384' width='378' height='150' rx='10' fill='{NOTE[ORANGE]}' stroke='{ORANGE}' stroke-width='1.4'/>",
          ink_text(640, 430, t['cl'], 28, ORANGE, 'start', True), ink_text(640, 464, t['cl1'], 18, INK, 'start'),
          ink_text(640, 492, t['cl2'], 18, INK, 'start'), '</g>', face(588, 444, 'claude', ORANGE, 30), tape(860, 384, ORANGE, w=70, rot=-3)]
    # 箭头：守夜人↓事件桥（事件）；事件桥→GPT（叫醒）；额度调度→两个会话（下次间隔，标签只写一次）
    def arrow(d, dash=False):
        extra = " stroke-dasharray='6 5'" if dash else ''
        return f"<path d='{d}' fill='none' stroke='{INK}' stroke-width='1.6' stroke-linecap='round' marker-end='url(#a)'{extra}/>"
    b += [arrow('M232 234 L232 254'), ink_text(244, 249, t['e1'], 16, MUTED, 'start', True),
          arrow('M422 292 C 470 292, 490 240, 536 236'), ink_text(470, 262, t['e2'], 18, MUTED, 'middle', True),
          arrow('M422 388 C 470 388, 490 300, 536 292', True), arrow('M422 388 C 470 388, 490 452, 536 456'),
          ink_text(478, 410, t['e3'], 18, MUTED, 'middle', True)]
    b.append(doodles([('star', 934, 40, TEAL), ('heart', 950, 560, ROSE)]))
    return svg(W, 572, ''.join(b), t['ca_label'])


QTEXT = {
    'en': dict(title="A question's life", sub='From your question to the result: who picks it up, who wakes whom, who reviews.',
               lanes=['You', 'Claude', 'GPT', 'Plain programs', 'Files'],
               A=('You ask', ['in the room, or', 'in a chat window']), B=('Record message', ['kept word for word']),
               C=('Patrol moves up', ['mentioned: within 20 min']), D=('Make a task', ['Claude writes the', 'delivery terms']),
               E=('GPT takes it', ['unclear? ask #2884', 'and Claude answers']), F=('Dispatcher', ['optional: queue', 'GPU jobs']),
               G=('Night watch', ['every 10 min:', 'job finished']), H=('Deliver', ['first line is', 'a number']),
               I=('Review', ['accept, or', 'send it back']), J=('Write finding', ['keep the accepted', 'result']),
               K=('Result arrives', ['one sentence', 'in the room']),
               a1='said in the room', a2='said in a window: right away', a3='wake', a4='needs a GPU', a5='done without GPU',
               a6='wake', a7='send back', a8='record',
               foot='The night watch watches tasks and GPUs, not messages; a mention moves the next patrol up instead.',
               label='A question goes from you to Claude and GPT, through programs and files, and back as a result'),
    'zh-CN': dict(title='一个问题的一生', sub='从你提问到结果送达：谁接手、谁叫醒谁、谁验收。',
                  lanes=['你', 'Claude', 'GPT', '普通程序', '文件'],
                  A=('你提问', ['在讨论室，或', '在对话窗口里']), B=('记下消息', ['原话原样保留']),
                  C=('巡检提前', ['被点名：20 分钟内']), D=('拆成任务', ['Claude 写清', '交付要求']),
                  E=('GPT 接手', ['有疑问先提问', '#2884，Claude 作答']), F=('调度器', ['可选：把显卡', '作业排进空卡']),
                  G=('守夜人', ['每 10 分钟', '发现作业完成']), H=('交付', ['第一句', '就是数字']),
                  I=('验收', ['通过，或', '退回重做']), J=('写进研究发现', ['保留验收', '过的结果']),
                  K=('结果送达', ['讨论室里', '一句话说结果']),
                  a1='在讨论室说', a2='在窗口里说：立刻', a3='叫醒', a4='要显卡时', a5='不用显卡直接交', a6='叫醒', a7='退回',
                  a8='记录', foot='守夜人只看任务和显卡，不读消息；消息靠“被点名”把下一次巡检提前。',
                  label='一个问题从你出发，经过 Claude、GPT、程序和文件，变成结果回到你手里'),
}


def question_flow(lang):
    q = QTEXT[lang]
    W, H = 1200, 1000
    lane_y = [100, 260, 420, 580, 740]
    colors = [ROSE, ORANGE, LAV, TEAL, SAND]
    b = [ink_text(32, 46, q['title'], 34, INK, 'start', True), ink_text(34, 76, q['sub'], 17, MUTED, 'start')]
    for y, col, name in zip(lane_y, colors, q['lanes']):
        b.append(M.band(18, y, 1164, 140, col, name))
    cols = [52, 240, 428, 616, 804, 992]
    w, h = 176, 100
    place = dict(A=(0, 0), B=(1, 4), C=(1, 3), D=(2, 1), E=(3, 2), F=(4, 3), G=(5, 3), H=(5, 2), I=(5, 1), J=(4, 4), K=(5, 0))
    rot = dict(A=-1, B=.7, C=-.6, D=.8, E=-.7, F=.6, G=-.8, H=.7, I=-.6, J=.8, K=-.7)
    box = {}
    for key, (c, l) in place.items():
        x, y = cols[c], lane_y[l] + 26
        box[key] = (x, y)
    def cx(k): return box[k][0] + w / 2
    def top(k): return box[k][1]
    def bot(k): return box[k][1] + h
    def left(k): return box[k][0]
    def right(k): return box[k][0] + w
    def mid(k): return box[k][1] + h / 2
    E_ = M.elbow
    arrows = [
        E_([(cx('A'), bot('A')), (cx('A'), mid('B')), (left('B') - 2, mid('B'))], label=q['a1'], label_xy=(cx('A') + 50, mid('B') - 70)),
        E_([(cx('B'), top('B')), (cx('B'), bot('C') + 2)]),
        E_([(right('C'), mid('C')), (cx('D') - 30, mid('C')), (cx('D') - 30, bot('D') + 2)], label=q['a3'], label_xy=(cx('D') - 4, mid('C') - 60)),
        E_([(right('A'), mid('A')), (cx('D'), mid('A')), (cx('D'), top('D') - 2)], dash=True, label=q['a2'], label_xy=(right('A') + 110, mid('A') - 10)),
        E_([(right('D'), mid('D')), (cx('E'), mid('D')), (cx('E'), top('E') - 2)]),
        E_([(cx('E'), bot('E')), (cx('E'), mid('F')), (left('F') - 2, mid('F'))], label=q['a4'], label_xy=(cx('E') - 62, mid('F') - 26)),
        E_([(right('F'), mid('F')), (left('G') - 2, mid('G'))]),
        E_([(cx('G'), top('G')), (cx('G'), bot('H') + 2)], label=q['a6'], label_xy=(cx('G') + 44, top('G') - 18)),
        E_([(right('E'), mid('E')), (left('H') - 2, mid('H'))], dash=True, label=q['a5'], label_xy=((right('E') + left('H')) / 2, mid('H') - 12)),
        E_([(cx('H'), top('H')), (cx('H'), bot('I') + 2)]),
        E_([(left('I'), mid('I') + 20), (cx('E') + 40, mid('I') + 20), (cx('E') + 40, top('E') - 2)], RED, True, q['a7'], (cx('E') + 120, mid('I') + 10)),
        E_([(right('I'), mid('I')), (1170, mid('I')), (1170, mid('J')), (right('J') + 2, mid('J'))], label=q['a8'], label_xy=(1150, mid('G') + 70)),
        E_([(cx('I'), top('I')), (cx('I'), bot('K') + 2)]),
    ]
    b.append(''.join(arrows).replace("font-size='16'", "font-size='20'"))  # 箭头上的字放大
    for key in place:
        x, y = box[key]
        title, lines = q[key]
        col = colors[place[key][1]]
        b.append(M.note(x, y, w, h, col, title, lines, rot=rot[key], title_size=24))
    b += [ink_text(34, 930, q['foot'], 17, MUTED, 'start'), doodles([('heart', 1154, 42, ROSE), ('star', 1150, 950, TEAL)])]
    return svg(W, 960, ''.join(b), q['label'])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ZH.update(ZH_ARCH)
    reused = {'01-overview': M.how_it_works, '05-authority': M.who_decides, '06-wake-loop': M.wake_loop}
    for name, render in reused.items():
        raw = relabel(render())
        missing = sorted({s for s in re.findall(r'>([^<>]+)</text>', raw) if s not in ZH})
        assert not missing, (name, missing)
        (OUT / f'{name}.svg').write_text(outlined(raw, 'en'), encoding='utf-8')
        (OUT / f'{name}.zh-CN.svg').write_text(outlined(raw, 'zh-CN'), encoding='utf-8')
    for name, render in {'02-channels': channels, '03-question': question_flow, '04-cadence': cadence}.items():
        (OUT / f'{name}.svg').write_text(outlined(render('en'), 'en'), encoding='utf-8')
        zh = render('zh-CN')
        ZH.update({s: s for s in re.findall(r'>([^<>]+)</text>', zh)}); ZH.update({m: m for m in re.findall(r"aria-label='([^']*)'", zh)})
        (OUT / f'{name}.zh-CN.svg').write_text(outlined(zh, 'zh-CN'), encoding='utf-8')
    print('12 architecture diagrams written to', OUT)


if __name__ == '__main__':
    main()
