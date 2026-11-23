"""Pure checks: no sockets, subprocesses, database or filesystem mutation."""
from pathlib import Path
import unittest
import tempfile

from ci_browser import restart_environment, restart_target_spec


class RestartSafetyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()).resolve()
        self.run_id = 'a' * 32
        self.path = self.root / ('migramind-restart-' + self.run_id) / ('synthetic-' + self.run_id + '.sqlite')
        self.marker = {'classification':'SYNTHETIC_RESTART_ONLY', 'run_id':self.run_id}

    def test_exact_fresh_synthetic_target_is_review_only(self):
        self.assertEqual(restart_target_spec(self.root,self.run_id,self.path,self.marker,
            existing_target=False,symlinked=False),'REVIEW_ONLY_NOT_AUTHORIZATION')

    def test_refuses_existing_linked_or_ambiguous_target(self):
        for exists,linked in ((True,False),(False,True),(None,False)):
            with self.assertRaises(ValueError):restart_target_spec(self.root,self.run_id,self.path,self.marker,
                existing_target=exists,symlinked=linked)
        for path in (self.root/'migramind.db',self.path.with_name('other.sqlite')):
            with self.assertRaises(ValueError):restart_target_spec(self.root,self.run_id,path,self.marker,
                existing_target=False,symlinked=False)
        with self.assertRaises(ValueError):restart_target_spec(self.root,self.run_id,self.path,{},
            existing_target=False,symlinked=False)

    def test_child_environment_discards_application_and_database_settings(self):
        env=restart_environment({'PATH':'synthetic','DATABASE_URL':'unread','PGHOST':'unread',
            'APP_ENV':'production','MIGRAMIND_API_PROXY':'unread','PYTHONPATH':'unread'},self.path,18000,15173)
        self.assertEqual(env['APP_ENV'],'development')
        self.assertEqual(env['MIGRAMIND_API_PROXY'],'http://127.0.0.1:18000')
        self.assertNotIn('PGHOST',env);self.assertNotIn('PYTHONPATH',env)
        self.assertNotEqual(env['DATABASE_URL'],'unread')
        for ports in ((18000,18000),(0,15173),(True,15173)):
            with self.assertRaises(ValueError):restart_environment({},self.path,*ports)
        with self.assertRaises(ValueError):restart_environment({},self.root/'migramind.db',18000,15173)


if __name__ == '__main__': unittest.main()
