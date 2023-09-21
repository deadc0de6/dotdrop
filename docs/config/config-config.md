# Config block

The **config** entry (mandatory) contains global settings.

Entry    | Description | Default
-------- | ------------- | ------------
`backup` | Create a backup of the existing destination; see [backup entry](config-config.md#backup-entry)) | true
`banner` | Display the banner  | true
`check_version` | Check if a new version of dotdrop is available on github | false
`chmod_on_import` | Always add a chmod entry on newly imported dotfiles (see `--preserve-mode`) | false
`clear_workdir` | On `install` clear the `workdir` before installing dotfiles (see `--workdir-clear`) | false
`compare_workdir` | On `compare` notify on files in `workdir` not tracked by dotdrop | false
`cmpignore` | List of patterns to ignore when comparing, applied to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns)) | -
`create` | Create a directory hierarchy when installing dotfiles if it doesn't exist | true
`default_actions` | List of action keys to execute for all installed dotfiles (See [actions](config-actions.md)) | -
`diff_command` | The diff command to use for diffing files | `diff -r -u {0} {1}`
`dotpath` | Path to the directory containing the dotfiles to be managed by dotdrop (absolute path or relative to the config file location) | `dotfiles`
`filter_file` | List of paths to load templating filters from (See [Templating available filters](../template/template-filters.md)) | -
`force_chmod` | If true, do not ask confirmation to apply permissions on install | false
`func_file` | List of paths to load templating functions from (See [Templating available methods](../template/template-methods.md)) | -
`ignore_missing_in_dotdrop` | Ignore missing files in dotdrop when comparing and importing (See [Ignore missing](config-file.md#ignore-missing)) | false
`ignoreempty` | Do not deploy template if empty | false
`impignore` | List of patterns to ignore when importing (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns)) | -
`import_actions` | List of paths to load actions from (absolute path or relative to the config file location; see [Import actions from file](config-config.md#import_actions-entry)) | -
`import_configs` | List of config file paths to be imported into the current config (absolute paths or relative to the current config file location; see [Import config files](config-config.md#import_configs-entry)) | -
`import_variables` | List of paths to load variables from (absolute paths or relative to the config file location; see [Import variables from file](config-config.md#import_variables-entry)) | -
`instignore` | List of patterns to ignore when installing, applied to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns)) | -
`keepdot` | Preserve leading dot when importing hidden file in the `dotpath` | false
`key_prefix` | Prefix dotfile key on `import` with `f<key_separator>` for file and `d<key_separator>` for directory | true
`key_separator` | Separator to use on dotfile key generation on `import` | `_`
`link_dotfile_default` | Set a dotfile's `link` attribute to this value when undefined. Possible values: *nolink*, *absolute*, *relative* (See [Symlinking dotfiles](config-file.md#symlinking-dotfiles)) | `nolink`
`link_on_import` | Set a dotfile's `link` attribute to this value when importing. Possible values: *nolink*, *absolute*, *relative* [Symlinking dotfiles](config-file.md#symlinking-dotfiles)) | `nolink`
`longkey` | Use long keys for dotfiles when importing (See [Import dotfiles](../usage.md#import-dotfiles)) | false
`minversion` | (*for internal use, do not modify*) Provides the minimal dotdrop version to use | -
`showdiff` | On install, show a diff before asking to overwrite (See `--showdiff`) | false
`template_dotfile_default` | Disable templating on all dotfiles when set to false | true
`upignore` | List of patterns to ignore when updating, appled to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns)) | -
`workdir` | Path to the directory where templates are installed before being symlinked when using `link:absolute|relative|link_children` (absolute path or relative to the config file location) | `~/.config/dotdrop`
<s>link_by_default</s> | When importing a dotfile, set `link` to this value by default | false


## import_variables entry

It is possible to load variables/dynvariables from external files by providing their
paths in the config entry `import_variables`.

The paths can be absolute or relative to the config file location.

`config.yaml`
```yaml
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - variables.d/myvars.yaml
```

`variables.d/myvars.yaml`
```yaml
variables:
  var1: "extvar1"
dynvariables:
  dvar1: "echo extdvar1"
```

Dotdrop will fail if an imported path points to a non-existing file.
It is possible to make non-existing paths not fatal by appending `:optional` to the path:
```yaml
import_variables:
- variables.d/myvars.yaml:optional
```

## import_actions entry

It is possible to load actions from external files by providing their
paths in the config entry `import_actions`.

The paths can be absolute or relative to the config file location.

`config.yaml`
```yaml
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - actions.d/myactions.yaml
dotfiles:
  f_abc:
    dst: ~/.abc
    src: abc
    actions:
      - dateme
```

`actions.d/myactions.yaml`
```yaml
actions:
  dateme: date > /tmp/timestamp
```

External/imported variables will take precedence over variables defined
inside the main config file.

Dotdrop will fail if an imported path points to a non-existing file.
It is possible to make non-existing paths not fatal by appending `:optional` to the path:
```yaml
import_actions:
- actions.d/myactions.yaml:optional
```

## import_configs entry

Entire config files can be imported using the `import_configs` entry.
This means making the following available from the imported config file in the original config file:

* dotfiles
* profiles
* actions
* read/write transformations
* variables/dynvariables

Paths to import can be absolute or relative to the importing config file
location.

`config.yaml`
```yaml
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - other-config.yaml
dotfiles:
  f_abc:
    dst: ~/.abc
    src: abc
    actions:
    - show
profiles:
  my-host:
    dotfiles:
    - f_abc
    - f_def
  my-haskell:
    include:
    - other-host
```

`other-config.yaml`
```yaml
config:
  backup: true
  create: true
  dotpath: dotfiles-other
  import_actions:
  - actions.yaml
dotfiles:
  f_def:
    dst: ~/.def
    src: def
  f_ghci:
    dst: ~/.ghci
    src: ghci
profiles:
  other-host:
    dotfiles:
    - f_gchi
```

`actions.yaml`
```yaml
actions:
  post:
    show: less
```

In this example, `config.yaml` imports `other-config.yaml`. The dotfile `f_def`
used in the profile `my-host` is defined in `other-config.yaml`, and so is the
profile `other-host` included from `my-haskell`. The action `show` is defined
in `actions.yaml`, which is in turn imported by `other-config.yaml`.

Dotdrop will fail if an imported path points to a non-existing file.
It is possible to make non-existing paths not fatal by appending `:optional` to the path.
```yaml
import_configs:
- other-config.yaml:optional
```

## default_actions entry

Dotdrop allows to execute an action for any dotfile installation. These actions work as any other action (`pre` or `post`).

For example, the below action will log each dotfile installation to a file.

```yaml
actions:
  post:
    loginstall: "echo {{@@ _dotfile_abs_src @@}} installed to {{@@ _dotfile_abs_dst @@}} >> {0}"
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - loginstall "/tmp/dotdrop-installation.log"
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
profiles:
  hostname:
    dotfiles:
    - f_vimrc
```

## backup entry

When set to `true`, existing files that would be replaced
by a dotdrop `install`, are backed up with the
extension `.dotdropbak` if their content differ.

Note:
* directories will **not** be backed up, only files
* when using a different `link` value than `nolink` with directories,
  the files under the directory will **not** be backed up
  (See [Symlinking dotfiles](config-file.md#symlinking-dotfiles)),