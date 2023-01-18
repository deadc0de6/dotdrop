# Symlink dotfiles

Dotdrop is able to install dotfiles in four different ways,
which are controlled by the `link` config attribute of each dotfile:

* `link: nolink`: The dotfile (file or directory) is copied to its destination
* `link: absolute`: The dotfile (file or directory) is linked to its destination using an absolute symlink
* `link: relative`: The dotfile (file or directory) is linked to its destination using a relative symlink
* `link: link_children`: The direct children of the dotfile (directory only) are symlinked to their destination. For every direct child of `src`, symlink `dst/<childrenX>` to `src/<childrenX>` (See [Link children](#link-children))

Note that if the dotfile uses template directives, it will first be installed to your
`workdir` (defaults to `~/.config/dotdrop`) and then symlinked
(see [Templating symlinked dotfiles](#templating-symlinked-dotfiles)).

Although the config entries `link_on_import` and `link_dotfile_default` can be set to the value `link_children`,
it is not recommended, since operations on a dotfile that is not a directory with the option `link_children`
will fail.

## Symlink a dotfile

Below is an ad-hoc way to symlink a dotfile when [link_dotfile_default](https://dotdrop.readthedocs.io/en/latest/config/config-config/)
and [link_on_import](https://dotdrop.readthedocs.io/en/latest/config/config-config/) use their default values.

Import the file:
```bash
$ dotdrop import ~/.bashrc
	-> "/home/user/.bashrc" imported
```

Edit the `config.yaml` and set the `link` value to `absolute`:
```yaml
dotfiles:
  f_bashrc:
    src: bashrc
    dst: ~/.bashrc
    link: absolute
```

Install the dotfile, which will remove your `~/.bashrc` and replace it with a link to the file stored in dotdrop:
```bash
$ dotdrop install
Remove "/home/user/.bashrc" for link creation? [y/N] ? y
	-> linked /home/user/.bashrc to /home/user/dotdrop/dotfiles/bashrc

1 dotfile(s) installed.
```

The dotfile then points to the file in dotdrop:
```bash
$ readlink ~/.bashrc
/home/user/dotdrop/dotfiles/bashrc
```

## Link children

The `link_children` option can be very useful for dotfiles when you don't want the entire
directory to be symlinked but still want to keep a clean config file (with a
limited number of entries). Note that `link_children` can only be applied to directories.

*Make sure to do a backup of your dotfiles with something like `cp -r <my-important-dotfile>{,.bak}`.*

A good example of its use is when managing `~/.vim` with dotdrop.
First let's see what it looks like when using `link: absolute`:
```yaml
config:
  dotpath: dotfiles
dotfiles:
  vim:
    dst: ~/.vim
    src: vim
    link: absolute
```

The top directory `~/.vim` is symlinked to the `<dotpath>/vim` location:
```bash
$ readlink ~/.vim
~/.dotfiles/vim/
$ ls ~/.dotfiles/vim/
after  autoload  plugged  plugin  snippets  spell  swap  vimrc
```

As a result, all files under `~/.vim` will be managed by
dotdrop (including unwanted directories like `spell`, `swap`, etc.).

Now with `link_children` dotdrop allows to only symlink
direct children of the dotfile directory. Let's say only `after`, `plugin`, `snippets`, and `vimrc`
need to be managed in dotdrop. `~/.vim` is imported in dotdrop and cleaned of all unwanted
files/directories, and then the `link` entry is set to `link_children` in the config file:
```yaml
config:
  dotpath: dotfiles
dotfiles:
  vim:
    dst: ~/.vim/
    src: vim
    link: link_children
```

Now all children of the `vim` dotfile's directory in the *dotpath* will be symlinked under `~/.vim/`
without affecting the rest of the local files, keeping the config file clean
and all unwanted files only on the local system.
```bash
$ readlink -f ~/.vim
~/.vim
$ tree -L 1 ~/.vim
~/.vim
├── after -> ~/.dotfiles/vim/after
├── autoload
├── plugged
├── plugin -> ~/.dotfiles/vim/plugin
├── snippets -> ~/.dotfiles/vim/snippets
├── spell
├── swap
└── vimrc -> ~/.dotfiles/vim/vimrc
```

## Templating symlinked dotfiles

Dotfiles not using any templating directives are directly linked
to dotdrop's `dotpath` directory (see [the config file doc](../config/config-file.md)).

When using templating directives, however, the dotfiles are first installed into
`workdir` (defaults to *~/.config/dotdrop*; see [the doc](../config/config-config.md))
and then symlinked there.
This applies to both dotfiles with `link: absolute|relative` and `link: link_children`.

For example:
```bash
# with template
/home/user/.xyz -> /home/user/.config/dotdrop/.xyz

# without template
/home/user/.xyz -> /home/user/dotfiles/xyz
```
