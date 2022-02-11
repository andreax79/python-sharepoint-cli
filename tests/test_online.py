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
from commons import Testing


site = os.environ.get('SITE', '').rstrip('/')
assert site, 'SITE environment variable not set'


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
        self._exec('ls "{}/{}2.txt"'.format(site, t), stdout_check=lambda r: len(r.stdout.split('\n')) == 2)
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
        self._exec('mkdir "{}/{}"'.format(site, t), expected_exit_code=1, stdout_check=lambda r: 'directory exists' in r.stderr)
        self._exec('mkdir "{}/{}/1"'.format(site, t))
        self._exec('rmdir "{}/{}"'.format(site, t), expected_exit_code=1, stdout_check=lambda r: 'not empty' in r.stderr)
        self._exec('rmdir "{}/{}/1"'.format(site, t))
        # self._exec('rmdir "{}/{}/1"'.format(site, t), expected_exit_code=1)  # TODO
        self._exec('rmdir "{}/{}"'.format(site, t))
        self._exec('rmdir "{}/{}"'.format(site, t), expected_exit_code=1)
        self._exec('rmdir "{}/{}/1"'.format(site, t), expected_exit_code=1)


if __name__ == '__main__':
    unittest.main()
