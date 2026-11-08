import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from correlab import audit,demo,history
from correlab.exact import jsonify
ROOT=Path(__file__).resolve().parents[1]
class CliTests(unittest.TestCase):
    def run_cli(self,*args):return subprocess.run([sys.executable,'-m','correlab',*args],text=True,capture_output=True,cwd=ROOT)
    def test_full_demo_fixture(self):
        r=self.run_cli('demo');self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout,(ROOT/'examples/demo.json').read_text());self.assertEqual(json.loads(r.stdout),jsonify(demo()))
    def test_audit_full(self):
        path=ROOT/'examples/audit-input.json';r=self.run_cli('audit',str(path));self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),jsonify(audit(**json.loads(path.read_text()))))
    def test_history_full(self):
        path=ROOT/'examples/history-input.json';r=self.run_cli('history',str(path));self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),jsonify(history(**json.loads(path.read_text()))))
    def test_bad_json_schema(self):
        for text in ('[]','{}','{"row_payoffs":[],"row_payoffs":[]}','NaN','{"row_payoffs":[[1]],"column_payoffs":[[1]],"joint":[[1.0]]}','{"row_payoffs":[[1]],"column_payoffs":[[1]],"joint":[[1]],"extra":0}'):
            with self.subTest(text=text),tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
                f.write(text);f.flush();r=self.run_cli('audit',f.name);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'')
    def test_oversize_and_missing_file(self):
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(' '*2_000_001);f.flush();self.assertEqual(self.run_cli('audit',f.name).returncode,2)
        self.assertEqual(self.run_cli('audit','/nonexistent/correlab-fixture.json').returncode,2)
    def test_bad_command(self):self.assertEqual(self.run_cli('unknown').returncode,2)
