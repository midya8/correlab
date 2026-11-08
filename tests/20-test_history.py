from fractions import Fraction as F
from itertools import product
import copy,unittest
from correlab import audit,demo,history

class HistoryTests(unittest.TestCase):
    def test_all_256_four_round_2x2_histories(self):
        a=[[2,-1],[0,3]];b=[[-2,1],[4,0]]
        for acts in product(tuple(product(range(2),repeat=2)),repeat=4):
            r=history(a,b,acts,[1,2,4])
            for p in r['prefixes']:
                t=p['rounds'];counts=[[sum((i,j)==x for x in acts[:t]) for j in range(2)] for i in range(2)]
                self.assertEqual(p['counts'],counts)
                self.assertEqual(p['audit'],audit(a,b,[[F(v,t) for v in row] for row in counts]))
                for cert,player in zip(p['realized_certificates'],p['audit']['players']):
                    self.assertEqual(cert['external_regret_total'],t*player['external_regret'])
                    self.assertEqual(cert['swap_regret_total'],t*player['swap_regret'])
    def test_aggregate_not_last(self):
        r=demo()['history'];self.assertTrue(r['prefixes'][-1]['audit']['is_cce']);self.assertFalse(r['last_round_audit']['is_cce'])
        self.assertEqual(r['last_round_audit']['ce_swap_epsilon'],F(11,10))
    def test_order_final_invariant_prefix_not(self):
        a=[[2,0],[0,1]];acts=[[0,0],[1,1]];r=history(a,a,acts,[1,2]);s=history(a,a,acts[::-1],[1,2])
        self.assertEqual(r['prefixes'][-1],s['prefixes'][-1]);self.assertNotEqual(r['prefixes'][0],s['prefixes'][0])
    def test_replication(self):
        a=[[1,2],[3,0]];acts=[[0,1],[1,0],[0,0]];r=history(a,a,acts);s=history(a,a,acts*3)
        self.assertEqual(r['prefixes'][-1]['audit'],s['prefixes'][-1]['audit'])
        self.assertEqual(3*r['prefixes'][-1]['realized_certificates'][0]['swap_regret_total'],s['prefixes'][-1]['realized_certificates'][0]['swap_regret_total'])
    def test_checkpoint_defaults_and_no_mutation(self):
        a=[[1]];acts=[[0,0]];before=copy.deepcopy((a,acts));r=history(a,a,acts)
        self.assertEqual(r['checkpoints'],[1]);self.assertEqual((a,acts),before)
    def test_invalid_actions(self):
        for acts in ([],[[0,0]]*1001,[[True,0]],[[0.0,0]],[[-1,0]],[[1,0]],[[0]],'0,0'):
            with self.subTest(actions=str(acts)[:20]),self.assertRaises(ValueError):history([[1]],[[1]],acts)
    def test_invalid_checkpoints(self):
        for points in ([],[0],[True],[2],[1,1],[1]*101,'1'):
            with self.subTest(checkpoints=points),self.assertRaises(ValueError):history([[1]],[[1]],[[0,0]],points)
        with self.assertRaises(ValueError):history([[1]],[[1]],[[0,0]]*2,[1])
    def test_capacity_1000_rounds(self):
        r=history([[1]],[[0]],[[0,0]]*1000)
        self.assertEqual(r['prefixes'][0]['realized_certificates'][0]['actual_total'],1000)
