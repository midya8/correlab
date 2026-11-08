"""Developed controls; first game/distribution adapted from Aaron Roth lecture 8."""
from .core import audit
from .history import history


def demo():
    a=[[1,-1,0],[-1,1,0],[0,0,'-11/10']]
    q=[['1/3',0,0],[0,'1/3',0],[0,0,'1/3']]
    coarse=audit(a,a,q)
    coord=audit([[2,0],[0,1]],[[2,0],[0,1]],[['1/2',0],[0,'1/2']])
    rare=audit([[1,1],[0,0]],[[0,0],[0,0]],[['999/1000',0],['1/1000',0]])
    aggregate=audit([[0],[0],[1]],[[0],[0],[0]],[['1/3'],['1/3'],['1/3']])
    trace=history(a,a,[[2,2],[0,0],[1,1],[0,0],[1,1],[2,2]],[1,2,3,6])
    assert coarse['is_cce'] and not coarse['is_ce']
    assert coord['is_ce'] and not coord['product_control']['is_ce']
    assert rare['ce_pairwise_epsilon']*1000==rare['ce_conditional_epsilon']
    assert aggregate['ce_swap_epsilon']==2*aggregate['ce_pairwise_epsilon']
    assert trace['prefixes'][-1]['audit']['is_cce'] and not trace['last_round_audit']['is_cce']
    return {'cce_not_ce':coarse,'coordination':coord,'rare_recommendation':rare,'aggregate_swap':aggregate,'history':trace}
