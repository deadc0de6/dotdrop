* [ignore patterns](#ignore-patterns)
* [examples](#examples)

---

# ignore patterns

It is possible to ignore specific patterns when using dotdrop. For example for `compare` when temporary
files don't need to appear in the output.

* for [install](../usage.md#install-dotfiles)
    * using `instignore` in [the config file](config.md)
* for [compare](../usage.md#compare-dotfiles)
    * using `cmpignore` in [the config file](config.md)
    * using the command line switch `-i --ignore`
* for [update](../usage.md#update-dotfiles)
    * using `upignore` in [the config file](config.md)
    * using the command line switch `-i --ignore`

The ignore pattern must follow Unix shell-style wildcards like for example `*/path/to/file`.
Make sure to quote those when using wildcards in the config file.

Patterns used on a specific dotfile can be specified relative to the dotfile destination (`dst`).

```yaml
config:
  cmpignore:
  - '*/README.md'
  upignore:
  - '*/README.md'
  instignore:
  - '*/README.md'
...
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    upignore:
    - "*/undo-dir"
    - "*/plugged"
...
```

# examples

To completely ignore comparison of a specific dotfile:
```yaml
dotfiles:
  d_vim
    dst: ~/.vim
    src: vim
    cmpignore:
    - "*"
```

To ignore specific directory when updating
```yaml
dotfiles:
  d_colorpicker:
    src: config/some_directory
    dst: ~/.config/some_directory
    upignore:
      - '*sub_directory_to_ignore'
```
