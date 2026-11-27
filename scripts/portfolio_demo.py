"""Start the synthetic portfolio demo; reset keeps the previous directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from demo_research import run

MARKER = '.portfolio-demo.json'
IDENTITY = {'kind': 'miss-and-dragon-portfolio-demo', 'schema': 1}


def prepare(data_dir, *, workspace=ROOT/'work', reset=False):
    workspace = Path(workspace).resolve()
    target = Path(data_dir).resolve()
    if target == workspace or not target.is_relative_to(workspace):
        raise ValueError('Choose a demo directory inside this repository work directory')
    archive = None
    populated = target.exists() and any(target.iterdir())
    if populated:
        try:
            marker = json.loads((target/MARKER).read_text('utf-8'))
            project = json.loads((target/'project.json').read_text('utf-8'))
        except (OSError, ValueError) as error:
            raise ValueError('Choose an empty directory or a portfolio demo created by this launcher') from error
        if marker != IDENTITY or project.get('name') != 'Paired cache pilot':
            raise ValueError('Existing data belongs to another project; choose a new demo directory')
        if not reset:
            return {'action':'reused', 'data_dir':str(target), 'model_calls':0}
        archive = target.with_name(target.name+'.archive-'+uuid.uuid4().hex[:12])
        if archive.parent.resolve() != target.parent or archive.exists():
            raise ValueError('Choose another archive name')
        target.rename(archive)
    result = run(target)
    (target/MARKER).write_text(json.dumps(IDENTITY, indent=2)+'\n', encoding='utf-8')
    result['action'] = 'reset' if archive else 'created'
    if archive:
        result['archive'] = str(archive)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT/'work/portfolio-demo')
    parser.add_argument('--port', type=int, default=18780)
    parser.add_argument('--reset', action='store_true', help='Archive this marked demo and build a fresh one; stop its server first')
    parser.add_argument('--init-only', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port between 1024 and 65535')
    try:
        result = prepare(args.data_dir, reset=args.reset)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if not args.init_only:
        return subprocess.call([sys.executable, '-m', 'board', 'start',
                                '--data-dir', result['data_dir'], '--port', str(args.port)], cwd=ROOT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
