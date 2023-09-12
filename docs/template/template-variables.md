# Template variables

## Available variables

The following variables are available in templates:

* `{{@@ profile @@}}` contains the profile provided to dotdrop.
* `{{@@ env['MY_VAR'] @@}}` contains environment variables (see [Environment variables](#environment-variables)).
* `{{@@ header() @@}}` contains the dotdrop header (see [Dotdrop header](templating.md#dotdrop-header)).
* `{{@@ _dotdrop_dotpath @@}}` contains the [dotpath](../config/config-config.md) absolute path.
* `{{@@ _dotdrop_cfgpath @@}}` contains the [config file](../config/config-file.md) absolute path.
* `{{@@ _dotdrop_workdir @@}}` contains the [workdir](../config/config-config.md) absolute path.
* All variables defined [in the config](../config/config-file.md#variables)
* Dotfile specific variables (see [Dotfile variables](#dotfile-variables))

## Enriched variables

The below variables are added to the available variables within templates. If the variable
is already set by the user (through the config file for example) it will not be overwritten.

* `{{@@ os @@}}` will contain the OS name as provided by <https://docs.python.org/3/library/platform.html#platform.system>
* `{{@@ release @@}}` will contain the OS release version as provided by <https://docs.python.org/3/library/platform.html#platform.release>
* `{{@@ distro_id @@}}` will contain the distribution ID as provided by <https://distro.readthedocs.io/en/latest/#distro.id>
* `{{@@ distro_version @@}}` will contain the distribution version as provided by <https://distro.readthedocs.io/en/latest/#distro.version>
* `{{@@ distro_like @@}}` will contain a space-separated list of distro IDs that are closely related to the current OS distro as provided by <https://distro.readthedocs.io/en/latest/#distro.like>

## Dotfile variables

When a dotfile is handled by dotdrop, the following variables are also available for templating:

* `{{@@ _dotfile_abs_src @@}}` contains the processed dotfile absolute source path.
* `{{@@ _dotfile_abs_dst @@}}` contains the processed dotfile absolute destination path.
* `{{@@ _dotfile_key @@}}` contains the processed dotfile key.
* `{{@@ _dotfile_link @@}}` contains the processed dotfile `link` string value.

In addition to the above, the following variables are set in each file processed by dotdrop:

* `{{@@ _dotfile_sub_abs_src @@}}` contains the absolute source path of each file when handled by dotdrop.
* `{{@@ _dotfile_sub_abs_dst @@}}` contains the absolute destination path of each file when handled by dotdrop.

For example, a directory dotfile (like `~/.ssh`) would process several files
(`~/.ssh/config` and `~/.ssh/authorized_keys`, for example). In `~/.ssh/config`:

* `_dotfile_abs_dst` would be `/home/user/.ssh`
* `_dotfile_sub_abs_dst` would be `/home/user/.ssh/config`

## Environment variables

It's possible to access environment variables inside the templates:
```
{{@@ env['MY_VAR'] @@}}
```

This allows for storing host-specific properties and/or secrets in environment variables.
It is recommended to use `variables` (see [config variables](../config/config-file.md#variables))
instead of environment variables unless these contain sensitive information that
shouldn't be versioned in Git (see [handle secrets doc](../howto/sensitive-dotfiles.md)).

## Variables dictionary

All variables are also available through the dictionary `_vars`
```
{%@@ for key in _vars @@%}
key:{{@@ key @@}} - value:{{@@ _vars[key] @@}}
{%@@ endfor @@%}
```