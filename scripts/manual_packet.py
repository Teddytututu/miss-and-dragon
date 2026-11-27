"""Build, paste, review and inspect a local manual packet; prints JSON."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from board import manual_packets


def main(argv=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-dir',type=Path,required=True)
    sub=parser.add_subparsers(dest='action',required=True)
    create=sub.add_parser('create'); create.add_argument('--title',required=True);create.add_argument('--question',type=Path,required=True)
    create.add_argument('--source',type=Path,action='append',default=[]);create.add_argument('--task',default='')
    paste=sub.add_parser('paste');paste.add_argument('--answer',type=Path,required=True);paste.add_argument('--file',type=Path,action='append',default=[])
    review=sub.add_parser('review');review.add_argument('--version',required=True);review.add_argument('--decision',choices=['accepted','partial','rejected'],required=True)
    review.add_argument('--note',required=True);review.add_argument('--task',default='')
    review.add_argument('--adopt-file',action='append',help='A registered returned file selected by this review; repeat for each file')
    sub.add_parser('show')
    a=parser.parse_args(argv)
    a.packet_dir=a.packet_dir.resolve()
    try:
        if a.action=='create':result=manual_packets.create(a.packet_dir,a.title,a.question.read_text('utf-8-sig'),a.source,task=a.task)
        elif a.action=='paste':result=manual_packets.paste(a.packet_dir,a.answer.read_text('utf-8-sig'),a.file)
        elif a.action=='review':result=manual_packets.review(a.packet_dir,a.version,a.decision,a.note,task=a.task,adopted_files=a.adopt_file)
        else:result=manual_packets.snapshot(a.packet_dir)
    except (ValueError,OSError) as error:
        print(json.dumps(dict(ok=False,packet_dir=str(a.packet_dir),error=str(error)),ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
