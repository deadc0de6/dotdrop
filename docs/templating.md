# Templating

Dotdrop leverages the power of [Jinja2](https://palletsprojects.com/p/jinja/) to handle the
templating of dotfiles. See [the Jinja2 templates docs](https://jinja.palletsprojects.com/en/2.11.x/templates/)
or the below sections for more information on how to template your dotfiles.

## Templating or not templating

The dotfile config entry [template](config-dotfiles.md#dotfiles-block)
and the global config entry [template_dotfile_default](config-config.md)
allow to control whether a dotfile is processed by the templating engine.

Obviously, if the dotfile uses template directives, it needs to be templated. However, if it
is not, disabling templating will speed up its installation (since it won't have to be
processed by the engine).

For dotfiles being symlinked (`absolute`, `relative` or `link_children`), see
[the dedicated doc](howto/symlink-dotfiles.md#templating-symlinked-dotfiles).

## Delimiters

Dotdrop uses different delimiters than
[Jinja2](https://palletsprojects.com/p/jinja/)'s defaults:

* Block/statement start = `{%@@`
* Block/statement end = `@@%}`
* Variable/expression start = `{{@@`
* Variable/expression end = `@@}}`
* Comment start = `{#@@`
* Comment end = `@@#}`

More info in [Jinja2 templating docs](https://jinja.palletsprojects.com/en/2.11.x/templates/?highlight=delimiter)

## Template variables

The following variables are available in templates:

* `{{@@ profile @@}}` contains the profile provided to dotdrop.
* `{{@@ env['MY_VAR'] @@}}` contains environment variables (see [Environment variables](#environment-variables)).
* `{{@@ header() @@}}` contains the dotdrop header (see [Dotdrop header](#dotdrop-header)).
* `{{@@ _dotdrop_dotpath @@}}` contains the [dotpath](config-config.md) absolute path.
* `{{@@ _dotdrop_cfgpath @@}}` contains the absolute path to the [config file](config-file.md).
* `{{@@ _dotdrop_workdir @@}}` contains the [workdir](config-config.md) absolute path.
* The [enriched variables](#variables-enrichment)
* Dotfile specific variables (see [Dotfile variables](#dotfile-variables))
* All defined config variables (see [Variables](config-file.md#variables))
* All defined config interpreted variables (see [Interpreted variables](config-dynvars.md#dynvariables-entry))

## Variables enrichment

The below variables are added to the available variables within templates. If the variable
is already set by the user (through the config file for example), it will not be overwritten.

* `os`: will contain the OS name as provided by <https://docs.python.org/3/library/platform.html#platform.system>
* `release`: will contain the OS release version as provided by <https://docs.python.org/3/library/platform.html#platform.release>
* `distro_id`: will contain the distribution ID as provided by <https://distro.readthedocs.io/en/latest/#distro.id>
* `distro_version`: will contain the distribution version as provided by <https://distro.readthedocs.io/en/latest/#distro.version>
* `distro_like`: will contain a space-separated list of distro IDs that are closely related to the current OS distro as provided by <https://distro.readthedocs.io/en/latest/#distro.like>

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
It is recommended to use `variables` (see [config variables](config-file.md#variables))
instead of environment variables unless these contain sensitive information that
shouldn't be versioned in Git (see [handle secrets doc](howto/sensitive-dotfiles.md)).

## Template methods

Besides [Jinja2 global functions](https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions),
the following methods can be used within templates:

* `exists(path)`: returns true when path exists
```
{%@@ if exists('/dev/null') @@%}
it does exist
{%@@ endif @@%}
```

* `exists_in_path(name, path=None)`: returns true when executable exists in `$PATH`
```
{%@@ if exists_in_path('exa') @@%}
alias ls='exa --git --color=always'
{%@@ endif @@%}
```

* `basename(path)`: returns the `basename` of the path argument
```
{%@@ set dotfile_filename = basename( _dotfile_abs_dst ) @@%}
dotfile dst filename: {{@@ dotfile_filename @@}}
```

* `dirname(path)`: returns the `dirname` of the path argument
```
{%@@ set dotfile_dirname = dirname( _dotfile_abs_dst ) @@%}
dotfile dst dirname: {{@@ dotfile_dirname @@}}
```

Custom user-defined functions can be loaded with the help of the
config entry `func_file`.

Example:

The config file:
```yaml
config:
  func_file:
  - /tmp/myfuncs_file.py
```

The python function under `/tmp/myfuncs_file.py`:
```python
def myfunc(arg):
  return not arg
```

The dotfile content:
```
{%@@ if myfunc(False) @@%}
this should exist
{%@@ endif @@%}
```

## Template filters

Besides [Jinja2 builtin filters](https://jinja.palletsprojects.com/en/2.11.x/templates/#builtin-filters),
custom user-defined filter functions can be loaded using the config entry `filter_file`:

Example:

The config file:
```yaml
config:
  filter_file:
  - /tmp/myfilter_file.py
```

The python filter under `/tmp/myfilter_file.py`:
```python
def myfilter(arg1):
  return str(int(arg1) - 10)
```

The dotfile content:
```
{{@@ "13" | myfilter() @@}}
```

For more information on how to create filters,
see [the Jinja2 official docs](https://jinja.palletsprojects.com/en/2.11.x/api/#writing-filters).

## Importing macros

Macros must be imported `with context` in order to have access to the variables:
```
{%@@ from 'macro_file' import macro with context @@%}
```

For more information, see the [dedicated Jinja2 docs](https://jinja.palletsprojects.com/en/2.11.x/templates/#macros).

## Dotdrop header

Dotdrop is able to insert a header in the generated dotfiles. This allows
to remind anyone opening the file for editing that this file is managed by dotdrop.

Here's what it looks like:
```none
This dotfile is managed using dotdrop
```

The header can be automatically added with:
```none
{{@@ header() @@}}
```

Properly commenting the header in templates is the responsibility of the user,
as [Jinja2](https://palletsprojects.com/p/jinja/) has no way of knowing what is the proper char(s) used for comments.
Either prepend the directive with the commenting char(s) used in the dotfile
(for example `# {{@@ header() @@}}`) or provide it as an argument `{{@@ header('# ') @@}}`.
The results are equivalent.

## Debugging templates

To debug the result of a template, one can install the dotfiles to a temporary
directory with the `install` command and the `-t` switch:
```bash
$ dotdrop install -t
Installed to tmp /tmp/dotdrop-6ajz7565
```
