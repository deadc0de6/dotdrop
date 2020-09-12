* [Dotfile actions](#dotfile-actions)
* [Default actions](#default-actions)
* [Profile actions](#profile-actions)
* [Fake dotfile and actions](#fake-dotfile-and-actions)

---

**Note**: any action with a key starting with an underscore (`_`) won't be shown in output. 
This can be useful when working with sensitive data containing passwords for example. 

# Dotfile actions

It is sometimes useful to execute some kind of action
when deploying a dotfile. 

Note that dotfile actions are only
executed when the dotfile is installed.

For example let's consider
[Vundle](https://github.com/VundleVim/Vundle.vim) is used
to manage vim's plugins, the following action could
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

Thus when `f_vimrc` is installed, the command
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

If you don't specify neither `post` nor `pre`, the action will be executed
after the dotfile deployment (which is equivalent to `post`).
Actions cannot obviously be named `pre` or `post`.

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

# Default actions

Dotdrop allows to execute an action for any dotfile installation. These actions work as any other action (*pre* or *post*).

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

# Profile actions

Profile can be either `pre` or `post` actions. Those are executed before
any dotfile installation (for `pre`) and after all dotfiles installation (for `post`)
only if at least one dotfile has been installed.

# Fake dotfile and actions

*Fake* dotfile can be created by specifying no `dst` and no `src` (see [config format](https://github.com/deadc0de6/dotdrop/wiki/config#format)). By binding an action to such a *fake* dotfile, you make sure the action is always executed since *fake* dotfile are always considered installed.

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
