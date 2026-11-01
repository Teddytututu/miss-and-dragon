"""Discover citation neighbours from arXiv seeds, with caching and daily filtering.

python scripts/citation_chain.py seeds.txt output --hop2 2
python scripts/citation_chain.py seeds.txt output/DATE --since YYYY-MM-DD --exclude seen.csv

The output includes candidates.csv and fetch.log. Read abstracts and grade candidates
separately; metadata discovery alone does not assign a research reading status.
"""
import csv, hashlib, json, sys, time, argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

API = 'https://api.semanticscholar.org/graph/v1/paper/'
FIELDS = 'paperId,title,abstract,year,venue,citationCount,externalIds,publicationDate'


def get(url, cache, log):
    key = cache / (hashlib.sha1(url.encode()).hexdigest() + '.json')
    if key.exists():
        return json.loads(key.read_text(encoding='utf-8'))
    wait = 3
    for attempt in range(8):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'lit-chain/1.0'}), timeout=60) as r:
                data = json.loads(r.read().decode('utf-8'))
            key.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            time.sleep(1.2)
            return data
        except HTTPError as e:
            if e.code == 404:
                log(f'404 {url}')
                return None
            log(f'{e.code} 第{attempt + 1}次，等 {wait}s')
        except (URLError, TimeoutError) as e:
            log(f'网络 {e} 第{attempt + 1}次，等 {wait}s')
        time.sleep(wait)
        wait = min(wait * 2, 120)
    raise SystemExit(f'连续失败，停在 {url}；重跑会从cache接着来')


def pages(pid, edge, cache, log):
    side = 'citingPaper' if edge == 'citations' else 'citedPaper'
    out, offset = [], 0
    while True:
        url = f'{API}{quote(pid)}/{edge}?fields={FIELDS}&limit=1000&offset={offset}'
        data = get(url, cache, log)
        if not data:
            break
        rows = [d[side] for d in data.get('data') or [] if d.get(side, {}).get('paperId')]
        out += rows
        if data.get('next') is None or not rows:
            break
        offset = data['next']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('seeds')
    ap.add_argument('outdir')
    ap.add_argument('--hop2', type=int, default=0, help='被至少 N 个种子连到的再扩一层；0 不扩')
    ap.add_argument('--since', default='', help='每日模式：只要这天及以后发表的（YYYY-MM-DD），并且只抓“cites_seed的”')
    ap.add_argument('--exclude', default='', help='已推送清单 CSV（有 paperId 列），里面的跳过')
    a = ap.parse_args()
    out = Path(a.outdir); cache = out / 'cache'; cache.mkdir(parents=True, exist_ok=True)
    log_path = out / 'fetch.log'

    def log(msg):
        line = time.strftime('%H:%M:%S ') + msg
        print(line, flush=True)
        with log_path.open('a', encoding='utf-8') as logf:logf.write(line + '\n')

    seeds = [l.split('#')[0].strip() for l in Path(a.seeds).read_text(encoding='utf-8').splitlines()]
    seeds = [s for s in seeds if s]
    papers, links = {}, {}

    def add(p, seed, rel):
        pid = p['paperId']
        papers.setdefault(pid, p)
        links.setdefault(pid, set()).add((seed, rel))

    for s in seeds:
        meta = get(f'{API}arXiv:{s}?fields={FIELDS}', cache, log)
        if not meta:
            log(f'种子 {s} 找不到，跳过'); continue
        papers[meta['paperId']] = meta
        refs = [] if a.since else pages(meta['paperId'], 'references', cache, log)
        cits = pages(meta['paperId'], 'citations', cache, log)
        for p in refs: add(p, s, 'seed_reference')
        for p in cits: add(p, s, 'cites_seed')
        log(f'种子 {s}「{(meta.get("title") or "")[:50]}」引用 {len(refs)}，被引 {len(cits)}')

    seed_ids = {p['paperId'] for p in papers.values() if (p.get('externalIds') or {}).get('ArXiv') in seeds}
    if a.hop2:
        hubs = [pid for pid, l in links.items() if len({s for s, _ in l}) >= a.hop2 and pid not in seed_ids]
        log(f'第二层：{len(hubs)} 篇被 ≥{a.hop2} 个种子连到，抓引用它们的')
        for pid in hubs:
            name = 'hop2:' + (papers[pid].get('title') or pid)[:30]
            for p in pages(pid, 'citations', cache, log): add(p, name, 'cites_hub')

    skip = set()
    if a.exclude and Path(a.exclude).exists():
        with open(a.exclude, encoding='utf-8-sig') as f:
            skip = {r.get('paperId') for r in csv.DictReader(f)}
    rows = []
    for pid, p in papers.items():
        if pid in seed_ids or pid in skip:
            continue
        if a.since and (p.get('publicationDate') or str(p.get('year') or '')) < a.since:
            continue
        l = links.get(pid, set())
        ids = p.get('externalIds') or {}
        rows.append(dict(
            seed_links=len({s for s, _ in l if not s.startswith('hop2:')}),
            connections=' | '.join(sorted(f'{r}:{s}' for s, r in l)),
            title=p.get('title') or '', year=p.get('year') or '', date=p.get('publicationDate') or '',
            venue=p.get('venue') or '', citations=p.get('citationCount') or 0,
            arXiv=ids.get('ArXiv') or '', DOI=ids.get('DOI') or '', paperId=pid,
            abstract=(p.get('abstract') or '').replace('\n', ' '),
            grade='', reason=''))
    rows.sort(key=lambda r: (-r['seed_links'], -(r['year'] or 0), -r['citations']))
    if not rows:
        log('No new candidates')
    with (out / 'candidates.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['title'])
        w.writeheader(); w.writerows(rows)
    no_abs = sum(1 for r in rows if not r['abstract'])
    log(f'完成：去重后 {len(rows)} 篇，其中没有摘要 {no_abs} 篇 → {out / "candidates.csv"}')


if __name__ == '__main__':
    main()
