"""Finite realized-play certificates, not a learning rule or statistical estimator."""
from fractions import Fraction as F
from .core import game,audit


def history(row_payoffs,column_payoffs,actions,checkpoints=None):
    a,b=game(row_payoffs,column_payoffs);m,n=len(a),len(a[0])
    if not isinstance(actions,(tuple,list)) or not 1<=len(actions)<=1000:
        raise ValueError('actions needs 1..1000 realized joint actions')
    for pair in actions:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(type(v) is not int for v in pair):
            raise ValueError('each action must be a pair of integer indices, never bool')
        if not (0<=pair[0]<m and 0<=pair[1]<n):raise ValueError('action index out of range')
    total=len(actions)
    if checkpoints is None:checkpoints=[total]
    if not isinstance(checkpoints,(tuple,list)) or not 1<=len(checkpoints)<=100:
        raise ValueError('checkpoints needs 1..100 strictly increasing indices')
    if any(type(t) is not int or not 1<=t<=total for t in checkpoints) or any(x>=y for x,y in zip(checkpoints,checkpoints[1:])):
        raise ValueError('checkpoints must be strictly increasing valid round indices')
    if checkpoints[-1]!=total:raise ValueError('last checkpoint must be final round')
    counts=[[0]*n for _ in range(m)];prefixes=[]
    for t,(i,j) in enumerate(actions,1):
        counts[i][j]+=1
        if t not in checkpoints:continue
        q=[[F(v,t) for v in row] for row in counts];report=audit(a,b,q)
        certificates=[]
        for k,p in enumerate(report['players']):
            u=(a,b)[k];actual=sum(u[r][c] for r,c in actions[:t])
            fixed=[sum(u[d][c] if k==0 else u[r][d] for r,c in actions[:t]) for d in range((m,n)[k])]
            mapping=p['attaining_swap']
            swapped=sum(u[mapping[r]][c] if k==0 else u[r][mapping[c]] for r,c in actions[:t])
            external=max(F(0),max(fixed)-actual)
            assert actual==t*p['expected_payoff'] and external==t*p['external_regret']
            assert swapped-actual==t*p['swap_regret']
            certificates.append({'player':p['player'],'actual_total':actual,'fixed_action_totals':fixed,
                                 'external_regret_total':external,'attaining_swap':mapping,
                                 'swapped_total':swapped,'swap_regret_total':swapped-actual})
        prefixes.append({'rounds':t,'counts':[r[:] for r in counts],'audit':report,'realized_certificates':certificates})
    return {'rounds':total,'actions':[list(x) for x in actions],'checkpoints':list(checkpoints),
            'prefixes':prefixes,'last_round_audit':audit(a,b,[[F(int((r,c)==tuple(actions[-1]))) for c in range(n)] for r in range(m)])}
