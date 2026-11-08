import base64,copy,importlib.util,json,unittest,zlib
from pathlib import Path
from xml.etree import ElementTree as ET
from correlab import signal_demo
from correlab.exact import jsonify
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_signals',ROOT/'examples/render_signals.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class SignalFigureTests(unittest.TestCase):
    def test_reproducible_and_full_metadata(self):
        report=signal_demo();text=r.render(report)
        self.assertEqual(text,(ROOT/'assets/private-signals.svg').read_text())
        root=ET.fromstring(text);meta=root.find('{http://www.w3.org/2000/svg}metadata')
        self.assertEqual(json.loads(zlib.decompress(base64.b64decode(meta.text))),jsonify(report))

    def test_every_numeric_cell(self):
        report=jsonify(signal_demo());want=r.values(report);root=ET.fromstring(r.render(report));seen={}
        for node in root.iter():
            if node.attrib.get('id','').startswith('cell-'):
                key=node.attrib['id'][5:];self.assertNotIn(key,seen)
                self.assertEqual(node.text,str(want[key]));self.assertEqual(node.attrib['data-value'],str(want[key]));seen[key]=1
        self.assertEqual(set(seen),set(want));self.assertEqual(len(seen),25)

    def test_hidden_lift_term_changes_metadata(self):
        report=signal_demo();bad=copy.deepcopy(report)
        bad['identity_to_noise']['certificates'][0]['lifted_coarse_policy'][0]['choice_distribution'][0]['probability']+=1
        self.assertEqual(r.values(jsonify(report)),r.values(jsonify(bad)))
        self.assertNotEqual(r.render(report),r.render(bad))
