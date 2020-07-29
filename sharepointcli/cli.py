#!/usr/bin/env python

import os
import os.path
import re
import sys
import argparse
import traceback
import fnmatch
import configparser
from requests_ntlm import HttpNtlmAuth
from getpass import getpass
from typing import Optional, List, NoReturn, Tuple, IO
from contextlib import contextmanager
from .sso import SSOAuth
from shareplum import Site  # type: ignore
from shareplum.site import Version  # type: ignore
from shareplum.errors import ShareplumRequestError  # type: ignore
from shareplum.folder import _Folder  # type: ignore

__all__ = [
    'SPOCli',
    'get_sharepoint_site',
    'split_url',
    'get_folder',
    'main'
]

ENV_CREDENTIALS = 'SPO_CREDENTIALS_FILE'
ENV_USERNAME = 'SPO_CREDENTIALS'
ENV_PASSWORD = 'SPO_CREDENTIALS'
CREDENTIALS = '~/.spo/credentials'
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_PARSER_ERROR = 2
RE_SHAREPOINT_COM = re.compile('^https://[^\\.]+.sharepoint.com/.*')
USAGE = """\
{prog} [-u USERNAME] [-p PASSWORD] [-v] <command> [parameters]

To see help text, you can run:

  {prog} help
  {prog} help <command>
  """


class ArgumentParserError(Exception):
    pass


class ArgumentException(Exception):
    pass


class NotFoundError(Exception):
    pass


def split_url(url: str) -> Tuple[str, str]:
    site_url = '/'.join(url.split('/')[:5]) + '/'  # 'https://XXXXX.sharepoint.com/sites/'
    path = url[len(site_url):]  # 'Shared Documents/...'
    return (site_url, path)


def is_remote(url: str) -> bool:
    return url.startswith('https://')


def is_office365_sharepoint(url: str) -> bool:
    return RE_SHAREPOINT_COM.match(url)


def load_credentials(site_url: str,
                     username: Optional[str] = None,
                     password: Optional[str] = None) -> Tuple[str, str]:
    username = username or os.environ.get('ENV_USERNAME')
    password = password or os.environ.get('ENV_PASSWORD')
    if username and password:
        return (username, password)
    config = configparser.ConfigParser()
    config.read(os.path.expanduser(os.environ.get('ENV_CREDENTIALS') or CREDENTIALS))
    domain = site_url.split('/')[2]
    section = domain
    if section not in config:
        section = 'default'
    if section not in config:
        raise ArgumentParserError('Add [{}] section to {} or specify username and password'.format(
            domain, CREDENTIALS))
    username = config[section]['username']
    password = config[section]['password']
    return (username, password)


@contextmanager
def get_sharepoint_site(site_url: str,
                        username: Optional[str] = None,
                        password: Optional[str] = None,
                        verbose: bool = False,
                        version: Version = None) -> Site:
    if version is None:
        version = Version.v365 if is_office365_sharepoint(site_url) else Version.v2013
    username, password = load_credentials(site_url, username, password)
    if is_office365_sharepoint(site_url):
        sso_auth = SSOAuth(site_url, username=username, password=password, verbose=verbose)
        try:
            authcookie = sso_auth.get_cookies()
            site = Site(site_url, version=version, authcookie=authcookie)
        except ShareplumRequestError:
            authcookie = sso_auth.get_cookies(force_login=True)
            site = Site(site_url, version=version, authcookie=authcookie)
    else:
        auth = HttpNtlmAuth(username, password)
        site = Site(site_url, version=version, auth=auth)
        # site._session.headers['Accept'] = 'application/json;odata=verbose'
    try:
        yield site
    finally:
        site._session.close()


def get_folder(site: Site, path: str) -> _Folder:
    " Get site folder by path "
    folder = site.Folder('')
    path = path.strip('/')
    if not path:
        return folder  # root folder
    try:
        for part in path.split('/'):
            if part not in folder.folders:
                raise NotFoundError('{} does not exist'.format(path))
            folder = site.Folder(folder.folder_name + ('/' if folder.folder_name else '') + part)
    except ShareplumRequestError:
        raise NotFoundError('{} does not exist'.format(path))
    return folder


def format_help(md: str) -> str:
    " Render markdown help to text "
    result = []
    for line in (md or '').split('\n'):
        line = line.strip()
        if line.startswith('```'):
            continue
        line = line.replace("`", "")
        if line.startswith('### '):
            line = line[4:].upper()
        elif line.startswith('#### '):
            line = line[5:]
        elif line.startswith('$ '):
            line = '  ' + line[2:]
        else:
            line = '  ' + line
        result.append(line.rstrip())
    return '\n'.join(result)


class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, stderr: IO[str] = sys.stderr, **kargs) -> None:
        super().__init__(**kargs)
        self.stderr = stderr

    def exit(self, status: int = 0, message: Optional[str] = None) -> NoReturn:
        if message:
            self._print_message(message, self.stderr)
        raise ArgumentParserError()

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        args.argv = argv
        return args


class SPOCli(object):

    def __init__(self,
                 prog: Optional[str] = None,
                 stdout: IO[str] = sys.stdout,
                 stderr: IO[str] = sys.stderr) -> None:
        self.prog = os.path.basename(prog or sys.argv[0] or '')
        self.stdout = stdout
        self.stderr = stderr
        self.commands = sorted([x[3:] for x in dir(self) if x.startswith('do_')])

    def cmd(self, args: Optional[List[str]]) -> int:
        parser = ArgumentParser(prog=self.prog, add_help=False)
        parser.add_argument('command',
                            choices=self.commands)
        parser.add_argument('args', nargs='*')
        parser.add_argument('-u', '--username',
                            dest='username')
        parser.add_argument('-p', '--password',
                            dest='password')
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            dest='verbose')
        parser.usage = USAGE.format(prog=self.prog)
        options = None
        try:
            options = parser.parse_args(args=args)
            method = getattr(self, 'do_' + options.command)
            return method(options.args, options)
        except ArgumentParserError:
            return EXIT_PARSER_ERROR
        except ArgumentException:
            return self.usage(options)
        except Exception as ex:
            print('{}: {}'.format(options.command if options else self.prog, ex),
                  file=self.stderr)
            if options and options.verbose:
                traceback.print_exc(file=self.stderr)
            return EXIT_FAILURE

    def usage(self, options: argparse.Namespace) -> int:
        " Prints command usage "
        doc = getattr(self, 'do_' + options.command).__doc__
        doc = format_help(doc)
        usage = ''
        usage_section = None
        for line in doc.split('\n'):
            if not line.strip():
                continue
            elif line.startswith('Usage'):
                usage_section = True
            elif usage_section:
                usage = line.strip()
                break
        print('usage: {}'.format(usage),
              file=self.stderr)
        return EXIT_PARSER_ERROR

    def do_configure(self, args: List[str], options: argparse.Namespace) -> int:
        """
### configure

Configures credentials.

#### Usage

```console
$ spo configure [domain]
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        domain: str = args[0] if len(args) > 0 else ''
        prompt: str = 'SharePoint domain (e.g. example.sharepoint.com){}: ' \
                      .format((' [' + domain + ']') if domain else '')
        domain = input(prompt).strip() or domain
        try:
            username, password = load_credentials('https://' + domain, options.username, options.password)
        except Exception:
            username = options.username
            password = options.password
        prompt = 'Username{}: '.format((' [' + username + ']') if username else '')
        username  = input(prompt).strip() or username
        prompt = 'Password{}: '.format((' [' + '*' * len(password) + ']') if password else '')
        password  = getpass(prompt).strip() or password
        if not domain or not username or not password:
            return EXIT_FAILURE
        # Check credentials
        url = 'https://' + domain + '/'
        sso_auth = SSOAuth(url,
                           username=username,
                           password=password,
                           verbose=options.verbose)
        if is_office365_sharepoint(url):
            authcookie = sso_auth.get_cookies()
            site = Site(url, version=Version.v365, authcookie=authcookie)
        else:
            auth = HttpNtlmAuth(username, password)
            site = Site(url, version=Version.v2013, auth=auth)
        assert(site)
        # Write credentials
        config_path = os.path.expanduser(CREDENTIALS)
        os.makedirs(os.path.dirname(config_path), mode=0o700, exist_ok=True)
        config = configparser.ConfigParser()
        config.read(config_path)
        config[domain] = {
            'username': username,
            'password': password
        }
        with open(config_path, 'w') as f:
            config.write(f)
        return EXIT_SUCCESS

    def do_cp(self, args: List[str], options: argparse.Namespace) -> int:
        """
### cp

Copying a local file to SharePoint.

#### Usage

```console
$ spo cp <LocalPath> <SharePointUrl>   or   cp <SharePointUrl> <LocalPath>
```

#### Examples

The following cp command copies a single file to a specified site:

```console
$ spo cp test.txt 'https://example.sharepoint.com/sites/example/Shared documents/test.txt'
upload: test.txt to https://example.sharepoint.com/sites/example/Shared documents/test.txt
```

The following cp command copies a single file from a SharePoint site:

```console
$ spo cp 'https://example.sharepoint.com/sites/example/Shared documents/test.txt' test.txt
download: https://example.sharepoint.com/sites/example/Shared documents/test.txt' to test.txt
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        if len(args) != 2:
            raise ArgumentException()
        source: str = args[0]
        target: str = args[1] if len(args) > 1 else ''

        if is_remote(source) and not is_remote(target):  # download
            filename = os.path.basename(source)
            url = os.path.dirname(source)
            if not target:
                target = filename
            elif os.path.isdir(target):
                target = os.path.join(target, filename)
            site_url, path = split_url(url)
            with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
                folder = get_folder(site, path)
                if filename not in [x['Name'] for x in folder.files]:
                    raise NotFoundError('{} does not exist'.format(os.path.join(folder.folder_name, filename)))
                print('download: {} to {}'.format(source, target), file=self.stderr)
                content = folder.get_file(filename)
                with open(target, 'wb') as f:
                    f.write(content)
            return EXIT_SUCCESS

        elif not is_remote(source) and is_remote(target):  # upload
            if target.endswith('/'):
                filename = os.path.basename(source)
                url = target
            else:
                filename = os.path.basename(target)
                url = os.path.dirname(target)
            site_url, path = split_url(url)
            with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
                folder = get_folder(site, path)
                with open(source, 'rb') as f:
                    content = f.read()
                print('upload: {} to {}'.format(source, target), file=self.stderr)
                folder.upload_file(content, filename)
            return EXIT_SUCCESS

        else:
            raise ArgumentException()

    def do_help(self, args: List[str], options: argparse.Namespace) -> int:
        """
### help

Displays commands help.

#### Usage

```console
$ spo help [topic]
```
        """
        if set(options.argv) - set(['--raw']):
            raise ArgumentException('Unrecognized arguments')
        if len(args) == 1 and args[0] in self.commands:
            doc = getattr(self, 'do_' + args[0]).__doc__
            if '--raw' not in options.argv:
                doc = format_help(doc)
            print(doc, file=self.stdout)
        else:
            if len(args) > 0:
                print("""
Sorry, no help available on {}.

Help is available on:
""".format(args[0]), file=self.stdout)
            else:
                print("""
Help can be obtained on a particular topic by running:

  spo help topic

Additional help is available on:
""", file=self.stdout)
            for command in self.commands:
                doc = [x.strip() for x in getattr(self, 'do_' + command).__doc__.split('\n')]
                print('  {command:20} {help}'.format(command=command, help=doc[3]), file=self.stdout)
        print('', file=self.stdout)
        return EXIT_SUCCESS

    def do_ls(self, args: List[str], options: argparse.Namespace) -> int:
        """
### ls

Lists files and folders.

#### Usage

```console
$ spo ls <SharePointUrl>
```

#### Examples

```console
$ spo ls 'https://example.sharepoint.com/sites/example/Shared documents/*.txt'
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0]
        site_url, path = split_url(url)
        match = False
        with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
            try:
                folder = get_folder(site, path)
                filename = None
                match = True
            except NotFoundError:
                try:
                    folder = get_folder(site, os.path.dirname(path))
                    filename = os.path.basename(path)
                except NotFoundError:
                    return EXIT_FAILURE
            for f in folder.folders:
                if not filename or fnmatch.fnmatch(f, filename):
                    match = True
                    print('{t:16} {Length:>13} {Name}'.format(t='', Length='PRE', Name=f + '/'),
                          file=self.stdout)
            for f in folder.files:
                if not filename or fnmatch.fnmatch(f['Name'], filename):
                    match = True
                    t = f['TimeLastModified'].replace('T', ' ')[:16]
                    print('{t:16} {Length:>13} {Name}'.format(t=t, **f),
                          file=self.stdout)
        return EXIT_SUCCESS if match else EXIT_FAILURE

    def do_mkdir(self, args: List[str], options: argparse.Namespace) -> int:
        """
### mkdir

Creates folder.

#### Usage

```console
$ spo mkdir <SharePointUrl>
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0].rstrip('/')
        site_url, path = split_url(url)
        with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
            parent_folder = get_folder(site, os.path.dirname(path))
            name = os.path.basename(path)
            if name in parent_folder.folders:
                print('mkdir: cannot create directory {}: directory exists'.format(path),
                      file=self.stderr)
                return EXIT_FAILURE
            folder = site.Folder(path)
            print('mkdir: {} created'.format(folder.folder_name),
                  file=self.stdout)
        return EXIT_SUCCESS

    def do_rm(self, args: List[str], options: argparse.Namespace) -> int:
        """
### rm

Deletes files.

#### Usage

```console
$ spo rm <SharePointUrl>
```

#### Examples

```console
$ spo rm 'https://example.sharepoint.com/sites/example/Shared documents/*.txt'
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = os.path.dirname(args[0])
        filename: str = os.path.basename(args[0])
        site_url, path = split_url(url)
        with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
            folder = get_folder(site, path)
            match = False
            for f in folder.files:
                if fnmatch.fnmatch(f['Name'], filename):
                    match = True
                    folder.delete_file(f['Name'])
            if not match:
                raise NotFoundError('{} does not exist'.format(os.path.join(folder.folder_name, filename)))
            print('rm: {} deleted'.format(os.path.join(folder.folder_name, filename)),
                  file=self.stdout)
        return EXIT_SUCCESS

    def do_rmdir(self, args: List[str], options: argparse.Namespace) -> int:
        """
### rmdir

Deletes folder.

#### Usage

```console
$ spo rmdir <SharePointUrl>
```
        """
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0].rstrip('/')
        site_url, path = split_url(url)
        with get_sharepoint_site(site_url, options.username, options.password, options.verbose) as site:
            folder = get_folder(site, path)
            if folder.files or folder.folders:
                print('rmdir: failed to remove {}: not empty'.format(folder.folder_name),
                      file=self.stderr)
                return EXIT_FAILURE
            folder.delete_folder(folder.folder_name)
            print('rmdir: {} deleted'.format(folder.folder_name),
                  file=self.stdout)
        return EXIT_SUCCESS

    def do_version(self, args: List[str], options: argparse.Namespace) -> int:
        """
### version

Prints the version number.

#### Usage

```console
$ spo version
```
        """
        from . import __version__
        if set(options.argv):
            raise ArgumentException('Unrecognized arguments')
        print('{} {}'.format(self.prog, __version__),
              file=self.stdout)
        return EXIT_SUCCESS


def main(args: Optional[List[str]] = None,
         stdout: IO[str] = sys.stdout,
         stderr: IO[str] = sys.stderr) -> int:
    cli = SPOCli(stdout=stdout, stderr=stderr)
    return cli.cmd(args)
