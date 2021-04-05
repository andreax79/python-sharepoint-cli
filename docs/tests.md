Tests
-----

To run the unit tests:

* create the ~/.spo/credentials credentials file
* export your SharePoint test site url as environment variable 'SITE'

```console
$ spo configure
SharePoint domain (e.g. example.sharepoint.com):
Tenant Id: db3fe96d-1b57-4119-a5fd-bd139021158d
Client Id: fa3ecc92-5994-475e-a647-1f81931aac43
Client Secret: ~vaXZkx&836mH56FymE6Gx7j$t&JT.-5em
$ expot SITE='https://example.sharepoint.com/sites/example/Shared documents/test folder'
$ make test
```

