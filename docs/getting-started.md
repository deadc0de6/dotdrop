# Getting started

## Repository setup

Either create a Git repository on your prefered platform and clone it or create one locally.
This repository will contain two main elements, dotdrop's config file (`config.yaml`)
and a directory containing all your dotfiles managed by dotdrop.
```bash
## clone your repository (my-dotfiles)
$ git clone <some-url>/my-dotfiles
$ cd my-dotfiles

## within the repository create a directory to store your dotfiles
## (refered by "dotpath" in the config, which defaults to "dotfiles")
$ mkdir dotfiles
```

Then add a config file. You can get a
[minimal config file](https://github.com/deadc0de6/dotdrop/blob/master/config.yaml)
from dotdrop's repository with:
```bash
$ wget https://raw.githubusercontent.com/deadc0de6/dotdrop/master/config.yaml
```
It is recommended to store your config file directly within your repository
(*my-dotfiles* in the example above), but you could save it in different places if you wish;
see [config location](config/config-file.md#location) for more.

```bash
$ tree my-dotfiles
my-dotfiles
├── config.yaml
└── dotfiles
```

If your config file is in an exotic location, you can add an alias
in your preferred shell to call dotdrop with the config file path argument.
```
alias dotdrop='dotdrop --cfg=<path-to-your-config.yaml>'
```

For more info on the config file format, see [the config file doc](config/config-file.md).

## Basic usage

The basic use of dotdrop is:

* Import a file/directory to manage (this will copy the files from the filesystem to your `dotpath`): `dotdrop import <somefile>`
* Install the dotfiles (this will *copy/link* them from your `dotpath` to the filesystem): `dotdrop install`

Then if you happen to update the file/directory directly on the filesystem (add a new file/dir, edit content, etc.) you can use the `update` command to mirror back those changes in dotdrop.

For more advanced uses:

* `dotdrop --help` for the CLI usage.
* [The usage doc](usage.md)
* [The example](https://github.com/deadc0de6/dotdrop#getting-started)
* [The howto](howto/howto.md)