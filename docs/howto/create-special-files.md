# Create files on install

One way to create symlinks (or any other special file) is to use a combination of
[actions](../config/config-actions.md) and a *fake* dotfile.

Let's say, for example, you have a list of directories you want to link
from under `~/.original` to `~/symlinks`.
```bash
$ tree ~/.original
/home/user/.original
├── dir1
├── dir2
└── dir3
```

First you would store these directory names in a text file in your `<dotpath>/links.txt`:
```
dir1
dir2
dir3
```

The config file would contain different elements:

* A `dynvariables` that will read the above text file
* A few `variables` for the source and destination
* An action that will create the destination directory and symlink those directories
* A *fake* dotfile (with no `src` and no `dst` values) that will be always installed with the above action

```yaml
dynvariables:
  links_list: "cat {{@@ _dotdrop_dotpath @@}}/links.txt | xargs"
...
variables:
  links_dst: "{{@@ env['HOME'] @@}}/.symlinks"
  links_src: "{{@@ env['HOME'] @@}}/.original"
...
actions:
  symlink_them: 'mkdir -p "{1}" && for lnk in {0}; do ln -s "{{@@ links_src @@}}/$lnk" "{1}/$lnk"; done'
...
  fake:
    src:
    dst:
    actions:
      - symlink_them '{{@@ links_list @@}}' '{{@@ links_dst @@}}'
```

The result would be:
```bash
$ tree ~/.symlinks
/home/user/.symlinks
├── dir1 -> /home/user/.original/dir1
├── dir2 -> /home/user/.original/dir2
└── dir3 -> /home/user/.original/dir3
```

For reference, see [issue 243](https://github.com/deadc0de6/dotdrop/issues/243).
