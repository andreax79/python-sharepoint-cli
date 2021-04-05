#!/usr/bin/env python

import re

__all__ = [
    "ENV_CREDENTIALS",
    "ENV_CLIENT_ID",
    "ENV_CLIENT_SECRET",
    "ENV_HOME",
    "ENV_TENANT_ID",
    "CREDENTIALS",
    "HOME",
    "EXIT_SUCCESS",
    "EXIT_FAILURE",
    "EXIT_PARSER_ERROR",
    "RE_SHAREPOINT_COM",
    "ISO_FMT",
    "O365_SCOPES",
    "ArgumentParserError",
    "ArgumentException",
]

ENV_CREDENTIALS = "SPO_CREDENTIALS_FILE"
ENV_CLIENT_ID = "SPO_CLIENT_ID"
ENV_CLIENT_SECRET = "SPO_CLIENT_SECRET"
ENV_HOME = "SPO_HOME"
ENV_TENANT_ID = "SPO_TENANT_ID"
CREDENTIALS = "credentials"
HOME = "~/.spo"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_PARSER_ERROR = 2
RE_SHAREPOINT_COM = re.compile("^https://[^\\.]+.sharepoint.com/.*")
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
O365_SCOPES = ["basic", "sharepoint_dl"]


class ArgumentParserError(Exception):
    pass


class ArgumentException(Exception):
    pass
