# Templating

Dotdrop leverages the power of [Jinja2](https://palletsprojects.com/p/jinja/) to handle the
templating of dotfiles. See [the Jinja2 templates docs](https://jinja.palletsprojects.com/en/2.11.x/templates/)
or the below sections for more information on how to template your dotfiles.

## Templating or not templating

The dotfile config entry [template](../config/config-dotfiles.md#dotfiles-block)
and the global config entry [template_dotfile_default](../config/config-config.md)
allow to control whether a dotfile is processed by the templating engine.

Obviously, if the dotfile uses template directives, it needs to be templated. However, if it
is not, disabling templating will speed up its installation (since it won't have to be
processed by the engine).

For dotfiles being symlinked (`absolute`, `relative` or `link_children`), see
[the dedicated doc](../howto/symlink-dotfiles.md#templating-symlinked-dotfiles).

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