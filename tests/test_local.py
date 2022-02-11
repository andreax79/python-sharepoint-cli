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


class LocalTesting(Testing):
    def test_argument_parser(self):
        parser = ArgumentParser(commands=['aaa', 'bbb', 'ccc'], prog='test')
        options = parser.parse_args(args=['-v', '-a', 'aaa', '1', '2', '-b'])
        self.assertEqual(options.verbose, True)
        self.assertEqual(options.command, 'aaa')
        self.assertEqual(options.client_id, None)
        self.assertEqual(options.args, ['1', '2'])
        self.assertEqual(options.argv, ['-a', '-b'])
        parser = ArgumentParser(commands=['aaa', 'bbb', 'ccc'], prog='test')
        options = parser.parse_args(args=['aaa', '-v', '-a', '-b', '1', '2'])
        self.assertEqual(options.verbose, True)
        self.assertEqual(options.command, 'aaa')
        self.assertEqual(options.args, ['1', '2'])
        self.assertEqual(options.argv, ['-a', '-b'])

    def test_version(self):
        self._exec('version', stdout_check=lambda r: __version__ in r.stdout)

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
        self._exec('help help', stdout_check=lambda r: 'help [topic]' in r.stdout)
        self._exec('help')

    def test_usage(self):
        self._exec('ls', expected_exit_code=2, stdout_check=lambda r: 'usage: spo ls [options] <SharePointUrl>' in r.stderr)

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


if __name__ == '__main__':
    unittest.main()
