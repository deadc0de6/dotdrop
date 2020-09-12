# Templating

Dotdrop leverage the power of [jinja2](http://jinja.pocoo.org/) to handle the
templating of dotfiles. See [jinja2 template doc](http://jinja.pocoo.org/docs/2.9/templates/)
or the below sections for more information on how to template your dotfiles.

* [Delimiters](#delimiters)
* [Template variables](#template-variables)
    * [Dotfile variables](#dotfile-variables)
    * [Environment variables](#environment-variables)
    * [Dotdrop header](#dotdrop-header)
* [Available methods](#available-methods)
* [Available filters](#available-filters)
* [Import macros](#import-macros)
* [Ignore empty template](#ignore-empty-template)
* [Include file or template in template](#include-file-or-template-in-template)
* [Debug templates](#debug-templates)

---

# Delimiters

Dotdrop uses different delimiters than
[jinja2](http://jinja.pocoo.org/)'s defaults:

* block/statement start = `{%@@`
* block/statement end = `@@%}`
* variable/expression start = `{{@@`
* variable/expression end = `@@}}`
* comment start = `{#@@`
* comment end = `@@#}`

More info in [jinja2 templating doc](https://jinja.palletsprojects.com/en/2.11.x/templates/?highlight=delimiter)

# Template variables

Following variables are available in templates:

* `{{@@ profile @@}}` contains the profile provided to dotdrop.
* `{{@@ env['MY_VAR'] @@}}` contains environment variables (see [Environment variables](#environment-variables)).
* `{{@@ header() @@}}` contains dotdrop header (see [Dotdrop header](#dotdrop-header)).
* `{{@@ _dotdrop_dotpath @@}}` contains the [dotpath](https://github.com/deadc0de6/dotdrop/wiki/config) absolute path.
* `{{@@ _dotdrop_cfgpath @@}}` contains the absolute path to the [config file](https://github.com/deadc0de6/dotdrop/wiki/config).
* `{{@@ _dotdrop_workdir @@}}` contains the [workdir](https://github.com/deadc0de6/dotdrop/wiki/config) absolute path.
* dotfile specific variables (see [Dotfile variables](#dotfile-variables))
* config variables (see [Variables](config-variables)).
* config interpreted variables (see [Interpreted variables](config-variables)).

# Dotfile variables

When a dotfile is handled by dotdrop, the following variables are added:

* `{{@@ _dotfile_abs_src @@}}` contains the processed dotfile absolute source path.
* `{{@@ _dotfile_abs_dst @@}}` contains the processed dotfile absolute destination path.
* `{{@@ _dotfile_key @@}}` contains the processed dotfile key.
* `{{@@ _dotfile_link @@}}` contains the processed dotfile `link` string value.

Additionally to the above, the following variables are set in each file processed by dotdrop.

* `{{@@ _dotfile_sub_abs_src @@}}` contains the absolute source path of each file when handled by dotdrop.
* `{{@@ _dotfile_sub_abs_dst @@}}` contains the absolute destination path of each file when handled by dotdrop.

For example a directory dotfile (like `~/.ssh`) would process several files
(`~/.ssh/config` and `~/.ssh/authorized_keys` for example). In `~/.ssh/config`:
* `_dotfile_abs_dst` would be `/home/user/.ssh`
* `_dotfile_sub_abs_dst` would be `/home/user/.ssh/config`

# Environment variables

It's possible to access environment variables inside the templates.
```
{{@@ env['MY_VAR'] @@}}
```

This allows for storing host-specific properties and/or secrets in environment variables.
It is recommended to use `variables` (see [Config variables](#config-variables))
instead of environment variables unless these contain sensitive information that
shouldn't be versioned in git.

For example you can have a `.env` file in the directory where your `config.yaml` lies:
```
## Some secrets
pass="verysecurepassword"
```
If this file contains secrets that should not be tracked by git,
put it in your `.gitignore`.

You can then invoke dotdrop with the help of an alias
```bash
# when dotdrop is installed as a submodule
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) ~/dotfiles/dotdrop.sh'

# when dotdrop is installed from pypi or aur
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) /usr/bin/dotdrop --cfg=~/dotfiles/config.yaml'
```

The above aliases load all the variables from `~/dotfiles/.env`
(while omitting lines starting with `#`) before calling dotdrop.

# Dotdrop header

Dotdrop is able to insert a header in the generated dotfiles. This allows
to remind anyone opening the file for editing that this file is managed by dotdrop.

Here's what it looks like:
```
This dotfile is managed using dotdrop
```

The header can be automatically added with:
```
{{@@ header() @@}}
```

Properly commenting the header in templates is the responsibility of the user
as [jinja2](http://jinja.pocoo.org/) has no way of knowing what is the proper char(s) used for comments.
Either prepend the directive with the commenting char(s) used in the dotfile
(for example `# {{@@ header() @@}}`) or provide it as an argument `{{@@ header('# ') @@}}`.
The result is equivalent.

# Available methods

Beside [jinja2 global functions](http://jinja.pocoo.org/docs/2.10/templates/#list-of-global-functions)
the following methods can be used within the templates:

* `exists(path)`: return true when path exists
```
{%@@ if exists('/dev/null') @@%}
it does exist
{%@@ endif @@%}
```

* `exists_in_path(name, path=None)`: return true when executable exists in `$PATH`
```
{%@@ if exists_in_path('exa') @@%}
alias ls='exa --git --color=always'
{%@@ endif @@%}
```

* `basename(path)`: return the `basename` of the path argument
```
{%@@ set dotfile_filename = basename( _dotfile_abs_dst ) @@%}
dotfile dst filename: {{@@ dotfile_filename @@}}
```

* `dirname(path)`: return the `dirname` of the path argument
```
{%@@ set dotfile_dirname = dirname( _dotfile_abs_dst ) @@%}
dotfile dst dirname: {{@@ dotfile_dirname @@}}
```

Custom user-defined functions can be loaded with the help of the
config entry `func_file`.

Example:

```yaml
config:
  func_file:
  - /tmp/myfuncs_file.py
```

`/tmp/myfuncs_file.py`
```python
def myfunc(arg):
  return not arg
```

dotfile content
```
{%@@ if myfunc(False) @@%}
this should exist
{%@@ endif @@%}
```

# Available filters

Beside [jinja2 builtin filters](https://jinja.palletsprojects.com/en/2.10.x/templates/#builtin-filters)
custom user-defined filter functions can be loaded using the config entry `filter_file`:

Example:

```yaml
config:
  filter_file:
  - /tmp/myfilter_file.py
```

`/tmp/myfilter_file.py`
```python
def myfilter(arg1):
  return str(int(arg1) - 10)
```

dotfile content
```
{{@@ "13" | myfilter() @@}}
```

For more information on how to create filters,
see [jinja2 official doc](https://jinja.palletsprojects.com/en/2.10.x/api/#writing-filters).

# Import macros

Macros must be imported `with context` in order to have access to the variables:
```
{%@@ from 'macro_file' import macro with context @@%}
```

For more see the [dedicated jinja2 doc](https://jinja.palletsprojects.com/en/2.11.x/templates/#macros).

# Ignore empty template

It is possible to avoid having an empty rendered template being
deployed by setting the `ignoreempty` entry to *true*. This can be set
globally for all dotfiles or only for specific dotfiles.

For more see the [Config](config).

# Include file or template in template

[Jinja2](http://jinja.pocoo.org/docs/2.10/templates/) provides the ability to include an external file/template from within a template with the directive `include`. See the [related doc](http://jinja.pocoo.org/docs/2.10/templates/#include) for more. The path must be relative to the `dotpath`.

For example:
```yaml
{%@@ include 'colors/black.colors' @@%}
```

Of course, paths could be also dynamically generated using variables.
For example:
```yaml
{%@@ include colors_path + '/black.colors' @@%}
```

# Debug templates

To debug the result of a template, one can install the dotfiles to a temporary
directory with the `install` command and the `-t` switch:
```bash
$ dotdrop install -t
Installed to tmp /tmp/dotdrop-6ajz7565
```
