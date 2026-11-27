"""Build a timing report from one adopted answer, with a read-only consistency check."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path
import csv
import hashlib
import io
import math
import re
import zipfile

from . import manual_packets, storage

SCHEMA = 'paired-timing-report-v1'


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
        raise ValueError('Use a report or packet name containing letters, numbers, hyphens or underscores')
    return value


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _number(value, label):
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(label + ' must be a finite nonnegative number of seconds') from error
    if not number.is_finite() or number < 0 or not math.isfinite(float(number)):
        raise ValueError(label + ' must be a finite nonnegative number of seconds')
    return number


def _text(number):
    value = format(number, 'f')
    return value.rstrip('0').rstrip('.') if '.' in value else value


def measurements(raw, expected_batches):
    """Require one row per original input; preserve source order and explicit seconds."""
    try:
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        required = ['batch', 'baseline_seconds', 'cache_seconds']
        if reader.fieldnames != required:
            raise ValueError('Timing CSV columns must be batch,baseline_seconds,cache_seconds; revise and review mixed-unit answers first')
        rows = []
        seen = set()
        for line, row in enumerate(reader, 2):
            batch = (row.get('batch') or '').strip()
            if None in row or not batch or batch in seen:
                raise ValueError('Timing CSV row %d needs one distinct batch and exactly three columns' % line)
            seen.add(batch)
            baseline = _number(row['baseline_seconds'], 'Row %d baseline_seconds' % line)
            cached = _number(row['cache_seconds'], 'Row %d cache_seconds' % line)
            rows.append(dict(batch=batch, baseline_seconds=_text(baseline), cache_seconds=_text(cached)))
    except UnicodeError as error:
        raise ValueError('Timing CSV must use UTF-8') from error
    if not rows or seen != set(expected_batches):
        raise ValueError('Timing CSV must contain exactly the original input batches: ' + ', '.join(expected_batches))
    baseline = sum((Decimal(row['baseline_seconds']) for row in rows), Decimal(0))
    cached = sum((Decimal(row['cache_seconds']) for row in rows), Decimal(0))
    if not math.isfinite(float(baseline)) or not math.isfinite(float(cached)):
        raise ValueError('Timing totals must be finite')
    return rows, baseline, cached


def _inputs(folder):
    archive = storage.relative_file(folder, 'materials.zip')
    raw = archive.read_bytes()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            content = bundle.read('inputs.csv').decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames or 'batch' not in reader.fieldnames:
            raise ValueError('Original inputs.csv needs a batch column')
        batches = [(row.get('batch') or '').strip() for row in reader]
    except (KeyError, UnicodeError, zipfile.BadZipFile) as error:
        raise ValueError('The packet materials.zip must contain UTF-8 inputs.csv with a batch column') from error
    if not batches or any(not name for name in batches) or len(set(batches)) != len(batches):
        raise ValueError('Original inputs.csv needs one distinct, nonempty batch per row')
    return batches, _digest(raw)


def _bound_review(selected):
    review = selected['review']
    if not isinstance(review.get('artifacts'), list) or not isinstance(review.get('inputs'), dict):
        raise ValueError('Review this legacy answer once to bind its saved files and original inputs before generating a current report')
    if not {'ask.md', 'materials.zip'} <= set(review['inputs']):
        raise ValueError('Register ask.md and materials.zip as packet inputs, then review this answer again before reporting')
    return review


def _selected(root, packet, filename=None):
    folder = storage.relative_file(root, 'attachments/manual-packets/' + _name(packet))
    selected = manual_packets.adopted(folder)
    files = selected.get('files', [])
    candidates = [name for name in files if Path(name).suffix.lower() == '.csv']
    if filename is None:
        if len(candidates) != 1:
            raise ValueError('The adopted answer must have exactly one timing CSV, or select a registered file with --file')
        filename = candidates[0]
    if filename not in files:
        raise ValueError('Choose a CSV registered with the adopted answer')
    review = _bound_review(selected)
    if (('adopted_files' in review and filename not in review['adopted_files']) or
            (review['decision'] == 'partial' and 'adopted_files' not in review)):
        raise ValueError('Record the adopted timing CSV explicitly: review this answer with --adopt-file ' + filename)
    source = storage.relative_file(folder, filename)
    raw = source.read_bytes()
    batches, input_digest = _inputs(folder)
    rows, baseline, cached = measurements(raw, batches)
    return folder, selected, source, raw, rows, baseline, cached, input_digest


def _html(title, rows, baseline, cached, answer_number, review, csv_link, answer_link):
    comparison = 'reduced' if cached < baseline else 'increased' if cached > baseline else 'kept'
    heading = ('Caching kept the paired time at %s seconds' % _text(baseline)
               if cached == baseline else
               'Caching %s the paired time from %s to %s seconds' % (comparison, _text(baseline), _text(cached)))
    table = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' %
                    (escape(row['batch']), row['baseline_seconds'], row['cache_seconds']) for row in rows)
    scale = max(baseline, cached)
    bars = []
    for y, label, value, color in [(30, 'Baseline', baseline, '#527d9f'), (90, 'Cached', cached, '#77a18d')]:
        width = float(value / scale) * 300 if scale else 0
        bars.append('<text x="0" y="%d">%s</text><rect x="110" y="%d" width="%.3f" height="28" rx="4" fill="%s"/><text x="430" y="%d">%s s</text>' %
                    (y, label, y - 20, width, color, y, _text(value)))
    partial = ('The timing CSV is included in the explicitly adopted files; read the review note for its scope.'
               if review['decision'] == 'partial' else 'The lead adopted this timing answer.')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>body{{font:16px/1.7 system-ui;color:#263b49;background:#f5f8fa;margin:0}}main{{max-width:760px;padding:28px;margin:auto;background:white}}svg{{width:100%;height:auto}}table{{width:100%;border-collapse:collapse;border-block:2px solid #425b69}}th,td{{text-align:left;padding:8px}}thead{{border-bottom:1px solid #425b69}}td{{border-bottom:1px solid #dce5eb}}</style>
<main><h1>{heading}</h1><p>This fictional {count}-batch example compares the original inputs in seconds. Its next decision is whether to measure memory on the same inputs.</p>
<svg viewBox="0 0 580 130" role="img" aria-label="Baseline {baseline} seconds, cached {cached} seconds">{bars}</svg>
<table><thead><tr><th>Batch</th><th>Baseline seconds</th><th>Cached seconds</th></tr></thead><tbody>{table}</tbody><tfoot><tr><th>Total</th><th>{baseline}</th><th>{cached}</th></tr></tfoot></table>
<h2>Which answer supports this result?</h2><p>Snapshot from answer {answer_number}. {partial}</p><p>{note}</p>
<p><a href="{csv_link}">Paired measurements</a> · <a href="{answer_link}">Adopted answer text</a></p>
<p>A changed adoption requires an explicit report refresh. Earlier answer text and returned files remain in the packet.</p></main></html>'''.format(
        title=escape(title), heading=escape(heading), count=len(rows), baseline=_text(baseline), cached=_text(cached),
        bars=''.join(bars), table=table, answer_number=answer_number, partial=partial,
        note=escape(str(review.get('note', ''))), csv_link=escape(csv_link, quote=True), answer_link=escape(answer_link, quote=True))


def build(root, packet='cache-pilot', *, filename=None, name='cache-pilot'):
    root = Path(root).resolve()
    name = _name(name)
    with storage.locked(root):
        folder, selected, source, raw, rows, baseline, cached, input_digest = _selected(root, packet, filename)
        versions = manual_packets.snapshot(folder)['answer_versions']
        answer_number = next(i + 1 for i, row in enumerate(versions) if row['id'] == selected['id'])
        report = storage.relative_file(root, 'reports/' + name + '.html')
        csv_path = report.with_name('paired.csv' if name == 'cache-pilot' else name + '-data.csv')
        answer_path = storage.relative_file(folder, selected['answer'])
        answer_raw = answer_path.read_bytes()
        # Keep human-facing links local so moving the whole project preserves them.
        import os
        answer_link = Path(os.path.relpath(answer_path, report.parent)).as_posix()
        text = _html('Paired cache pilot', rows, baseline, cached, answer_number, selected['review'], csv_path.name, answer_link)
        manifest = dict(schema=SCHEMA, packet=packet, answer_id=selected['id'], answer_number=answer_number,
                        review=selected['review'], source=source.relative_to(root).as_posix(),
                        source_sha256=_digest(raw), answer=answer_path.relative_to(root).as_posix(),
                        answer_sha256=_digest(answer_raw), inputs_sha256=input_digest,
                        report=report.relative_to(root).as_posix(), report_sha256=_digest(text.encode('utf-8')),
                        csv=csv_path.relative_to(root).as_posix(), rows=rows,
                        baseline_seconds=float(baseline), cached_seconds=float(cached),
                        created_at=datetime.now(timezone.utc).isoformat())
        storage.write_bytes(csv_path, raw)
        storage.write_bytes(report, text.encode('utf-8'))
        storage.write(report.with_suffix('.provenance.json'), manifest)
        overview = storage.read(root / 'overview.json', {})
        def update_nodes(nodes):
            changed = False
            for node in nodes:
                if node.get('page') == manifest['report']:
                    node.update(report_answer=selected['id'], summary='The same batches take %s seconds baseline and %s seconds cached' %
                                (_text(baseline), _text(cached)))
                    changed = True
                changed = update_nodes(node.get('children', [])) or changed
            return changed
        if update_nodes(overview.get('tree', [])):
            storage.write(root / 'overview.json', overview)
    return check(root, name=name)


def check(root, *, name='cache-pilot'):
    """Inspect saved files without creating locks or updating projections."""
    root = Path(root).resolve()
    path = storage.relative_file(root, 'reports/' + _name(name) + '.provenance.json')
    value = storage.read(path)
    if not isinstance(value, dict) or value.get('schema') != SCHEMA:
        raise ValueError('Generate the paired report first; a valid provenance file is required')
    problems = []
    required = ['packet', 'answer_id', 'source', 'answer', 'report', 'csv', 'source_sha256', 'answer_sha256', 'report_sha256', 'inputs_sha256']
    if any(not isinstance(value.get(key), str) or not value[key] for key in required):
        raise ValueError('The report provenance is incomplete; regenerate it from a reviewed answer')
    folder = storage.relative_file(root, 'attachments/manual-packets/' + _name(value['packet']))
    meta = manual_packets.snapshot(folder)
    adopted = meta.get('adopted_answer')
    if adopted != value['answer_id']:
        problems.append('The adopted answer has changed; refresh the report before using it for the current decision')
    else:
        selected = manual_packets.adopted(folder)
        _bound_review(selected)
        if selected.get('review') != value.get('review'):
            problems.append('The review decision or adopted scope has changed; refresh the report')
    for field, digest in [('source', 'source_sha256'), ('answer', 'answer_sha256'), ('report', 'report_sha256'), ('csv', 'source_sha256')]:
        target = storage.relative_file(root, value[field])
        if not target.is_file() or _digest(target.read_bytes()) != value[digest]:
            problems.append('Saved %s has changed or is missing: %s' % (field, value[field]))
    batches, input_digest = _inputs(folder)
    if input_digest != value['inputs_sha256']:
        problems.append('The original input bundle has changed')
    source = storage.relative_file(root, value['source'])
    if source.is_file():
        rows, baseline, cached = measurements(source.read_bytes(), batches)
        if rows != value.get('rows') or float(baseline) != value.get('baseline_seconds') or float(cached) != value.get('cached_seconds'):
            problems.append('Recorded totals or rows do not match the source CSV')
    return dict(ok=not problems, status='current' if not problems else 'refresh_required',
                packet=value['packet'], adopted_answer=adopted, report_answer=value['answer_id'],
                answer_number=value.get('answer_number'), baseline_seconds=value.get('baseline_seconds'),
                cached_seconds=value.get('cached_seconds'), report=value['report'], csv=value['csv'], problems=problems)


def reader_notice(root, target):
    """Make an outdated generated report visible without changing saved bytes."""
    root, target = Path(root).resolve(), Path(target)
    if target.parent != root / 'reports' or not target.with_suffix('.provenance.json').is_file():
        return ''
    try:
        result = check(root, name=target.stem)
        if target.resolve() != (root / result['report']).resolve():
            message = 'Historical snapshot: this file is not the report tracked by the current provenance. Open the generated report for the adopted answer.'
        else:
            message = ('This report matches the currently adopted answer.' if result['ok'] else
                   'Historical snapshot: refresh the report from the currently adopted answer before using it for a new decision.')
    except (OSError, ValueError, KeyError, TypeError):
        message = 'The report source needs review. Ask the lead to check the saved packet and refresh this report.'
    return '<aside role="status" style="padding:12px;background:#fff2c9;color:#342e20">' + escape(message) + '</aside>'
