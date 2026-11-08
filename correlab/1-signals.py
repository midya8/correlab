"""Private override-signal certificates for a trusted baseline action executor.

The player sees ONLY its signal, not its baseline recommendation. A pass action
leaves the hidden baseline action unchanged. This is not a transformed CE game.
"""
from fractions import Fraction as F
from math import prod
from .core import game,law,_player
from .exact import matrix


def channel(value,rows):
    k=matrix(value)
    if len(k)!=rows:raise ValueError('channel row count mismatch')
    if any(v<0 for r in k for v in r) or any(sum(r)!=1 for r in k):
        raise ValueError('each channel row must be nonnegative and sum exactly to one')
    return k


def _signals(payoff,q,k,player):
    if player=='column':payoff=[list(r) for r in zip(*payoff)];q=[list(r) for r in zip(*q)]
    n,h,s=len(q),len(q[0]),len(k[0]);records=[]
    baseline=sum(q[i][j]*payoff[i][j] for i in range(n) for j in range(h))
    for z in range(s):
        mass=sum(q[i][j]*k[i][z] for i in range(n) for j in range(h))
        candidates=[{'choice':'pass','weighted_gain':F(0),'conditional_gain':F(0) if mass else None,'terms':[]}]
        for d in range(n):
            terms=[{'baseline_action':i,'opponent_action':j,'joint_probability':q[i][j],
                    'signal_probability':k[i][z],'joint_signal_mass':q[i][j]*k[i][z],
                    'payoff_difference':payoff[d][j]-payoff[i][j],
                    'contribution':q[i][j]*k[i][z]*(payoff[d][j]-payoff[i][j])}
                   for i in range(n) for j in range(h)]
            gain=sum(t['contribution'] for t in terms)
            candidates.append({'choice':d,'weighted_gain':gain,'conditional_gain':gain/mass if mass else None,'terms':terms})
        best=max(c['weighted_gain'] for c in candidates)
        ties=[c['choice'] for c in candidates if c['weighted_gain']==best]
        records.append({'signal':z,'mass':mass,'candidates':candidates,'best_gain':best,
                        'best_choices':ties,'attaining_choice':ties[0]})
    value=sum(r['best_gain'] for r in records)
    original=_player(payoff,q,'row') # already oriented for this player
    assert original['external_regret']<=value<=original['swap_regret']
    chosen=[next(c for c in r['candidates'] if c['choice']==r['attaining_choice']) for r in records]
    assert sum(c['weighted_gain'] for c in chosen)==value
    return {'player':player,'channel':k,'expected_baseline_payoff':baseline,'signals':records,
            'override_gain':value,'attaining_policy':[r['attaining_choice'] for r in records],
            'optimal_policy_count':prod(len(r['best_choices']) for r in records),
            'attaining_payoff':baseline+value,'coarse_lower_bound':original['external_regret'],
            'full_swap_upper_bound':original['swap_regret']}


def signals(row_payoffs,column_payoffs,joint,row_channel,column_channel):
    """Audit unilateral overrides, with the opponent left at its baseline action."""
    a,b=game(row_payoffs,column_payoffs);q=law(joint,len(a),len(a[0]))
    kr=channel(row_channel,len(a));kc=channel(column_channel,len(a[0]))
    ps=[_signals(a,q,kr,'row'),_signals(b,q,kc,'column')]
    return {'model':'hidden-baseline-private-signal-pass-or-override','shape':[len(a),len(a[0])],
            'row_payoffs':a,'column_payoffs':b,'joint':q,'players':ps,
            'max_unilateral_override_gain':max(p['override_gain'] for p in ps)}


def _compose(k,h):
    return [[sum(k[i][z]*h[z][t] for z in range(len(h))) for t in range(len(h[0]))] for i in range(len(k))]


def garble(row_payoffs,column_payoffs,joint,row_channel,column_channel,row_garbling,column_garbling):
    """Certify a supplied post-garbling; no search for channel dominance."""
    original=signals(row_payoffs,column_payoffs,joint,row_channel,column_channel)
    ks=[p['channel'] for p in original['players']]
    hs=[channel(row_garbling,len(ks[0][0])),channel(column_garbling,len(ks[1][0]))]
    coarse=signals(row_payoffs,column_payoffs,joint,*[_compose(k,h) for k,h in zip(ks,hs)])
    certificates=[]
    for high,low,h in zip(original['players'],coarse['players'],hs):
        lifted=[];liftgain=F(0)
        for z,rec in enumerate(high['signals']):
            weights=[F(0)]*len(rec['candidates'])
            for t,choice in enumerate(low['attaining_policy']):weights[0 if choice=='pass' else choice+1]+=h[z][t]
            terms=[{'choice':c['choice'],'probability':w,'gain_if_chosen':c['weighted_gain'],
                    'contribution':w*c['weighted_gain']} for w,c in zip(weights,rec['candidates'])]
            g=sum(x['contribution'] for x in terms);slack=rec['best_gain']-g
            assert sum(weights)==1 and slack>=0
            lifted.append({'original_signal':z,'choice_distribution':terms,'gain':g,'optimality_slack':slack});liftgain+=g
        assert liftgain==low['override_gain']
        loss=high['override_gain']-low['override_gain']
        assert loss==sum(x['optimality_slack'] for x in lifted)>=0
        certificates.append({'player':high['player'],'garbling':h,'lifted_coarse_policy':lifted,
                             'lifted_gain':liftgain,'information_loss':loss,'monotone':True})
    return {'original':original,'garbled':coarse,'certificates':certificates}


def partitions(n):
    """Canonical restricted-growth labels; Bell(1..4) = 1,2,5,15."""
    if isinstance(n,bool) or not isinstance(n,int) or not 1<=n<=4:raise ValueError('partition size must be 1..4')
    labels=[0]*n
    def walk(i,top):
        if i==n:yield labels[:];return
        for z in range(top+2):
            labels[i]=z;yield from walk(i+1,max(top,z))
    yield from walk(1,0)


def partition_audit(row_payoffs,column_payoffs,joint):
    """All deterministic own-action partitions independently for each player."""
    a,b=game(row_payoffs,column_payoffs);q=law(joint,len(a),len(a[0]));out=[]
    for player,payoff,n in [('row',a,len(a)),('column',b,len(a[0]))]:
        records=[]
        for labels in partitions(n):
            k=[[F(int(labels[i]==z)) for z in range(max(labels)+1)] for i in range(n)]
            result=_signals(payoff,q,k,player)
            records.append({'labels':labels,'audit':result})
        edges=[]
        for i,fine in enumerate(records):
            for j,coarse in enumerate(records):
                f,c=fine['labels'],coarse['labels']
                if i!=j and all(f[u]!=f[v] or c[u]==c[v] for u in range(n) for v in range(n)):
                    loss=fine['audit']['override_gain']-coarse['audit']['override_gain'];assert loss>=0
                    edges.append({'fine_index':i,'coarse_index':j,'information_loss':loss})
        out.append({'player':player,'partitions':records,'strict_refinement_edges':edges})
    return {'shape':[len(a),len(a[0])],'players':out}


def signal_demo():
    a=[[1,-1,0],[-1,1,0],[0,0,'-11/10']];q=[['1/3',0,0],[0,'1/3',0],[0,0,'1/3']]
    identity=[[1,0,0],[0,1,0],[0,0,1]];noise=[['1/2','1/2']]*3
    # C is revealed with probability alpha; A and B always emit the common signal.
    controls=[]
    for alpha in (F(0),F(1,4),F(1,2),F(1)):
        k=[[1,0],[1,0],[1-alpha,alpha]]
        controls.append({'reveal_probability':alpha,'audit':signals(a,a,q,k,k)})
    r={'reveal_controls':controls,'identity_to_noise':garble(a,a,q,identity,identity,noise,noise),
       'partitions':partition_audit(a,a,q),
       'cyclic_partitions':partition_audit([[0,-10,3],[1,0,-10],[-10,2,0]],[[0,0,0]]*3,q)}
    assert [x['audit']['players'][0]['override_gain'] for x in controls]==[F(0),F(11,120),F(11,60),F(11,30)]
    assert r['identity_to_noise']['certificates'][0]['information_loss']==F(11,30)
    return r
