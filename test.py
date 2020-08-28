#!/usr/bin/env python

import os
import os.path
import sys
import shlex
import hashlib
import inspect
import unittest
import datetime
import filecmp
from io import StringIO
from sharepointcli import main, __version__
from sharepointcli.cli import format_help, ArgumentParser
from collections import namedtuple

Result = namedtuple('Result', 'exit_code stdout stderr')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
if sys.version_info <= (3, 0):
    print('Python 2 is vintage. Please use Python 3.')
    sys.exit(1)

site = os.environ.get('SITE','').rstrip('/')
assert site, 'SITE environment variable not set'


class Testing(unittest.TestCase):

    def _exec(self, cmd, expected_exit_code=0, stdout_check=None):
        args = shlex.split(cmd)
        stdout = StringIO()
        stderr = StringIO()
        exit_code = main(args=args, stdout=stdout, stderr=stderr)
        r = Result(exit_code, stdout.getvalue(), stderr.getvalue())
        if expected_exit_code is not None:
            self.assertEqual(r.exit_code, expected_exit_code)
        if stdout_check:
            if inspect.isfunction(stdout_check):
                self.assertTrue(stdout_check(r))
            else:
                self.assertEqual(r.stdout, stdout_check)
        return r

    def _t(self):
        t = datetime.datetime.now().isoformat()
        h = hashlib.sha256(t.encode())
        return h.hexdigest()


class LocalTesting(Testing):

    def test_argument_parser(self):
        parser = ArgumentParser(commands=['aaa','bbb','ccc'], prog='test')
        options = parser.parse_args(args=['-v', '-a', 'aaa', '1', '2', '-b'])
        self.assertEqual(options.verbose, True)
        self.assertEqual(options.command, 'aaa')
        self.assertEqual(options.username, None)
        self.assertEqual(options.args, ['1','2'])
        self.assertEqual(options.argv, ['-a','-b'])
        parser = ArgumentParser(commands=['aaa','bbb','ccc'], prog='test')
        options = parser.parse_args(args=['aaa', '-v', '-a', '-b', '1', '2'])
        self.assertEqual(options.verbose, True)
        self.assertEqual(options.command, 'aaa')
        self.assertEqual(options.args, ['1','2'])
        self.assertEqual(options.argv, ['-a','-b'])

    def test_version(self):
        self._exec('version',
                   stdout_check=lambda r: __version__ in r.stdout)

    def test_format_help(self):
        md = """
### help

Displays commands help.

#### Usage

```console
$ spo help [topic]
```
        """
        res = """

HELP

  Displays commands help.

Usage

  spo help [topic]
"""
        t = format_help(md)
        self.assertEqual(t.strip(), res.strip())

    def test_help(self):
        self._exec('help help',
                   stdout_check=lambda r: 'help [topic]' in r.stdout)
        self._exec('help')

    def test_usage(self):
        self._exec('ls',
                   expected_exit_code=2,
                   stdout_check=lambda r: 'usage: spo ls <SharePointUrl>' in r.stderr)

    def test_args(self):
        self._exec('cp', expected_exit_code=2)
        self._exec('rm', expected_exit_code=2)
        self._exec('ls', expected_exit_code=2)
        self._exec('mkdir', expected_exit_code=2)
        self._exec('rmdir', expected_exit_code=2)
        self._exec('cp --dummy a b', expected_exit_code=2)
        self._exec('rm --dummy a', expected_exit_code=2)
        self._exec('ls --dummy a', expected_exit_code=2)
        self._exec('mkdir --dummy a', expected_exit_code=2)
        self._exec('rmdir --dummy a', expected_exit_code=2)
        self._exec('version --dummy', expected_exit_code=2)
        self._exec('help --dummy', expected_exit_code=2)


class OnlineTesting(Testing):

    def test_cp(self):
        t = self._t()
        self._exec('ls "{}/"'.format(site))
        self._exec('cp ./tests/f1.txt./tests/f1.txt', expected_exit_code=2)
        self._exec('cp ./tests/f1.txt "{}/"'.format(site, t))
        self._exec('rm "{}/f1.txt"'.format(site))
        self._exec('cp ./tests/f1.txt "{}/{}1.txt"'.format(site, t))
        self._exec('cp ./tests/f1.txt "{}/{}2.txt"'.format(site, t))
        self._exec('ls "{}/{}1.txt"'.format(site, t))
        self._exec('ls "{}/{}2.txt"'.format(site, t),
                   stdout_check=lambda r: len(r.stdout.split('\n')) == 2)
        self._exec('rm "{}/{}1.txt"'.format(site, t))
        self._exec('rm "{}/{}2.txt"'.format(site, t))
        self._exec('ls "{}/{}1.txt"'.format(site, t), expected_exit_code=1)
        self._exec('rm "{}/{}1.txt"'.format(site, t), expected_exit_code=1)

    def test_cp_download(self):
        t = self._t()
        self._exec('cp ./tests/f2.bin "{}/{}2.bin"'.format(site, t))
        self._exec('cp "{}/{}2.bin" f2.bin'.format(site, t))
        self.assertTrue(filecmp.cmp('./tests/f2.bin', 'f2.bin'))
        os.unlink('f2.bin')
        self._exec('rm "{}/{}2.bin"'.format(site, t))

    def test_ls(self):
        self._exec('ls "{}/"'.format(site))
        self._exec('ls "{}/*"'.format(site))
        self._exec('ls "{}/xxxxxxxx"'.format(site), expected_exit_code=1)
        self._exec('ls "{}/xxx/xxxxx"'.format(site), expected_exit_code=1)

    def test_mkdir_rmdir(self):
        t = self._t()
        self._exec('mkdir "{}/{}"'.format(site, t))
        self._exec('mkdir "{}/{}"'.format(site, t),
                   expected_exit_code=1,
                   stdout_check=lambda r: 'directory exists' in r.stderr)
        self._exec('mkdir "{}/{}/1"'.format(site, t))
        self._exec('rmdir "{}/{}"'.format(site, t),
                   expected_exit_code=1,
                   stdout_check=lambda r: 'not empty' in r.stderr)
        self._exec('rmdir "{}/{}/1"'.format(site, t))
        self._exec('rmdir "{}/{}/1"'.format(site, t), expected_exit_code=1)
        self._exec('rmdir "{}/{}"'.format(site, t))
        self._exec('rmdir "{}/{}"'.format(site, t), expected_exit_code=1)
        self._exec('rmdir "{}/{}/1"'.format(site, t), expected_exit_code=1)


if __name__ == '__main__':
    unittest.main()
