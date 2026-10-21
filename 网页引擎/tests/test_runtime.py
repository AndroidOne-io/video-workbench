"""Version pinning, safe upgrades, independent projects and export authorization."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runtime',ROOT/'sync_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def create(self,name):
        dest=self.root/name
        subprocess.run([sys.executable,str(ROOT/'init_project.py'),str(dest)],check=True,capture_output=True)
        return dest
    def test_new_projects_are_independent_and_share_runtime(self):
        a,b=self.create('one'),self.create('two')
        self.assertNotEqual(json.loads((a/'project.json').read_text())['id'],json.loads((b/'project.json').read_text())['id'])
        self.assertEqual(runtime.install(a,check=True)['version'],'1.0.0')
        for name in runtime.FILES:self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
        before=(a/'project.json').read_bytes()
        subprocess.run([sys.executable,str(a/'build.py')],check=True,capture_output=True)
        self.assertEqual(before,(a/'project.json').read_bytes())
        result=subprocess.run([sys.executable,str(ROOT/'init_project.py'),str(a)],capture_output=True)
        self.assertNotEqual(result.returncode,0)
    def test_local_edits_block_upgrade_before_any_file_changes(self):
        a=self.create('one');(a/'player.js').write_text('// local change')
        hashes={n:(a/n).read_bytes() for n in runtime.FILES}
        with self.assertRaises(ValueError):runtime.install(a)
        self.assertEqual(hashes,{n:(a/n).read_bytes() for n in runtime.FILES})
        runtime.install(a,adopt=True)
        runtime.install(a,check=True)
    def test_scene_list_and_caption_contract(self):
        a=self.create('one');p=json.loads((a/'project.json').read_text())
        (a/'second.js').write_text('// another project scene')
        p['sceneScripts']=['scenes.js','second.js'];(a/'project.json').write_text(json.dumps(p))
        subprocess.run([sys.executable,str(a/'build.py')],check=True,capture_output=True)
        self.assertIn('src="second.js"',(a/'index.html').read_text())
        p['sceneScripts']=['../outside.js'];(a/'project.json').write_text(json.dumps(p))
        self.assertNotEqual(subprocess.run([sys.executable,str(a/'build.py')],capture_output=True).returncode,0)
    def test_export_needs_authorization_before_dependencies_or_output(self):
        out=self.root/'not-created.mp4'
        result=subprocess.run([sys.executable,str(ROOT/'export_mp4.py'),'--url','http://127.0.0.1:1','--out',str(out)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('--authorized-export',result.stderr)
        self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
