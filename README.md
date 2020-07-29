Installation
------------

```console
$ pip install sharepointcli
```

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
SharePoint domain (e.g. example.sharepoint.com): example.sharepoint.com
Username: test@example.com
Password: *****
```

The credentials take precedence in the following order:

1. Command line options
2. Environment variables
3. Credentials file

#### Command line options

You can use the following command line options to override the default configuration settings.

* **--username <string>**

  Specifies the username.

* **--password <string>**

  Specifies the password associated with the username.

#### Environment variables

Environment variables provide another way to specify credentials, and can be
useful for scripting.
If you specify an option by using a parameter on the command line, it
overrides any value from the environment variables or the configuration file.

The CLI supports the following environment variables:

* **SPO_CREDENTIALS_FILE**

  Specifies the location of the file that the CLI to store credentials.
  The default path is ~/.spo/credentials.

* **SPO_USERNAME**

  Specifies the username.

* **SPO_PASSWORD**

  Specifies the password associated with the username.

#### Credentials file

The CLI stores sensitive credential information in a file named credentials in a directory named `.spo` in your home directory.
For example, the file generated with `spo configure` looks similar to the following:

```ini
[example.sharepoint.com]
username = user@example.com
password = secret
```

Usage
-----


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
$ spo ls <SharePointUrl>
```

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
$ spo rm <SharePointUrl>
```

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
SharePoint domain (e.g. example.sharepoint.com): example.sharepoint.com
Username: test@example.com
Password: *****
$ expot SITE='https://example.sharepoint.com/sites/example/Shared documents/test folder'
$ make test
```

License
-------

This project is licensed under the MIT license.

Links
-----

* [Project home page (GitHub)](https://github.com/andreax79/python-sharepoint-cli)
* [SharePlum](https://github.com/jasonrollins/shareplum)
* [Office 365 CLI](https://github.com/pnp/office365-cli)

