Installation
------------

```console
$ pip install sharepointcli
```

Configuration
-------------

To allow authentication you first need to register your application.
For steps on how to configure the app in the Azure portal, see [Register your app](https://docs.microsoft.com/en-us/graph/auth-register-app-v2)

For general use, the `spo configure` command is the fastest way to set up SharePoint CLI.
When you enter this command, the CLI prompts you for the following configurations:

* SharePoint domain
* Application (client) ID
* Application (client) secret

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

Usage
-----


### authenticate

Performs the OAuth authentication flow using the console.

#### Usage

```console
$ spo authenticate [domain]
```



### configure

Configures credentials.

#### Usage

```console
$ spo configure [domain]
```



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



### help

Displays commands help.

#### Usage

```console
$ spo help [topic]
```



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



### mkdir

Creates folder.

#### Usage

```console
$ spo mkdir <SharePointUrl>
```



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



### rmdir

Deletes folder.

#### Usage

```console
$ spo rmdir <SharePointUrl>
```



### version

Prints the version number.

#### Usage

```console
$ spo version
```


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

Register your app for dummies
-----------------------------

1. Sign in to the [Azure portal](https://portal.azure.com/).
1. Select Azure Active Directory.
1. Under Manage, select App registrations > New registration.
1. Enter a display name for the authentication and click the Register button.
1. Copy the Application (client) ID and use it as Client Id for the configuration.
1. Under Manage, select Authentication > Add a platform.
1. Select Web as platform.
1. Set Redirect URI to https://login.microsoftonline.com/common/oauth2/nativeclient
1. Click on the Configure button to complete the platform configuration.
1. Select Certificates & secrets > Client secrets > New client secret.
1. Add a description.
1. Select an expiration for the secret (e.g. 24 months).
1. Click on the Add button.
1. Copy the secret's value for use in configuration as Client Secret. **The secret value is never displayed again after you leave this page.**

```console
$ spo configure
SharePoint domain (e.g. example.sharepoint.com): <-- your SharePoint domain
Tenant Id: db3fe96d-1b57-4119-a5fd-bd139021158d <-- automagical
Client Id: <<-- copy the Application (client) ID 
Client Secret: <<-- copy Client Secret
https://login.microsoftonline.com/db3fe96d-1b57-4119-a5fd-bd139021158d/v2.0/authorize?response_type=code&client_id=...
(open the link in your Browser, and authorize the app)
Paste the authenticated url here:
(paste the Browser's URL, i.e. https://login.microsoftonline.com/common/oauth2/nativeclient?code=0...)
Authentication Flow Completed. Oauth Access Token Stored. You can now use the API.
Authenticated!
```

License
-------

This project is licensed under the MIT license.

Links
-----

* [Project home page (GitHub)](https://github.com/andreax79/python-sharepoint-cli)
* [O365](https://github.com/O365/python-o365)
* [SharePlum](https://github.com/jasonrollins/shareplum)
* [Office 365 CLI](https://github.com/pnp/office365-cli)

