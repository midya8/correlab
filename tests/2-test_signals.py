"""Independent enumeration of every signal-to-choice policy, not the optimizer."""
import itertools,json,subprocess,sys,tempfile,unittest
from fractions import Fraction as F
from pathlib import Path
from correlab import signals,garble,partition_audit,signal_demo,audit
from correlab.signals import partitions


def reference(a,q,k):
    n,h,s=len(q),len(q[0]),len(k[0]);scores=[]
    for policy in itertools.product(range(-1,n),repeat=s):
        gain=sum(q[i][j]*k[i][z]*(0 if d==-1 else a[d][j]-a[i][j])
                 for z,d in enumerate(policy) for i in range(n) for j in range(h))
        scores.append((gain,['pass' if d==-1 else d for d in policy]))
    best=max(g for g,_ in scores)
    policies=[p for g,p in scores if g==best]
    return best,policies


def eye(n):return [[F(int(i==j)) for j in range(n)] for i in range(n)]


class SignalTests(unittest.TestCase):
    def check(self,a,b,q,kr,kc):
        r=signals(a,b,q,kr,kc)
        for p,aa,qq,k in zip(r['players'],(a,list(map(list,zip(*b)))),(q,list(map(list,zip(*q)))),(kr,kc)):
            best,policies=reference(aa,qq,k)
            self.assertEqual(p['override_gain'],best);self.assertEqual(p['attaining_policy'],policies[0])
            self.assertEqual(p['optimal_policy_count'],len(policies))
            self.assertEqual(sum(x['mass'] for x in p['signals']),1)
            self.assertEqual(p['attaining_payoff'],p['expected_baseline_payoff']+best)
            for rec in p['signals']:
                for c in rec['candidates']:
                    self.assertEqual(sum(t['contribution'] for t in c['terms']),c['weighted_gain'])
                    self.assertEqual(c['conditional_gain'],c['weighted_gain']/rec['mass'] if rec['mass'] else None)
        return r

    def test_all_2835_small_laws_with_three_channels(self):
        ks=[eye(2),[[F(1)],[F(1)]],[[F(3,4),F(1,4)],[F(1,4),F(3,4)]]]
        count=0
        for flat in itertools.product((-1,0,1),repeat=4):
            a=[list(flat[:2]),list(flat[2:])];b=[[-v for v in a[1]],a[0][:]]
            for v in itertools.product(range(5),repeat=3):
                if sum(v)>4:continue
                ps=[F(x,4) for x in (*v,4-sum(v))];q=[ps[:2],ps[2:]]
                for k in ks:self.check(a,b,q,k,k)
                full=audit(a,b,q)
                for i,p in enumerate(full['players']):
                    self.assertEqual(signals(a,b,q,ks[0],ks[0])['players'][i]['override_gain'],p['swap_regret'])
                    self.assertEqual(signals(a,b,q,ks[1],ks[1])['players'][i]['override_gain'],p['external_regret'])
                count+=1
        self.assertEqual(count,2835)

    def test_rectangular_four_signal_policy_enumeration(self):
        count=0
        for m,n in ((1,4),(4,1),(2,3),(3,2),(3,4),(4,3),(4,4)):
            for offset in range(4):
                a=[[F((3*i+2*j+offset)%7-3) for j in range(n)] for i in range(m)]
                b=[[F((i+4*j+offset)%5-2) for j in range(n)] for i in range(m)]
                weights=[[1+(i+j+offset)%3 for j in range(n)] for i in range(m)];total=sum(map(sum,weights))
                q=[[F(v,total) for v in r] for r in weights]
                kr=[[F((i+z+offset)%4,6) for z in range(4)] for i in range(m)]
                kc=[[F((i+z+offset)%4,6) for z in range(4)] for i in range(n)]
                self.check(a,b,q,kr,kc);count+=1
        self.assertEqual(count,28)

    def test_243_post_garbling_certificates(self):
        choices=[F(0),F(1,2),F(1)];count=0
        a=[[2,-1],[0,1]];b=[[-2,3],[1,0]];q=[[F(1,8),F(3,8)],[F(1,4),F(1,4)]]
        for x,y,u,v in itertools.product(choices,repeat=4):
            k=[[x,1-x],[y,1-y]];h=[[u,1-u],[v,1-v]]
            for w in choices:
                kc=[[w,1-w],[1-w,w]]
                r=garble(a,b,q,k,kc,h,h)
                for hi,lo,c in zip(r['original']['players'],r['garbled']['players'],r['certificates']):
                    self.assertGreaterEqual(c['information_loss'],0)
                    self.assertEqual(c['lifted_gain'],lo['override_gain'])
                    self.assertEqual(sum(z['optimality_slack'] for z in c['lifted_coarse_policy']),c['information_loss'])
                    for z in c['lifted_coarse_policy']:
                        self.assertEqual(sum(t['probability'] for t in z['choice_distribution']),1)
                        self.assertEqual(sum(t['contribution'] for t in z['choice_distribution']),z['gain'])
                count+=1
        self.assertEqual(count,243) # 3**4 channels/garblings times three column channels

    def test_composition_associativity_and_identity(self):
        from correlab.signals import _compose
        k=[[F(1,4),F(3,4)],[F(2,3),F(1,3)]];h=[[F(1,3),F(1,3),F(1,3)],[F(1,2),0,F(1,2)]]
        g=[[1,0],[0,1],[F(1,2),F(1,2)]]
        self.assertEqual(_compose(_compose(k,h),g),_compose(k,_compose(h,g)))
        self.assertEqual(_compose(k,eye(2)),k)

    def test_partition_bell_counts_and_refinement(self):
        for n,count in zip(range(1,5),(1,2,5,15)):
            labels=list(partitions(n));self.assertEqual(len(labels),count)
            self.assertEqual(len({tuple(x) for x in labels}),count)
            for x in labels:
                self.assertEqual(x[0],0)
                for i in range(1,n):self.assertLessEqual(x[i],max(x[:i])+1)
            a=[[F(i-j) for j in range(n)] for i in range(n)];q=[[F(1,n*n)]*n for _ in range(n)]
            r=partition_audit(a,a,q)
            for p in r['players']:
                self.assertEqual(len(p['partitions']),count)
                for edge in p['strict_refinement_edges']:
                    self.assertGreaterEqual(edge['information_loss'],0)
                    fine=p['partitions'][edge['fine_index']];coarse=p['partitions'][edge['coarse_index']]
                    self.assertEqual(edge['information_loss'],fine['audit']['override_gain']-coarse['audit']['override_gain'])

    def test_demo_all_five_three_action_partitions(self):
        r=signal_demo()
        self.assertEqual([x['audit']['players'][0]['override_gain'] for x in r['reveal_controls']],[F(0),F(11,120),F(11,60),F(11,30)])
        p=r['partitions']['players'][0]
        self.assertEqual([(x['labels'],x['audit']['override_gain']) for x in p['partitions']],
                         [([0,0,0],F(0)),([0,0,1],F(11,30)),([0,1,0],F(11,30)),([0,1,1],F(11,30)),([0,1,2],F(11,30))])

    def test_partition_value_depends_on_which_actions_are_pooled(self):
        p=signal_demo()['cyclic_partitions']['players'][0]
        self.assertEqual([x['audit']['override_gain'] for x in p['partitions']],
                         [F(0),F(4,3),F(5,3),F(1),F(2)])

    def test_unreachable_signals_ties_and_pass(self):
        r=self.check([[1,1],[1,1]],[[0,0],[0,0]],[[F(1),0],[0,0]],[[F(1),0,0,0]]*2,[[F(1),0,0,0]]*2)
        for p in r['players']:
            self.assertEqual(p['optimal_policy_count'],3**4);self.assertEqual(p['attaining_policy'],['pass']*4)
            self.assertIsNone(p['signals'][1]['candidates'][1]['conditional_gain'])
        # Negative fixed gains still permit pass; two-player baseline remains unchanged.
        d=signal_demo()['identity_to_noise']['garbled']['players'][0]
        self.assertEqual(d['override_gain'],0);self.assertEqual(d['attaining_policy'],['pass','pass'])
        self.assertTrue(all(c['weighted_gain']<0 for c in d['signals'][0]['candidates'][1:]))

    def test_noise_independence_and_split_signals(self):
        a=[[1,0],[0,2]];q=[[F(1,4)]*2]*2;k=[[F(1)]]*2
        r=signals(a,a,q,k,k);s=signals(a,a,q,[[F(1,3),F(2,3)]]*2,[[F(1,3),F(2,3)]]*2)
        for p,t in zip(r['players'],s['players']):self.assertEqual(p['override_gain'],t['override_gain'])

    def test_positive_scaling_shifts_and_player_exchange(self):
        a=[[2,-1],[0,1]];b=[[-2,3],[1,0]];q=[[F(1,8),F(3,8)],[F(1,4),F(1,4)]];k=eye(2)
        r=signals(a,b,q,k,k);t=signals([[3*v+11 for v in x] for x in a],[[3*v-7 for v in x] for x in b],q,k,k)
        swapped=signals(list(map(list,zip(*b))),list(map(list,zip(*a))),list(map(list,zip(*q))),k,k)
        for i in range(2):
            self.assertEqual(t['players'][i]['override_gain'],3*r['players'][i]['override_gain'])
            self.assertEqual(swapped['players'][1-i]['override_gain'],r['players'][i]['override_gain'])

    def test_inputs_no_mutation(self):
        import copy
        a=[[1,0],[0,1]];q=[['1/2',0],[0,'1/2']];k=[[1,0],[0,1]];args=[a,a,q,k,k];before=copy.deepcopy(args)
        signals(*args);garble(*args,k,k);partition_audit(a,a,q)
        self.assertEqual(args,before)

    def test_invalid_channels_and_garblings(self):
        a=[[0,0],[0,0]];q=[[1,0],[0,0]];k=eye(2)
        for invalid in ([],[[1]],[[1,0],[0,0]],[[2,-1],[1,0]],[[0.5,0.5],[1,0]],[[True,0],[1,0]],[[1,0],[1]],[[1]*5]*2):
            with self.assertRaises(ValueError):signals(a,a,q,invalid,k)
            with self.assertRaises(ValueError):garble(a,a,q,k,k,invalid,k)
        for n in (True,0,5,'2'):
            with self.assertRaises(ValueError):list(partitions(n))

    def test_cli_new_modes_and_strict_keys(self):
        from correlab.exact import jsonify
        root=Path(__file__).resolve().parents[1]
        for mode,fn in [('signals',signals),('garble',garble),('partitions',partition_audit)]:
            inp=json.loads((root/f'examples/{mode}-input.json').read_text())
            p=subprocess.run([sys.executable,'-m','correlab',mode,str(root/f'examples/{mode}-input.json')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),jsonify(fn(**inp)))
        p=subprocess.run([sys.executable,'-m','correlab','signal-demo'],capture_output=True,text=True)
        self.assertEqual(json.loads(p.stdout),jsonify(signal_demo()))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'x.json'
            for text in ('{"row_payoffs":[],"row_payoffs":[]}','{"x":NaN}','{"x":1}'):
                path.write_text(text)
                for mode in ('signals','garble','partitions'):
                    p=subprocess.run([sys.executable,'-m','correlab',mode,str(path)],capture_output=True,text=True)
                    self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'')
