"""Build a complete fictional research workflow using local files only."""
from pathlib import Path
import argparse, csv, io, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from board import project, storage
from demo_manual_packet import run as packet_demo


def run(root):
    root=Path(root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError('Choose an empty directory for the fictional example')
    project.initialize(root,'Paired cache pilot','Does caching speed up the same batches?',
                       'A paired timing report and a reproducible next task','Demo reader')
    packet=packet_demo(root/'attachments/manual-packets/cache-pilot')
    source=ROOT/'demo/manual-packet/result-v2.csv'
    rows=list(csv.DictReader(io.StringIO(source.read_text('utf-8'))))
    baseline=sum(float(r['baseline_seconds']) for r in rows)
    cached=sum(float(r['cache_seconds']) for r in rows)
    report=root/'reports/cache-pilot.html';report.parent.mkdir(parents=True)
    shutil.copyfile(source,report.with_name('paired.csv'))
    report.write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paired cache pilot</title><style>body{font:16px/1.7 system-ui;color:#263b49;background:#f5f8fa;margin:0}main{max-width:760px;padding:28px;margin:auto;background:white}svg{width:100%;height:auto}table{width:100%;border-collapse:collapse;border-block:2px solid #425b69}th,td{text-align:left;padding:8px}thead{border-bottom:1px solid #425b69}td{border-bottom:1px solid #dce5eb}</style>
<main><h1>Caching reduced the paired time from 5 to 3 seconds</h1><p>This fictional two-batch example answers the timing question. The next task measures memory on the same inputs.</p>
<svg viewBox="0 0 580 130" role="img" aria-label="Baseline 5 seconds, cached 3 seconds"><text x="0" y="30">Baseline</text><rect x="110" y="12" width="350" height="28" rx="4" fill="#527d9f"/><text x="475" y="33">5 s</text><text x="0" y="90">Cached</text><rect x="110" y="72" width="210" height="28" rx="4" fill="#77a18d"/><text x="335" y="93">3 s</text></svg>
<table><thead><tr><th>Batch</th><th>Baseline seconds</th><th>Cached seconds</th></tr></thead><tbody><tr><td>A</td><td>2</td><td>1</td></tr><tr><td>B</td><td>3</td><td>2</td></tr></tbody></table>
<h2>What changed the decision</h2><p>The first answer mixed units and different batches. The lead returned it. The second answer uses paired inputs; its timing table supports the next experiment. The lead adopted that table and opened T002 for memory.</p><p><a href="paired.csv">Paired measurements</a></p></main></html>''',encoding='utf-8')
    resource=json.loads((ROOT/'demo/resource-plan.json').read_text('utf-8'))
    resource['jobs'][0].update(title='Measure one batch',purpose='Measure time on the paired inputs')
    resource['jobs'][1].update(title='Compare after the trial',purpose='Run the paired comparison after its trial')
    storage.write(root/'attachments/resource-plan.json',resource)
    overview=storage.read(root/'overview.json')
    overview.update(todo=[dict(what='Send the next manual packet',when='After reading the timing table',how='Copy its question and upload ask.md plus materials.zip')],
                    progress_lines=[dict(line='Paired cache pilot',text='Timing table adopted; memory measurement is the next task')],
                    tree=[dict(id='paired-cache',title='Paired cache pilot',status='done',summary='The same batches take 5 seconds baseline and 3 seconds cached',page='reports/cache-pilot.html',children=[])],
                    links=[dict(title='Paired cache pilot',path='reports/cache-pilot.html',cat='研究'),dict(title='Paired measurements',path='reports/paired.csv',under='reports/cache-pilot.html',cat='研究')])
    storage.write(root/'overview.json',overview)
    (root/'board.md').write_text('# Paired cache pilot\n\n| ID | 工作 | 状态 | 负责人 |\n| --- | --- | --- | --- |\n| T002 | Measure memory | 排队：测量同一批输入 | GPT |\n',encoding='utf-8')
    return dict(data_dir=str(root),baseline_seconds=baseline,cached_seconds=cached,
                answer_versions=len(packet['answer_versions']),adopted_answer=packet['adopted_answer'],model_calls=0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.data_dir),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
