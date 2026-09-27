"""Exercise the installed hook with local Git transports only."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / 'scripts' / 'install_hooks.py'


class PushGuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='kizuki push ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        self.remote = self.base / 'remote.git'
        self.env = os.environ.copy()
        for name in tuple(self.env):
            if name.startswith('GIT_'):
                del self.env[name]
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
        self.git(self.base, 'init', '--bare', str(self.remote))
        self.git(self.base, 'init', '-b', 'work', str(self.repo))
        self.git(self.repo, 'commit', '--allow-empty', '-m', 'base')
        self.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        for branch in ('main', 'develop', 'dev', 'stg'):
            self.git(self.repo, 'push', 'origin', f'HEAD:refs/heads/{branch}')
        self.git(self.repo, 'commit', '--allow-empty', '-m', 'change')

    def git(self, cwd, *args, success=True):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env,
                                text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def install(self, cwd=None):
        return subprocess.run([sys.executable, '-B', str(INSTALLER)],
                              cwd=cwd or self.repo, env=self.env, text=True, capture_output=True)

    def refs(self):
        return self.git(self.remote, 'show-ref').stdout

    def test_blocked_refs_force_deletion_and_mixed_push_are_unchanged(self):
        self.assertEqual(self.install().returncode, 0)
        before = self.refs()
        for branch in ('main', 'develop', 'dev', 'stg'):
            for refspec in (f'HEAD:refs/heads/{branch}', f'+HEAD:refs/heads/{branch}',
                            f':refs/heads/{branch}'):
                with self.subTest(refspec=refspec):
                    result = self.git(self.repo, 'push', 'origin', refspec, success=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('PR', result.stderr)
                    self.assertEqual(self.refs(), before)
        self.assertNotEqual(self.git(self.repo, 'push', 'origin',
                                    'HEAD:refs/heads/allowed', 'HEAD:refs/heads/main', success=False).returncode, 0)
        self.assertEqual(self.refs(), before)

    def test_allowed_branch_and_same_named_tag(self):
        self.assertEqual(self.install().returncode, 0)
        self.git(self.repo, 'push', 'origin', 'HEAD:refs/heads/feature', 'HEAD:refs/tags/main')
        self.git(self.repo, 'push', 'origin', ':refs/heads/feature')

    def test_install_from_linked_worktree_survives_its_removal(self):
        linked = self.base / 'linked worktree'
        self.git(self.repo, 'worktree', 'add', '-b', 'linked', str(linked))
        result = self.install(linked)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.install().returncode, 0)
        self.assertNotEqual(self.git(linked, 'push', 'origin', 'HEAD:main', success=False).returncode, 0)
        self.git(self.repo, 'worktree', 'remove', str(linked))
        self.assertNotEqual(self.git(self.repo, 'push', 'origin', 'HEAD:main', success=False).returncode, 0)
        self.git(self.repo, 'push', 'origin', 'HEAD:refs/heads/feature')

    def test_existing_hook_is_preserved(self):
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nexit 42\n')
        hook.chmod(0o755)
        config = (self.repo / '.git/config').read_bytes()
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(hook.read_text(), '#!/bin/sh\nexit 42\n')
        self.assertEqual((self.repo / '.git/config').read_bytes(), config)

    def test_existing_hooks_path_is_preserved(self):
        self.git(self.repo, 'config', 'core.hooksPath', 'other hooks')
        config = (self.repo / '.git/config').read_bytes()
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual((self.repo / '.git/config').read_bytes(), config)

    @unittest.skipIf(os.name == 'nt', 'symlink creation requires Windows privileges')
    def test_symlink_install_directory_does_not_change_external_files(self):
        external = self.base / 'external'
        external.mkdir()
        (self.repo / '.git/kizuki-hooks').symlink_to(external, target_is_directory=True)
        config = (self.repo / '.git/config').read_bytes()
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(list(external.iterdir()), [])
        self.assertEqual((self.repo / '.git/config').read_bytes(), config)

    def test_malformed_input_fails_closed(self):
        self.assertEqual(self.install().returncode, 0)
        hook = self.repo / '.git/kizuki-hooks/pre-push'
        for data in ('invalid\n', 'invalid', 'a b refs/heads/main c extra\n'):
            with self.subTest(data=data):
                result = subprocess.run(['sh', str(hook)], input=data, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_worktree_specific_config_requires_manual_resolution(self):
        self.git(self.repo, 'config', 'extensions.worktreeConfig', 'true')
        config = (self.repo / '.git/config').read_bytes()
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual((self.repo / '.git/config').read_bytes(), config)

    def test_existing_install_tampering_is_not_overwritten(self):
        self.assertEqual(self.install().returncode, 0)
        hook = self.repo / '.git/kizuki-hooks/pre-push'
        hook.write_text('other hook\n')
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(hook.read_text(), 'other hook\n')


if __name__ == '__main__':
    unittest.main()
