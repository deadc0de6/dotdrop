# Config format

The dotdrop config file uses [YAML](https://yaml.org/) syntax.

Here is a minimal config file to start with:
[config.yaml](https://github.com/deadc0de6/dotdrop/blob/master/config.yaml).

## config entry

The **config** entry (mandatory) contains settings for the deployment.

Entry    | Description | Default
-------- | ------------- | ------------
`backup` | Create a backup of the dotfile in case it differs from the one that will be installed by dotdrop  | true
`banner` | Display the banner  | true
`check_version` | Check if a new version of dotdrop is available on github | false
`chmod_on_import` | Always add a chmod entry on newly imported dotfiles (see `--preserve-mode`) | false
`clear_workdir` | On `install` clear the `workdir` before installing dotfiles (see `--workdir-clear`) | false
`compare_workdir` | On `compare` notify on files in `workdir` not tracked by dotdrop | false
`cmpignore` | List of patterns to ignore when comparing, applied to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns)) | -
`create` | Create a directory hierarchy when installing dotfiles if it doesn't exist | true
`default_actions` | List of action keys to execute for all installed dotfiles (See [actions](config-details.md#actions-entry)) | -
`diff_command` | The diff command to use for diffing files | `diff -r -u {0} {1}`
`dotpath` | Path to the directory containing the dotfiles to be managed by dotdrop (absolute path or relative to the config file location) | `dotfiles`
`filter_file` | List of paths to load templating filters from (See [Templating available filters](templating.md#template-filters)) | -
`force_chmod` | If true, do not ask confirmation to apply permissions on install | false
`func_file` | List of paths to load templating functions from (See [Templating available methods](templating.md#template-methods)) | -
`ignore_missing_in_dotdrop` | Ignore missing files in dotdrop when comparing and importing (See [Ignore missing](usage.md#ignore-missing)) | false
`ignoreempty` | Do not deploy template if empty | false
`impignore` | List of patterns to ignore when importing (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns)) | -
`import_actions` | List of paths to load actions from (absolute path or relative to the config file location; see [Import actions from file](config-details.md#import_actions-entry)) | -
`import_configs` | List of config file paths to be imported into the current config (absolute paths or relative to the current config file location; see [Import config files](config-details.md#import_configs-entry)) | -
`import_variables` | List of paths to load variables from (absolute paths or relative to the config file location; see [Import variables from file](config-details.md#import_variables-entry)) | -
`instignore` | List of patterns to ignore when installing, applied to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns)) | -
`keepdot` | Preserve leading dot when importing hidden file in the `dotpath` | false
`link_dotfile_default` | Set a dotfile's `link` attribute to this value when undefined. Possible values: *nolink*, *link* (See [Symlinking dotfiles](config.md#symlinking-dotfiles)) | `nolink`
`link_on_import` | Set a dotfile's `link` attribute to this value when importing. Possible values: *nolink*, *link* [Symlinking dotfiles](config.md#symlinking-dotfiles)) | `nolink`
`longkey` | Use long keys for dotfiles when importing (See [Import dotfiles](usage.md#import-dotfiles)) | false
`minversion` | (*for internal use, do not modify*) Provides the minimal dotdrop version to use | -
`showdiff` | On install, show a diff before asking to overwrite (See `--showdiff`) | false
`template_dotfile_default` | Disable templating on all dotfiles when set to false | true
`upignore` | List of patterns to ignore when updating, appled to all dotfiles (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns)) | -
`workdir` | Path to the directory where templates are installed before being symlinked when using `link:link` or `link:link_children` (absolute path or relative to the config file location) | `~/.config/dotdrop`
<s>link_by_default</s> | When importing a dotfile, set `link` to this value by default | false

## dotfiles entry

The **dotfiles** entry (mandatory) contains a YAML object with sub-objects for the dotfiles managed by dotdrop.  The entries in the sub-objects are as follows:

Entry    | Description
-------- | -------------
`dst` | Where this dotfile needs to be deployed (dotfiles with empty `dst` are ignored and considered installed, can use `variables`, make sure to quote)
`src` | Dotfile path within the `dotpath` (dotfiles with empty `src` are ignored and considered installed, can use `variables`, make sure to quote)
`link` | Defines how this dotfile is installed. Possible values: *nolink*, *link*, *link_children* (See [Symlinking dotfiles](config.md#symlinking-dotfiles)) (defaults to value of `link_dotfile_default`)
`actions` | List of action keys that need to be defined in the **actions** entry below (See [actions](config-details.md#actions-entry))
`chmod` | Defines the file permissions in octal notation to apply during installation (See [permissions](config.md#permissions))
`cmpignore` | List of patterns to ignore when comparing (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns))
`ignore_missing_in_dotdrop` | Ignore missing files in dotdrop when comparing and importing (see [Ignore missing](usage.md#ignore-missing))
`ignoreempty` | If true, an empty template will not be deployed (defaults to the value of `ignoreempty`)
`instignore` | List of patterns to ignore when installing (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns))
`template` | If false, disable templating for this dotfile (defaults to the value of `template_dotfile_default`)
`trans_read` | Transformation key to apply when installing this dotfile (must be defined in the **trans_read** entry below; see [transformations](config-details.md#transformations-entry))
`trans_write` | Transformation key to apply when updating this dotfile (must be defined in the **trans_write** entry below; see [transformations](config-details.md#transformations-entry))
`upignore` | List of patterns to ignore when updating (enclose in quotes when using wildcards; see [ignore patterns](config.md#ignore-patterns))
<s>link_children</s> | Replaced by `link: link_children`
<s>trans</s> | Replaced by `trans_read`

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

## profiles entry

The **profiles** entry (mandatory) contains a YAML object with sub-objects for the profiles for the different dotfiles that need to be managed.  The entries in the sub-objects are as follows:

Entry    | Description
-------- | -------------
`dotfiles` | The dotfiles associated with this profile
`import` | List of paths containing dotfile keys for this profile (absolute path or relative to the config file location; see [Import profile dotfiles from file](config-details.md#profile-import-entry)).
`include` | Include all elements (dotfiles, actions, (dyn)variables, etc) from another profile (See [Include dotfiles from another profile](config-details.md#profile-include-entry))
`variables` | Profile-specific variables (See [Variables](config.md#variables))
`dynvariables` | Profile-specific interpreted variables (See [Interpreted variables](config-details.md#dynvariables-entry))
`actions` | List of action keys that need to be defined in the **actions** entry below (See [actions](config-details.md#actions-entry))

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

## actions entry

The **actions** entry (optional) contains an actions mapping (See [actions](config-details.md#actions-entry)).

```yaml
actions:
  <action-key>: <command-to-execute>
```

*pre* actions:
```yaml
actions:
  pre:
    <action-key>: <command-to-execute>
```

*post* actions:
```yaml
actions:
  post:
    <action-key>: <command-to-execute>
```

## trans_read entry

The **trans_read** entry (optional) contains a transformations mapping (See [transformations](config-details.md#transformations-entry)).

```yaml
trans_read:
   <trans-key>: <command-to-execute>
```

## trans_write entry

The **trans_write** entry (optional) contains a write transformations mapping (See [transformations](config-details.md#transformations-entry)).

```yaml
trans_write:
   <trans-key>: <command-to-execute>
```

## variables entry

The **variables** entry (optional) contains a variables mapping (See [variables](config.md#variables)).

```yaml
variables:
  <variable-name>: <variable-content>
```

## dynvariables entry

The **dynvariables** entry (optional) contains an interpreted variables mapping
(See [Interpreted variables](config-details.md#dynvariables-entry)).

```yaml
dynvariables:
  <variable-name>: <shell-oneliner>
```

## uservariables entry

The **uservariables** entry (optional) contains a collection of variables
whose values are queried from the user
(See [User variables](config-details.md#uservariables-entry)).

```yaml
uservariables:
  <variable-name>: <prompt>
```
