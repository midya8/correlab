"""Exact finite bimatrix obedience audits. Both players maximize their own payoff."""
from fractions import Fraction as F
from math import prod
from .exact import matrix


def game(row_payoffs,column_payoffs):
    a,b=matrix(row_payoffs),matrix(column_payoffs)
    if (len(a),len(a[0]))!=(len(b),len(b[0])):raise ValueError('payoff shapes differ')
    return a,b


def law(joint,m,n):
    q=matrix(joint)
    if (len(q),len(q[0]))!=(m,n):raise ValueError('joint shape mismatch')
    if any(v<0 for r in q for v in r) or sum(map(sum,q))!=1:
        raise ValueError('joint probabilities must be nonnegative and sum exactly to one')
    return q


def _player(payoff,q,player):
    # Transpose both arrays for column, preserving its own payoff-maximizing orientation.
    if player=='column':payoff=[list(r) for r in zip(*payoff)];q=[list(r) for r in zip(*q)]
    k,h=len(q),len(q[0]);mass=list(map(sum,q))
    baseline=sum(q[i][j]*payoff[i][j] for i in range(k) for j in range(h))
    internal=[]
    for i in range(k):
        row=[]
        for d in range(k):
            terms=[{'opponent_action':j,'probability':q[i][j],
                    'payoff_difference':payoff[d][j]-payoff[i][j],
                    'contribution':q[i][j]*(payoff[d][j]-payoff[i][j])} for j in range(h)]
            g=sum(t['contribution'] for t in terms)
            row.append({'recommendation':i,'deviation':d,'mass':mass[i],
                        'weighted_gain':g,'conditional_gain':g/mass[i] if mass[i] else None,'terms':terms})
        internal.append(row)
    gains=[[cell['weighted_gain'] for cell in r] for r in internal]
    coarse=[]
    for d in range(k):
        by_rec=[gains[i][d] for i in range(k)]
        coarse.append({'deviation':d,'by_recommendation':by_rec,'gain':sum(by_rec),
                       'deviating_payoff':baseline+sum(by_rec)})
    max_raw=max(c['gain'] for c in coarse);external=max(F(0),max_raw)
    pair=max(map(max,gains));ties=[[d for d in range(k) if gains[i][d]==max(gains[i])] for i in range(k)]
    mapping=[t[0] for t in ties];swap=sum(max(r) for r in gains)
    cells=[{'recommended_action':i,'opponent_action':j,'chosen_action':mapping[i],
            'probability':q[i][j],'payoff_difference':payoff[mapping[i]][j]-payoff[i][j],
            'contribution':q[i][j]*(payoff[mapping[i]][j]-payoff[i][j])} for i in range(k) for j in range(h)]
    assert sum(c['contribution'] for c in cells)==swap
    conditional=max(c['conditional_gain'] for r in internal for c in r if c['conditional_gain'] is not None)
    assert F(0)<=external<=swap and F(0)<=pair<=swap and pair<=conditional
    return {'player':player,'expected_payoff':baseline,'recommendation_masses':mass,
            'coarse_deviations':coarse,'coarse_max_raw_gain':max_raw,
            'coarse_best_actions':[c['deviation'] for c in coarse if c['gain']==max_raw],
            'external_regret':external,'internal_deviations':internal,
            'pairwise_internal_regret':pair,'worst_conditional_gain':conditional,
            'swap_regret':swap,'optimal_swap_choices':ties,'optimal_swap_count':prod(map(len,ties)),
            'attaining_swap':mapping,'attaining_swap_cells':cells,
            'attaining_swap_payoff':baseline+swap,
            'is_cce_obedient':max_raw<=0,'is_ce_obedient':pair==0}


def _audit(a,b,q):
    m,n=len(q),len(q[0]);x=list(map(sum,q));y=[sum(q[i][j] for i in range(m)) for j in range(n)]
    product=[[x[i]*y[j] for j in range(n)] for i in range(m)]
    players=[_player(a,q,'row'),_player(b,q,'column')]
    independent=q==product
    return {'shape':[m,n],'row_payoffs':a,'column_payoffs':b,'joint':q,'marginals':{'row':x,'column':y},
            'product_joint':product,'is_product':independent,
            'total_variation_from_product':sum(abs(q[i][j]-product[i][j]) for i in range(m) for j in range(n))/2,
            'players':players,'cce_epsilon':max(p['external_regret'] for p in players),
            'ce_pairwise_epsilon':max(p['pairwise_internal_regret'] for p in players),
            'ce_swap_epsilon':max(p['swap_regret'] for p in players),
            'ce_conditional_epsilon':max(p['worst_conditional_gain'] for p in players),
            'is_cce':all(p['is_cce_obedient'] for p in players),
            'is_ce':all(p['is_ce_obedient'] for p in players),
            'is_nash_product':independent and all(p['is_cce_obedient'] for p in players)}


def audit(row_payoffs,column_payoffs,joint):
    """Audit one supplied law, plus the explicitly different product-marginals control."""
    a,b=game(row_payoffs,column_payoffs);q=law(joint,len(a),len(a[0]))
    result=_audit(a,b,q);result['product_control']=_audit(a,b,result['product_joint'])
    return result
