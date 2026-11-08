"""Reproducible exact report figure. Coordinates only are display quantities."""
import base64,html,json,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from correlab import demo
from correlab.exact import jsonify


def values(r):
    d={};c=r['cce_not_ce'];p=c['players'][0]
    d.update({'coarse-payoff':p['expected_payoff'],'coarse-fixed':max(x['deviating_payoff'] for x in p['coarse_deviations']),
              'coarse-raw':p['coarse_max_raw_gain'],'coarse-epsilon':c['cce_epsilon'],
              'coarse-pair':c['ce_pairwise_epsilon'],'coarse-swap':c['ce_swap_epsilon'],'coarse-conditional':c['ce_conditional_epsilon']})
    c=r['coordination'];p=c['product_control']
    for key,report in (('joint',c),('product',p)):
        for i in range(2):
            for j in range(2):d[f'{key}-{i}-{j}']=report['joint'][i][j]
        d[key+'-payoff']=report['players'][0]['expected_payoff'];d[key+'-epsilon']=report['ce_swap_epsilon']
    p=r['rare_recommendation']['players'][0];d.update({'rare-mass':p['recommendation_masses'][1],'rare-weighted':p['pairwise_internal_regret'],'rare-conditional':p['worst_conditional_gain']})
    p=r['aggregate_swap']['players'][0];d.update({'aggregate-pair':p['pairwise_internal_regret'],'aggregate-swap':p['swap_regret']})
    for i,v in enumerate(p['attaining_swap']):d[f'map-{i}']=v
    for i,p in enumerate(r['history']['prefixes']):d[f'prefix-{i}-rounds']=p['rounds'];d[f'prefix-{i}-epsilon']=p['audit']['cce_epsilon']
    d['last-epsilon']=r['history']['last_round_audit']['cce_epsilon']
    return d


def render(report):
    r=jsonify(report);d=values(r)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1280" viewBox="0 0 1120 1280">',
         '<rect width="1120" height="1280" fill="#edf2f5"/><rect x="16" y="16" width="1088" height="1248" rx="18" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#24313b}.muted{fill:#5c6c78}</style>']
    def t(x,y,s,size=17,extra=''):out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(k,x,y):t(x,y,d[k],18,f'id="cell-{k}" data-value="{d[k]}"')
    t(42,58,'Correlab / the recommendation changes the deviation',26,'font-weight="700"')
    t(42,88,'Exact supplied joint-play audits. Both players maximize. No sampling, training or equilibrium search.',17,'class="muted"')
    t(42,135,'1 Coarse obedience does not imply recommendation-wise obedience',21,'font-weight="700"')
    t(42,166,'Roth lecture-8 game: diagonal payoffs 1, 1, -11/10; joint law is uniform on that diagonal.',17)
    t(42,197,'Both players have the same figures. On recommendation C, switching to A or B gains 11/10.',17)
    for y,label,key in ((239,'Expected obey payoff','coarse-payoff'),(277,'Best fixed-action payoff','coarse-fixed'),(315,'Best fixed gain (raw)','coarse-raw'),(353,'Clipped CCE epsilon','coarse-epsilon')):
        t(55,y,label,17);cell(key,375,y)
    for y,label,key in ((239,'Pairwise weighted epsilon','coarse-pair'),(277,'Full-swap epsilon','coarse-swap'),(315,'Worst conditional epsilon','coarse-conditional')):
        t(570,y,label,17);cell(key,930,y)
    t(570,353,'CCE: yes. CE: no. One attaining swap is [A,B,A].',16)
    t(42,411,'2 The product of the marginals is a different, exploitable law',21,'font-weight="700"')
    t(42,443,'Coordination game: both payoff tables are [[2,0],[0,1]]. Joint play uses the two diagonal cells.',17)
    for xx,key,label in ((70,'joint','Supplied joint law'),(360,'product','Product control')):
        t(xx,480,label,17,'font-weight="700"')
        for i in range(2):
            for j in range(2):
                x,y=xx+80*j,499+48*i;out.append(f'<rect x="{x}" y="{y}" width="71" height="40" rx="4" fill="#dceae9"/>');cell(f'{key}-{i}-{j}',x+17,y+27)
    for y,label in ((517,'Expected payoff'),(564,'Full-swap epsilon')):
        t(640,y,label,16)
    t(850,481,'Joint',16,'font-weight="700"');t(965,481,'Product',16,'font-weight="700"')
    for x,k in ((850,'joint'),(965,'product')):cell(k+'-payoff',x,517);cell(k+'-epsilon',x,564)
    t(42,630,'3 A rare recommendation can hide a large conditional gain',21,'font-weight="700"')
    t(42,662,'Row action 0 always pays 1; action 1 pays 0. Action 1 is recommended only once per thousand.',17)
    for x,label,key in ((60,'Recommendation mass','rare-mass'),(400,'Weighted gain','rare-weighted'),(770,'Conditional gain','rare-conditional')):
        t(x,705,label,17,'font-weight="700"');cell(key,x+60,745)
    t(42,800,'4 Full swap regret adds gains across recommendations',21,'font-weight="700"')
    t(42,832,'One-column game: row payoffs [0,0,1], three equally likely recommendations.',17)
    t(60,875,'Largest one-pair gain',17);cell('aggregate-pair',335,875)
    t(570,875,'Full-swap gain',17);cell('aggregate-swap',820,875)
    t(60,921,'Attaining action map:',17)
    for i,x in enumerate((335,400,465)):cell(f'map-{i}',x,921)
    t(570,921,'Pairwise epsilon and swap epsilon differ.',16)
    t(42,976,'5 A finite-history identity is not a last-round or learning guarantee',21,'font-weight="700"')
    t(42,1008,'Developed realized play in the first game: CC, AA, BB, AA, BB, CC.',17)
    t(60,1052,'Prefix rounds',16,'font-weight="700"');t(60,1095,'Empirical CCE epsilon',16,'font-weight="700"')
    for i,x in enumerate((380,525,670,815)):cell(f'prefix-{i}-rounds',x,1052);cell(f'prefix-{i}-epsilon',x,1095)
    t(60,1141,'Final empirical law is CCE, but last-round CCE epsilon is',17);cell('last-epsilon',820,1141)
    t(42,1192,'All deviation terms, conditional gains, swap choices and realized regret totals remain in the JSON.',16)
    t(42,1226,'Small supplied games only. No causal, convergence, statistical, safety or real-agent performance claim.',15,'class="muted"')
    blob=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode()
    out.append('<metadata id="report-zlib-base64">'+blob+'</metadata></svg>');return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'assets/obedience-audit.svg';s=render(demo())
    if sys.argv[1:]==['--check']:
        if p.read_text()!=s:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:p.write_text(s)
    else:raise SystemExit('usage: render_demo.py [--check]')
