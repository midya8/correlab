"""Reproducible signal figure with every numeric cell and full report bound."""
import base64,html,json,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from correlab import signal_demo
from correlab.exact import jsonify


def values(r):
    d={}
    for i,c in enumerate(r['reveal_controls']):
        d[f'reveal-{i}']=c['reveal_probability'];d[f'gain-{i}']=c['audit']['players'][0]['override_gain']
    for i,p in enumerate(r['cyclic_partitions']['players'][0]['partitions']):
        d[f'partition-{i}']=''.join(map(str,p['labels']));d[f'partition-value-{i}']=p['audit']['override_gain']
    g=r['identity_to_noise'];d['high']=g['original']['players'][0]['override_gain'];d['low']=g['garbled']['players'][0]['override_gain']
    d['lift']=g['certificates'][0]['lifted_gain'];d['loss']=g['certificates'][0]['information_loss']
    for i,s in enumerate(g['certificates'][0]['lifted_coarse_policy']):d[f'slack-{i}']=s['optimality_slack']
    return d


def render(report):
    r=jsonify(report);d=values(r)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1140" viewBox="0 0 1120 1140">',
         '<rect width="1120" height="1140" fill="#edf2f5"/><rect x="16" y="16" width="1088" height="1108" rx="18" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#24313b}.muted{fill:#5c6c78}</style>']
    def t(x,y,s,size=17,extra=''):out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(k,x,y):t(x,y,d[k],20,f'id="cell-{k}" data-value="{d[k]}"')
    t(42,58,'Correlab / what can the player actually observe?',27,'font-weight="700"')
    t(42,90,'Trusted baseline executor. Private signal only. Pass or unilateral override. Exact rational witnesses.',17,'class="muted"')
    t(42,137,'The information model is part of the certificate',22,'font-weight="700"')
    t(42,170,'Draw baseline (i,j) from Q. Player sees z from K[i,z], NOT the hidden baseline action i.',18)
    t(42,203,'Pass keeps i. Override chooses d. Opponent stays at j. Payoff changes are scored cell by cell.',17)
    t(42,244,'Coarse gain  <=  supplied-channel override gain  <=  full-swap gain',21,'font-weight="700"')
    t(42,294,'1 A rare reveal changes the available override policy',22,'font-weight="700"')
    t(42,327,'Roth fixture: reveal C with probability alpha, otherwise emit one common signal.',18)
    t(42,359,'Uniform diagonal baseline; both players have the same values. No learned channel.',17,'class="muted"')
    t(65,410,'Reveal probability',18,'font-weight="700"');t(65,459,'Override gain',18,'font-weight="700"')
    for i,x in enumerate((400,555,710,865)):cell(f'reveal-{i}',x,410);cell(f'gain-{i}',x,459)
    t(42,515,'2 The number of signals alone does not determine incentive value',22,'font-weight="700"')
    t(42,548,'Developed cyclic table [[0,-10,3],[1,0,-10],[-10,2,0]], uniform diagonal Q; column pays 0.',17)
    t(65,595,'Partition labels',18,'font-weight="700"');t(65,644,'Row override gain',18,'font-weight="700"')
    for i,x in enumerate((355,490,625,760,895)):cell(f'partition-{i}',x,595);cell(f'partition-value-{i}',x,644)
    t(42,689,'001, 010, 011 each use two signals, but pool different baseline actions. They are incomparable.',17)
    t(42,742,'3 Supplied post-garbling: a lifted policy proves monotonicity',22,'font-weight="700"')
    t(42,775,'Roth identity signals -> independent fair-bit signals. The lifted policy passes everywhere.',17)
    for x,label,k in ((65,'Original gain','high'),(320,'Garbled gain','low'),(575,'Lifted gain','lift'),(830,'Information loss','loss')):
        t(x,824,label,17,'font-weight="700"');cell(k,x+45,865)
    t(65,916,'Original-signal slacks:',17)
    for i,x in enumerate((400,555,710)):cell(f'slack-{i}',x,916)
    t(65,954,'Information loss = sum of nonnegative original-signal optimality slacks.',18)
    t(42,1007,'Every signal/candidate retains full joint-cell terms, conditional gains, ties and an attaining policy.',17)
    t(42,1042,'All 1, 2, 5, 15 deterministic partitions for 1..4 actions; every strict refinement is checked.',17)
    t(42,1083,'No transformed CE, simultaneous override, channel-order search, privacy, learning or safety claim.',16,'class="muted"')
    blob=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode()
    out.append('<metadata id="report-zlib-base64">'+blob+'</metadata></svg>');return '\n'.join(out)+'\n'


if __name__=='__main__':
    path=Path(__file__).resolve().parents[1]/'assets/private-signals.svg';text=render(signal_demo())
    if sys.argv[1:]==['--check']:
        if path.read_text()!=text:raise SystemExit('signal SVG differs')
    elif not sys.argv[1:]:path.write_text(text)
    else:raise SystemExit('usage: render_signals.py [--check]')
