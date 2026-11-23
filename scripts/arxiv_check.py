"""Compatibility entry for arXiv title verification and the local cache."""
from pathlib import Path
import citation_check as core
from citation_check import ID, sim, time

CACHE = Path.cwd() / '.arxiv_cache.json'

def load_cache(path=None):
    return core.load_cache(CACHE if path is None else path)

def fetch(ids, cache):
    return core.fetch(ids, cache, cache_path=CACHE)

def main(argv=None):
    core.CACHE = CACHE
    return core.main(argv)

if __name__ == '__main__':
    raise SystemExit(main())
