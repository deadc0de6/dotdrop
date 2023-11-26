# <img src="https://raw.githubusercontent.com/deadc0de6/dotdrop/master/assets/dotdrop.svg" width="100" height="100" align="left"> dotdrop
<br/>
<br/>

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/deadc0de6/dotdrop)](https://github.com/deadc0de6/dotdrop/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)

[![Tests Status](https://github.com/deadc0de6/dotdrop/workflows/tests/badge.svg?branch=master)](https://github.com/deadc0de6/dotdrop/actions)
[![Doc Status](https://readthedocs.org/projects/dotdrop/badge/?version=latest)](https://dotdrop.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/github/deadc0de6/dotdrop/graph/badge.svg?token=SscGyrtgYL)](https://codecov.io/github/deadc0de6/dotdrop)
![CodeQL](https://github.com/deadc0de6/dotdrop/workflows/CodeQL/badge.svg)

[![Python](https://img.shields.io/pypi/pyversions/dotdrop.svg)](https://pypi.python.org/pypi/dotdrop)

[![PyPI](https://img.shields.io/pypi/v/dotdrop)](https://badge.fury.io/py/dotdrop)
[![Homebrew version](https://img.shields.io/homebrew/v/dotdrop)](https://formulae.brew.sh/formula/dotdrop)
[![AUR](https://img.shields.io/aur/version/dotdrop.svg)](https://aur.archlinux.org/packages/dotdrop)
[![Snap](https://badgen.net/snapcraft/v/dotdrop)](https://snapcraft.io/dotdrop)

[![Donate](https://img.shields.io/badge/donate-KoFi-blue.svg)](https://ko-fi.com/deadc0de6)

*Save your dotfiles once, deploy them everywhere*

[Dotdrop](https://github.com/deadc0de6/dotdrop) makes the management of dotfiles between different hosts easy.
It allows you to store your dotfiles in Git and automagically deploy
different versions of the same file on different setups.

It also allows to manage different *sets* of dotfiles.
For example, you can have a set of dotfiles for your home laptop and
a different set for your office desktop. Those sets may overlap, and different
versions of the same dotfiles can be deployed using different predefined *profiles*.
Or you may have a main set of dotfiles for your
everyday host and a subset you only need to deploy to temporary
hosts (cloud VM etc.) that may be using
a slightly different version of some of the dotfiles.

Features:

* Sync once every dotfile in Git for different usages
* Allow dotfile templating
* Dynamically generated dotfile contents with pre-defined variables
* Comparison between deployed and stored dotfiles
* Handling multiple profiles with different sets of dotfiles
* Easily import and update dotfiles
* Handle files and directories
* Support symlinking of dotfiles
* Associate actions to the deployment of specific dotfiles
* Associate transformations for storing encrypted/compressed dotfiles
* Provide solutions for handling dotfiles containing sensitive information

Check the [example](#getting-started), the [documentation](https://dotdrop.readthedocs.io/) or
how [people are using dotdrop](https://dotdrop.readthedocs.io/en/latest/misc/people-using-dotdrop/)
for more.

Quick start:
```bash
## using dotdrop as a submodule
mkdir dotfiles && cd dotfiles
git init
git submodule add https://github.com/deadc0de6/dotdrop.git
pip3 install -r dotdrop/requirements.txt --user
./dotdrop/bootstrap.sh
./dotdrop.sh --help
```

A mirror of this repository is available on GitLab under <https://gitlab.com/deadc0de6/dotdrop>.

## Why dotdrop?

There exist many tools to manage dotfiles; however, not
many allow to deploy different versions of the same dotfile
on different hosts. Moreover, dotdrop allows to specify the
set of dotfiles that need to be deployed for a specific profile.

See the [example](#getting-started) for a concrete example of
why [dotdrop](https://github.com/deadc0de6/dotdrop) rocks.

---

**Table of Contents**

* [Installation](#installation)
* [Getting started](#getting-started)
* [Documentation](#documentation)
* [Thank you](#thank-you)

# Installation

See the [installation instructions](https://dotdrop.readthedocs.io/en/latest/installation/).

Dotdrop is available on:

* [PyPI](https://pypi.org/project/dotdrop/)
* [Homebrew](https://formulae.brew.sh/formula/dotdrop)
* [AUR (stable)](https://aur.archlinux.org/packages/dotdrop/)
* [AUR (git version)](https://aur.archlinux.org/packages/dotdrop-git/)
* [Snapcraft](https://snapcraft.io/dotdrop)
* [Pacstall](https://github.com/pacstall/pacstall-programs/blob/master/packages/dotdrop/dotdrop.pacscript)

# Getting started

[Create a new repository](https://dotdrop.readthedocs.io/en/latest/getting-started/#repository-setup)
to store your dotfiles with dotdrop. *Init* or *clone* that new repository and
[install dotdrop](https://dotdrop.readthedocs.io/en/latest/installation/).

Then import any dotfiles (files or directories) you want to manage with dotdrop.
You can either use the default profile (which resolves to the *hostname* of the host
you are running dotdrop on) or provide it explicitly using the switch `-p`/`--profile`.

Import dotfiles on host *home*:
```bash
$ dotdrop import ~/.vimrc ~/.xinitrc ~/.config/polybar
```

Dotdrop does two things:

* Copy the dotfiles to the *dotpath* directory
  (defined in `config.yaml`, defaults to *dotfiles*)
* Create the associated entries in the `config.yaml` file
  (in the `dotfiles` and `profiles` entries)

Your config file will look like something similar to this:
```yaml
config:
  backup: true
  banner: true
  create: true
  dotpath: dotfiles
  ignoreempty: false
  keepdot: false
  longkey: false
  showdiff: false
  workdir: ~/.config/dotdrop
dotfiles:
  d_polybar:
    dst: ~/.config/polybar
    src: config/polybar
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
  f_xinitrc:
    dst: ~/.xinitrc
    src: xinitrc
profiles:
  home:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
```
For a description of the different fields and their use,
see the [config doc](https://dotdrop.readthedocs.io/en/latest/config/config-config/).

Commit and push your changes with git.

Then go to another host where your dotfiles need to be managed as well,
clone the previously set up repository,
and compare the local dotfiles with the ones stored in dotdrop:
```bash
$ dotdrop compare --profile=home
```

Now you might want to adapt the `config.yaml` file to your liking on
that second host. Let's say, for example, that you only want `d_polybar` and
`f_xinitrc` to be deployed on that second host. You would then change your config
to something like this (assuming that the second host's hostname is *office*):
```yaml
…
profiles:
  home:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
  office:
    dotfiles:
    - f_xinitrc
    - d_polybar
```

Then adapt any dotfile using the [templating](https://dotdrop.readthedocs.io/en/latest/template/templating/)
feature (if needed). For example, you might want different fonts sizes in Polybar for each host.

Edit `<dotpath>/config/polybar/config`:
```bash
…
{%@@ if profile == "home" @@%}
font0 = sans:size=10;0
{%@@ elif profile == "office" @@%}
font0 = sans:size=14;0
{%@@ endif @@%}
font1 = "Material Design Icons:style=Regular:size=14;0"
font2 = "unifont:size=6;0"
…
```

You also want to have the correct interface set on the wireless network in
the Polybar config.

Add a [variable](https://dotdrop.readthedocs.io/en/latest/config/config-variables/)
to the config file (In the below example, *home* gets the default `wlan0` value for
the variable `wifi` while *office* gets `wlp2s0`):
```yaml
…
variables:
  wifi: "wlan0"
…
profiles:
  home:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
  office:
    dotfiles:
    - f_xinitrc
    - d_polybar
    variables:
      wifi: "wlp2s0"
```

Then you can adapt the Polybar config file so that the
variable `wifi` gets correctly replaced during installation:
```bash
[module/wireless-network]
type = internal/network
interface = {{@@ wifi @@}}
```

Also, the home computer is running [awesomeWM](https://awesomewm.org/),
and the office computer [bspwm](https://github.com/baskerville/bspwm).
The `~/.xinitrc` file will therefore be different while still sharing some lines.

Edit `<dotpath>/xinitrc`:
```bash
#!/bin/bash

# load Xresources
userresources=$HOME/.Xresources
if [ -f "$userresources" ]; then
      xrdb -merge "$userresources" &
fi

# launch the wm
{%@@ if profile == "home" @@%}
exec awesome
{%@@ elif profile == "office" @@%}
exec bspwm
{%@@ endif @@%}
```

Finally you want everything installed with the *office* profile
to be logged; you thus add an action to the config file:
```yaml
…
actions:
  loginstall: "echo {{@@ _dotfile_abs_src @@}} installed to {{@@ _dotfile_abs_dst @@}} >> {0}"
…
profiles:
  home:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
  office:
    dotfiles:
    - f_xinitrc
    - d_polybar
    variables:
      wifi: "wlp2s0"
    actions:
      - loginstall "/tmp/dotdrop-installation.log"
```

When done, you can install your dotfiles using:
```bash
$ dotdrop install
```

If you are unsure, you can always run `dotdrop compare` to see
how your local dotfiles would be updated by dotdrop before running
`install` or you could run install with `--dry`.

That's it, a single repository with all your dotfiles for your different hosts.

For more, see the [docs](https://dotdrop.readthedocs.io):

* [Create actions](https://dotdrop.readthedocs.io/en/latest/config/config-actions/)
* [Use transformations](https://dotdrop.readthedocs.io/en/latest/config/config-transformations/)
* [Use variables](https://dotdrop.readthedocs.io/en/latest/config/config-variables/)
* [Symlink dotfiles](https://dotdrop.readthedocs.io/en/latest/howto/symlink-dotfiles/)
* [and more](https://dotdrop.readthedocs.io/en/latest/howto/howto/)

# Documentation

Dotdrop's documentation is hosted on [Read the Docs](https://dotdrop.readthedocs.io/en/latest/).

# Thank you

If you like dotdrop, [buy me a coffee](https://ko-fi.com/deadc0de6).

# Contribution

If you are having trouble installing or using dotdrop,
[open an issue](https://github.com/deadc0de6/dotdrop/issues).

If you want to contribute, feel free to do a PR (please follow PEP8).
Have a look at the
[contribution guidelines](https://github.com/deadc0de6/dotdrop/blob/master/CONTRIBUTING.md).

# License

This project is licensed under the terms of the GPLv3 license.
