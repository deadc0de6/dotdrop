# Dotfiles block

The **dotfiles** entry (mandatory) contains a YAML object with sub-objects for the dotfiles managed by dotdrop.  The entries in the sub-objects are as follows:

Entry    | Description
-------- | -------------
`dst` | Where this dotfile needs to be deployed (dotfiles with empty `dst` are ignored and considered installed, can use `variables`, make sure to quote)
`src` | Dotfile path within the `dotpath` (dotfiles with empty `src` are ignored and considered installed, can use `variables`, make sure to quote)
`link` | Defines how this dotfile is installed. Possible values: *nolink*, *absolute*, *relative*, *link_children* (See [Symlinking dotfiles](config-file.md#symlinking-dotfiles)) (defaults to value of `link_dotfile_default`)
`actions` | List of action keys that need to be defined in the **actions** entry below (See [actions](config-actions.md))
`chmod` | Defines the file permissions in octal notation to apply during installation or the special keyword `preserve` (See [permissions](config-file.md#permissions))
`cmpignore` | List of patterns to ignore when comparing (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns))
`ignore_missing_in_dotdrop` | Ignore missing files in dotdrop when comparing and importing (see [Ignore missing](config-file.md#ignore-missing))
`ignoreempty` | If true, an empty template will not be deployed (defaults to the value of `ignoreempty`)
`instignore` | List of patterns to ignore when installing (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns))
`template` | If false, disable templating for this dotfile (defaults to the value of `template_dotfile_default`)
`trans_install` | Transformation key to apply when installing this dotfile (must be defined in the **trans_install** entry below; see [transformations](config-transformations.md))
`trans_update` | Transformation key to apply when updating this dotfile (must be defined in the **trans_update** entry below; see [transformations](config-transformations.md))
`upignore` | List of patterns to ignore when updating (enclose in quotes when using wildcards; see [ignore patterns](config-file.md#ignore-patterns))
<s>link_children</s> | Replaced by `link: link_children`
<s>trans</s> | Replaced by `trans_install`
<s>trans_read</s> | Replaced by `trans_install`
<s>trans_write</s> | Replaced by `trans_update`

```yaml
<dotfile-key-name>:
  dst: <where-this-file-is-deployed>
  src: <filename-within-the-dotpath>
  ## Optional
  link: (nolink|absolute|relative|link_children)
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
  trans_install: <transformation-key>
  trans_update: <transformation-key>
```

## Dotfile actions

It is sometimes useful to execute some kind of action
when deploying a dotfile.

Note that a dotfile's actions are only
executed when the dotfile is installed (that is, when
the version present in dotdrop differs from the one
in the filesystem).

For example, let's consider Vundle, used
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

## Dynamic dotfile paths

Dotfile source (`src`) and destination (`dst`) paths can be dynamically constructed using
defined variables ([variables and dynvariables](config-file.md#variables)).

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
defined variables ([variables and dynvariables](config-file.md#variables)).

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
      link_value: "absolute"
  windows:
    dotfiles:
    - f_test
```

Make sure to quote the link value in the config file.