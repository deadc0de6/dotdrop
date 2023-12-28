# Config file

## Location

The default config file used by dotdrop is
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

* Dotfile `src` and `dst` paths (See [Dynamic dotfile paths](config-dotfiles.md#dynamic-dotfile-paths))
* External paths
    * `import_variables`
    * `import_actions`
    * `import_configs`
    * Profiles' `import`
    * Profiles' `include`
* `actions`
* `transformations`

Note that variables used in `actions` and `transformations`
are resolved when the action/transformation is executed
(See [Dynamic actions](config-actions.md#dynamic-actions),
[Dynamic transformations](config-transformations.md#dynamic-transformations) and [Templating](../template/templating.md)).

The following variables are available in the config files:

* [Variables defined in the config](config-variables.md)
* [Interpreted variables defined in the config](config-dynvars.md)
* [User variables defined in the config](config-variables.md)
* [Profile variables defined in the config](config-profiles.md#profile-variables-entry)
* Environment variables: `{{@@ env['MY_VAR'] @@}}`
* The [enriched variables](../template/template-variables.md#enriched-variables)
* Dotdrop header: `{{@@ header() @@}}` (see [Dotdrop header](../template/templating.md#dotdrop-header))

as well as all [template methods](../template/template-methods.md) and [template filters](../template/template-filters.md).

Note that all variables available in the config file will
then be available during [templating](../template/templating.md).

Here are some rules on the use of variables in configs:

* [dynvariables](config-dynvars.md) are executed in their own file.
* [dynvariables](config-dynvars.md) and
  [variables](config-variables.md) are templated before
  [dynvariables](config-dynvars.md) are executed.
* Config files do not have access to variables defined above in the import tree
  (variables defined in importing config are not seen by the imported config file,
  where *import* can be any of `import_configs`, `import_variables`, `import_actions`,
  profile's `import` and profile's `include`)
* [dynvariables](config-dynvars.md) take precedence over [variables](config-variables.md).
* Profile `(dyn)variables` take precedence over any other `(dyn)variables`.
* Profile `(dyn)variables` take precedence over profile's included `(dyn)variables`.
* External/imported `(dyn)variables` take precedence over
  `(dyn)variables` defined inside the main config file.
* [uservariables](config-uservars.md) are ignored if
  any other variable with the same key is defined.

For more see the [CONTRIBUTING doc](/CONTRIBUTING.md).

## Permissions

Dotdrop allows to control the permissions applied to a dotfile using the
config dotfile entry [chmod](config-dotfiles.md).
A [chmod](config-dotfiles.md) entry on a directory
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
  f_preserve:
    src: pfile
    dst: ~/pfile
    chmod: preserve
```

The `chmod` value defines the file permissions in octal notation to apply to the dotfile. If undefined
new files will get the system default permissions (see `umask`, `777-<umask>` for directories and
`666-<umask>` for files).

The special keyword `preserve` allows to ensure that if the dotfiles already exists
on the filesystem, its permission is not altered during `install` and the `chmod` config value won't
be changed during `update`.

On `import`, the following rules are applied:

* If the `-m`/`--preserve-mode` switch is provided or the config option
  `chmod_on_import` is true, the imported file's permissions are
  stored in a `chmod` entry
* If the imported file's permissions differ from the umask, then the permissions are automatically
  stored in the `chmod` entry.
* Otherwise, no `chmod` entry is added

On `install`, the following rules are applied:

* If `chmod` is specified in the dotfile, it will be applied to the installed dotfile.
* Otherwise, the permissions of the dotfile in the `dotpath` are applied.
* If the global setting `force_chmod` is set to true, dotdrop will not ask
  for confirmation to apply permissions.
* If `chmod` is `preserve` and the destination exists with a different permission set
  than system default, then it is not altered

On `update`, the following rule is applied:

* If the permissions of the file in the filesystem differ from the dotfile in the `dotpath`,
  then the dotfile entry `chmod` is added/updated accordingly (unless `chmod` value is `preserve`)

## Symlinking dotfiles

see the [symlink dotfiles documentation](../howto/symlink-dotfiles.md).

## Template config entries

Some entries in the config can be templated (See [templating](../template/templating.md)):

Entry    | Related doc
-------- | -------------
dotpath | [config entries](config-config.md#config-block)
dotfile src | [dynamic dotfile paths](config-dotfiles.md#dynamic-dotfile-paths)
dotfile dst | [dynamic dotfile paths](config-dotfiles.md#dynamic-dotfile-paths)
dotfile link | [dynamic dotfile link value](config-dotfiles.md#dynamic-dotfile-link-value)
variables | [variables](config-variables.md)
dynvariables | [dynvariables](config-dynvars.md)
actions | [dynamic actions](config-dynvars.md)
profile include | [Profile include](config-profiles.md#profile-include-entry)
profile import | [Profile import](config-profiles.md#profile-import-entry)
import_variables | [import_variables](config-config.md#import_variables-entry)
import_actions | [import_actions](config-config.md#import_actions-entry)
import_configs | [import_configs](config-config.md#import_configs-entry)

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

* For [install](../usage.md#install-dotfiles):
    * Using config block [instignore](config-config.md)
    * Using dotfiles block [instignore](config-dotfiles.md)
* For [import](../usage.md#import-dotfiles):
    * Using config block [impignore](config-config.md)
* For [compare](../usage.md#compare-dotfiles):
    * Using config block [cmpignore](config-config.md)
    * Using dotfiles block [cmpignore](config-dotfiles.md)
    * Using the command line switch `-i`/`--ignore`
* For [update](../usage.md#update-dotfiles):
    * Using config block [upignore](config-config.md)
    * Using dotfiles block [upignore](config-dotfiles.md)
    * Using the command line switch `-i`/`--ignore`

The ignore pattern must follow Unix shell-style wildcards, like for example `*/path/to/file` for files and
`*/path/to/directory/*` for directories.
Make sure to quote these when using wildcards in the config file.

```yaml
config:
  cmpignore:
  - '*/README.md'
  upignore:
  - '*/README.md'
  instignore:
  - '*/README.md'
  impignore:
  - '*/README.md'
...
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    upignore:
    - '*/undo-dir/*'
    - '*/plugged/*'
    instignore:
    - '*/internal/*'
    cmpignore:
    - '*/ignore-me'
...
```

Patterns used for a specific dotfile can be specified relative to the dotfile destination (`dst`).

Similar to a `.gitignore` file, you can prefix ignore patterns with an exclamation point (`!`).
This so-called "negative ignore pattern" will cause any files that match that pattern to __not__ be ignored,
provided they *would have* been ignored by an earlier ignore pattern (dotdrop will warn if that is not the
case). This feature allows to, for example, ignore all files within a certain directory, except for a
particular one (See examples below).

For example to ignore everything but the `colors` directory under `~/.vim`
```yaml
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    cmpignore:
      - '*'
      - '!*/colors/*'
```

To completely ignore comparison of a specific dotfile:
```yaml
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    cmpignore:
      - '*'
```

To ignore a specific directory when updating:
```yaml
dotfiles:
  d_colorpicker:
    src: config/some_directory
    dst: ~/.config/some_directory
    upignore:
      - '*/sub_directory_to_ignore/*'
```

To ignore a specific file `testfile` and directory `testdir` when importing:
```yaml
config:
  impignore:
    - "*/testfile"
    - "testdir"
```

To ignore all files within a certain directory relative to `dst`, except one called `custom_plugin.zsh`:
```yaml
dotfiles:
  d_zsh:
    src: zsh
    dst: ~/.config/zsh
    upignore:
      - "*/plugins/*"
      - "!plugins/custom_plugin.zsh"
```

To ignore everything except a single file named `file`:
```yaml
dotfiles:
  d_dir
    src: dir
    dst: ~/dir
    cmpignore:
      - '!file'
      - '[a-zA-Z0-9]*'
```

To ignore specific files on different profiles (same `src` but some files
are not installed for specific profile)
```yaml
dotfiles:
  d_testdir_p1:
    src: testdir
    dst: ~/.testdir
    instignore:
    - '*/ignore-me-1'
  d_testdir_p2:
    src: testdir
    dst: ~/.testdir
    instignore:
    - '*/ignore-me-2'
profiles:
  p1:
    dotfiles:
    - d_testdir_p1
  p2:
    dotfiles:
    - d_testdir_p2
```

## Ignore missing

Sometimes, it is nice to have [update](../usage.md#update-dotfiles) not copy all the files in the installed directory
or [compare](../usage.md#compare-dotfiles) diff them.

For example,
maybe you only want to include a single configuration file in your repository
and don't want to include other files the program uses,
such as a cached files.
Maybe you only want to change one file and don't want the others cluttering your repository.
Maybe the program changes these files quite often and creates unnecessary diffs in your dotfiles.

In these cases, you can use the [ignore-missing](config-config.md) option.
This option is available as a flag (`--ignore-missing` or `-z`) to the `update` and `compare` commands,
or [as ignore-missing in the config](config-config.md).

To configure globally, place the following in `config.yaml`:
```yaml
config:
  ignore_missing_in_dotdrop: true
```

To configure per dotfile:
```yaml
dotfiles:
  f_abc:
    ignore_missing_in_dotdrop: true
```

## toml

Dotdrop should be able to handle `toml` config file however this
feature hasn't been extensively tested.
A base [config.toml](/config.toml) is available to get started.

The script [yaml_to_toml.py](https://github.com/deadc0de6/dotdrop/blob/master/scripts/yaml_to_toml.py) allows to convert a `yaml` dotdrop
config file to `toml`.

For more see issue [#343](https://github.com/deadc0de6/dotdrop/issues/343).