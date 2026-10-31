"""Language labels and font outlines for portable, zoomable README SVGs."""
from pathlib import Path
from functools import lru_cache
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
FONTS = Path(__file__).resolve().parent / 'fonts'
ZH = {
    'Owner · Big Fish': '发起人 · 大肥鱼',
    'sets direction and budget': '定方向与预算',
    'approves external actions': '批准对外行动', 'and deletion': '与删除范围',
    'Lead · Miss': '主线 · 大小姐', 'designs experiments,': '设计实验',
    'decides, reviews': '拍板与审阅', 'every delivery': '验收每份成果',
    'Executor · Dragon': '执行 · 龙娘', 'runs jobs, builds pages,': '跑作业、搭页面',
    'reports results first': '先汇报具体结果', 'direction': '方向',
    'conclusions': '结论', 'orders': '指令', 'ask / deliver': '提问交付',
    'Shared records: plain files': '共享记录：普通文件', 'task board': '任务看板',
    'exchange notes': '交流板', 'decide / veto log': '决定与否决记录',
    'events': '事件', 'findings': '研究发现', 'read / write': '读写',
    'Plain programs: no model, no quota': '普通程序：独立检查与唤醒',
    'night watch': '守夜人', 'turns changes into events': '把变化转成事件',
    'event bridge': '事件桥', 'wakes the right chat': '叫醒对应会话',
    'checks': '检查', 'flow, jobs, idle GPUs': '流程、作业与空卡',
    'guardian': '服务卫士', 'restarts local services': '恢复本机服务',
    'watch': '观察', 'wake': '唤醒', 'event or heartbeat': '事件或定时兜底',
    '1 · events': '1 · 处理事件', 'handle, acknowledge': '处理并登记回执',
    '2 · idle GPUs': '2 · 查看空卡', 'fill the queue': '接续就绪作业',
    '3 · Lead orders': '3 · 主线指令', 'do each one': '逐条做完',
    '4 · open tasks': '4 · 推进任务', 'move each a step': '每项向前推进',
    'only waiting?': '只剩等待？', 'patrol, then sleep': '登记巡检后休息',
    'old loop: slept right after the event while GPUs sat idle — the wake contract now refuses it':
        '旧做法：处理一个事件就休息，空卡仍闲着；现在按完整清单接续工作',
    'Owner, Lead and Executor share plain-file records; plain programs watch the records and wake the Executor':
        '发起人、主线与执行共用文件记录，普通程序观察变化并叫醒执行会话',
    'One wake: events, idle GPUs, Lead orders, open tasks; sleep only when everything left is waiting':
        '每轮依次处理事件、空卡、主线指令与进行中任务，只剩等待时登记巡检',
}


@lru_cache(None)
def font(name):
    f = TTFont(FONTS / name)
    return f, f.getGlyphSet(), f.getBestCmap()


@lru_cache(None)
def glyph(name, char):
    f, glyphs, cmap = font(name)
    key = cmap.get(ord(char))
    if key is None:
        raise ValueError(f'Missing diagram glyph: {name} U+{ord(char):04X}')
    pen = SVGPathPen(glyphs)
    glyphs[key].draw(pen)
    return pen.getCommands(), f['hmtx'][key][0]


def outlined(raw, language='en'):
    """Keep every label accessible while drawing its exact glyph contours."""
    root = ET.fromstring(raw)
    chinese = language == 'zh-CN'
    root.set('lang', language)
    if chinese:
        root.set('aria-label', ZH[root.get('aria-label')])
    labels = []
    for parent in list(root.iter()):
        for element in list(parent):
            if element.tag == f'{{{SVG}}}style':
                parent.remove(element)
                continue
            if element.tag != f'{{{SVG}}}text':
                continue
            text = ''.join(element.itertext())
            if chinese:
                text = ZH[text]
            labels.append(text)
            hand = 'MD Hand' in element.get('font-family', '')
            bold = int(element.get('font-weight', '500')) >= 600
            name = ('Xiaolai-Diagrams.ttf' if chinese else
                    'Caveat-Bold.ttf' if hand else
                    'Nunito-Bold.ttf' if bold else 'Nunito-Medium.ttf')
            f, _, _ = font(name)
            size = float(element.get('font-size', '16'))
            if chinese and size < 19:
                size = max(16, size)
            scale = size / f['head'].unitsPerEm
            parts = [glyph(name, c) for c in text]
            width = sum(advance for _, advance in parts) * scale
            x = float(element.get('x', '0'))
            y = float(element.get('y', '0'))
            anchor = element.get('text-anchor', 'start')
            x -= width / 2 if anchor == 'middle' else width if anchor == 'end' else 0
            keep = {k: v for k, v in element.attrib.items() if k not in
                    ['x', 'y', 'font-family', 'font-size', 'font-weight', 'text-anchor']}
            group = ET.Element(f'{{{SVG}}}g', keep)
            group.set('aria-label', text)
            ET.SubElement(group, f'{{{SVG}}}title').text = text
            contours = ET.SubElement(group, f'{{{SVG}}}g',
                transform=f'translate({x:.4f} {y:.4f}) scale({scale:.6f} {-scale:.6f})')
            cursor = 0
            for d, advance in parts:
                if d:
                    ET.SubElement(contours, f'{{{SVG}}}path', d=d,
                                  transform=f'translate({cursor} 0)')
                cursor += advance
            parent.insert(list(parent).index(element), group)
            parent.remove(element)
    ET.SubElement(root, f'{{{SVG}}}desc').text = '\n'.join(labels)
    return ET.tostring(root, encoding='unicode')
