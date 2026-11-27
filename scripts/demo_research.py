"""Build a complete fictional research workflow using local files only."""
from pathlib import Path
import argparse
import csv, io, math
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from board import lifecycle, paired_report, project, storage
from demo_manual_packet import run as packet_demo


def paired_measurements(raw, expected_batches):
    """Read one snapshot and require a finite timing pair for every input batch."""
    expected = [str(batch).strip() for batch in expected_batches]
    if not expected or any(not batch for batch in expected) or len(set(expected)) != len(expected):
        raise ValueError('Input batches must be nonempty and unique')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    required = {'batch', 'baseline_seconds', 'cache_seconds'}
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)) or not required.issubset(headers):
        raise ValueError('Unique columns with batch and both timing measurements required')
    rows = []
    seen = set()
    for row in reader:
        batch = (row.get('batch') or '').strip()
        if None in row or any(value is None for value in row.values()):
            raise ValueError('Each measurement must match the CSV columns')
        if batch not in expected or batch in seen:
            raise ValueError('Each input batch requires exactly one measurement pair')
        try:
            baseline = float(row['baseline_seconds'])
            cached = float(row['cache_seconds'])
        except (ValueError, TypeError) as error:
            raise ValueError('Numeric seconds required') from error
        if not all(math.isfinite(value) and value >= 0 for value in (baseline, cached)):
            raise ValueError('Finite nonnegative seconds required')
        rows.append(dict(batch=batch, baseline=baseline, cached=cached))
        seen.add(batch)
    if seen != set(expected):
        raise ValueError('Measurements must cover every input batch')
    try:
        baseline = math.fsum(row['baseline'] for row in rows)
        cached = math.fsum(row['cached'] for row in rows)
    except OverflowError as error:
        raise ValueError('Finite timing totals required') from error
    if not all(math.isfinite(value) for value in (baseline, cached)):
        raise ValueError('Finite timing totals required')
    return rows, baseline, cached



def run(root):
    root = Path(root).resolve()
    if root.exists() and not root.is_dir():
        raise ValueError('The data path is a file: %s. Choose a new or empty directory.' % root)
    if root.exists() and any(root.iterdir()):
        raise ValueError('The fictional example needs an empty directory: %s. To read an existing run, start the board with this --data-dir; to run again, choose a new directory.' % root)
    required = ['demo/resource-plan.json'] + ['demo/manual-packet/' + name for name in
               ['question.md', 'inputs.csv', 'answer-v1.md', 'result-v1.csv', 'answer-v2.md', 'result-v2.csv']]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        raise ValueError('The source package is incomplete; restore: ' + ', '.join(missing))
    source = ROOT / 'demo/manual-packet/result-v2.csv'
    raw = source.read_bytes()
    inputs = csv.DictReader(io.StringIO((source.parent / 'inputs.csv').read_text('utf-8-sig')))
    batches = [row.get('batch') or '' for row in inputs]
    paired_measurements(raw, batches)
    paired_report.measurements(raw, batches)
    project.initialize(root, 'Paired cache pilot', 'Does caching speed up the same batches?',
                       'A paired timing report and a reproducible next task', 'Demo reader')
    packet = packet_demo(root / 'attachments/manual-packets/cache-pilot')
    result = paired_report.build(root)
    tasks = root / 'tasks'
    tasks.mkdir(exist_ok=True)
    (tasks / 'T001-cache-pilot.md').write_text(
        '# Cache timing\n\nCompare batches A and B in seconds. Deliver a paired CSV.\n'
        'Acceptance: both original batches occur once; timing and memory have separate claims.\n', encoding='utf-8')
    (tasks / 'T002-memory.md').write_text(
        '# Measure memory\n\nMeasure peak memory on the same batches A and B.\n'
        'Acceptance: record units, both methods and the measurement procedure.\n'
        'This is the next fictional task; the timing table supplies no memory measurement.\n', encoding='utf-8')
    lifecycle.transition(root, 'new', 'T001', by='Claude', title='Cache timing', when='Inputs ready', node='Paired cache pilot')
    lifecycle.transition(root, 'start', 'T001', by='GPT', status='0/2 · Compare batches · 约 23:00')
    first = packet['answer_versions'][0]
    second = packet['answer_versions'][1]
    evidence = 'attachments/manual-packets/cache-pilot/'
    lifecycle.transition(root, 'deliver', 'T001', by='GPT', evidence=evidence + first['answer'])
    lifecycle.transition(root, 'reject', 'T001', by='Claude', reason=first['review']['note'])
    lifecycle.transition(root, 'start', 'T001', by='GPT', status='0/2 · Repeat paired run · 约 23:00')
    lifecycle.transition(root, 'deliver', 'T001', by='GPT', evidence=evidence + second['answer'])
    lifecycle.transition(root, 'accept', 'T001', by='Claude', summary='Paired timing table adopted; memory remains a separate task', owner_step='none')
    lifecycle.transition(root, 'new', 'T002', by='Claude', title='Measure memory', when='ready now: measure the same inputs')
    (root / 'findings.md').write_text(
        '# Findings\n\nT001 initial result (answer 2): the fictional paired timing totals were %.6g seconds baseline and %.6g seconds cached.\n'
        'That reviewed snapshot supports timing only; T002 measures memory separately. See reports/cache-pilot.html for the current adopted result.\n' %
        (result['baseline_seconds'], result['cached_seconds']), encoding='utf-8')
    resource = storage.read(ROOT / 'demo/resource-plan.json')
    resource['jobs'][0].update(title='Measure one batch', purpose='Measure time on the paired inputs')
    resource['jobs'][1].update(title='Compare after the trial', purpose='Run the paired comparison after its trial')
    storage.write(root / 'attachments/resource-plan.json', resource)
    overview = storage.read(root / 'overview.json')
    overview.update(
        todo=[dict(what='Read the adopted timing table', when='Now', how='Open Paired cache pilot and compare both answer versions')],
        progress_lines=[dict(line='Paired cache pilot', text='Timing table adopted; memory measurement is the next task')],
        tree=[dict(id='paired-cache', title='Paired cache pilot', status='done', tasks=['T001'],
                   report_answer=result['report_answer'],
                   summary='The same batches take %.6g seconds baseline and %.6g seconds cached' %
                   (result['baseline_seconds'], result['cached_seconds']), page=result['report'], children=[])],
        links=[dict(title='Paired cache pilot', path=result['report'], cat='研究'),
               dict(title='Paired measurements', path=result['csv'], under=result['report'], cat='研究')])
    storage.write(root / 'overview.json', overview)
    return dict(data_dir=str(root), baseline_seconds=result['baseline_seconds'], cached_seconds=result['cached_seconds'],
                answer_versions=len(packet['answer_versions']), adopted_answer=packet['adopted_answer'],
                report=result['report'], report_check=result['status'], next_task='T002', model_calls=0,
                background_registrations=0)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.data_dir)
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps(dict(ok=False, error=str(error)), ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
