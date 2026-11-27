"""Run the fictional two-return manual handoff entirely on local files."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from board import manual_packets

def run(folder):
    source=ROOT/'demo'/'manual-packet'
    manual_packets.create(folder,'Cache pilot',(source/'question.md').read_text('utf-8'),[source/'inputs.csv'],task='T001')
    first=manual_packets.paste(folder,(source/'answer-v1.md').read_text('utf-8'),[source/'result-v1.csv'])
    manual_packets.review(folder,first['answer_versions'][0]['id'],'rejected','Mixed units and different batches; repeat the paired measurement',task='T001')
    second=manual_packets.paste(folder,(source/'answer-v2.md').read_text('utf-8'),[source/'result-v2.csv'])
    version=second['answer_versions'][1]
    return manual_packets.review(folder,version['id'],'partial','Adopt the paired timing table; measure memory separately',task='T002',adopted_files=version['files'])

def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    try:
        result=run(a.output)
    except (ValueError,OSError) as error:
        print(json.dumps(dict(ok=False,packet_dir=str(a.output.resolve()),error=str(error)),ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
