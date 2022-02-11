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

__all__ = ['Result', 'Testing']


class Testing(unittest.TestCase):
    def _exec(self, cmd, expected_exit_code=0, stdout_check=None):
        args = shlex.split(cmd)
        stdout = StringIO()
        stderr = StringIO()
        exit_code = main(args=args, stdout=stdout, stderr=stderr)
        r = Result(exit_code, stdout.getvalue(), stderr.getvalue())
        try:
            if expected_exit_code is not None:
                self.assertEqual(r.exit_code, expected_exit_code)
            if stdout_check:
                if inspect.isfunction(stdout_check):
                    self.assertTrue(stdout_check(r))
                else:
                    self.assertEqual(r.stdout, stdout_check)
        except Exception as ex:
            print('cmd:', cmd)
            print('stdout:', r.stdout)
            print('stderr:', r.stderr)
            print('exit code:', exit_code)
            raise ex
        return r

    def _t(self):
        t = datetime.datetime.now().isoformat()
        h = hashlib.sha256(t.encode())
        return h.hexdigest()
