# Symlink dotfiles

Dotdrop offers two ways to symlink a dotfile through its
config entry `link`:

* Setting `link: link` for a dotfile will symlink `dst` to `src`
* Setting `link: link_children` will, for every direct child of `src`, symlink `dst/<childrenX>` to `src/<childrenX>` (See [Link children](#link-children))

where `src` is the file stored in your *dotpath* and
`dst` is the file located in your `$HOME`.

Note that if the dotfile uses template directives, it will be symlinked into
`~/.config/dotdrop` instead of directly into your *dotpath*
(see [Templating symlinked dotfiles](#templating-symlinked-dotfiles))

Although the config entries `link_on_import` and `link_dotfile_default` can be set to the value `link_children`,
it is not recommended, since operations on a dotfile that is not a directory with the option `link_children`
will fail.

## Symlink a dotfile

Below is an ad-hoc way to symlink a dotfile when [link_dotfile_default](https://dotdrop.readthedocs.io/en/latest/config-format/#config-entry)
and [link_on_import](https://dotdrop.readthedocs.io/en/latest/config-format/#config-entry) use their default values.

Import the file:
```bash
$ ./dotdrop.sh import ~/.bashrc
	-> "/home/user/.bashrc" imported
```

Edit the `config.yaml` and set the `link` value to `link`:
```yaml
dotfiles:
  f_bashrc:
    src: bashrc
    dst: ~/.bashrc
    link: link
```

Install the dotfile, which will remove your `~/.bashrc` and replace it with a link to the file stored in dotdrop:
```bash
$ ./dotdrop.sh install
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
limited number of entries).

Setting this option on a file that is not a directory will make any operation on the dotfile fail.

*Make sure to do a backup of your dotfiles with something like `cp -r <my-important-dotfile>{,.bak}`.*

A good example of its use is when managing `~/.vim` with dotdrop.

Here's what it looks like when using `link: link`:
```yaml
config:
  dotpath: dotfiles
dotfiles:
  vim:
    dst: ~/.vim
    src: vim
    link: link
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

A cleaner solution is to use `link_children` which allows to only symlink
files under the dotfile directory. Let's say only `after`, `plugin`, `snippets`, and `vimrc`
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
to dotdrop's `dotpath` directory (see [the config file doc](../config-file.md)).

When using templating directives, however, the dotfiles are first installed into
`workdir` (defaults to *~/.config/dotdrop*; see [the doc](../config-config.md))
and then symlinked there.
This applies to both dotfiles with `link: link` and `link: link_children`.

For example:
```bash
# with template
/home/user/.xyz -> /home/user/.config/dotdrop/.xyz

# without template
/home/user/.xyz -> /home/user/dotfiles/xyz
```
