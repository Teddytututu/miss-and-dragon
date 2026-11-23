"""Read-only dependency scan. Exit 0: clear; 1: references; 2: scan error."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

SUFFIXES = {'.py', '.sh', '.json', '.ps1', '.cmd', '.bat', '.yaml', '.yml', '.toml', '.md', '.js', '.cjs'}
EXCLUDED = {'done', 'failed', 'results', 'logs', '__pycache__', '.git'}


def local_refs(target, roots):
    roots = [Path(root).resolve(strict=True) for root in roots]
    if not roots or any(not root.is_dir() for root in roots):
        raise ValueError('Specify existing scan directories')
    target = Path(target)
    if not target.is_absolute():
        candidates = [root / target for root in roots if (root / target).is_dir()]
        if len(candidates) != 1:
            raise ValueError('Specify one existing target directory')
        target = candidates[0]
    target = target.resolve(strict=True)
    if not target.is_dir() or not any(target.is_relative_to(root) for root in roots):
        raise ValueError('Target must be a directory inside a scan root')
    needles = {target.name, str(target), target.as_posix()}
    found = set()
    def scan_error(error):
        raise error
    for root in roots:
        for folder, names, files in os.walk(root, onerror=scan_error, followlinks=False):
            parent = Path(folder)
            names[:] = [name for name in names if name not in EXCLUDED and not name.startswith('superseded-')
                        and not (parent / name).is_symlink() and (parent / name).resolve() != target]
            if parent.is_relative_to(target):
                names[:] = []
                continue
            for name in files:
                path = parent / name
                if path.suffix.lower() not in SUFFIXES or path.is_symlink():
                    continue
                text = path.read_text(encoding='utf-8-sig', errors='replace')
                if any(needle in text for needle in needles):
                    found.add(str(path.resolve()))
    return sorted(found)


def refs(target, *, roots, host=None):
    if host is None:
        return local_refs(target, roots)
    if not isinstance(host, str) or not host or host.startswith('-') or any(c.isspace() for c in host):
        raise ValueError('Specify a valid SSH host')
    args = ['python3', '-', str(target)]
    for root in roots:
        args += ['--root', str(root)]
    args += ['--json']
    command = ' '.join(shlex.quote(arg) for arg in args)
    try:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', host, command],
                                input=Path(__file__).read_bytes(), capture_output=True, timeout=240)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError('Dependency scan failed: ' + str(error)) from error
    if result.returncode not in (0, 1):
        raise RuntimeError('Dependency scan failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    try:
        value = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError('Dependency scanner returned invalid JSON') from error
    if (not isinstance(value, dict) or value.get('status') != 'checked' or not isinstance(value.get('references'), list)
            or not all(isinstance(p, str) for p in value['references'])):
        raise RuntimeError('Dependency scanner returned an incomplete result')
    if result.returncode != bool(value['references']):
        raise RuntimeError('Dependency scanner exit status conflicts with its references')
    return value['references']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target')
    parser.add_argument('--root', action='append', required=True, dest='roots')
    parser.add_argument('--host')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        found = refs(args.target, roots=args.roots, host=args.host)
        if args.json:
            print(json.dumps(dict(status='checked', references=found), ensure_ascii=False))
        else:
            print(f'references={len(found)}')
            for path in found:
                print(path)
        return 1 if found else 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
