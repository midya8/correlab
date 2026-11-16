from fractions import Fraction as F
from itertools import product
import copy
import inspect
import json
import random
import unittest
from unittest.mock import patch
from correlab import audit, demo
from correlab.exact import jsonify
from correlab import verify_audit
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def test_demo_native_and_json_without_production_engine(self):
        reports = [v for v in demo().values() if isinstance(v, dict) and 'row_payoffs' in v]
        self.assertEqual(len(reports), 4)
        with patch('correlab.core._player', side_effect=AssertionError('production called')), patch('correlab.core._audit', side_effect=AssertionError('production called')):
            for report in reports:
                self.assertTrue(verify_audit(report)['valid'])
                self.assertTrue(verify_audit(json.loads(json.dumps(jsonify(report))))['valid'])
        import correlab.verify
        source = inspect.getsource(correlab.verify)
        self.assertNotIn('from .core', source)
        self.assertNotIn('import core', source)

    def test_2835_exact_game_law_reports(self):
        laws = []
        for a in range(5):
            for b in range(5-a):
                for c in range(5-a-b):
                    laws.append([[F(a,4),F(b,4)],[F(c,4),F(4-a-b-c,4)]])
        checked = 0
        for values in product((-1,0,1),repeat=4):
            a = [list(values[:2]),list(values[2:])]
            b = [[values[2],-values[0]],[-values[3],values[1]]]
            for q in laws:
                result = verify_audit(audit(a,b,q))
                self.assertTrue(result['valid'],result)
                checked += 1
        self.assertEqual(checked,2835)

    def test_rectangular_four_actions_and_zero_mass_ties(self):
        for m,n in ((1,1),(1,4),(4,1),(2,3),(3,2),(3,4),(4,3),(4,4)):
            for seed in range(4):
                a = [[F((7*i+5*j+seed)%9-4,3) for j in range(n)] for i in range(m)]
                b = [[F((3*i+2*j+seed)%7-3,2) for j in range(n)] for i in range(m)]
                weights = [[(i*3+j+seed)%5 for j in range(n)] for i in range(m)]
                if not sum(map(sum,weights)):weights[0][0]=1
                total = sum(map(sum,weights))
                q = [[F(v,total) for v in row] for row in weights]
                self.assertTrue(verify_audit(audit(a,b,q))['valid'])
        r = audit([[0]*4]*4,[[0]*4]*4,[[1,0,0,0]]+[[0]*4]*3)
        self.assertEqual(r['players'][0]['optimal_swap_count'],256)
        self.assertTrue(verify_audit(r)['valid'])

    def test_every_leaf_tamper_in_complete_report_is_rejected(self):
        report = jsonify(audit([[2,-1],[0,3]],[[-2,1],[4,0]],[['1/2','1/4'],[0,'1/4']]))
        def leaves(value,path=()):
            if isinstance(value,dict):
                for k,v in value.items():yield from leaves(v,path+(k,))
            elif isinstance(value,list):
                for k,v in enumerate(value):yield from leaves(v,path+(k,))
            else:yield path,value
        count = 0
        for path,value in leaves(report):
            # The embedded problem is supplied evidence, not a signed original.
            # Tamper every leaf including those inputs; inconsistent copies fail.
            bad = copy.deepcopy(report);parent=bad
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]] = not value if type(value)is bool else value+1 if type(value)is int else 'tampered'
            self.assertFalse(verify_audit(bad)['valid'],path);count+=1
        self.assertGreater(count,350)

    def test_shapes_keys_types_truncation_and_invalid_embedded_inputs(self):
        report=jsonify(audit([[0,1],[2,-1]],[[1,2],[0,3]],[[1,0],[0,0]]))
        for value in (None,[],{},dict(report,joint=[[0,0],[0,0]]),dict(report,row_payoffs=[[True]]),dict(report,column_payoffs=[[0]])):
            self.assertFalse(verify_audit(value)['valid'])
        for key in report:
            bad=copy.deepcopy(report);del bad[key];self.assertFalse(verify_audit(bad)['valid'],key)
        bad=copy.deepcopy(report);bad['players'][0]['hidden']=0;self.assertFalse(verify_audit(bad)['valid'])
        for replacement in (True,1.0,'1'):
            bad=copy.deepcopy(report);bad['shape'][0]=replacement;self.assertFalse(verify_audit(bad)['valid'])
        bad=copy.deepcopy(report);bad['players'][0]['internal_deviations'][0][0]['terms']=[];self.assertFalse(verify_audit(bad)['valid'])
        bad=copy.deepcopy(report);bad['product_control']['is_ce']=not bad['product_control']['is_ce'];self.assertFalse(verify_audit(bad)['valid'])

    def test_input_output_rng_isolation_and_bounded_diagnostics(self):
        report=audit([[1,-1],[-1,1]],[[0,1],[2,0]],[['1/2',0],[0,'1/2']]);before=copy.deepcopy(report);state=random.getstate()
        result=verify_audit(report);self.assertEqual(report,before);self.assertEqual(random.getstate(),state)
        result['mismatches'].append('changed');self.assertTrue(verify_audit(report)['valid'])
        bad=jsonify(report)
        for p in bad['players']:
            for row in p['internal_deviations']:
                for cell in row:
                    cell['weighted_gain']='999';cell['conditional_gain']='999'
                    for term in cell['terms']:term['contribution']='999'
        first=verify_audit(bad);second=verify_audit(bad)
        self.assertEqual(first,second);self.assertFalse(first['valid']);self.assertLessEqual(len(first['mismatches']),20)

    def test_verify_cli_valid_invalid_and_unreadable(self):
        r=audit([[2,-1],[0,3]],[[-2,1],[4,0]],[['1/2','1/4'],[0,'1/4']])
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/'report.json';f.write_text(json.dumps(jsonify(r)))
            def run():return subprocess.run([sys.executable,'-m','correlab','verify',str(f)],cwd=ROOT,capture_output=True)
            p=run();self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),verify_audit(r));self.assertEqual(p.stderr,b'')
            bad=jsonify(r);bad['players'][0]['swap_regret']='999';f.write_text(json.dumps(bad));p=run()
            self.assertEqual(p.returncode,1);self.assertFalse(json.loads(p.stdout)['valid']);self.assertEqual(p.stderr,b'')
            f.write_text('{}');p=run();self.assertEqual(p.returncode,1);self.assertFalse(json.loads(p.stdout)['valid'])
            for raw in (b'{"x":1,"x":2}',b'NaN',b'\xff',b'['*2000+b']'*2000,b' '*2000001):
                f.write_bytes(raw);p=run();self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'');self.assertNotIn(b'Traceback',p.stderr)
            f.unlink();p=run();self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')
