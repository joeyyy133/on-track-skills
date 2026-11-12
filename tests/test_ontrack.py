"""Synthetic isolated fixtures, not evidence for any business application."""
import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/on-track-dev/scripts/ontrack.py'
spec = importlib.util.spec_from_file_location('ontrack', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Gates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ontrack-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.f = self.root / '.ontrack'
        m.init(self.root)
    def load(self, name):
        return json.loads((self.f / name).read_text())
    def save(self, name, value):
        m.write(self.f / name, value)
    def baseline(self):
        s = self.load('state.json')
        s['requirements']['approval'] = {'actor':'user','reference':'synthetic test confirmation'}
        s['acceptance'] = [{'id':'R1','criterion':'fixture behavior','required':True}]
        s['tasks'] = [{'id':'T1','requirements':['R1'],'status':'done','files':['app.py']}]
        s['current_task'] = None
        self.save('state.json', s)
        return s
    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.PIPE).decode().strip()
    def ready(self):
        s = self.baseline()
        self.git('init')
        self.git('config','user.email','fixture@example.invalid')
        self.git('config','user.name','Fixture')
        (self.root / 'app.py').write_text('print("fixture")\n')
        self.git('add','.')
        self.git('commit','-m','synthetic baseline')
        head = self.git('rev-parse','HEAD')
        actual = subprocess.check_output(['python3',str(self.root/'app.py')]).decode().strip()
        e = [{'id':'E1','requirements_revision':s['requirements']['revision'],
              'requirements_sha256':s['requirements']['sha256'],'requirement_ids':['R1'],
              'source_sha256':m.source_digest(self.root),'commit':head,'command':'python3 app.py','result':'passed','output':actual,
              'limitations':'Only tests this synthetic gate fixture.'}]
        self.save('evidence.json',e)
        return s, e, head
    def test_init_cannot_pass_or_overwrite(self):
        self.assertTrue(m.check(self.root))
        before=(self.f/'state.json').read_bytes()
        with self.assertRaises(FileExistsError): m.init(self.root)
        self.assertEqual(before,(self.f/'state.json').read_bytes())
    def test_normal_pending_is_allowed(self):
        s=self.baseline(); s['tasks'][0]['status']='pending';self.save('state.json',s)
        self.assertEqual([],m.check(self.root))
        self.assertTrue(m.check(self.root,complete=True))
    def test_changed_requirement_is_rejected(self):
        self.baseline();(self.f/'requirements.md').write_text('changed requirement')
        self.assertTrue(any('需求内容变化' in x for x in m.check(self.root)))
    def test_bad_mapping_is_rejected(self):
        s=self.baseline();s['tasks'][0]['requirements']=['R99'];self.save('state.json',s)
        self.assertTrue(m.check(self.root))
    def test_complete_requires_real_current_git_and_evidence(self):
        self.ready();self.assertEqual([],m.check(self.root,complete=True))
    def test_dirty_source_is_rejected(self):
        self.ready();(self.root/'app.py').write_text('print("changed")\n')
        self.assertTrue(any('工作区不干净' in x for x in m.check(self.root,release=True)))
    def test_old_commit_is_rejected(self):
        self.ready();(self.root/'app.py').write_text('print("new")\n')
        self.git('add','app.py');self.git('commit','-m','new')
        self.assertTrue(any('通过证据' in x for x in m.check(self.root,release=True)))
    def test_complete_without_git(self):
        s=self.baseline()
        self.save('evidence.json',[{'id':'E1','requirements_revision':'REQ-001',
          'requirements_sha256':s['requirements']['sha256'], 'source_sha256':m.source_digest(self.root),
          'requirement_ids':['R1'],'commit':None,'command':'synthetic check','result':'passed',
          'output':'synthetic fixture only','limitations':'synthetic fixture only'}])
        self.assertEqual([],m.check(self.root,complete=True))
        self.assertTrue(m.check(self.root,release=True))
    def test_changed_source_rejects_workspace_evidence(self):
        self.ready();(self.root/'app.py').write_text('print("other")')
        self.assertTrue(any('通过证据' in x for x in m.check(self.root,complete=True)))
    def test_old_revision_is_rejected(self):
        s,e,h=self.ready();s['requirements']['revision']='REQ-002';self.save('state.json',s)
        self.assertTrue(any('通过证据' in x for x in m.check(self.root,release=True)))
    def test_unrun_or_empty_output_is_rejected(self):
        s,e,h=self.ready()
        for key,value in [('result','not_run'),('output','')]:
            changed=copy.deepcopy(e);changed[0][key]=value;self.save('evidence.json',changed)
            self.assertTrue(any('通过证据' in x for x in m.check(self.root,release=True)))
    def test_final_requires_confirmation_and_actual_tag(self):
        s,e,h=self.ready()
        self.assertTrue(m.check(self.root,final=True))
        r={'milestones':[{'version':'V1.0.0','commit':h,'tag':'V1.0.0','artifacts':[]}],
           'final':{'version':'V1.0.0','commit':h,'approval':{'actor':'user','reference':'synthetic final confirmation'}}}
        self.save('releases.json',r)
        self.assertTrue(any('标签不存在' in x for x in m.check(self.root,final=True)))
        self.git('tag','V1.0.0')
        self.assertEqual([],m.check(self.root,final=True))
        r['final']['approval']['reference']='';self.save('releases.json',r)
        self.assertTrue(m.check(self.root,final=True))
    def test_later_failure_overrides_pass(self):
        s,e,h=self.ready()
        failed=copy.deepcopy(e[0]);failed['id']='E2';failed['result']='failed'
        self.save('evidence.json',e+[failed])
        self.assertTrue(any('通过证据' in x for x in m.check(self.root,complete=True)))
    def test_outside_artifact_is_rejected(self):
        s,e,h=self.ready();self.git('tag','V1.0.0')
        self.save('releases.json',{'milestones':[{'version':'V1.0.0','commit':h,'tag':'V1.0.0','artifacts':['../outside']}],
          'final':{'version':'V1.0.0','commit':h,'approval':{'actor':'user','reference':'fixture'}}})
        self.assertTrue(any('越界' in x for x in m.check(self.root,final=True)))
    def test_symlink_ledger_rejected(self):
        original=self.f/'evidence.json'; original.unlink(); original.symlink_to(self.f/'state.json')
        with self.assertRaises(ValueError):m.check(self.root)

    def test_resume_is_read_only_and_current(self):
        self.baseline()
        before={p.name:p.read_bytes() for p in self.f.iterdir()}
        result=m.resume(self.root)
        self.assertEqual('V1.0.0',result['product_version'])
        self.assertEqual('REQ-001',result['requirements']['revision'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.f.iterdir()})
    def test_resume_detects_stale_requirements(self):
        self.baseline();(self.f/'requirements.md').write_text('new requirement')
        self.assertEqual('needs_review',m.resume(self.root)['status'])
    def test_existing_framework_not_initialized(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'openspec').mkdir()
            self.assertEqual('existing_framework',m.resume(root)['status'])
            self.assertFalse((root/'.ontrack').exists())
    def test_incomplete_failure_cannot_hide_behind_success(self):
        s,e,h=self.ready();bad=copy.deepcopy(e[0]);bad['id']='E2';bad['result']='failed';bad['output']=''
        self.save('evidence.json',e+[bad]);self.assertTrue(m.check(self.root,complete=True))

if __name__=='__main__':unittest.main(verbosity=2)
