"""Bundled character art."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def avatars():
    path=ROOT/'board/art/fanart.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def reaction_catalog(data):
    """Read installer-provided local images without resolving any remote URLs."""
    from . import storage

    try:
        manifest = storage.relative_file(data, 'emotes/manifest.json')
        if not manifest.is_file() or manifest.stat().st_size > 256 * 1024:
            return []
        rows = json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    if not isinstance(rows, list):
        return []

    catalog = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'label'}:
            continue
        ident, label = row['id'], row['label']
        if type(ident) is not int or not 0 < ident < 10**12 or not isinstance(label, str) or not label.strip() or len(label) > 80:
            continue
        name = f'{ident}.png'
        try:
            image = storage.relative_file(data, f'emotes/{name}')
            if not image.is_file() or not 24 <= image.stat().st_size <= 512 * 1024:
                continue
            with image.open('rb') as stream:
                if stream.read(8) != b'\x89PNG\r\n\x1a\n':
                    continue
        except (OSError, ValueError):
            continue
        key = f'bili:{ident}'
        catalog[key] = dict(key=key, label=label, url=f'/room-reactions/{name}', fallback='🙂')
    return list(catalog.values())
