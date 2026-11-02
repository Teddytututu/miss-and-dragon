"""Run due process checks, or inspect their saved observations."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from board import checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT/'data')
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args(argv)
    print(json.dumps(checks.run(args.root, show_only=args.show), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
