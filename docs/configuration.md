Configuration
-------------

For general use, the `spo configure` command is the fastest way to set up SharePoint CLI.
When you enter this command, the CLI prompts you for the following configurations:

* SharePoint domain
* Username
* Password

The `spo configure` command stores the credentials in the credentials file.
You can configure configure multiple credentials for different SharePoint domains.
Example:

```console
$ spo configure
SharePoint domain (e.g. example.sharepoint.com):
Tenant Id: db3fe96d-1b57-4119-a5fd-bd139021158d
Client Id: fa3ecc92-5994-475e-a647-1f81931aac43
Client Secret: ~vaXZkx&836mH56FymE6Gx7j$t&JT.-5em
Visit the following url to give consent:
https://login.microsoftonline.com/db3fe96d-1b57-4119-a5fd-bd139021158d/oauth2/v2.0/authorize?response_type=...
Paste the authenticated url here:
https://login.microsoftonline.com/common/oauth2/nativeclient?code=....
Authentication Flow Completed. Oauth Access Token Stored. You can now use the API.
Authenticated!

```

The credentials take precedence in the following order:

1. Command line options
2. Environment variables
3. Credentials file

#### Command line options

You can use the following command line options to override the default configuration settings.

* **--client_id <string>**

  Specifies the Client Id.

* **--client_secret <string>**

  Specifies the Client Secret

* **--tenant_id <string>**

  Specifies the Tenant Id

#### Environment variables

Environment variables provide another way to specify credentials, and can be
useful for scripting.
If you specify an option by using a parameter on the command line, it
overrides any value from the environment variables or the configuration file.

The CLI supports the following environment variables:

* **SPO_HOME**

  Specifies the home directory.
  The default path is "~/.spo".

* **SPO_CREDENTIALS_FILE**

  Specifies the location of the file that the CLI to store credentials.
  The default path is "~/.spo/credentials".

* **SPO_CLIENT_ID**

  Specifies the Client Id.

* **SPO_CLIENT_SECRET**

  Specifies the Client Secret

* **SPO_TENANT_ID**

  Specifies the Tenant Id


#### Credentials file

The CLI stores sensitive credential information in a file named credentials in a directory named `.spo` in your home directory.
For example, the file generated with `spo configure` looks similar to the following:

```ini
[example.sharepoint.com]
client_id = fa3ecc92-5994-475e-a647-1f81931aac43
client_secret = ~vaXZkx&836mH56FymE6Gx7j$t&JT.-5em
tenant_id = db3fe96d-1b57-4119-a5fd-bd139021158d
```

