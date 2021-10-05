# Config

## Location

The config file used by dotdrop is
[config.yaml](https://github.com/deadc0de6/dotdrop/blob/master/config.yaml).

Unless specified otherwise, dotdrop will look in the following places for its config file
and use the first one found:

* Current/working directory or the directory where [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh) is located if used
* `${XDG_CONFIG_HOME}/dotdrop/`
* `~/.config/dotdrop/`
* `/etc/xdg/dotdrop/`
* `/etc/dotdrop/`

You can force dotdrop to use a different file either by using the `-c`/`--cfg` CLI switch
or by defining the `DOTDROP_CONFIG` environment variable.

## Variables

Multiple variables can be used within the config file to
parametrize the following elements of the config:

* Dotfile `src` and `dst` paths (See [Dynamic dotfile paths](config-details.md#dynamic-dotfile-paths))
* External path specifications
  * `import_variables`
  * `import_actions`
  * `import_configs`
  * Profiles' `import`
  * Profiles' `include`

`actions` and `transformations` also support the use of variables,
but those are resolved when the action/transformation is executed
(See [Dynamic actions](config-details.md#dynamic-actions),
[Dynamic transformations](config-details.md#dynamic-transformations) and [Templating](templating.md)).

The following variables are available in the config files:

* [Variables defined in the config](config-details.md#entry-variables)
* [Interpreted variables defined in the config](config-details.md#entry-dynvariables)
* [User variables defined in the config](config-details.md#entry-uservariables)
* [Profile variables defined in the config](config-details.md#entry-profile-variables)
* Environment variables: `{{@@ env['MY_VAR'] @@}}`
* Dotdrop header: `{{@@ header() @@}}` (see [Dotdrop header](templating.md#dotdrop-header))

as well as all [template methods](templating.md#template-methods) and [template filters](templating.md#template-filters).

Note that all variables available in the config file will
then be available during [templating](templating.md).

Here are some rules on the use of variables in configs:

* [Interpreted variables](config-details.md#entry-dynvariables) are executed in their own file.
* [Interpreted variables](config-details.md#entry-dynvariables) and
  [variables](config-details.md#entry-variables) are templated before
  [interpreted variables](config-details.md#entry-dynvariables) are executed.
* Config files do not have access to variables defined above in the import tree.
* `dynvariables` take precedence over `variables`.
* Profile `(dyn)variables` take precedence over any other `(dyn)variables`.
* Profile `(dyn)variables` take precedence over profile's included `(dyn)variables`.
* External/imported `(dyn)variables` take precedence over
  `(dyn)variables` defined inside the main config file.
* [User variables](config-details.md#entry-uservariables) are ignored if
  any other variable with the same key is defined.

## Permissions

Dotdrop allows you to control the permissions applied to a dotfile using the
config dotfile entry [chmod](config-format.md#dotfiles-entry).
A [chmod](config-format.md#dotfiles-entry) entry on a directory
is applied to the directory only, not recursively.

For example:
```yaml
dotfiles:
  f_file:
    src: file
    dst: ~/file
    chmod: 644
  f_dir:
    src: dir
    dst: ~/dir
    chmod: 744
```

On `import`, the following rules are applied:

* If the `-m`/`--preserve-mode` switch is provided, the imported file's permissions are
  stored in a `chmod` entry
* If the imported file's permissions differ from the umask, then the permissions are automatically
  stored in the `chmod` entry.
* Otherwise, no `chmod` entry is added

On `install`, the following rules are applied:

* If `chmod` is specified in the dotfile, it will be applied to the installed dotfile.
* Otherwise, the permissions of the dotfile in the `dotpath` are applied.
* If the global setting `force_chmod` is set to true, dotdrop will not ask
  for confirmation to apply permissions.

On `update`:

* If the permissions of the file in the filesystem differ from the dotfile in the `dotpath`,
  then the dotfile entry `chmod` is added/updated accordingly.


## Symlinking dotfiles

Dotdrop is able to install dotfiles in three different ways,
which are controlled by the `link` config attribute of each dotfile:

* `link: nolink`: The dotfile (file or directory) is copied to its destination
* `link: link`: The dotfile (file or directory) is symlinked to its destination
* `link: link_children`: The files/directories found under the dotfile (directory) are symlinked to their destination

For more, see [this how-to](howto/symlink-dotfiles.md).

## Template config entries

Some entries in the config can use the templating feature (See [templating](templating.md)):

Entry    | Related doc
-------- | -------------
dotfile src | [Dynamic dotfile paths](config-details.md#dynamic-dotfile-paths)
dotfile dst | [Dynamic dotfile paths](config-details.md#dynamic-dotfile-paths)
dotfile link | [Dynamic dotfile link value](config-details.md#dynamic-dotfile-link-value)
variables | [variables](config-details.md#variables-entry)
dynvariables | [dynvariables](config-details.md#dynvariables-entry)
actions | [dynamic actions](config-details.md#dynamic-actions)
profile include | [Profile include](config-details.md#profile-include-entry)
profile import | [Profile import](config-details.md#profile-import-entry)
import_variables | [import_variables](config-details.md#import_variables-entry)
import_actions | [import_actions](config-details.md#import_actions-entry)
import_configs | [import_configs](config-details.md#import_configs-entry)

## All dotfiles for a profile

To use all defined dotfiles in a profile, simply use
the keyword `ALL`.

For example:
```yaml
dotfiles:
  f_xinitrc:
    dst: ~/.xinitrc
    src: xinitrc
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
profiles:
  host1:
    dotfiles:
    - ALL
  host2:
    dotfiles:
    - f_vimrc
```

## Ignore patterns

It is possible to ignore specific patterns when using dotdrop.

* For [install](usage.md#install-dotfiles):
    * Using `instignore` in the config file
* For [import](usage.md#import-dotfiles):
    * Using `impignore` in the config file
* For [compare](usage.md#compare-dotfiles):
    * Using `cmpignore` in the config file
    * Using the command line switch `-i`/`--ignore`
* For [update](usage.md#update-dotfiles):
    * Using `upignore` in the config file
    * Using the command line switch `-i`/`--ignore`

The ignore pattern must follow Unix shell-style wildcards, like, for example `*/path/to/file`.
Make sure to quote these when using wildcards in the config file.

Patterns used for a specific dotfile can be specified relative to the dotfile destination (`dst`).

Similar to a `.gitignore` file, you can prefix ignore patterns with an exclamation point (`!`).
This so-called "negative ignore pattern" will cause any files that match that pattern to __not__ be ignored,
provided they *would have* been ignored by an earlier ignore pattern (dotdrop will warn if that is not the
case). This feature allows you to, for example, ignore all files within a certain directory, except for one
particular one (See example below).

```yaml
config:
  cmpignore:
  - '*/README.md'
  upignore:
  - '*/README.md'
  instignore:
  - '*/README.md'
...
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    upignore:
    - "*/undo-dir"
    - "*/plugged"
...
```

To completely ignore comparison of a specific dotfile:
```yaml
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    cmpignore:
    - "*"
```

To ignore a specific directory when updating:
```yaml
dotfiles:
  d_colorpicker:
    src: config/some_directory
    dst: ~/.config/some_directory
    upignore:
      - '*sub_directory_to_ignore'
```

To ignore a specific file `testfile` and directory `testdir` when importing:
```yaml
config:
  impignore:
  - "*/testfile"
  - "testdir"
...
```

To ignore all files within a certain directory relative to `dst`, except one called `custom_plugin.zsh`:
```yaml
dotfiles:
  d_zsh:
    src: zsh
    dst: ~/.config/zsh
    upignore:
    - "plugins/*"
    - "!plugins/custom_plugin.zsh"
```
