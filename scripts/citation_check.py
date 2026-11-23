"""Verify arXiv IDs and titles; use --offline --cache for reproducible checks."""
import argparse
import csv
import difflib
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata
import urllib.request
from urllib.parse import urlsplit
import uuid
import xml.etree.ElementTree as ET

CACHE = Path.cwd() / '.arxiv_cache.json'
ID = re.compile(r'(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?![\d])')
NS = {'atom': 'http://www.w3.org/2005/Atom'}


def load_cache(path=None):
    path = Path(CACHE if path is None else path)
    value = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError('arXiv cache must be a JSON object')
    if not all(isinstance(row, dict) and isinstance(row.get('title'), str) for row in value.values()):
        raise ValueError('arXiv cache entries require title strings')
    return value


def write_cache(path, cache):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(cache, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def fetch(ids, cache, *, cache_path=None):
    """Successful Atom responses add metadata; transport failures stay unresolved."""
    need = sorted({i for i in ids if i not in cache})
    for offset in range(0, len(need), 40):
        chunk = need[offset:offset + 40]
        url = 'https://export.arxiv.org/api/query?max_results=100&id_list=' + ','.join(chunk)
        feed = None
        for attempt in range(3):
            try:
                response = urllib.request.urlopen(url, timeout=30)
                try:
                    feed = ET.fromstring(response.read())
                finally:
                    if hasattr(response, 'close'):
                        response.close()
                if feed.tag != '{' + NS['atom'] + '}feed':
                    raise ValueError('Expected an Atom feed')
                break
            except (OSError, ValueError, ET.ParseError):
                feed = None
                if attempt < 2:
                    time.sleep(3)
        if feed is None:
            continue
        found = {}
        for entry in feed.findall('atom:entry', NS):
            parsed = urlsplit(entry.findtext('atom:id', '', NS))
            match = ID.fullmatch(parsed.path.removeprefix('/abs/'))
            if parsed.hostname not in {'arxiv.org', 'www.arxiv.org'} or match is None:
                continue
            pid = match.group(1)
            title = re.sub(r'\s+', ' ', entry.findtext('atom:title', '', NS)).strip()
            if pid in chunk and title:
                found[pid] = dict(title=title, published=entry.findtext('atom:published', '', NS)[:10])
        cache.update(found)
        write_cache(CACHE if cache_path is None else cache_path, cache)
        if offset + 40 < len(need):
            time.sleep(3)
    return cache


def sim(a, b):
    def norm(text):
        return re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()
    a, b = norm(a), norm(b)
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--id-col')
    parser.add_argument('--title-col')
    parser.add_argument('--show', type=int, default=0)
    parser.add_argument('--cache', type=Path, default=Path(CACHE))
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args(argv)
    if args.title_col and not args.id_col:
        parser.error('--title-col requires --id-col')
    try:
        pairs = []
        if args.id_col:
            with args.path.open(encoding='utf-8-sig', newline='') as stream:
                reader = csv.DictReader(stream)
                required = {args.id_col} | ({args.title_col} if args.title_col else set())
                if not required <= set(reader.fieldnames or []):
                    raise ValueError('CSV columns are missing')
                for row in reader:
                    match = ID.search(row.get(args.id_col, '') or '')
                    if not match:
                        raise ValueError('CSV row contains an invalid arXiv ID')
                    title = (row.get(args.title_col, '') or '') if args.title_col else ''
                    if args.title_col and not title.strip():
                        raise ValueError('CSV row requires a title to verify')
                    pairs.append((match.group(1), title))
        else:
            pairs = [(pid, '') for pid in sorted(set(ID.findall(args.path.read_text(encoding='utf-8-sig'))))]
        if not pairs:
            raise ValueError('Input contains no arXiv IDs')
        cache = load_cache(args.cache)
        ids = sorted({pid for pid, _ in pairs})
        if not args.offline:
            fetch(ids, cache, cache_path=args.cache)
        bad = unresolved = 0
        for pid, title in pairs:
            real = cache.get(pid, {}).get('title')
            if not real or real == '__NOT_FOUND__':
                unresolved += 1
                print('UNRESOLVED ' + pid)
            elif title and sim(title, real) < .5:
                bad += 1
                print(f'MISMATCH {pid} | supplied={title} | arxiv={real}')
        for pid in ids[:args.show]:
            row = cache.get(pid, {})
            print(pid, row.get('published', ''), row.get('title', 'UNRESOLVED'))
        print(f'ids={len(ids)} unresolved={unresolved} title_mismatch={bad}')
        return 2 if unresolved else 1 if bad else 0
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
