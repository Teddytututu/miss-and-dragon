"""Print the same optional resource forecast used by the board."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from board.ticket_schedule import from_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=ROOT / "data/attachments/resource-plan.json")
    parser.add_argument("--cards", type=int)
    parser.add_argument("--now", help="ISO date/time including timezone, for reproducible examples")
    args = parser.parse_args()
    print(json.dumps(from_file(args.file, cards=args.cards, now=args.now), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
