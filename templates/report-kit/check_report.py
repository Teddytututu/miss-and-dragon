"""Check report structure and configured scientific presentation rules."""
import html as H
import re
import sys
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_internal_names(root=None):
    """Read optional private display names from this project's data settings."""
    root = ROOT.parent / 'data' if root is None else Path(root)
    path = root / 'project.json'
    if not path.is_file():
        return []
    settings = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(settings, dict):
        return []
    aliases = settings.get('report_internal_names', [])
    names = [settings.get('user_name')] + (aliases if isinstance(aliases, list) else [])
    return sorted({name.strip() for name in names if isinstance(name, str) and name.strip()},
                  key=lambda name: (-len(name), name))


def load_rules(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name('report_rules.json')
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    rules = value.get('room_banned') if isinstance(value, dict) else None
    if not isinstance(rules, list):
        raise ValueError('报告规则需要room_banned列表。')
    for row in rules:
        if not isinstance(row, list) or len(row) != 2 or not all(isinstance(s, str) for s in row):
            raise ValueError('每条报告规则需要正则表达式和说明。')
        re.compile(row[0])
    return rules

AI_TONE = [
    (r'不是[^。，]{1,20}而是', '“不是……而是……”句式'),
    (r'不再把|清楚的负结论|白花|及时止损|本身就是一条结论|撞的是|预言|值得一提|不难发现|由此可见|综上所述|总而言之|一方面.{0,30}另一方面', 'AI 腔'),
    (r'赋能|抓手|颗粒度|闭环|证据链|全链路|矩阵|打通|沉淀|对齐了', '空心大词'),
]
PROCESS = [
    (r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/root/|/data/|autodl-tmp', '本机或服务器路径'),
    (r'\b[\w\-]+\.(py|jsonl|json|csv|npz|log|md)\b', '文件名（放进附件或任务文件）'),
    (r'\bT\d{3}\b', '任务编号（读者不认识）'),
    (r'(白话说|说白了|通俗地说|简单说|换句话说|用大白话说)[，,：:]', '铺垫说法（直接写具体内容）'),
    (r'第[一二三四五]版|新版|旧版|上一版|这一版|v[0-9]版', '版本说法（新结果整篇重写，不讲版本）'),
    (r'交差|直接发给|(?<![A-Za-z0-9])P\d{3}(?!\d)', '内部称呼（交付对象和工具包号留在聊天、待办与方法记录，正文只写读者需要的内容）'),
    (r'\b(PID|SHA|sha256|exit ?code|OOM)\b|解析器|修复记录|冻结协议|回归测试|锁文件|断点续跑|队列', '过程细节'),
    (r'共完成\s*\d+|读了\s*\d+\s*篇|\d+\s*个任务|分工如下|同时上\s*\d+\s*门', '工作量展示'),
    (r'\d{1,2}[-/月]\d{1,2}日?\s*更新|更新于|（更新）|【更新】', '更新横幅（新结果就整篇重写）'),
    (r'分别展示|另作比较|资格|单列|重放|接棒|收尾|封口|口径|按各自|用时条件|预约|回执|准入|有效对照|完整性', '过程词（用读者词：草稿、终图、查出、改对）'),
    (r'冻结|原票|复评|计账|按既有|统一采用|同源|逐图标签|原尺寸|\bCUDA\b|\bCPU\b|FP32|bf16|Lanczos|sigma|前向', '执行口径（正文用“计算次数”“独立评测”这类读者词；口径放进折叠的“方法与口径”）'),
    # 正文按研究内容组织，工具使用数量留在方法记录。
    (r'Pro\s*包|外置大脑|\d+\s*个\s*(?:Pro\s*)?包(?!括|含|装|裹)', '按工具单位汇报（按研究内容和具体行动组织，工具使用数量记在核对记录里）'),
]
# 统计方法名：正文出现一次结论里的 p 值可以，方法说明放折叠区
STATS = r'McNemar|Holm|bootstrap|重采样|符号翻转|精确二项|经验分布|聚类重采样'

READER_HINTS = r'点开看|点击查看|点击展开|如下图所示|见下图|下图中|红色表示|蓝色表示|颜色表示|灰色表示|图例|左图|右图'
BAD_HEADINGS = r'^(做了什么|我们做了什么|几个例子|三个例子|例子|背景|小结|总结|其他|补充说明|说明|更新|附录|结果|主要结果)$'
BAD_TITLE_END = r'(报告|材料|总结|汇报|说明|介绍|整理|进展|汇总|概览|笔记|文档)$'

# These scientific terms are exempt from workflow wording checks.
# Keep exemptions specific so ordinary process prose is still checked.
SCIENTIFIC_TERMS = re.compile(
    r'随机矩阵理论|score列构成矩阵|退化矩阵|'
    r'(?:自|跨)?注意力矩阵|奖励(?:相关)?矩阵|相关矩阵|'
    r'冻结\s*(?:文本编码器|扩散网络|FLUX\.1-dev)|'
    r'文本条件容量|低容量重构|前向过程|前向加噪'
)


def language_text(text):
    return SCIENTIFIC_TERMS.sub(lambda match: ' ' * len(match.group()), text)


def text_of(fragment):
    # 伪代码与图形标记按代码处理，跳过正文用语检查。
    fragment = re.sub(r'(?s)<(script|style|svg|math|pre)[^>]*>.*?</\1>', ' ', fragment)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def section_after(body, keys):
    """标题含 keys 之一的那个 h2 到下一个 h2 之间的 HTML；找不到返回 None。"""
    for m in re.finditer(r'(?s)<h2[^>]*>(.*?)</h2>', body):
        if any(k in text_of(m.group(1)) for k in keys):
            nxt = body.find('<h2', m.end())
            return body[m.end(): nxt if nxt >= 0 else len(body)]
    return None


def audit_research(body, E, W, *, internal_names=()):
    """Check the evidence, structure and recommendations in a research result page."""
    # a. 标题下一行写设置：模型、步数/帧、题数、判分、日期
    h1_end = body.find('</h1>')
    head = text_of(body[h1_end: body.find('<h2', h1_end) if '<h2' in body[h1_end:] else h1_end + 2000]) if h1_end >= 0 else ''
    missing = [what for what, pat in (('题数或组数', r'\d+\s*(?:题|组|条|张|个提示)'), ('判分方法', r'判分|评测|GenEval|检测器|盲读|人工|VQA|打分'),
                                      ('日期', r'\d{1,2}[-/月]\d{1,2}|20\d\d'), ('模型', r'[A-Z][\w.\-]*\d|Qwen|SDXL|SD3|FLUX|Wan|BAGEL|模型'))
               if not re.search(pat, head)]
    if missing:
        E('标题下一行要写设置（模型、分辨率/帧/步数、题数和来源、判分方法、日期），现在缺：' + '、'.join(missing))
    # b. 简要结论三四行、带数字，只写已完成的结论。
    concl = section_after(body, ('结论',))
    if concl is not None:
        lines = [text_of(x) for x in re.findall(r'(?s)<li[^>]*>(.*?)</li>', concl)] or \
                [text_of(x) for x in re.findall(r'(?s)<p[^>]*>(.*?)</p>', concl)]
        lines = [x for x in lines if x]
        if not 2 <= len(lines) <= 5:
            W(f'“简要结论”有 {len(lines)} 行：写三四行，每行一个结论')
        no_num = [x[:20] for x in lines[:-1] if not re.search(r'\d', x)]
        if no_num:
            E('“简要结论”这几行没有数字：' + '；'.join(no_num))
        # 待做事项留在看板，报告呈现已完成的结论。
        if lines and re.search(r'还在跑|还在做|进行中|待补|还没开始|在等', lines[-1]):
            E('“简要结论”里写了还在跑/还在做的事：报告只放做完的结论，待做的放看板')
    # c. 实验目的：起因要链到上一份结果页
    purpose = section_after(body, ('要回答', '目的', '为什么做'))
    if purpose is not None:
        if not re.search(r'href=["\'][^"\']*(?:/result-report/|\.html)', purpose):
            E('“实验目的”的起因要链到上一份结果页（上位实验没有网页的，先补一页再链）')
        if not re.search(r'预期|预计|假设|事先', text_of(purpose)):
            W('“实验目的”没写事先预期：写清做之前猜会怎样，结果出来才能对照')
    # d. 结尾“局限与下一步”
    if not re.search(r'(?s)<h2[^>]*>[^<]*(局限|下一步)', body):
        E('结尾要有“下一步”一节（局限只写真正影响结论的内容）')
    nxt = section_after(body, ('下一步',))
    # 下一步明确给出推荐、原因和决策人。
    recommendation = r'推荐|建议|我们定|就做|先做|决定|拍板'
    if internal_names:
        recommendation += '|' + '|'.join(re.escape(name) + '定' for name in internal_names)
    if nxt is not None and not re.search(recommendation, text_of(nxt)):
        W('“下一步”没给明确推荐：写清推荐做哪个、为什么，要谁拍板什么')
    if nxt is not None and re.search(r'补(题|跑|样|数据|实验)|加题|再跑|追加', text_of(nxt)):
        E('“下一步”写成了补实验：要补就一次跑完再报；下一步写结论往哪推（例：图像成立了，看视频成不成立）')
    # e. 实现细节折叠
    if not re.search(r'(?s)<details', body):
        W('实现细节（参数、口径、文件）放进折叠的“方法与实现记录”<details>')
    # f. 判分员按用途分开：用了官方判分就要写独立判分或和人工的一致率
    t = text_of(body)
    if re.search(r'GenEval|官方判分|检测器', t) and not re.search(r'一致率|一致\s*\d|独立(?:判分|评测|盲)', t):
        W('只看到官方判分：判方法好坏要有独立判分并写和人工的一致率，没核过的写进局限')
    # g. 只有 1 题的结果不单独成节
    for m in re.finditer(r'(?s)<h2[^>]*>(.*?)</h2>', body):
        if re.search(r'(?:^|\D)1\s*题|单题|n\s*=\s*1\b', text_of(m.group(1))):
            E(f'“{text_of(m.group(1))}”只有 1 题，不单独成节，并进例子或局限')


def result_links(raw, *, root=None, known=None):
    """页内 /result-report/ 链接必须能在总览文件卡里找到、文件存在。"""
    bad = []
    tokens = set(re.findall(r'/(?:result-report|report)/([a-f0-9]{24})/', raw))
    if not tokens:
        return bad
    if known is None:
        try:
            root = ROOT.parents[0] / 'data' if root is None else Path(root)
            sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
            from board import report_reader
            known = {url.split('/')[2]:path for url,path in report_reader.catalog(root).items()}
        except Exception as error:
            return [f'无法核对结果页链接：{error}']
    for tok in sorted(tokens):
        if tok not in known:
            bad.append(f'链接 /result-report/{tok}/… 在总览里找不到对应文件卡（页面改名或归档了），换成现在的链接')
    return bad


def check(path, *, rules_path=None, result_root=None):
    room_banned = load_rules(rules_path)
    internal_names = load_internal_names(result_root)
    raw = Path(path).read_text(encoding='utf-8')
    body = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', '', raw)
    errors, warns = [], []
    E = lambda m: errors.append(m)
    W = lambda m: warns.append(m)

    # 1. 单文件：不能依赖外网
    for pat, what in [(r'<script[^>]+src=["\']https?:', '外链脚本'), (r'<link[^>]+href=["\']https?:', '外链样式或字体'),
                      (r'<img[^>]+src=["\']https?:', '外链图片'), (r'@import\s+url\(["\']?https?:', '外链 CSS')]:
        if re.search(pat, raw, re.I):
            E(f'{what}：图片转 base64、公式用 MathML，页面要离线能看')
    for m in re.finditer(r'<img[^>]+src=["\'](?!data:)([^"\']+)', raw):
        W(f'图片用相对路径 {m.group(1)[:50]}：单独发这个文件时图会丢，用 report_kit.photo() 内嵌')

    # 宽窄屏图形各自需要切换样式，避免两份同时显示。
    for cls in ('narrow-only', 'wide-only'):
        if f'class="{cls}"' in raw and f'.{cls}' not in raw:
            E(f'用了 {cls} 却没写对应样式，宽屏、窄屏两份图会同时显示（同一张图画两遍）')

    # 2. 标题是结论
    h1 = re.findall(r'(?s)<h1[^>]*>(.*?)</h1>', body)
    if len(h1) != 1:
        E(f'要有且只有一个 h1（现在 {len(h1)} 个）')
    else:
        t = text_of(h1[0])
        if re.search(BAD_TITLE_END, t) or len(t) < 4:
            E(f'大标题“{t}”是空名目，写实验的名字，例如“视频按类别早筛”“基线复现”')

    # 3. 小标题正式、说清这节讲什么
    for lvl, h in re.findall(r'(?s)<(h[23])[^>]*>(.*?)</\1>', body):
        t = text_of(h)
        core = re.sub(r'^([一二三四五六七八九十]+、|\d+[.、]\s*)', '', t)
        if re.match(r'^0\d', t):
            E(f'小标题“{t}”：不用 01/02 编号，用“一、”或不编号')
        if re.match(BAD_HEADINGS, core):
            E(f'小标题“{t}”太空，写成这一节的内容（例：“计算量与正确数的关系”）')
        # 标题直接表达工作内容。
        if re.search(r'请教', core):
            E(f'小标题“{t}”：不写请教，我们是干活的；能定的自己定，写进下一步')
        # 正式小标题使用内容或结论，避免口语问句。
        if lvl == 'h2' and re.search(r'从哪里来|哪来的|是什么|怎么(做|来|走)|为什么|做了什么|长什么样|[？?]$|原料|而不是', core):
            E(f'小标题“{t}”是口语问句或“不是……而是”，写成正式的内容或结论（例：“数据来源与评测隔离”）')
        if re.search(r'[（(][^）)]*\d+[^）)]*[）)]$', t):
            W(f'小标题“{t}”带括注口径，数量直接写进标题（“· 48 组”）或删掉')

    # 3.5 有图表的实验页检查研究结构；调研、笔记与工作入口分别处理。
    # 调研页以至少五篇论文链接识别，开头呈现结论。
    survey = len(re.findall(r'arxiv\.org|doi\.org|openreview\.net|aclanthology|proceedings\.|cvf\.com|neurips\.cc', raw, re.I)) >= 5
    research = bool(re.search(r'<table|<svg|<img', body) and not survey and not re.search(r'调研|清单|笔记|复盘|入口|纪要|讨论|论文工作稿|阅读|精读|今早要做|待办|讲解|怎么做', ''.join(text_of(x) for x in h1)))
    if survey:
        h2s = [text_of(h) for h in re.findall(r'(?s)<h2[^>]*>(.*?)</h2>', body)][:3]
        if not any('结论' in h for h in h2s):
            W('调研页开头要有一节“结论”：几行说清查到了什么、对我们的研究意味着什么')
    if research:
        # 顺序：标题下一句结果 → 实验目的 → 方法 → 图与例子 → 结论 → 下一步。
        all_h2 = [text_of(h) for h in re.findall(r'(?s)<h2[^>]*>(.*?)</h2>', body)]
        h2s = all_h2[:3]
        if all_h2 and '实验目的' not in all_h2[0]:
            E('第一节要是“实验目的”（先讲实验和流程、再看数据图、最后给结论）')
        ci = next((i for i, h in enumerate(all_h2) if '结论' in h), None)
        if ci is None:
            E('要有一节“结论”：放在数据图后面，三四行，每行一个带数字的结论')
        else:
            pos = [m.start() for m in re.finditer(r'(?s)<h2[^>]*>', body)][ci]
            if not re.search(r'<svg|<img', body[:pos]):
                E('“结论”一节要放在流程图和数据图后面')
        head_p = re.search(r'(?s)</h1>\s*<p[^>]*>(.*?)</p>', body)
        if not head_p or not re.search(r'\d', text_of(head_p.group(1))):
            E('标题下第一句要直接写结果、带数字（结论虽然放后面，开头一句先让人知道结果）')
        if any('这个实验要回答什么' in h for h in h2s):
            E('这一节标题就叫“实验目的”，不要写“这个实验要回答什么”')
        elif not any('实验目的' in h for h in h2s):
            E('前面要有一节“实验目的”：问题、起因（配前一个结果页链接）、做法、事先预期')
        audit_research(body, E, W, internal_names=internal_names)
        # 实验页至少有一张图，并展示真图或视频例子。
        if not re.search(r'<svg|<img', body):
            E('实验结果页没有一张图：比较类结论先放图')
        if not re.search(r'(?s)<h2[^>]*>[^<]*例子[^<]*</h2>.*?(<img|<video|<svg)', body):
            E('没有“例子”一节（真图或视频，写清这种情况占几张）：让读者亲眼看到具体情况')
        if re.search(r'进行中|阶段结果|中期|初步|小批|部分结果', ''.join(text_of(x) for x in h1)):
            E('大标题写着进行中/初步/小批：半成品不出报告页，做完每类错误再交')
        if len(h1) == 1 and len(text_of(h1[0])) > 20:
            t = text_of(h1[0])
            E(f'大标题“{t[:30]}…”太长（{len(t)} 字）：大标题写实验的短名字（≤20 字），结论放开头一段和“结论”一节')
        # 事先预期检验所需数据完整后再提交结果页。
        concl = re.search(r'(?s)<h2[^>]*>[^<]*结论[^<]*</h2>(.*?)(?=<h2|$)', body)
        head = (text_of(h1[0]) if len(h1) == 1 else '') + ' ' + (text_of(concl.group(1)) if concl else '')
        miss = re.search(r'检不了|没检成|没法检|无法检验|未能检验|数据不够|数据不足|样本不足|识别信息有限|留待|留给.{0,12}检验|待补数据|这次看不出', head)
        if miss:
            E(f'标题或简要结论写着“{miss.group(0)}”：有预期因为数据不够没检完，这页不算做完。先补数据把它检完再交')

    # 4. 第一屏有加粗结论且带数字
    first = body[:body.find('<h2') if '<h2' in body else len(body)]
    first_sec = re.search(r'(?s)<section.*?</section>', body)
    lead = first + (first_sec.group(0) if first_sec else '')
    bolds = [text_of(b) for b in re.findall(r'(?s)<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>', lead)]
    if not bolds:
        E('第一屏没有加粗的结论句：开头就用一句加粗论断回答“答案是什么”')
    elif not re.search(r'\d', text_of(lead)):
        W('第一屏没有数字：结论后面跟两三句带数字的证据')

    # 附录提供图表或例子，少量文字并入相关章节。
    for s_ in re.findall(r'(?s)<section[^>]*>(.*?)</section>', body):
        hm_ = re.search(r'(?s)<h2[^>]*>(.*?)</h2>', s_)
        if hm_ and text_of(hm_.group(1)).startswith('附') and not re.search(r'<svg|<img|<table|<video', s_):
            E(f'“{text_of(hm_.group(1))}”只有几句话、没有图表或例子：少量文字并入相关章节')
    # 5. 每节要有证据（图、表、照片、公式）
    secs = re.findall(r'(?s)<section[^>]*>(.*?)</section>', body)
    for s in secs:
        hm = re.search(r'(?s)<h2[^>]*>(.*?)</h2>', s)
        name = text_of(hm.group(1)) if hm else '(无标题)'
        has_ev = re.search(r'<svg|<img|<table|<math|<video', s) or re.search(r'结论|要回答|目的|方法|记录|局限', name)
        nums = len(re.findall(r'\d+(?:\.\d+)?\s*(?:%|组|题|张|个|次|步|对|vs)', text_of(s)))
        reading = bool(re.search(r'精读|阅读|读后|调研|笔记|设计清单', ''.join(text_of(x) for x in h1)))   # 阅读页允许在正文引用论文数字。
        if not has_ev and nums >= 12 and not reading:
            E(f'“{name}”一节文字里有 {nums} 个数字但没有图或表：比较类结论先放图，精确数字放图下的表')
        elif not has_ev and nums >= 3:
            W(f'“{name}”有 {nums} 个数字没有图或表：如果是在比较，画一张图')
        if hm is None:
            W('有一节没有 h2 标题')
        if not re.search(r'(?s)<(?:b|strong)', s) and hm:
            W(f'“{name}”没有加粗结论句：每节开头一句加粗论断')

    # 6. 文字：段落长度、AI 腔、过程细节、读图说明
    plain = text_of(body)
    main_text = text_of(re.sub(r'(?s)<details[^>]*>.*?</details>', ' ', body))   # 折叠区里允许写口径
    for m in list(re.finditer(STATS, main_text))[:2]:
        W(f'统计方法名“{m.group(0)}”在正文：正文只留结论和 p 值，方法写进 <details><summary>方法与口径</summary>')
    for p in re.findall(r'(?s)<p(?:\s[^>]*)?>(.*?)</p>', body):
        t = text_of(p)
        if len(t) > 220:
            W(f'段落 {len(t)} 字太长：“{t[:30]}……”拆开，或把数字挪进表')
    lexical_plain = language_text(plain)
    lexical_main = language_text(main_text)
    for pat, what in AI_TONE:
        for m in list(re.finditer(pat, lexical_plain))[:3]:
            E(f'{what}：“…{plain[max(0, m.start()-12):m.end()+12]}…”')
    reading_page = bool(re.search(r'精读|阅读|读后|调研|笔记', ''.join(text_of(x) for x in h1)))
    process_rules = list(PROCESS)
    if internal_names:
        process_rules.append(('|'.join(re.escape(name) for name in internal_names),
                              '内部称呼（项目显示名与内部别名留在协作记录，报告使用读者需要的正式称呼）'))
    for pat, what in process_rules:
        if what.startswith('内部称呼') and re.search(r'今早要做|待办|逐件清单|任务清单|设计清单|入口|阅读资料|报告与文件|报告阅读|集中在这里|【协作系统】|Master', ''.join(text_of(x) for x in h1)):
            continue   # 项目内部工作页允许使用配置的称呼。
        if reading_page and what.startswith(('工作量展示', '过程词', '执行口径')):
            continue   # 阅读页中的数量与术语按论文内容处理。
        for m in list(re.finditer(pat, lexical_main))[:3]:
            E(f'{what}：“…{main_text[max(0, m.start()-12):m.end()+12]}…”')
    for pat, what in room_banned:
        if reading_page and what.startswith(('后台用语', '内部流程词')):
            continue   # 读论文页里的“完整性、产物、容量”是论文的术语
        if '路径' in what or '文件名' in what or '编号' in what:
            continue   # 上面已经按报告口径查过
        for m in list(re.finditer(pat, lexical_plain))[:2]:
            E(f'{what}：“…{plain[max(0, m.start()-12):m.end()+12]}…”')
    for m in list(re.finditer(READER_HINTS, plain))[:3]:
        E(f'读图说明或读者提示“{m.group(0)}”：图要不靠说明也看得懂，颜色直接写在线和条旁边')

    # 7. 图：一图一结论，有标题
    svgs = re.findall(r'(?s)<svg[^>]*>', raw)
    for tag in svgs:
        if 'viewBox' not in tag:
            W('有 SVG 没写 viewBox，手机上会溢出')
    if re.search(r'<svg', raw) and not re.search(r'aria-label=', raw):
        W('SVG 没有 aria-label：写上这张图说的那句结论')

    # 8. 比较要带基线
    alltext = H.unescape(re.sub(r'<[^>]+>', ' ', body))
    if re.search(r'Best-of-?N|BoN|画完四张', alltext) and not re.search(r'直接画一张|直接画|单张|不做筛选|直接生成|N\s*=\s*1|BoN1', alltext):
        W('有和 Best-of-N 的比较，但没看到“直接画一张”的基线')

    # 9. 小样本百分比
    for m in re.finditer(r'(\d{1,3}(?:\.\d+)?)%\s*[（(]\s*(\d+)\s*/\s*(\d+)', plain):
        if int(m.group(3)) < 10:
            W(f'“{m.group(0)}”分母只有 {m.group(3)}，直接写个数，不写百分比')

    # 9.5 不确定性集中说明一次，正文直接表达发现。
    hedges = re.findall(r'不能证明|不能解释成|不能直接|并不成立|不代表|不等于|并非|仅限于|不能据此|不能推广|不能当作|不能说明|不足以', plain)
    if len(hedges) > 3:
        E(f'防御性限定 {len(hedges)} 处（{"、".join(sorted(set(hedges))[:5])}）：不确定的地方在“范围”里说一次，正文用肯定句直接写发现')

    # 10. 页内结果链接均指向已登记文件。
    for m in result_links(raw, root=result_root):
        E(m)
    return errors, warns


def main():
    parser = argparse.ArgumentParser(description='检查报告形式和可见正文。')
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--rules', type=Path, help='明确指定语言规则JSON')
    parser.add_argument('--root', type=Path, help='含 project.json 与结果页登记的项目数据目录')
    args = parser.parse_args()
    bad = 0
    for p in args.paths:
        errors, warns = check(p, rules_path=args.rules, result_root=args.root)
        print(f'== {p}：错误 {len(errors)}，提醒 {len(warns)}')
        for e in errors:
            print('  [错误]', e)
        for w in warns:
            print('  [提醒]', w)
        bad += bool(errors)
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
