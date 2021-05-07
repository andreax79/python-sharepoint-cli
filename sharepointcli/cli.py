#!/usr/bin/env python

import os
import os.path
import sys
import argparse
import traceback
import configparser
import glob
from datetime import datetime, timezone
from typing import IO, List, NoReturn, Optional
from .commons import (
    EXIT_PARSER_ERROR,
    EXIT_SUCCESS,
    EXIT_FAILURE,
    ArgumentParserError,
    ArgumentException,
)
from .utils import (
    get_credentials_path,
    get_sharepoint_site,
    get_folder,
    is_remote,
    split_url,
    load_credentials,
    get_tenant_id,
    get_account,
    filter_folder_files,
)

__all__ = ["SPOCli", "main"]

USAGE = """\
{prog} [--client_id client_id] [--client_secret client_secret] [--tenant_id tenant_id] [-v] <command> [parameters]

To see help text, you can run:

  {prog} help
  {prog} help <command>
  """


def format_help(md: str) -> str:
    " Render markdown help to text "
    result = []
    for line in (md or "").split("\n"):
        line = line.strip()
        if line.startswith("```"):
            continue
        line = line.replace("`", "")
        if line.startswith("### "):
            line = line[4:].upper()
        elif line.startswith("#### "):
            line = line[5:]
        elif line.startswith("$ "):
            line = "  " + line[2:]
        else:
            line = "  " + line
        result.append(line.rstrip())
    return "\n".join(result)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, commands: List[str], prog: Optional[str] = None, stderr: IO[str] = sys.stderr, **kargs) -> None:
        super().__init__(add_help=False, **kargs)
        self.stderr = stderr
        self.add_argument("command", choices=commands)
        self.add_argument("args", nargs="*")
        self.add_argument("--client_id", dest="client_id")
        self.add_argument("--client_secret", dest="client_secret")
        self.add_argument("--tenant_id", dest="tenant_id")
        self.add_argument("-v", "--verbose", action="store_true", dest="verbose")
        self.add_argument("-mtime", "--mtime", dest="mtime", type=str)
        self.add_argument("-help", "--help", dest="help", action="store_true", default=False)
        self.usage = USAGE.format(prog=self.prog)

    def exit(self, status: int = 0, message: Optional[str] = None) -> NoReturn:
        if message:
            self._print_message(message, self.stderr)
        raise ArgumentParserError()

    def parse_args(self, args=None, namespace=None):
        args, remaining_args = self.parse_known_args(args, namespace)
        args.argv = []
        for arg in remaining_args:
            if arg.startswith("-"):
                args.argv.append(arg)
            else:
                args.args.append(arg)
        # Parse mtime option (file data was last modified n*24 hours ago)
        if args.mtime:
            args.mtime_now = datetime.now(timezone.utc)
            if args.mtime.startswith("+"):
                mtime = int(args.mtime[1:])
                args.mtime_check = lambda m: m > mtime
            elif args.mtime.startswith("-"):
                mtime = int(args.mtime[1:])
                args.mtime_check = lambda m: m < mtime
            else:
                mtime = int(args.mtime)
                args.mtime_check = lambda m: m == mtime
        return args


class SPOCli(object):
    def __init__(
        self,
        prog: Optional[str] = None,
        stdout: IO[str] = sys.stdout,
        stderr: IO[str] = sys.stderr,
    ) -> None:
        self.prog = os.path.basename(prog or sys.argv[0] or "")
        self.stdout = stdout
        self.stderr = stderr
        self.commands = sorted([x[3:] for x in dir(self) if x.startswith("do_")])

    def cmd(self, args: Optional[List[str]]) -> int:
        parser = ArgumentParser(commands=self.commands, prog=self.prog)
        options = None
        try:
            options = parser.parse_args(args=args)
            if options.verbose:
                print(options, file=self.stderr)
            if options.help:
                options.args = [options.command]
                options.command = "help"
            method = getattr(self, "do_" + options.command)
            return method(options.args, options)
        except ArgumentParserError:
            return EXIT_PARSER_ERROR
        except ArgumentException:
            return self.usage(options)
        except Exception as ex:
            print(
                "{}: {}".format(options.command if options else self.prog, ex),
                file=self.stderr,
            )
            if options and options.verbose:
                traceback.print_exc(file=self.stderr)
            return EXIT_FAILURE

    def usage(self, options: argparse.Namespace) -> int:
        " Prints command usage "
        doc = getattr(self, "do_" + options.command).__doc__
        doc = format_help(doc)
        usage = ""
        usage_section = None
        for line in doc.split("\n"):
            if not line.strip():
                continue
            elif line.startswith("Usage"):
                usage_section = True
            elif usage_section:
                usage = line.strip()
                break
        print("usage: {}".format(usage), file=self.stderr)
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
            raise ArgumentException("Unrecognized arguments")
        tenant: str = args[0] if len(args) > 0 else ""
        if not tenant:
            prompt: str = "SharePoint domain (e.g. example.sharepoint.com): "
            tenant = input(prompt).strip()
        try:
            print("SharePoint domain: {}".format(tenant))
            client_id, client_secret, tenant_id = load_credentials(
                tenant, options.client_id, options.client_secret, options.tenant_id
            )
        except Exception:
            client_id = options.client_id
            client_secret = options.client_secret
            tenant_id = options.tenant_id
        if tenant_id is None:
            tenant_id = get_tenant_id(tenant)
        if tenant_id is None:
            print("Tenant not found", file=self.stderr)
            return EXIT_FAILURE
        print("Tenant Id: {}".format(tenant_id))
        if not options.client_id:
            prompt = "Client Id{}: ".format((" [" + client_id + "]") if client_id else "")
            client_id = input(prompt).strip() or client_id
        if not options.client_secret:
            prompt = "Client Secret{}: ".format((" [" + client_secret + "]") if client_secret else "")
            client_secret = input(prompt).strip() or client_secret
        if not tenant or not client_id or not client_secret:
            return EXIT_FAILURE
        # Check credentials
        account = get_account(tenant, client_id, client_secret, tenant_id, interactive=True)
        assert account
        # Write credentials
        credentials = get_credentials_path()
        os.makedirs(os.path.dirname(credentials), mode=0o700, exist_ok=True)
        config = configparser.ConfigParser()
        config.read(credentials)
        new_config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
        }
        # Copy old (obsolete) config parameters
        try:
            old_config = config[tenant]
        except Exception:
            old_config = None
        else:
            for key in ["username", "password"]:
                if old_config.get(key):
                    new_config[key] = old_config.get(key)
        config[tenant] = new_config
        with open(credentials, "w") as f:
            config.write(f)
        return EXIT_SUCCESS

    def do_authenticate(self, args: List[str], options: argparse.Namespace) -> int:
        """
        ### authenticate

        Performs the OAuth authentication flow using the console.

        #### Usage

        ```console
        $ spo authenticate [domain]
        ```
        """
        if set(options.argv):
            raise ArgumentException("Unrecognized arguments")
        tenant: str = args[0] if len(args) > 0 else ""
        if not tenant:
            prompt: str = "SharePoint domain (e.g. example.sharepoint.com): "
            tenant = input(prompt).strip()
        try:
            print("SharePoint domain: {}".format(tenant))
            client_id, client_secret, tenant_id = load_credentials(
                tenant, options.client_id, options.client_secret, options.tenant_id
            )
        except Exception:
            print("Tenant not found", file=self.stderr)
            return EXIT_FAILURE
        # Authenticate
        account = get_account(tenant, client_id, client_secret, tenant_id, interactive=True)
        if account:
            print("Authenticated", file=self.stdout)
        return EXIT_SUCCESS if account else EXIT_FAILURE

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
            raise ArgumentException("Unrecognized arguments")
        if len(args) != 2:
            raise ArgumentException()
        source: str = args[0]
        target: str = args[1] if len(args) > 1 else ""
        if is_remote(source) and not is_remote(target):  # download
            filename = os.path.basename(source)
            url = os.path.dirname(source)
            if not target:
                target = "."
            tenant, site_name, path = split_url(url)
            site = get_sharepoint_site(tenant, site_name, options)
            folder = get_folder(site, path)
            files = filter_folder_files(folder=folder, options=options, pattern=filename)
            if not files:
                raise FileNotFoundError("{} does not exist".format(source))
            elif len(files) > 1 and not os.path.isdir(target):
                raise NotADirectoryError("Target is not a directory")
            for f in files:
                print(
                    "download: {} to {}".format(os.path.join(path, f.name), target),
                    file=self.stderr,
                )
                if os.path.isdir(target):  # target is a directory
                    f.download(to_path=target)
                else:  # target is a filename
                    f.download(to_path=os.path.dirname(target), name=os.path.basename(target))
            return EXIT_SUCCESS

        elif not is_remote(source) and is_remote(target):  # upload
            tenant, site_name, path = split_url(target)
            site = get_sharepoint_site(tenant, site_name, options)
            files = glob.glob(source)
            if not files:
                raise FileNotFoundError("{} does not exist".format(source))
            try:  # target is a folder
                folder = get_folder(site, path)
                for f in files:
                    print("upload: {} to {}".format(f, target), file=self.stderr)
                    folder.upload_file(item=f)

            except FileNotFoundError:  # target is not a folder
                filename = os.path.basename(path)
                folder = get_folder(site, os.path.dirname(path))
                if len(files) > 1:
                    raise NotADirectoryError("Target is not a directory")
                for f in files:
                    print("upload: {} to {}".format(f, target), file=self.stderr)
                    folder.upload_file(item=f, item_name=filename)
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
        if set(options.argv) - set(["--raw"]):
            raise ArgumentException("Unrecognized arguments")
        if len(args) == 1 and args[0] in self.commands:
            doc = getattr(self, "do_" + args[0]).__doc__
            if "--raw" in options.argv:
                doc = "\n".join(line.strip() for line in doc.split("\n"))
            else:
                doc = format_help(doc)
            print(doc, file=self.stdout)
        else:
            if len(args) > 0:
                print(
                    """
Sorry, no help available on {}.

Help is available on:
""".format(
                        args[0]
                    ),
                    file=self.stdout,
                )
            else:
                print(
                    """
Help can be obtained on a particular topic by running:

  spo help topic

Additional help is available on:
""",
                    file=self.stdout,
                )
            for command in self.commands:
                doc = [x.strip() for x in getattr(self, "do_" + command).__doc__.split("\n")]
                print(
                    "  {command:20} {help}".format(command=command, help=doc[3]),
                    file=self.stdout,
                )
        print("", file=self.stdout)
        return EXIT_SUCCESS

    def do_ls(self, args: List[str], options: argparse.Namespace) -> int:
        """
        ### ls

        Lists files and folders.

        #### Usage

        ```console
        $ spo ls [options] <SharePointUrl>
        ```

        ##### Options

        -mtime n  File's status was last changed n*24 hours ago. ('+n' more than n, 'n' exactly n, '-n' less than n)

        #### Examples

        ```console
        $ spo ls 'https://example.sharepoint.com/sites/example/Shared documents/*.txt'
        ```
        """
        if set(options.argv):
            raise ArgumentException("Unrecognized arguments")
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0]
        tenant, site_name, path = split_url(url)
        match = False
        site = get_sharepoint_site(tenant, site_name, options)
        try:
            folder = get_folder(site, path)
            filename = None
            match = True
        except FileNotFoundError:
            try:
                folder = get_folder(site, os.path.dirname(path))
                filename = os.path.basename(path)
            except FileNotFoundError:
                return EXIT_FAILURE
        for f in filter_folder_files(folder=folder, options=options, pattern=filename, include_folders=True):
            match = True
            if f.is_folder:
                print(
                    "{modified:%Y-%m-%d %H:%M} {size:>13} {name}".format(name=f.name + "/", size="PRE", modified=f.modified),
                    file=self.stdout,
                )
            else:
                print(
                    "{modified:%Y-%m-%d %H:%M} {size:>13} {name}".format(name=f.name, size=f.size, modified=f.modified),
                    file=self.stdout,
                )
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
            raise ArgumentException("Unrecognized arguments")
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0].rstrip("/")
        tenant, site_name, path = split_url(url)
        site = get_sharepoint_site(tenant, site_name, options)
        parent_folder = get_folder(site, os.path.dirname(path))
        name = os.path.basename(path)
        if name in [x.name for x in parent_folder.get_items()]:
            print(
                "mkdir: cannot create directory {}: directory exists".format(url),
                file=self.stderr,
            )
            return EXIT_FAILURE
        parent_folder.create_child_folder(name=name)
        print("mkdir: {} created".format(url), file=self.stdout)
        return EXIT_SUCCESS

    def do_rm(self, args: List[str], options: argparse.Namespace) -> int:
        """
        ### rm

        Deletes files.

        #### Usage

        ```console
        $ spo rm [options] <SharePointUrl>
        ```

        ##### Options

        -mtime n  File's status was last changed n*24 hours ago. ('+n' more than n, 'n' exactly n, '-n' less than n)

        #### Examples

        ```console
        $ spo rm 'https://example.sharepoint.com/sites/example/Shared documents/*.txt'
        ```
        """
        if set(options.argv):
            raise ArgumentException("Unrecognized arguments")
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = os.path.dirname(args[0])
        filename: str = os.path.basename(args[0])
        tenant, site_name, path = split_url(url)
        site = get_sharepoint_site(tenant, site_name, options)
        folder = get_folder(site, path)
        match = False
        for f in filter_folder_files(folder=folder, options=options, pattern=filename):
            match = True
            f.delete()
        if not match:
            raise FileNotFoundError("{} does not exist".format(os.path.join(url, filename)))
        print(
            "rm: {} deleted".format(os.path.join(url, filename)),
            file=self.stdout,
        )
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
            raise ArgumentException("Unrecognized arguments")
        if len(args) != 1 or not is_remote(args[0]):
            raise ArgumentException()
        url: str = args[0].rstrip("/")
        tenant, site_name, path = split_url(url)
        site = get_sharepoint_site(tenant, site_name, options)
        folder = get_folder(site, path)
        if any(folder.get_items()):
            print(
                "rmdir: failed to remove {}: not empty".format(url),
                file=self.stderr,
            )
            return EXIT_FAILURE
        if folder.delete():
            print("rmdir: {} deleted".format(url), file=self.stdout)
            return EXIT_SUCCESS
        else:
            print("rmdir: error deleting {}".format(url), file=self.stderr)
            return EXIT_FAILURE

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
        from O365 import __version__ as o365_version

        if set(options.argv):
            raise ArgumentException("Unrecognized arguments")
        print("{} {}".format(self.prog, __version__), file=self.stdout)
        print("{} {}".format("O365", o365_version), file=self.stdout)
        return EXIT_SUCCESS


def main(
    args: Optional[List[str]] = None,
    stdout: IO[str] = sys.stdout,
    stderr: IO[str] = sys.stderr,
) -> int:
    cli = SPOCli(stdout=stdout, stderr=stderr)
    return cli.cmd(args)
