"""Refresh or verify the fictional paired timing report from its adopted answer."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from board import paired_report


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--packet', default='cache-pilot')
    parser.add_argument('--name', default='cache-pilot')
    parser.add_argument('--file', help='A timing CSV filename registered with the adopted answer')
    parser.add_argument('action', choices=['refresh', 'check'])
    args = parser.parse_args(argv)
    try:
        result = (paired_report.build(args.data_dir, args.packet, filename=args.file, name=args.name)
                  if args.action == 'refresh' else paired_report.check(args.data_dir, name=args.name))
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps(dict(ok=False, error=str(error)), ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
