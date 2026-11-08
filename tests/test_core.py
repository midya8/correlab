from fractions import Fraction as F
from itertools import product
import copy,random,unittest
from correlab import audit,demo,history
from correlab.exact import rational


def reference(a,b,q):
    m,n=len(a),len(a[0]);out=[]
    for k,u in enumerate((a,b)):
        d=(m,n)[k];baseline=sum(q[i][j]*u[i][j] for i in range(m) for j in range(n))
        maps=list(product(range(d),repeat=d));scores=[]
        for f in maps:
            scores.append(sum(q[i][j]*(u[f[i]][j] if k==0 else u[i][f[j]]) for i in range(m) for j in range(n))-baseline)
        coarse=[scores[maps.index((z,)*d)] for z in range(d)]
        pair=[]
        for rec in range(d):
            for dest in range(d):
                f=list(range(d));f[rec]=dest;pair.append(scores[maps.index(tuple(f))])
        out.append({'swap':max(scores),'map':list(maps[scores.index(max(scores))]),'count':scores.count(max(scores)),
                    'external':max(F(0),*coarse),'pair':max(pair),'raw':max(coarse)})
    return out


class CoreTests(unittest.TestCase):
    def check_reference(self,a,b,q):
        r=audit(a,b,q)
        for p,e in zip(r['players'],reference(a,b,q)):
            self.assertEqual(p['swap_regret'],e['swap']);self.assertEqual(p['attaining_swap'],e['map'])
            self.assertEqual(p['optimal_swap_count'],e['count']);self.assertEqual(p['external_regret'],e['external'])
            self.assertEqual(p['pairwise_internal_regret'],e['pair']);self.assertEqual(p['coarse_max_raw_gain'],e['raw'])
            self.assertEqual(sum(c['contribution'] for c in p['attaining_swap_cells']),p['swap_regret'])
            for row in p['internal_deviations']:
                for c in row:
                    self.assertEqual(sum(x['contribution'] for x in c['terms']),c['weighted_gain'])
                    self.assertEqual(c['conditional_gain'],c['weighted_gain']/c['mass'] if c['mass'] else None)
        return r
    def test_2835_games_laws_all_maps(self):
        qs=[]
        for aa in range(5):
            for bb in range(5-aa):
                for cc in range(5-aa-bb):
                    qs.append([[F(aa,4),F(bb,4)],[F(cc,4),F(4-aa-bb-cc,4)]])
        self.assertEqual(len(qs),35)
        count=0
        for v in product((-1,0,1),repeat=4):
            a=[list(v[:2]),list(v[2:])];b=[[v[2],-v[0]],[-v[3],v[1]]]
            for q in qs:self.check_reference(a,b,q);count+=1
        self.assertEqual(count,2835)
    def test_rectangular_and_256_swap_maps(self):
        for m,n in ((1,4),(4,1),(2,3),(3,2),(3,4),(4,3),(4,4)):
            for seed in range(4):
                a=[[F((7*i+5*j+seed)%9-4,3) for j in range(n)] for i in range(m)]
                b=[[F((3*i+2*j+seed)%7-3,2) for j in range(n)] for i in range(m)]
                w=[[1+(i*3+j+seed)%5 for j in range(n)] for i in range(m)];s=sum(map(sum,w));q=[[F(v,s) for v in row] for row in w]
                self.check_reference(a,b,q)
    def test_cce_not_ce(self):
        r=demo()['cce_not_ce'];self.assertTrue(r['is_cce']);self.assertFalse(r['is_ce'])
        self.assertEqual(r['ce_swap_epsilon'],F(11,30));self.assertEqual(r['ce_conditional_epsilon'],F(11,10))
        self.assertEqual(r['players'][0]['attaining_swap'],[0,1,0])
    def test_negative_coarse_is_not_negative_regret(self):
        p=demo()['cce_not_ce']['players'][0]
        self.assertEqual(p['coarse_max_raw_gain'],-F(3,10));self.assertEqual(p['external_regret'],0)
    def test_product_loses_coordination(self):
        r=demo()['coordination'];self.assertTrue(r['is_ce']);self.assertFalse(r['is_nash_product'])
        p=r['product_control'];self.assertFalse(p['is_ce']);self.assertEqual(p['cce_epsilon'],F(1,4))
        self.assertEqual(r['players'][0]['expected_payoff'],F(3,2));self.assertEqual(p['players'][0]['expected_payoff'],F(3,4))
        self.assertEqual(r['total_variation_from_product'],F(1,2))
    def test_rare_recommendation(self):
        r=demo()['rare_recommendation'];self.assertEqual(r['ce_pairwise_epsilon'],F(1,1000));self.assertEqual(r['ce_conditional_epsilon'],1)
    def test_swap_is_sum_not_pair_max(self):
        r=demo()['aggregate_swap'];self.assertEqual(r['ce_pairwise_epsilon'],F(1,3));self.assertEqual(r['ce_swap_epsilon'],F(2,3))
        self.assertEqual(r['players'][0]['attaining_swap'],[2,2,2])
    def test_zero_recommendations(self):
        r=audit([[1,0],[0,1]],[[0,0],[0,0]],[[1,0],[0,0]])
        for c in r['players'][0]['internal_deviations'][1]:self.assertIsNone(c['conditional_gain']);self.assertEqual(c['weighted_gain'],0)
    def test_tie_count_256(self):
        p=audit([[0]]*4,[[0]]*4,[[1],[0],[0],[0]])['players'][0]
        self.assertEqual(p['optimal_swap_count'],256);self.assertEqual(p['attaining_swap'],[0]*4)
    def test_singleton(self):
        r=audit([[7]],[[-9]],[[1]])
        self.assertTrue(r['is_nash_product']);self.assertEqual(r['ce_conditional_epsilon'],0)
    def test_product_nash(self):
        a=[[1,-1],[-1,1]];r=audit(a,[[-v for v in row] for row in a],[['1/4']*2]*2)
        self.assertTrue(r['is_product']);self.assertTrue(r['is_nash_product'])
    def test_player_specific_positive_affine(self):
        d=demo()['cce_not_ce'];a=d['row_payoffs'];b=d['column_payoffs'];q=d['joint']
        r=audit([[3*v+8 for v in row] for row in a],[[2*v-7 for v in row] for row in b],q)
        for k,factor in enumerate((3,2)):
            for key in ('external_regret','pairwise_internal_regret','swap_regret','worst_conditional_gain'):
                self.assertEqual(r['players'][k][key],factor*d['players'][k][key])
    def test_player_transpose(self):
        a=[[2,-1,4],[0,3,1]];b=[[0,5,-2],[3,1,4]];q=[['1/6']*3]*2
        r=audit(a,b,q);s=audit(list(zip(*b)),list(zip(*a)),list(zip(*q)))
        for k in range(2):
            for key in ('expected_payoff','external_regret','swap_regret','pairwise_internal_regret'):
                self.assertEqual(r['players'][k][key],s['players'][1-k][key])
    def test_no_mutation_rng(self):
        a=[[2,0],[0,1]];b=copy.deepcopy(a);q=[['1/2',0],[0,'1/2']];before=copy.deepcopy((a,b,q));state=random.getstate()
        audit(a,b,q);self.assertEqual((a,b,q),before);self.assertEqual(random.getstate(),state)
    def test_bad_payoffs_and_laws(self):
        bad=[([],[[1]],[[1]]),([[1,2],[3]],[[1]],[[1]]),([[1]]*5,[[1]]*5,[[1]]*5),([[1]],[[1,2]],[[1]]),([[1]],[[1]],[[0]]),([[1]],[[1]],[[-1]]),([[1]],[[1]],[[True]]),([[1.0]],[[1]],[[1]]),([[1]],[[1]],[[1,0]])]
        for args in bad:
            with self.subTest(args=args),self.assertRaises(ValueError):audit(*args)
    def test_exact_syntax_caps(self):
        for v in (True,0.1,'nan','1e3','1/0','+1','1_000','1/'+'9'*160,1<<513):
            with self.subTest(value=str(v)[:20]),self.assertRaises(ValueError):rational(v)
        self.assertEqual(rational('0.125'),F(1,8));self.assertEqual(rational('-3/7'),-F(3,7))
