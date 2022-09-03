# Template methods

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