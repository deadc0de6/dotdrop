## Syntax

Dotdrop config file uses [yaml](https://yaml.org/) syntax.

Here is a minimal config file to start with:
[config.yaml](https://github.com/deadc0de6/dotdrop/blob/master/config.yaml).

### config entry

The **config** entry (mandatory) contains settings for the deployment

Entry    | Description | Default
-------- | ------------- | ------------
`backup` | create a backup of the dotfile in case it differs from the one that will be installed by dotdrop  | true
`banner` | display the banner  | true
`cmpignore` | list of patterns to ignore when comparing, apply to all dotfiles (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns)) | -
`create` | create directory hierarchy when installing dotfiles if it doesn't exist | true
`default_actions` | list of action's keys to execute for all installed dotfile (see [actions](config-details.md#entry-actions)) | -
`diff_command` | the diff command to use for diffing files | `diff -r -u {0} {1}`
`dotpath` | path to the directory containing the dotfiles to be managed by dotdrop (absolute path or relative to the config file location) | `dotfiles`
`filter_file` | list of paths to load templating filters from (see [Templating available filters](templating.md#template-filters)) | -
`func_file` | list of paths to load templating functions from (see [Templating available methods](templating.md#template-methods)) | -
`ignore_missing_in_dotdrop` | ignore missing files in dotdrop when comparing and importing (see [Ignore missing](usage.md#ignore-missing)) | false
`ignoreempty` | do not deploy template if empty | false
`impignore` | list of patterns to ignore when importing (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns)) | -
`import_actions` | list of paths to load actions from (absolute path or relative to the config file location, see [Import actions from file](config-details.md#entry-import_actions)) | -
`import_configs` | list of config file paths to be imported in the current config (absolute path or relative to the current config file location, see [Import config files](config-details.md#entry-import_configs)) | -
`import_variables` | list of paths to load variables from (absolute path or relative to the config file location see [Import variables from file](config-details.md#entry-import_variables)) | -
`instignore` | list of patterns to ignore when installing, apply to all dotfiles (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns)) | -
`keepdot` | preserve leading dot when importing hidden file in the `dotpath` | false
`link_dotfile_default` | set dotfile's `link` attribute to this value when undefined. Possible values: *nolink*, *link* (see [Symlinking dotfiles](config.md#symlink-dotfiles)) | `nolink`
`link_on_import` | set dotfile's `link` attribute to this value when importing. Possible values: *nolink*, *link* [Symlinking dotfiles](config.md#symlink-dotfiles)) | `nolink`
`longkey` | use long keys for dotfiles when importing (see [Import dotfiles](usage.md#import-dotfiles)) | false
`minversion` | (*for internal use, do not modify*) provides the minimal dotdrop version to use | -
`showdiff` | on install show a diff before asking to overwrite (see `--showdiff`) | false
`template_dotfile_default` | disable templating on all dotfiles when set to false | true
`upignore` | list of patterns to ignore when updating, apply to all dotfiles (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns)) | -
`workdir` | path to the directory where templates are installed before being symlinked when using `link:link` or `link:link_children` (absolute path or relative to the config file location) | `~/.config/dotdrop`
<s>link_by_default</s> | when importing a dotfile set `link` to that value per default | false

### dotfiles entry

The **dotfiles** entry (mandatory) contains a list of dotfiles managed by dotdrop

Entry    | Description
-------- | -------------
`dst` | where this dotfile needs to be deployed (dotfile with empty `dst` are ignored and considered installed, can use `variables` and `dynvariables`, make sure to quote)
`src` | dotfile path within the `dotpath` (dotfile with empty `src` are ignored and considered installed, can use `variables` and `dynvariables`, make sure to quote)
`link` | define how this dotfile is installed. Possible values: *nolink*, *link*, *link_children* (see [Symlinking dotfiles](config.md#symlink-dotfiles)) (defaults to value of `link_dotfile_default`)
`actions` | list of action keys that need to be defined in the **actions** entry below (see [actions](config-details.md#entry-actions))
`chmod` | defines the file permissions in octal notation to apply during installation (see [permissions](config.md#permissions))
`cmpignore` | list of patterns to ignore when comparing (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns))
`ignore_missing_in_dotdrop` | ignore missing files in dotdrop when comparing and importing (see [Ignore missing](usage.md#ignore-missing))
`ignoreempty` | if true empty template will not be deployed (defaults to value of `ignoreempty`)
`instignore` | list of patterns to ignore when installing (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns))
`template` | if false disable template for this dotfile (defaults to value of `template_dotfile_default`)
`trans_read` | transformation key to apply when installing this dotfile (must be defined in the **trans_read** entry below, see [transformations](config-details.md#entry-transformations))
`trans_write` | transformation key to apply when updating this dotfile (must be defined in the **trans_write** entry below, see [transformations](config-details.md#entry-transformations))
`upignore` | list of patterns to ignore when updating (enclose in quotes when using wildcards, see [ignore patterns](config.md#ignore-patterns))
<s>link_children</s> | replaced by `link: link_children`
<s>trans</s> | replaced by `trans_read`

```yaml
<dotfile-key-name>:
  dst: <where-this-file-is-deployed>
  src: <filename-within-the-dotpath>
  ## Optional
  link: (nolink|link|link_children)
  ignoreempty: (true|false)
  cmpignore:
    - "<ignore-pattern>"
  upignore:
    - "<ignore-pattern>"
  instignore:
    - "<ignore-pattern>"
  actions:
    - <action-key>
  template: (true|false)
  chmod: '<file-permissions>'
  trans_read: <transformation-key>
  trans_write: <transformation-key>
```

### profiles entry

The **profiles** entry (mandatory) contains a list of profiles with the different dotfiles that
  need to be managed

Entry    | Description
-------- | -------------
`dotfiles` | the dotfiles associated to this profile
`import` | list of paths containing dotfiles keys for this profile (absolute path or relative to the config file location, see [Import profile dotfiles from file](config-details.md#entry-profile-import)).
`include` | include all elements (dotfiles, actions, (dyn)variables, etc) from another profile (see [Include dotfiles from another profile](config-details.md#entry-profile-include))
`variables` | profile specific variables (see [Variables](config.md#variables))
`dynvariables` | profile specific interpreted variables (see [Interpreted variables](config-details.md#entry-dynvariables))
`actions` | list of action keys that need to be defined in the **actions** entry below (see [actions](config-details.md#entry-actions))

```yaml
<some-profile-name-usually-the-hostname>:
  dotfiles:
  - <some-dotfile-key-name-defined-above>
  - <some-other-dotfile-key-name>
  - ...
  ## Optional
  include:
  - <some-other-profile>
  - ...
  variables:
    <name>: <value>
  dynvariables:
    <name>: <value>
  actions:
  - <some-action>
  - ...
  import:
  - <some-path>
  - ...
```

### actions entry

The **actions** entry (optional) contains a list of actions (see [actions](config-details.md#entry-actions))

```yaml
actions:
  <action-key>: <command-to-execute>
```

*pre* actions
```yaml
actions:
  pre:
    <action-key>: <command-to-execute>
```

*post* actions
```yaml
actions:
  post:
    <action-key>: <command-to-execute>
```

### trans_read entry

The **trans_read** entry (optional) contains a list of transformations (see [transformations](config-details.md#entry-transformations))

```yaml
trans_read:
   <trans-key>: <command-to-execute>
```

### trans_write entry

The **trans_write** entry (optional) contains a list of write transformations (see [transformations](config-details.md#entry-transformations))

```yaml
trans_write:
   <trans-key>: <command-to-execute>
```

### variables entry

The **variables** entry (optional) contains a list of variables (see [variables](config.md#variables))

```yaml
variables:
  <variable-name>: <variable-content>
```

### dynvariables entry

The **dynvariables** entry (optional) contains a list of interpreted variables
(see [Interpreted variables](config-details.md#entry-dynvariables))

```yaml
dynvariables:
  <variable-name>: <shell-oneliner>
```
