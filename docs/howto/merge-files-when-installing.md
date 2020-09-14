# Merge files on install

Dotdrop allows to merge multiple files into one using the jinja2's `include` directive.

For example let's consider you want to keep your `vimrc` split into multiple parts in dotdrop
* `<dotpath>/vimrc.d/top`: top part of the file
* `<dotpath>/vimrc.d/bottom`: bottom part of the file

And you want dotdrop to merge all those files into `~/.vimrc` whenever you process your vimrc with dotdrop.

First make sure `~/.vimrc` is present in your config file
```yaml
...
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
profiles:
  hostname:
    dotfiles:
    - f_vimrc
...
```

Note that the subfiles (`vimrc.d/top` and `vimrc.d/bottom`)
are not known to the config and do not need to be.

Edit the stored vimrc file to include the other files, for example:
```bash
$ cat <dotpath>/vimrc
{%@@ include 'vimrc.d/top' @@%}
filetype on
set t_Co=256
set tw=0
set tabstop=2
set shiftwidth=2
set expandtab
set nocompatible
set nomodeline
syntax on
{%@@ include 'vimrc.d/bottom' @@%}
```

The `include` path parameter needs to be relative to your `dotpath`.

Dotdrop will then automagically include the files into your vimrc when handling `f_vimrc`.

## Merge all files in a directory

To include all files in a directory, a combination of
[dynvariables](../config-details.md#entry-dynvariables)
and [jinja2 directives](http://jinja.pocoo.org/docs/2.10/) have to be used.

Let's say all files in `<dotpath>/toinclude` need to be included into a dotfile.

First define a [dynvariables](../config-details.md#entry-dynvariables)
in the config file which will look for files to include in the above directory:
```yaml
dynvariables:
  allfiles: "cd {{@@ _dotdrop_dotpath @@}}; find toinclude/ -type f | xargs"
```

Note that `_dotdrop_dotpath` is part of the built-in variables
(for more see [template variables](../templating.md#template-variables)).

And then use the generated list in the dotfile template:
```
{%@@ for f in allfiles.split() @@%}
  {%@@ include f @@%}
{%@@ endfor @@%}
```
