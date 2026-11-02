"""Read listed reports and their explicit project-local dependencies."""
from pathlib import Path
from urllib.parse import quote, urlsplit
import hashlib
import mimetypes

from . import md_render, reader_assets, storage

PREFIX = '/report/'
READABLE = reader_assets.READABLE


def report_url(value):
    key = hashlib.sha256(str(value).encode()).hexdigest()[:24]
    return PREFIX + key + '/' + quote(Path(value).name, safe='')


def eligible(root, target):
    root = Path(root).resolve()
    target = Path(target)
    try:
        relative = target.relative_to(root)
    except ValueError:
        return False
    if tuple(part.lower() for part in relative.parts[:2]) in {('attachments', 'discussion'), ('attachments', 'private')}:
        return False
    current = target
    while current != root:
        if current.is_symlink():
            return False
        current = current.parent
    resolved = target.resolve()
    if not resolved.is_relative_to(root):
        return False
    if tuple(part.lower() for part in resolved.relative_to(root).parts[:2]) in {('attachments', 'discussion'), ('attachments', 'private')}:
        return False
    return resolved.is_file() and resolved.suffix.lower() in READABLE


def catalog(root):
    out = {}
    for row in storage.read(Path(root) / 'overview.json', {}).get('links', []):
        value = row.get('path')
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            continue
        path = Path(root) / value
        if eligible(root, path):
            out[report_url(value)] = path.resolve()
    return out


def allowed_assets(root, report):
    return reader_assets.closure(report, frozenset(catalog(root).values()),
                                 eligible=lambda p: eligible(root, p))


def dispatch(handler, root, route):
    if not route.startswith(PREFIX):
        return False
    if handler.command not in {'GET', 'HEAD'}:
        handler.respond(405, dict(error='Use a read-only report link'), headers=[('Allow', 'GET, HEAD')])
        return True
    entries = catalog(root)
    # app.dispatch already decodes the URL path exactly once.
    routes = {urlsplit(url).path: path for url, path in entries.items()}
    from urllib.parse import unquote
    routes = {unquote(url): path for url, path in routes.items()}
    base = next((url for url in routes if route.startswith(url.rsplit('/', 1)[0] + '/')), None)
    report = routes.get(base)
    target = None
    allowed = set()
    if report is not None:
        allowed = allowed_assets(root, report)
        prefix = base.rsplit('/', 1)[0] + '/'
        name = route[len(prefix):]
        if route == base:
            target = report
        elif name.startswith('_asset/'):
            target = reader_assets.resolve_asset(allowed, name)
    if target is None or not eligible(root, target):
        handler.respond(404, dict(error='Choose a listed report or a referenced project file'))
        return True
    mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
    aliases = {path: url for url, path in entries.items()}
    def link(value):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            return value if parsed.scheme in {'https', 'http'} else '#'
        return reader_assets.routed_url(value, target, prefix, allowed, aliases)
    if target.suffix.lower() == '.md':
        content = md_render.render(target.read_text(encoding='utf-8-sig'), target.stem, link).encode()
        mime = 'text/html; charset=utf-8'
    elif target.suffix.lower() in {'.html', '.htm', '.css'}:
        rewrite = reader_assets.rewrite_css if target.suffix.lower() == '.css' else reader_assets.rewrite_html
        content = rewrite(target.read_text(encoding='utf-8-sig'), target, prefix, allowed, aliases).encode()
        mime += '; charset=utf-8'
    else:
        # Keep large report downloads bounded in memory, including HEAD.
        with target.open('rb') as stream:
            import os
            handler.send_response(200)
            for key, value in [
                ('Content-Type', mime), ('Content-Length', str(os.fstat(stream.fileno()).st_size)),
                ('Cache-Control', 'no-store, private'), ('X-Content-Type-Options', 'nosniff'),
                ('Referrer-Policy', 'no-referrer'), ('Content-Security-Policy', "default-src 'none'; frame-ancestors 'self'"),
            ]:
                handler.send_header(key, value)
            handler.end_headers()
            if handler.command == 'GET':
                while block := stream.read(128 * 1024):
                    handler.wfile.write(block)
        return True
    handler.respond(200, content, mime, headers=[
        ('Content-Security-Policy', "default-src 'self' data: blob:; script-src 'none'; style-src 'self' 'unsafe-inline'; connect-src 'none'; frame-ancestors 'self'; form-action 'none'; base-uri 'none'"),
    ])
    return True
