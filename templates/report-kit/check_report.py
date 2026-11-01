"""Check an offline reader-facing report: python check_report.py report.html."""
import html as H
import re
import sys
from pathlib import Path

ROOM_BANNED = []

AI_TONE = [
    (r'不是[^。，]{1,20}而是', '“不是……而是……”句式'),
    (r'不再把|清楚的负结论|白花|及时止损|本身就是一条结论|撞的是|预言|值得一提|不难发现|由此可见|综上所述|总而言之|一方面.{0,30}另一方面', 'AI 腔'),
    (r'赋能|抓手|颗粒度|闭环|证据链|全链路|矩阵|打通|沉淀|对齐了', '空心大词'),
]
PROCESS = [
    (r'\b[\w\-]+\.(py|jsonl|json|csv|npz|log|md)\b', '文件名（放进附件或任务文件）'),
    (r'\b(PID|SHA|sha256|exit ?code|OOM)\b|解析器|修复记录|冻结协议|回归测试|锁文件|断点续跑|队列', '过程细节'),
    (r'共完成\s*\d+|读了\s*\d+\s*篇|\d+\s*个任务|分工如下|同时上\s*\d+\s*门', '工作量展示'),
    (r'\d{1,2}[-/月]\d{1,2}日?\s*更新|更新于|（更新）|【更新】', '更新横幅（新结果就整篇重写）'),
    (r'冻结|原票|复评|计账|按既有|统一采用|同源|逐图标签|原尺寸|CUDA|CPU|FP32|bf16|Lanczos|sigma|前向', '执行口径（正文用“计算次数”“独立评测”这类读者词；口径放进折叠的“方法与口径”）'),
]
# 统计方法名：正文出现一次结论里的 p 值可以，方法说明放折叠区
STATS = r'McNemar|Holm|bootstrap|重采样|符号翻转|精确二项|经验分布|聚类重采样'

READER_HINTS = r'点开看|点击查看|点击展开|如下图所示|见下图|下图中|红色表示|蓝色表示|颜色表示|灰色表示|图例|左图|右图'
BAD_HEADINGS = r'^(做了什么|我们做了什么|几个例子|三个例子|例子|背景|小结|总结|其他|补充说明|说明|更新|附录|结果|主要结果)$'
BAD_TITLE_END = r'(报告|材料|总结|汇报|说明|介绍|整理|进展|汇总|概览|笔记|文档)$'


def text_of(fragment):
    fragment = re.sub(r'(?s)<(script|style|svg|math)[^>]*>.*?</\1>', ' ', fragment)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def check(path):
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

    # 2. 标题是结论
    h1 = re.findall(r'(?s)<h1[^>]*>(.*?)</h1>', body)
    if len(h1) != 1:
        E(f'要有且只有一个 h1（现在 {len(h1)} 个）')
    else:
        t = text_of(h1[0])
        if re.search(BAD_TITLE_END, t) or len(t) < 10:
            E(f'大标题“{t}”是名目，改成一句结论（例：“错误什么时候定下来，额外的算力就该什么时候花”）')

    # 3. 小标题正式、说清这节讲什么
    for lvl, h in re.findall(r'(?s)<(h[23])[^>]*>(.*?)</\1>', body):
        t = text_of(h)
        core = re.sub(r'^([一二三四五六七八九十]+、|\d+[.、]\s*)', '', t)
        if re.match(r'^0\d', t):
            E(f'小标题“{t}”：不用 01/02 编号，用“一、”或不编号')
        if re.match(BAD_HEADINGS, core):
            E(f'小标题“{t}”太空，写成这一节的内容（例：“计算量与正确数的关系”）')
        if re.search(r'[（(][^）)]*\d+[^）)]*[）)]$', t):
            W(f'小标题“{t}”带括注口径，数量直接写进标题（“· 48 组”）或删掉')

    # 4. 第一屏有加粗结论且带数字
    first = body[:body.find('<h2') if '<h2' in body else len(body)]
    first_sec = re.search(r'(?s)<section.*?</section>', body)
    lead = first + (first_sec.group(0) if first_sec else '')
    bolds = [text_of(b) for b in re.findall(r'(?s)<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>', lead)]
    if not bolds:
        E('第一屏没有加粗的结论句：开头就用一句加粗论断回答“答案是什么”')
    elif not re.search(r'\d', text_of(lead)):
        W('第一屏没有数字：结论后面跟两三句带数字的证据')

    # 5. 每节要有证据（图、表、照片、公式）
    secs = re.findall(r'(?s)<section[^>]*>(.*?)</section>', body)
    for s in secs:
        hm = re.search(r'(?s)<h2[^>]*>(.*?)</h2>', s)
        name = text_of(hm.group(1)) if hm else '(无标题)'
        has_ev = re.search(r'<svg|<img|<table|<math|<video', s)
        nums = len(re.findall(r'\d+(?:\.\d+)?\s*(?:%|组|题|张|个|次|步|对|vs)', text_of(s)))
        if not has_ev and nums >= 12:
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
    for pat, what in AI_TONE:
        for m in list(re.finditer(pat, plain))[:3]:
            E(f'{what}：“…{plain[max(0, m.start()-12):m.end()+12]}…”')
    for pat, what in PROCESS:
        for m in list(re.finditer(pat, main_text))[:3]:
            E(f'{what}：“…{main_text[max(0, m.start()-12):m.end()+12]}…”')
    for pat, what in ROOM_BANNED:
        if '路径' in what or '文件名' in what or '编号' in what:
            continue   # 上面已经按报告口径查过
        for m in list(re.finditer(pat, plain))[:2]:
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
    if re.search(r'Best-of-?N|BoN', alltext) and not re.search(r'直接画一张|直接画|单张|不做筛选|直接生成|N\s*=\s*1|BoN1', alltext):
        W('有和 Best-of-N 的比较，但没看到“直接画一张”的基线')

    # 9. 小样本百分比
    for m in re.finditer(r'(\d{1,3}(?:\.\d+)?)%\s*[（(]\s*(\d+)\s*/\s*(\d+)', plain):
        if int(m.group(3)) < 10:
            W(f'“{m.group(0)}”分母只有 {m.group(3)}，直接写个数，不写百分比')
    return errors, warns


def main():
    if len(sys.argv) < 2:
        sys.exit('用法：python check_report.py 页面.html [更多页面]')
    bad = 0
    for p in sys.argv[1:]:
        errors, warns = check(p)
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
