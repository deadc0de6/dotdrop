# Config details

## actions entry

Actions can be either `post` or `pre`.

* `post` action will be executed after the dotfile deployment.
* `pre` action will be executed before the dotfile deployment.

If you don't specify either `post` or `pre`, the action will be executed
after the dotfile deployment (which is equivalent to `post`).
Actions cannot obviously be named `pre` or `post`.

Four types of actions can be defined:

* [Dotfiles actions](#dotfile-actions)
* [Default actions](#default-actions)
* [Profile actions](#profile-actions)
* [Fake dotfiles and actions](#fake-dotfile-and-actions)

**Notes**:

* Any action with a key starting with an underscore (`_`) won't be shown in output. This can be useful when working with sensitive data containing passwords, for example.
* Make sure to quote your actions to avoid bad surprises
* Actions are executed using the default shell (`$SHELL`)
* To use shell variables in your actions, you need to escape the curly brackets (`${HOME}` becomes `${{HOME}}`)

### Dotfile actions

It is sometimes useful to execute some kind of action
when deploying a dotfile.

Note that a dotfile's actions are only
executed when the dotfile is installed (that is, when
the version present in dotdrop differs from the one
in the filesystem).

For example, let's consider
[Vundle](https://github.com/VundleVim/Vundle.vim), used
to manage Vim's plugins.  The following action could
be set to update and install the plugins when `vimrc` is
deployed:

```yaml
actions:
  vundle: vim +VundleClean! +VundleInstall +VundleInstall! +qall
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
    actions:
      - vundle
profiles:
  home:
    dotfiles:
    - f_vimrc
```

Thus, when `f_vimrc` is installed, the command
`vim +VundleClean! +VundleInstall +VundleInstall! +qall` will
be executed.

Sometimes, you may even want to execute some action prior to deploying a dotfile.
Let's take another example with
[vim-plug](https://github.com/junegunn/vim-plug):

```yaml
actions:
  pre:
    vim-plug-install: test -e ~/.vim/autoload/plug.vim || (mkdir -p ~/.vim/autoload; curl
      -fLo ~/.vim/autoload/plug.vim https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim)
  vim-plug: vim +PlugInstall +qall
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
    actions:
       - vim-plug-install
       - vim-plug
profiles:
  home:
    dotfiles:
    - f_vimrc
```

This way, we make sure [vim-plug](https://github.com/junegunn/vim-plug)
is installed prior to deploying the `~/.vimrc` dotfile.

You can also define `post` actions like this:

```yaml
actions:
  post:
    some-action: echo "Hello, World!" >/tmp/log
```

Actions can even be parameterized. For example:

```yaml
actions:
  echoaction: echo '{0}' > {1}
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
    actions:
      - echoaction "vim installed" /tmp/mydotdrop.log
  f_xinitrc:
    dst: ~/.xinitrc
    src: xinitrc
    actions:
      - echoaction "xinitrc installed" /tmp/myotherlog.log
profiles:
  home:
    dotfiles:
    - f_vimrc
    - f_xinitrc
```

The above will execute `echo 'vim installed' > /tmp/mydotdrop.log` when
vimrc is installed and `echo 'xinitrc installed' > /tmp/myotherlog.log'`
when xinitrc is installed.

### Default actions

Dotdrop allows you to execute an action for any dotfile installation. These actions work as any other action (`pre` or `post`).

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

### Profile actions

A profile action can be either a `pre` or `post` action (see [actions](config-details.md#actions-entry)).
These are executed before any dotfile installation (for `pre`) and after all dotfile installations (for `post`)
only if at least one dotfile has been installed.

### Fake dotfile and actions

*Fake* dotfile can be created by specifying no `dst` and no `src` (see [config format](config-format.md)).
By binding an action to such a *fake* dotfile, you make sure the action is always executed since
*fake* dotfile are always considered installed.

```yaml
actions:
  always_action: 'date > ~/.dotdrop.log'
dotfiles:
  fake:
    src:
    dst:
    actions:
    - always_action
```

## transformations entry

For examples of transformation uses, see:

* [Handle compressed directories](howto/store-compressed-directories.md)
* [Handle secrets](howto/sensitive-dotfiles.md)

**Notes**:

* Any transformation with a key starting with an underscore (`_`) won't be shown in output. This can be useful when working with sensitive data containing passwords, for example.
* Make sure to quote your transformations to avoid bad surprises
* Transformations are executed using the default shell (`$SHELL`)
* To use shell variables in your transformations you need to escape the curly brackets (`${HOME}` becomes `${{HOME}}`)

There are two types of transformations available:

* **Read transformations**: used to transform dotfiles before they are installed ([format](config-format.md) key `trans_read`)
    * Used for commands `install` and `compare`
    * They have two arguments:
        * **{0}** will be replaced with the dotfile to process
        * **{1}** will be replaced with a temporary file to store the result of the transformation
    * This Happens **before** the dotfile is templated (see [templating](templating.md))

* **Write transformations**: used to transform files before updating a dotfile ([format](config-format.md) key `trans_write`)
    * Used for command `update`
    * They have two arguments:
        * **{0}** will be replaced with the file path to update the dotfile with
        * **{1}** will be replaced with a temporary file to store the result of the transformation

A typical use-case for transformations is when dotfiles need to be
stored encrypted or compressed. For more, see [the howto](howto/howto.md).

Note that transformations cannot be used if the dotfile is to be linked (when `link: link` or `link: link_children`).

Transformations also support additional positional arguments that must start from 2 (since `{0}` and `{1}` are added automatically). The transformations themselves as well as their arguments can also be templated.

For example:
```yaml
trans_read:
  targ: echo "$(basename {0}); {{@@ _dotfile_key @@}}; {2}; {3}" > {1}
dotfiles:
  f_abc:
    dst: /tmp/abc
    src: abc
    trans_read: targ "{{@@ profile @@}}" lastarg
profiles:
  p1:
    dotfiles:
    - f_abc
```

will result in `abc; f_abc; p1; lastarg`.

## variables entry

Variables defined in the `variables` entry are made available within the config file.

Config variables are recursively evaluated, which means that
a config like the below:
```yaml
variables:
  var1: "var1"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
dynvariables:
  dvar1: "echo dvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
```

will result in the following available variables:

* var1: `var1`
* var2: `var1 var2`
* var3: `var1 var2 var3`
* var4: `echo var1 var2 var3`
* dvar1: `dvar1`
* dvar2: `dvar1 dvar2`
* dvar3: `dvar1 dvar2 dvar3`
* dvar4: `var1 var2 var3`

## dynvariables entry

It is also possible to have *dynamic* variables, in the sense that their
content will be interpreted by the shell before being substituted.

These need to be defined in the config file under the entry `dynvariables`.

For example:
```yaml
dynvariables:
  dvar1: head -1 /proc/meminfo
  dvar2: "echo 'this is some test' | rev | tr ' ' ','"
  dvar3: /tmp/my_shell_script.sh
  user: "echo $USER"
  config_file: test -f "{{@@ user_config @@}}" && echo "{{@@ user_config @@}}" || echo "{{@@ dfl_config @@}}"
variables:
  user_config: "profile_{{@@ user @@}}_uid.yaml"
  dfl_config: "profile_default.yaml"
```

They have the same properties as [Variables](config.md#variables).

## uservariables entry

If you want to manually enter variables' values, you can use the
`uservariables` entry. Each variable will be prompted to the user.

For example:
```yaml
uservariables:
  emailvar: "email"
```

will prompt the user to enter a value for the variable `emailvar`:
```
Please provide the value for "email":
```

And store the entered text as the value for the variable `email`.
The variable can then be used as any other [variable](config.md#variables).

`uservariables` are eventually saved to `uservariables.yaml` (relatively to the
config file).
This allows you to use the following construct to prompt once for some specific variables and
then store them in a file. You might also want to add `uservariables.yaml` to your `.gitignore`.
```yaml
uservariables:
  emailvar: "email"
config:
  import_variables:
    - uservariables.yaml:optional
```

For an example, see [prompt user for variables](howto/prompt-user-for-variables.md).

## Profile variables entry

Profile variables will take precedence over globally defined variables.
This means that you could do something like this:
```yaml
variables:
  git_email: home@email.com
dotfiles:
  f_gitconfig:
    dst: ~/.gitconfig
    src: gitconfig
profiles:
  work:
    dotfiles:
    - f_gitconfig
    variables:
      git_email: work@email.com
  private:
    dotfiles:
    - f_gitconfig
```

## Profile include entry

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

For more advanced use-cases, variables
([variables](config.md#variables) and [dynvariables](#dynvariables-entry))
can be used to specify the profile to include in a profile:

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

Note that profiles cannot include other profiles defined above in
the import tree (for example, when a profile exists in another file and is imported using `import_configs`).

## Profile import entry

A profile's dotfiles list can be loaded from external files
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

Variables can be used in `import`, which allow you to do something like:
```yaml
import:
- profiles.d/{{@@ profile @@}}.yaml
```

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

## Dynamic dotfile paths

Dotfile source (`src`) and destination (`dst`) paths can be dynamically constructed using
defined variables ([variables and dynvariables](config.md#variables)).

For example, to have a dotfile deployed on a unique Firefox profile where the
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

Or when you need to select the dotfile to deploy depending on
the profile used (`ssh_config.perso` for the profile `perso` and
`ssh_config.work` for the `work` profile):
```yaml
dotfiles:
  f_ssh_config:
    src: "{{@@ ssh_config_file @@}}"
    dst: ~/.ssh/config
profiles:
  perso:
    dotfiles:
    - f_ssh_config
    variables:
    - ssh_config_file: "ssh_config.perso"
  work:
    dotfiles:
    - f_ssh_config
    variables:
    - ssh_config_file: "ssh_config.work"
```

## Dynamic dotfile link value

Dotfile `link` values can be dynamically constructed using
defined variables ([variables and dynvariables](config.md#variables)).

For example:
```yaml
variables:
  link_value: "nolink"
dotfiles:
  f_test:
    src: test
    dst: ~/.test
    link: "{{@@ link_value @@}}"
profiles:
  linux:
    dotfiles:
    - f_test
    variables:
      link_value: "link"
  windows:
    dotfiles:
    - f_test
```

Make sure to quote the link value in the config file.

## Dynamic actions

Variables ([config variables and dynvariables](config.md#variables)
and [template variables](templating.md#template-variables)) can be used
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
the use of variables ([variables and dynvariables](config.md#variables)
and [template variables](templating.md#template-variables)).

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
