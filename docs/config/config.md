# Config

The config file used by dotdrop is
[config.yaml](https://github.com/deadc0de6/dotdrop/blob/master/config.yaml).

## Location

Unless specified dotdrop will look in following places for the config file (`config.yaml`)
and use the first one found

* current/working directory or the directory where [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh) is located if used
* `${XDG_CONFIG_HOME}/dotdrop/`
* `~/.config/dotdrop/`
* `/etc/xdg/dotdrop/`
* `/etc/dotdrop/`

You can force dotdrop to use a different file either by using the `-c --cfg` cli switch
or by defining the `DOTDROP_CONFIG` environment variable.

## Format

Dotdrop config file uses [yaml](https://yaml.org/) syntax.

Content Format:

* **config** entry (mandatory): contains settings for the deployment
    * `backup`: create a backup of the dotfile in case it differs from the
      one that will be installed by dotdrop (default *true*)
    * `banner`: display the banner (default *true*)
    * `cmpignore`: list of patterns to ignore when comparing, apply to all dotfiles
      (enclose in quotes when using wildcards, see [ignore patterns](ignore-pattern.md))
    * `create`: create directory hierarchy when installing dotfiles if
      it doesn't exist (default *true*)
    * `default_actions`: list of action's keys to execute for all installed dotfile
      (see [Use actions](usage-actions.md))
    * `diff_command`: the diff command to use for diffing files (default `diff -r -u {0} {1}`)
    * `dotpath`: path to the directory containing the dotfiles to be managed (default `dotfiles`)
      by dotdrop (absolute path or relative to the config file location)
    * `filter_file`: list of paths to load templating filters from
      (see [Templating available filters](../template/templating.md#available-filters))
    * `func_file`: list of paths to load templating functions from
       (see [Templating available methods](../template/templating.md#available-methods))
    * `ignoreempty`: do not deploy template if empty (default *false*)
    * `import_actions`: list of paths to load actions from
      (absolute path or relative to the config file location,
      see [Import actions from file](#import-actions-from-file))
    * `import_configs`: list of config file paths to be imported in
      the current config (absolute path or relative to the current config file location,
      see [Import config files](#import-config-files))
    * `import_variables`: list of paths to load variables from
      (absolute path or relative to the config file location,
      see [Import variables from file](#import-variables-from-file))
    * `instignore`: list of patterns to ignore when installing, apply to all dotfiles
      (enclose in quotes when using wildcards, see [ignore patterns](ignore-pattern.md))
    * `keepdot`: preserve leading dot when importing hidden file in the `dotpath` (default *false*)
    * `link_dotfile_default`: set dotfile's `link` attribute to this value when undefined.
      Possible values: *nolink*, *link*, *link_children* (default: *nolink*,
      see [Symlinking dotfiles](#symlinking-dotfiles))
    * `link_on_import`: set dotfile's `link` attribute to this value when importing.
      Possible values: *nolink*, *link*, *link_children* (default: *nolink*,
      see [Symlinking dotfiles](#symlinking-dotfiles))
    * `longkey`: use long keys for dotfiles when importing (default *false*,
      see [Import dotfiles](../usage.md#import-dotfiles))
    * `minversion`: (*for internal use, do not modify*) provides the minimal dotdrop version to use
    * `showdiff`: on install show a diff before asking to overwrite (see `--showdiff`) (default *false*)
    * `upignore`: list of patterns to ignore when updating, apply to all dotfiles
      (enclose in quotes when using wildcards, see [ignore patterns](ignore-pattern.md))
    * `workdir`: path to the directory where templates are installed before being symlinked
      when using `link:link` or `link:link_children`
      (absolute path or relative to the config file location, defaults to *~/.config/dotdrop*)
    * DEPRECATED `link_by_default`: when importing a dotfile set `link` to that value per default (default *false*)

* **dotfiles** entry (mandatory): a list of dotfiles
    * `dst`: where this dotfile needs to be deployed
      (dotfile with empty `dst` are ignored and considered installed,
      can use `variables` and `dynvariables`, make sure to quote)
    * `src`: dotfile path within the `dotpath`
      (dotfile with empty `src` are ignored and considered installed,
      can use `variables` and `dynvariables`, make sure to quote)
    * `link`: define how this dotfile is installed.
      Possible values: *nolink*, *link*, *link_children* (default: `link_dotfile_default`,
      see [Symlinking dotfiles](#symlinking-dotfiles))
    * `actions`: list of action keys that need to be defined in the **actions** entry below
      (see [Use actions](usage-actions.md))
    * `cmpignore`: list of patterns to ignore when comparing (enclose in quotes when using wildcards,
      see [ignore patterns](ignore-pattern.md))
    * `ignoreempty`: if true empty template will not be deployed (defaults to the value of `ignoreempty` above)
    * `instignore`: list of patterns to ignore when installing (enclose in quotes when using wildcards,
      see [ignore patterns](ignore-pattern.md))
    * `trans_read`: transformation key to apply when installing this dotfile
      (must be defined in the **trans_read** entry below, see [Use transformations](usage-transformations.md))
    * `trans_write`: transformation key to apply when updating this dotfile
      (must be defined in the **trans_write** entry below, see [Use transformations](usage-transformations.md))
    * `upignore`: list of patterns to ignore when updating (enclose in quotes when using wildcards,
      see [ignore patterns](ignore-pattern.md))
    * DEPRECATED `link_children`: replaced by `link: link_children`
    * DEPRECATED `trans`: replaced by `trans_read`

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
    trans_read: <transformation-key>
    trans_write: <transformation-key>
```

* **profiles** entry (mandatory): a list of profiles with the different dotfiles that
  need to be managed
    * `dotfiles`: the dotfiles associated to this profile
    * `import`: list of paths containing dotfiles keys for this profile
      (absolute path or relative to the config file location,
      see [Import profile dotfiles from file](#import-profile-dotfiles-from-file)).
    * `include`: include all elements (dotfiles, actions, (dyn)variables, etc) from another profile
      (see [Include dotfiles from another profile](#include-dotfiles-from-another-profile))
    * `variables`: profile specific variables
      (see [Variables](#variables))
    * `dynvariables`: profile specific interpreted variables
      (see [Interpreted variables](#interpreted-variables))
    * `actions`: list of action keys that need to be defined in the **actions** entry below
      (see [Use actions](usage-actions.md))

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

* **actions** entry (optional): a list of actions (see [Use actions](usage-actions.md))

```yaml
actions:
  <action-key>: <command-to-execute>
```

* **trans_read** entry (optional): a list of transformations (see [Use transformations](usage-transformations.md))

```yaml
trans_read:
   <trans-key>: <command-to-execute>
```

* **trans_write** entry (optional): a list of write transformations (see [Use transformations](usage-transformations.md))

```yaml
trans_write:
   <trans-key>: <command-to-execute>
```

* **variables** entry (optional): a list of variables (see [Variables](#variables))

```yaml
variables:
  <variable-name>: <variable-content>
```

* **dynvariables** entry (optional): a list of interpreted variables
  (see [Interpreted variables](#interpreted-variables))

```yaml
dynvariables:
  <variable-name>: <shell-oneliner>
```

## Actions

see [Actions](usage-actions.md)

## Transformations

see [Transformations](usage-transformations.md)

## Variables

see [Variables](config-variables.md)

## Interpreted variables

see [Interpreted variables](config-variables.md)

## Symlinking dotfiles

Dotdrop is able to install dotfiles in three different ways
which are controlled by the `link` attribute of each dotfile:

* `link: nolink`: the dotfile (file or directory) is copied to its destination
* `link: link`: the dotfile (file or directory) is symlinked to its destination
* `link: link_children`: the files/directories found under the dotfile (directory) are symlinked to their destination

For more see [this how-to](../howto/symlinked-dotfiles.md)

## All dotfiles for a profile

To use all defined dotfiles for a profile, simply use
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

## Include dotfiles from another profile

If one profile is using the entire set of another profile, one can use
the `include` entry to avoid redundancy.

Note that everything from the included profile is made available
(actions, variables/dynvariables, etc).

For example:
```yaml
profiles:
  host1:
    dotfiles:
      - f_xinitrc
    include:
      - host2
  host2:
    dotfiles:
      - f_vimrc
```
Here profile *host1* contains all the dotfiles defined for *host2* plus `f_xinitrc`.

For more advanced use-cases variables
([variables](config-variables.md) and [dynvariables](config-variables.md))
can be used to specify the profile to include in a profile

For example:
```yaml
variables:
  var1: "john"
dynvariables:
  d_user: "echo $USER"
profiles:
  profile_john:
    dotfiles:
    - f_john_dotfile
  profile_bill:
    dotfiles:
    - f_bill_dotfile
  p1:
    include:
    - "profile_{{@@ d_user @@}}"
  p2:
    include:
    - "profile_{{@@ var1 @@}}"
```

## Import profile dotfiles from file

Profile's dotfiles list can be loaded from external files
by specifying their paths in the config entry `import` under the specific profile.

The paths can be absolute or relative to the config file location.

`config.yaml`
```yaml
dotfiles:
  f_abc:
    dst: ~/.abc
    src: abc
  f_def:
    dst: ~/.def
    src: def
  f_xyz:
    dst: ~/.xyz
    src: xyz
profiles:
  p1:
    dotfiles:
    - f_abc
    import:
    - somedotfiles.yaml
```

`somedotfiles.yaml`
```
dotfiles:
  - f_def
  - f_xyz
```

Variables can be used in `import` and would allow to do something like
```yaml
import:
- profiles.d/{{@@ profile @@}}.yaml
```

## Import variables from file

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
It is possible to make non-existing paths not fatal by appending the path with `:optional`
```yaml
import_variables:
- variables.d/myvars.yaml:optional
```

## Import actions from file

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

External variables will take precedence over variables defined within
the source config file.

Dotdrop will fail if an imported path points to a non-existing file.
It is possible to make non-existing paths not fatal by appending the path with `:optional`
```yaml
import_actions:
- actions.d/myactions.yaml:optional
```

## Import config files

Entire config files can be imported. This means making the following available
from the imported config file in the original config file:

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

In this example `config.yaml` imports `other-config.yaml`. The dotfile `f_def`
used in the profile `my-host` is defined in `other-config.yaml`, and so is the
profile `other-host` included from `my-haskell`. The action `show` is defined
in `actions.yaml`, which is in turn imported by `other-config.yaml`.

Dotdrop will fail if an imported path points to a non-existing file.
It is possible to make non-existing paths not fatal by appending the path with `:optional`
```yaml
import_configs:
- other-config.yaml:optional
```

## Dynamic dotfile paths

Dotfile source (`src`) and destination (`dst`) can be dynamically constructed using
defined variables ([variables and dynvariables](config-variables.md)).

For example to have a dotfile deployed on the unique firefox profile where the
profile path is dynamically found using a shell oneliner stored in a dynvariable:
```yaml
dynvariables:
  mozpath: find ~/.mozilla/firefox -name '*.default'
dotfiles:
  f_somefile:
    dst: "{{@@ mozpath @@}}/somefile"
    src: firefox/somefile
profiles:
  home:
    dotfiles:
    - f_somefile
```

Make sure to quote the path in the config file.

## Dynamic actions

Variables ([config variables and dynvariables](config-variables.md)
and [template variables](../template/templating.md#template-variables)) can be used
in actions for more advanced use-cases.

```yaml
dotfiles:
  f_test:
    dst: ~/.test
    src: test
    actions:
      - cookie_mv_somewhere "/tmp/moved-cookie"
variables:
  cookie_dir_available: (test -d /tmp/cookiedir || mkdir -p /tmp/cookiedir)
  cookie_header: "{{@@ cookie_dir_available @@}} && echo 'header' > /tmp/cookiedir/cookie"
  cookie_mv: "{{@@ cookie_header @@}} && mv /tmp/cookiedir/cookie"
actions:
  cookie_mv_somewhere: "{{@@ cookie_mv @@}} {0}"
```

or even something like this:
```yaml
actions:
  log: "echo {0} >> {1}"
config:
  default_actions:
  - preaction '{{@@ _dotfile_key @@}} installed' "/tmp/log"
...
```

Make sure to quote the actions using variables.

## Dynamic transformations

As for [dynamic actions](#dynamic-actions), transformations support
the use of variables ([variables and dynvariables](config-variables.md)
and [template variables](../template/templating.md#template-variables)).

A very dumb example:
```yaml
trans_read:
  r_echo_abs_src: echo "{0}: {{@@ _dotfile_abs_src @@}}" > {1}
  r_echo_var: echo "{0}: {{@@ r_var @@}}" > {1}
trans_write:
  w_echo_key: echo "{0}: {{@@ _dotfile_key @@}}" > {1}
  w_echo_var: echo "{0}: {{@@ w_var @@}}" > {1}
variables:
  r_var: readvar
  w_var: writevar
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans_read: r_echo_abs_src
    trans_write: w_echo_key
  f_def:
    dst: ${tmpd}/def
    src: def
    trans_read: r_echo_var
    trans_write: w_echo_var
```
