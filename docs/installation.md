# Installation

* [As a submodule](#as-a-submodule)
* [As a submodule in a virtualenv](#as-a-submodule-in-a-virtualenv)
* [Submodule upgrade/downgrade](#submodule-upgradedowngrade)
* [PyPI package](#pypi-package)
- [pipx install](#pipx-install)
* [Homebrew package](#homebrew-package)
* [Debian unstable (sid)](#debian)
* [Ubuntu lunar (23.04)](#ubuntu)
* [AUR packages](#aur-packages)
* [Snap package](#snap-package)
* [From source](#from-source)
* [Pacstall package](https://github.com/pacstall/pacstall-programs/blob/master/packages/dotdrop/dotdrop.pacscript)

## As a submodule

Having dotdrop as a submodule guarantees that anywhere
you are cloning your dotfiles Git tree from you will have dotdrop shipped with it.
Note that when using dotdrop as a submodule you will be tracking the master branch (and not a specific version)

The following will create a Git repository for your dotfiles and
keep dotdrop as a submodule.
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

For macOS users, make sure to install `realpath` through Homebrew
(part of *coreutils*) and `libmagic`.

Using dotdrop as a submodule will require you to work with dotdrop by
using the generated script `dotdrop.sh` at the root
of your dotfiles repository. Note that this script updates the submodule
automatically unless called with the environment variable `DOTDROP_AUTOUPDATE`
set to `no`.

If you happened to encounter `ModuleNotFoundError` error after an
update, it means the dependencies have changed and you should re-install
dependencies with
```bash
pip3 install --user -r dotdrop/requirements.txt
```

To ease the use of dotdrop, it is recommended to add an alias to it in your
shell with the config file path; for example:
```
alias dotdrop=<absolute-path-to-dotdrop.sh> --cfg=<path-to-your-config.yaml>'
```

## As a submodule in a virtualenv

To install it in a [virtualenv](https://virtualenv.pypa.io):
```bash
## create the repository
$ mkdir dotfiles; cd dotfiles
$ git init

## install dotdrop as a submodule
$ git submodule add https://github.com/deadc0de6/dotdrop.git
$ virtualenv -p python3 env
$ echo 'env' >> .gitignore
$ env/bin/pip install -r dotdrop/requirements.txt
$ ./dotdrop/bootstrap.sh

# add the following in your .bashrc/.zshrc/etc
# or hardcode it in the dotdrop.sh script
$ export DOTDROP_VIRTUALENV=env

## use dotdrop
$ ./dotdrop.sh --help
```

When using a virtualenv, make sure to export the `DOTDROP_VIRTUALENV`
variable with the directory name of your virtualenv:
```bash
$ export DOTDROP_VIRTUALENV=env
$ ./dotdrop.sh --help
```

Then follow the instructions under [As a submodule](#as-a-submodule).

## Submodule upgrade/downgrade

### Upgrade dotdrop submodule

If using dotdrop as a submodule, one can control if dotdrop
is auto-updated through the [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh)
script by defining the environment variable `DOTDROP_AUTOUPDATE=yes`.
If undefined, `DOTDROP_AUTOUPDATE` will take the value `yes`.

If used as a submodule, update it with:
```bash
$ git submodule update --init --recursive
$ git submodule update --remote dotdrop

## install dependencies
$ pip3 install --user -r dotdrop/requirements.txt
```

You will then need to commit the changes with:
```bash
$ git add dotdrop
$ git commit -m 'update dotdrop'
$ git push
```

### Downgrade dotdrop submodule

If you wish to get a specific version of dotdrop when using
it as a submodule, the following operations can be done.

Here dotdrop is downgraded to the latest stable version:
```bash
## enter the repository containing the dotdrop submodule
$ cd my-dotfiles
## enter the dotdrop submodule
$ cd dotdrop
## update the list of tags
$ git fetch --tags
## checkout the latest stable version
$ git checkout `git tag -l | tail -1`
```

If using the `dotdrop.sh` script, make sure it doesn't
automatically update dotdrop back to the latest commit.

## PyPI package

[PyPI package](https://pypi.org/project/dotdrop/)

Install dotdrop:
```bash
$ pip3 install dotdrop --user
```

### PyPI package in a virtualenv

Install dotdrop from PyPI in a virtualenv:
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

Then follow the instructions under [PyPI package](#pypi-package).

## pipx install

[pipx](https://pipx.pypa.io/) allows to install a package in an isolated
environment.

It is packaged in all main Linux distributions, and macOS.

### PyPI package with pipx

To install the last PyPI package:
```bash
$ pipx install dotdrop
```

To upgrade an installed package to the last version.
```bash
$ pipx upgrade dotdrop
```

### From GitHub with pipx

To install the from the master branch on GitHub

```bash
$ pipx install git+https://github.com/deadc0de6/dotdrop.git
```

You can choose a branch or commit
```bash
$ pipx install git+https://github.com/deadc0de6/dotdrop.git@2c462c3
```

## Homebrew package

[Homebrew package](https://formulae.brew.sh/formula/dotdrop)

Install dotdrop from Homebrew with:
```bash
$ brew install dotdrop
```

## Debian

dotdrop is a
[Debian package](https://packages.debian.org/dotdrop) since bookworm (Debian 12), be
warned that the Debian version is usually behind the last stable release.

Install dotdrop
```bash
$ sudo apt install dotdrop
```

## Ubuntu

[Ubuntu package](https://packages.ubuntu.com/lunar/dotdrop) since lunar (23.04)

Install dotdrop
```bash
$ sudo apt install dotdrop
```

## Aur packages

Dotdrop is available on aur:

* Stable: <https://aur.archlinux.org/packages/dotdrop/>
* Git version: <https://aur.archlinux.org/packages/dotdrop-git/>

## Snap package

Dotdrop is available as a snap package: <https://snapcraft.io/dotdrop>.

Install it with:
```bash
$ snap install dotdrop
```

If you encounter warnings like `Warning: using regular magic file`,
try defining the following environment variable:
```bash
export MAGIC=$SNAP/usr/share/file/magic.mgc
```

## From source

Clone the repository:
```bash
$ git clone https://github.com/deadc0de6/dotdrop.git
```

Start using it directly through the `dotdrop.sh` script and
use the `--cfg` switch to make it point to your config file.

```bash
$ cd dotdrop/
$ ./dotdrop.sh --cfg <my-config-file> files
```

## Dependencies

Beside the Python dependencies defined in [requirements.txt](https://github.com/deadc0de6/dotdrop/blob/master/requirements.txt),
dotdrop depends on the following tools:

* `diff` (unless a different tool is used, see [diff_command](config/config-config.md#config-block))
* `git` (only if using the entry point script [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh))

For macOS users, make sure to install the below packages through [Homebrew](https://brew.sh/):

* [libmagic](https://formulae.brew.sh/formula/libmagic) (for python-magic)

For WSL (Windows Subsystem for Linux), make sure to install `python-magic-bin`:
```bash
pip install python-magic-bin
```

## Shell completion

Completion scripts exist for `bash`, `zsh` and `fish`;
see [the related doc](https://github.com/deadc0de6/dotdrop/blob/master/completion/README.md).

## Highlighters

Highlighters for dotdrop templates are available [here](https://github.com/deadc0de6/dotdrop/tree/master/highlighters).
