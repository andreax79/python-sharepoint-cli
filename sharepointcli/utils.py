#!/usr/bin/env python

import os
import os.path
import configparser
import argparse
import requests
import fnmatch
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from O365 import Account, FileSystemTokenBackend  # type: ignore
from O365.sharepoint import Site  # type: ignore
from O365.drive import Folder, DriveItem  # type: ignore
from .commons import (
    RE_SHAREPOINT_COM,
    ENV_CREDENTIALS,
    ENV_CLIENT_ID,
    ENV_CLIENT_SECRET,
    ENV_HOME,
    ENV_TENANT_ID,
    CREDENTIALS,
    HOME,
    O365_SCOPES,
    ArgumentParserError,
)

__all__ = [
    "load_credentials",
    "get_credentials_path",
    "get_account",
    "get_tenant_id",
    "split_url",
    "is_remote",
    "is_office365_sharepoint",
    "get_sharepoint_site",
    "get_folder",
    "filter_folder_files",
]


def get_tenant_id(tenant: str) -> Optional[str]:
    " Get tenant id from tenant name "
    try:
        name = tenant.split(".")[0]
        r = requests.get("https://login.windows.net/{}.onmicrosoft.com/.well-known/openid-configuration".format(name))
        return r.json()["token_endpoint"].split("/")[3]
    except Exception:
        return None


def get_credentials_path() -> str:
    " Get the path of the credentials file "
    if ENV_CREDENTIALS in os.environ:
        return os.environ[ENV_CREDENTIALS]
    else:
        return os.path.join(os.path.expanduser(os.environ.get(ENV_HOME) or HOME), CREDENTIALS)


def load_credentials(
    tenant: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Tuple[str, str, str]:
    client_id = client_id or os.environ.get(ENV_CLIENT_ID)
    client_secret = client_secret or os.environ.get(ENV_CLIENT_SECRET)
    tenant_id = tenant_id or os.environ.get(ENV_TENANT_ID)
    if client_id and client_secret:
        if not tenant_id:
            tenant_id = get_tenant_id(tenant)
        return (client_id, client_secret, tenant_id)
    credentials = get_credentials_path()
    config = configparser.ConfigParser()
    config.read(credentials)
    section = tenant
    if section not in config:
        section = "default"
    if section not in config:
        raise ArgumentParserError("Add [{}] section to {} or specify client_id and client_secret".format(tenant, credentials))
    client_id = config[section]["client_id"]
    client_secret = config[section]["client_secret"]
    tenant_id = config[section]["tenant_id"] or get_tenant_id(tenant)
    return (client_id, client_secret, tenant_id)


def get_account(tenant: str, client_id: str, client_secret: str, tenant_id: str, interactive: bool = False) -> Account:
    " Get O365 Account "
    credentials = (client_id, client_secret)
    token_backend = FileSystemTokenBackend(
        os.path.expanduser(os.environ.get(ENV_HOME) or HOME),
        token_filename=tenant_id + ".json",
    )
    account = Account(
        credentials,
        auth_flow_type="authorization",
        tenant_id=tenant_id,
        token_backend=token_backend,
    )
    if not account.is_authenticated:
        if account.con.auth_flow_type in ("authorization", "public") and not interactive:
            raise Exception("Please run 'spo configure' to authenticate")
        if account.authenticate(scopes=O365_SCOPES):
            print("Authenticated!")
    return account


def split_url(url: str) -> Tuple[str, str, str]:
    " Slit a Sharepoint url into tenant, site name and path) "
    # url = 'https://tenant.sharepoint.com/sites/site_name/path'
    p = urlparse(url)
    tenant = p.netloc
    site_name = p.path.split("/")[2]
    path = "/".join(p.path.split("/")[3:])
    return (tenant, site_name, path)


def is_remote(url_or_path: str) -> bool:
    " Check if a string is an url or a local path "
    return url_or_path.startswith("https://")


def is_office365_sharepoint(url: str) -> bool:
    return bool(RE_SHAREPOINT_COM.match(url))


def get_sharepoint_site(tenant: str, site_name: str, options: Optional[argparse.Namespace] = None) -> Site:
    " Get Sharepoint site "
    client_id, client_secret, tenant_id = load_credentials(
        tenant,
        options.client_id if options is not None else None,
        options.client_secret if options is not None else None,
    )
    account = get_account(tenant, client_id, client_secret, tenant_id)
    return account.sharepoint().get_site(tenant, "/sites/" + site_name)


def get_folder(site: Site, path: str) -> Folder:
    " Get site folder by path "
    parts = [x for x in path.split("/") if x]
    folder = RootFolder(site)
    for part in parts:
        parent = folder
        folder = None
        for item in parent.get_items():
            if item.is_folder and part == item.name:
                folder = item
                break
        if folder is None:
            if isinstance(parent, RootFolder):  # map any name to root folder "Shared Documents", ugly :(
                folder = site.get_default_document_library().get_root_folder()
            else:
                raise FileNotFoundError("{} does not exist".format(path))
    return folder


def filter_folder_files(
    folder: Folder,
    options: argparse.Namespace,
    pattern: Optional[str] = None,
    include_folders: bool = False,
) -> List[DriveItem]:
    " Filter files and folders by pattern and time "
    result: List[DriveItem] = []
    for f in folder.get_items():
        if not pattern or fnmatch.fnmatch(f.name, pattern):
            if not include_folders and f.is_folder:
                continue
            if options.mtime:
                m = (options.mtime_now - f.modified).days
                if not options.mtime_check(m):
                    continue
            result.append(f)
    return result


class RootFolder(DriveItem):
    def __init__(self, site: Site) -> None:
        self.site = site

    def get_items(self, limit=None, *, query=None, order_by=None, batch=None):
        result: List[Folder] = []
        for drive in self.site.site_storage.get_drives():
            folder: Folder = drive.get_root_folder()
            folder.name = drive.name
            result.append(folder)
        return result
