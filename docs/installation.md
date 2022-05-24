# Installation

Installing dotdrop [as a submodule](#as-a-submodule) is the recommended way.

If you want to keep your Python environment clean, use the virtualenv installation instructions
(see [As a submodule in a virtualenv](#as-a-submodule-in-a-virtualenv) and
[PyPI package in a virtualenv](#pypi-package-in-a-virtualenv)).
In that case, the virtualenv environment might need to be loaded before any attempt to use dotdrop.

## As a submodule

The following will create a Git repository for your dotfiles and
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

For macOS users, make sure to install `realpath` through Homebrew
(part of *coreutils*).

Using this solution will require you to work with dotdrop by
using the generated script `dotdrop.sh` at the root
of your dotfiles repository.

To ease the use of dotdrop, it is recommended to add an alias to it in your
shell with the config file path; for example:
```
alias dotdrop=<absolute-path-to-dotdrop.sh> --cfg=<path-to-your-config.yaml>'
```

## As a submodule in a virtualenv

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

When using a virtualenv, make sure to source the environment before using dotdrop:
```bash
$ source env/bin/activate
$ ./dotdrop.sh --help
```

Then follow the instructions under [As a submodule](#as-a-submodule).

## PyPI package

Install dotdrop:
```bash
$ pip3 install dotdrop --user
```

and then [set up your repository](repository-setup.md).

## PyPI package in a virtualenv

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

## Homebrew package

Install dotdrop from Homebrew with:
```bash
$ brew install dotdrop
```

## Aur packages

Dotdrop is available on aur:

* Stable: <https://aur.archlinux.org/packages/dotdrop/>
* Git version: <https://aur.archlinux.org/packages/dotdrop-git/>

Make sure to install the [python-magic-ahupp](https://aur.archlinux.org/packages/python-magic-ahupp/) from aur.

Then follow the [doc to setup your repository](repository-setup.md).

## Snap package

Dotdrop is available as a snap package: <https://snapcraft.io/dotdrop>.

Install it with:
```bash
snap install dotdrop
```

Then follow the [doc to setup your repository](repository-setup.md).

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
use the `--cfg` to make it point to your config file.

```bash
$ cd dotdrop/
$ ./dotdrop.sh --cfg <my-config-file> files
```

## Dependencies

Beside the Python dependencies defined in [requirements.txt](https://github.com/deadc0de6/dotdrop/blob/master/requirements.txt),
dotdrop depends on the following tools:

* `diff` (unless a different tool is used, see [diff_command](config-format.md#config-entry))
* `git` (only if using the entry point script [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh))
* `readlink` or `realpath` (only if using the entry point script [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh))

For macOS users, make sure to install the below packages through [Homebrew](https://brew.sh/):

* [coreutils](https://formulae.brew.sh/formula/coreutils) (only if using the entry point script [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh) which uses realpath)
* [libmagic](https://formulae.brew.sh/formula/libmagic) (for python-magic)

For WSL (Windows Subsystem for Linux), make sure to install `python-magic-bin`:
```bash
pip install python-magic-bin
```

## Update dotdrop submodule

If using dotdrop as a submodule, one can control if dotdrop
is auto-updated through the [dotdrop.sh](https://github.com/deadc0de6/dotdrop/blob/master/dotdrop.sh)
script by defining the environment variable `DOTDROP_AUTOUPDATE=yes`.
If undefined, `DOTDROP_AUTOUPDATE` will take the value `yes`.

If used as a submodule, update it with:
```bash
$ git submodule update --init --recursive
$ git submodule update --remote dotdrop
```

You will then need to commit the changes with:
```bash
$ git add dotdrop
$ git commit -m 'update dotdrop'
$ git push
```

## Downgrade dotdrop submodule

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

## Shell completion

Completion scripts exist for `bash`, `zsh` and `fish`;
see [the related doc](https://github.com/deadc0de6/dotdrop/blob/master/completion/README.md).

## Highlighters

Highlighters for dotdrop templates are available [here](https://github.com/deadc0de6/dotdrop/tree/master/highlighters).
