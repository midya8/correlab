import base64,copy,importlib.util,json,unittest,zlib
from pathlib import Path
from fractions import Fraction as F
import xml.etree.ElementTree as ET
from correlab import demo
from correlab.exact import jsonify
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_demo',ROOT/'examples/render_demo.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
NS={'s':'http://www.w3.org/2000/svg'}
class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=demo();cls.text=module.render(cls.r);cls.root=ET.fromstring(cls.text)
    def test_all_36_numeric_cells(self):
        expected={'coarse-payoff':'3/10','coarse-fixed':'0','coarse-raw':'-3/10','coarse-epsilon':'0','coarse-pair':'11/30','coarse-swap':'11/30','coarse-conditional':'11/10',
                  'joint-payoff':'3/2','product-payoff':'3/4','joint-epsilon':'0','product-epsilon':'1/4','rare-mass':'1/1000','rare-weighted':'1/1000','rare-conditional':'1','aggregate-pair':'1/3','aggregate-swap':'2/3','last-epsilon':'11/10'}
        for i in range(2):
            for j in range(2):expected[f'joint-{i}-{j}']='1/2' if i==j else '0';expected[f'product-{i}-{j}']='1/4'
        for i in range(3):expected[f'map-{i}']='2'
        for i,(t,e) in enumerate(((1,'11/10'),(2,'11/20'),(3,'0'),(6,'0'))):expected[f'prefix-{i}-rounds']=str(t);expected[f'prefix-{i}-epsilon']=e
        self.assertEqual(len(expected),36);self.assertEqual(len(self.root.findall('s:text[@data-value]',NS)),36)
        for key,v in expected.items():
            c=self.root.find(f"s:text[@id='cell-{key}']",NS);self.assertEqual(c.text,v);self.assertEqual(c.attrib['data-value'],v)
            self.assertTrue(20<float(c.attrib['x'])<1070);self.assertTrue(20<float(c.attrib['y'])<1240)
    def test_metadata_and_hidden_tamper(self):
        blob=self.root.find("s:metadata[@id='report-zlib-base64']",NS).text;self.assertEqual(json.loads(zlib.decompress(base64.b64decode(blob))),jsonify(self.r))
        x=copy.deepcopy(self.r);x['cce_not_ce']['players'][0]['internal_deviations'][0][0]['terms'][0]['contribution']=F(99,7)
        self.assertNotEqual(module.render(x),self.text)
    def test_exact_regeneration(self):self.assertEqual((ROOT/'assets/obedience-audit.svg').read_text(),self.text)
