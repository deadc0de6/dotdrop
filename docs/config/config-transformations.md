# Transformations entry

For examples of transformation uses, see:

* [Handle compressed directories](../howto/store-compressed-directories.md)
* [Handle secrets](../howto/sensitive-dotfiles.md)

**Notes**:

* Any transformation with a key starting with an underscore (`_`) won't be shown in output. This can be useful when working with sensitive data containing passwords, for example.
* Make sure to quote your transformations to avoid bad surprises
* Transformations are executed using the default shell (`$SHELL`)
* To use shell variables in your transformations you need to escape the curly brackets (`${HOME}` becomes `${{HOME}}`)

There are two types of transformations available:

* **Install transformations**: used to transform dotfiles before they are installed ([config](config-config.md) key `trans_install`)
    * Used for commands `install` and `compare`
    * They have two mandatory arguments:
        * **{0}** will be replaced with the dotfile to process
        * **{1}** will be replaced with a temporary file to store the result of the transformation
    * This Happens **before** the dotfile is templated (see [templating](../template/templating.md))

* **Update/Import transformations**: used to transform files before updating/importing a dotfile ([config](config-config.md) key `trans_update`)
    * Used for command `update` and `import`
    * They have two mandatory arguments:
        * **{0}** will be replaced with the file path to update the dotfile with
        * **{1}** will be replaced with a temporary file to store the result of the transformation

A typical use-case for transformations is when dotfiles need to be
stored encrypted or compressed. For more, see [the howto](../howto/howto.md).

Note that transformations cannot be used if the dotfile is to be linked (when `link: absolute|relative|link_children`).

Transformations also support additional positional arguments that must start from 2 (since `{0}` and `{1}` are added automatically). The transformations themselves as well as their arguments can also be templated.

For example:
```yaml
trans_install:
  targ: echo "$(basename {0}); {{@@ _dotfile_key @@}}; {2}; {3}" > {1}
dotfiles:
  f_abc:
    dst: /tmp/abc
    src: abc
    trans_install: targ "{{@@ profile @@}}" lastarg
profiles:
  p1:
    dotfiles:
    - f_abc
```

will result in `abc; f_abc; p1; lastarg`.

## trans_install entry

The **trans_install** entry (optional) contains a transformations mapping (See [transformations](config-transformations.md)).

```yaml
trans_install:
   <trans-key>: <command-to-execute>
```

## trans_update entry

The **trans_update** entry (optional) contains a write transformations mapping (See [transformations](config-transformations.md)).

```yaml
trans_update:
   <trans-key>: <command-to-execute>
```

## Dynamic transformations

As for [dynamic actions](config-actions.md#dynamic-actions), transformations support
the use of variables ([variables and dynvariables](config-file.md#variables)
and [template variables](../template/template-variables.md#template-variables)).

A very dumb example:
```yaml
trans_install:
  r_echo_abs_src: echo "{0}: {{@@ _dotfile_abs_src @@}}" > {1}
  r_echo_var: echo "{0}: {{@@ r_var @@}}" > {1}
trans_update:
  w_echo_key: echo "{0}: {{@@ _dotfile_key @@}}" > {1}
  w_echo_var: echo "{0}: {{@@ w_var @@}}" > {1}
variables:
  r_var: readvar
  w_var: writevar
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans_install: r_echo_abs_src
    trans_update: w_echo_key
  f_def:
    dst: ${tmpd}/def
    src: def
    trans_install: r_echo_var
    trans_update: w_echo_var
```
