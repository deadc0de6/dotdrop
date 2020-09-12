# Installation

Installing dotdrop [as a submodule](#as-a-submodule) is the recommended way.

If you want to keep your python environment clean, use the virtualenv installation instructions
(see [As a submodule in a virtualenv](#as-a-submodule-in-a-virtualenv) and
[With pypi in a virtualenv](#with-pypi-in-a-virtualenv)).
In that case, the virtualenv environment might need to be loaded before any attempt to use dotdrop.

Installation instructions

* Installation
  * [Install as a submodule](#as-a-submodule)
  * [Install as a submodule in a virtualenv](#as-a-submodule-in-a-virtualenv)
  * [Install with pypi](#with-pypi)
  * [Install with pypi in a virtualenv](#with-pypi-in-a-virtualenv)
  * [Aur packages](#aur-packages)
  * [Snap package](#snap-package)
* [Setup your repository](#setup-your-repository)
* [Shell completion](#shell-completion)
* [Dependencies](dependencies)

# As a submodule

The following will create a git repository for your dotfiles and
keep dotdrop as a submodule:
```bash
## create the repository
$ mkdir dotfiles; cd dotfiles
$ git init

## install dotdrop as a submodule
$ git submodule add https://github.com/deadc0de6/dotdrop.git
$ pip3 install --user -r dotdrop/requirements.txt
$ ./dotdrop/bootstrap.sh

## use dotdrop
$ ./dotdrop.sh --help
```

For MacOS users, make sure to install `realpath` through homebrew
(part of *coreutils*).

Using this solution will need you to work with dotdrop by
using the generated script `dotdrop.sh` at the root
of your dotfiles repository.

To ease the use of dotdrop, it is recommended to add an alias to it in your
shell with the config file path, for example
```
alias dotdrop=<absolute-path-to-dotdrop.sh> --cfg=<path-to-your-config.yaml>'
```

# As a submodule in a virtualenv

To install in a [virtualenv](https://virtualenv.pypa.io):
```bash
## create the repository
$ mkdir dotfiles; cd dotfiles
$ git init

## install dotdrop as a submodule
$ git submodule add https://github.com/deadc0de6/dotdrop.git
$ virtualenv -p python3 env
$ echo 'env' > .gitignore
$ source env/bin/activate
$ pip install -r dotdrop/requirements.txt
$ ./dotdrop/bootstrap.sh

## use dotdrop
$ ./dotdrop.sh --help
```

When using a virtualenv, make sure to source the environment before using dotdrop
```bash
$ source env/bin/activate
$ ./dotdrop.sh --help
```

Then follow the instructions under [As a submodule](#as-a-submodule).

# With pypi

Install dotdrop
```bash
$ pip3 install --user dotdrop
```

and then [setup your repository](#setup-your-repository).

# With pypi in a virtualenv

Install dotdrop in a virtualenv from pypi
```bash
$ virtualenv -p python3 env
$ source env/bin/activate
$ pip install dotdrop
```

When using a virtualenv, make sure to source the environment
before using dotdrop:
```bash
$ source env/bin/activate
$ dotdrop --help
```

Then follow the instructions under [With pypi](#with-pypi).

# Aur packages

Dotdrop is available on aur:
* stable: https://aur.archlinux.org/packages/dotdrop/
* git version: https://aur.archlinux.org/packages/dotdrop-git/

Then follow the [doc to setup your repository](#setup-your-repository).

# Snap package

Dotdrop is available as a snap package: <https://snapcraft.io/dotdrop>

Install it with
```bash
snap install dotdrop
```

Then follow the [doc to setup your repository](#setup-your-repository).

# Setup your repository

Either create a repository on your prefered platform and clone it or create one locally.
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
from dotdrop's repository with
```bash
$ wget https://raw.githubusercontent.com/deadc0de6/dotdrop/master/config.yaml
```
It is recommended to store your config file directly within your repository
(*my-dotfiles* in the example above) but you could save it in different places if you wish,
see [this doc](https://github.com/deadc0de6/dotdrop/wiki/config#location) for more.

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

For more info on the config file format, see [the config doc](https://github.com/deadc0de6/dotdrop/wiki/config)

Finally start using dotdrop with `dotdrop --help`. See the [usage doc](https://github.com/deadc0de6/dotdrop/wiki/usage) and [the example](https://github.com/deadc0de6/dotdrop/blob/master/README.md#getting-started).

# Shell completion

Completion scripts exist for `bash`, `zsh` and `fish`, see [the related doc](completion/README.md).