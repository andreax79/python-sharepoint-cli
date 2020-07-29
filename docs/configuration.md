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

