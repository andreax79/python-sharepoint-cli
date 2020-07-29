#!/usr/bin/env python

import sys
import re
import hashlib
import os
import os.path
import tempfile
from lxml import etree
from io import StringIO
from typing import Any
import requests
from encrypted_cookiejar import EncryptedCookieJar

__all__ = [
    'SSOAuth',
    'LoginException'
]

COUNTRY = 'US'
LANG = 'en-US'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': '{lang},en;q=0.5'.format(lang=LANG),
    'Accept-Encoding': 'gzip, deflate, br',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}


class LoginException(Exception):
    pass


class SSOAuth(object):

    def __init__(self, share_point_site: str, username: str, password: str, verbose: bool = False) -> None:
        self.share_point_site = share_point_site.rstrip('/')
        self.verbose = verbose
        self.username = username
        self.password = password
        # Prepare session
        self._session = requests.Session()
        self._session.cookies = EncryptedCookieJar(self._cookiejar_cache_path())
        self._session.headers.update(HEADERS)

    def _debug(self, *args: Any, **kargs: Any) -> None:
        if self.verbose:
            print(*args, file=sys.stderr, **kargs)

    def _cookiejar_cache_path(self) -> str:
        # Cookie Jar cache
        h = hashlib.sha256()
        h.update('{}|{}|{}'.format(self.username, self.password, self.share_point_site).encode('utf-8'))
        digest = h.hexdigest()
        return os.path.join(tempfile.gettempdir(), 'cookies.{}'.format(digest))

    def get_cookies(self, force_login: bool = False) -> EncryptedCookieJar:
        """
        Grabs the cookies form your Office Sharepoint site
        and uses it as Authentication for the rest of the calls
        """
        if not force_login:
            try:
                self._debug('get cookies from cache')
                self._session.cookies.load(password=self.share_point_site + self.password + self.username)
                return self._session.cookies
            except Exception:
                pass
        self._debug('login')
        self._login()
        self._session.cookies.save(password=self.share_point_site + self.password + self.username)
        return self._session.cookies

    def is_logged(self) -> bool:
        response = self._session.get(self.share_point_site + '/_layouts/15/userphoto.aspx?size=S')
        if response.status_code != 200:
            return False
        return True

    @classmethod
    def _parse_html(cls, content):
        parser = etree.HTMLParser()
        doc = content.decode('utf-8')
        tree = etree.parse(StringIO(doc), parser=parser)
        return tree

    def _login(self) -> None:
        # Get first page
        response = self._session.get(self.share_point_site)
        original_request = re.findall(b'"sCtx":"([^"]*)"', response.content)[0].decode('utf-8')

        # Get identity platform login page
        login_url = 'https://login.microsoftonline.com/common/GetCredentialType?mkt={lang}'.format(lang=LANG)
        login_response = self._session.post(login_url, json={
            "username": self.username,
            "isOtherIdpSupported": True,
            "checkPhones": True,
            "isRemoteNGCSupported": True,
            "isCookieBannerShown": False,
            "isFidoSupported": False,
            "originalRequest": original_request,
            "country": COUNTRY,
            "forceotclogin": False,
            "isExternalFederationDisallowed": False,
            "isRemoteConnectSupported": False,
            "federationFlags": 0,
            "isSignup": False,
            "flowToken": self._session.cookies['buid'],
            "isAccessPassSupported": True
        })

        # Post username/password into the user's teneant sign-in page
        try:
            federated_login_url = login_response.json()['Credentials']['FederationRedirectUrl']
            federated_login_response = self._session.get(federated_login_url)
            federated_login_response = self._session.post(federated_login_url, data={
                "UserName": self.username,
                "Password": self.password,
                "AuthMethod": "FormsAuthentication",
            })
        except KeyError:
            raise LoginException('Teneant not found')

        # Post response to identity platform
        tree = self._parse_html(federated_login_response.content)
        login_microsoftonline_url = tree.xpath('//form')[0].get('action')
        login_data = dict((x.get('name'), x.get('value')) for x in tree.xpath("//input") if x.get('name'))
        if not login_microsoftonline_url or not login_microsoftonline_url.startswith('http') or not login_data:
            raise LoginException('Invalid login')
        login_microsoftonline_response = self._session.post(login_microsoftonline_url, data=login_data)
        assert(login_microsoftonline_response)

        # SPO Auth
        site_response = self._session.get(self.share_point_site)
        tree = self._parse_html(site_response.content)
        url2 = tree.xpath('//form')[0].get('action')
        data2 = dict((x.get('name'), x.get('value')) for x in tree.xpath("//input") if x.get('name'))
        site_response2 = self._session.post(url2, data=data2)
        assert(site_response2)
        # cookies: FedAuth, rtFa
