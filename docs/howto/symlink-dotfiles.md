# Symlink dotfiles

Dotdrop offers two ways to symlink a dotfile through its
config entry `link`

* setting `link: link` for a dotfile will symlink `dst` to `src`
* setting `link: link_children` will, for every direct children of `src`, symlink `dst/<childrenX>` to `src/<childrenX>` (see [Link children](#link-children))

Where `src` is considered as the file stored in your *dotpath* and
`dst` as the file located in your `$HOME`.

Note that if the dotfile is using template directives, it will be symlinked into
`~/.config/dotdrop` instead of directly into your *dotpath*
(see [Templating symlinked dotfiles](#templating-symlinked-dotfiles))

# Link children

This feature can be very useful for dotfiles when you don't want the entire
directory to be symlink but still want to keep a clean config files (with a
limited number of entries).

*Make sure to do a backup of your dotfiles with something like `cp -r <my-important-dotfile>{,.bak}`*

A good example of its use is when managing `~/.vim` with dotdrop.

Here's what it looks like when using `link: link`.
```yaml
config:
  dotpath: dotfiles
dotfiles:
  vim:
    dst: ~/.vim
    src: vim
    link: link
```

The top directory `~/.vim` is symlinked to the `<dotpath>/vim` location
```bash
$ readlink ~/.vim
~/.dotfiles/vim/
$ ls ~/.dotfiles/vim/
after  autoload  plugged  plugin  snippets  spell  swap  vimrc
```

As a result, all files under `~/.vim` will be managed by
dotdrop (including unwanted directories like `spell`, `swap`, etc).

A cleaner solution is to use `link_children` which allows to only symlink
files under the dotfile directory. Let's say only `after`, `plugin`, `snippets`, and `vimrc`
need to be managed in dotdrop. `~/.vim` is imported in dotdrop, cleaned off all unwanted
files/directories and then the `link` entry is set to `link_children` in the config file.
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

# Templating symlinked dotfiles

For dotfiles not using any templating directives, those are directly linked
to dotdrop's `dotpath` directory (see [Config](../config.md)).

When using templating directives however the dotfiles are first installed into
`workdir` (defaults to *~/.config/dotdrop*, see [Config](../config.md))
and then symlinked there.
This applies to both dotfiles with `link: link` and `link: link_children`.

For example
```bash
# with template
/home/user/.xyz -> /home/user/.config/dotdrop/.xyz

# without template
/home/user/.xyz -> /home/user/dotfiles/xyz
```
