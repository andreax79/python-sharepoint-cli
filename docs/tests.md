Tests
-----

To run the unit tests:

* create the ~/.spo/credentials credentials file
* export your SharePoint test site url as environment variable 'SITE'

```console
$ spo configure
SharePoint domain (e.g. example.sharepoint.com): example.sharepoint.com
Username: test@example.com
Password: *****
$ expot SITE='https://example.sharepoint.com/sites/example/Shared documents/test folder'
$ make test
```

