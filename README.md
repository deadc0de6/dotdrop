# DOTDROP

[![Build Status](https://travis-ci.org/deadc0de6/dotdrop.svg?branch=master)](https://travis-ci.org/deadc0de6/dotdrop)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/deadc0de6/dotdrop/badge.svg?branch=master)](https://coveralls.io/github/deadc0de6/dotdrop?branch=master)
[![PyPI version](https://badge.fury.io/py/dotdrop.svg)](https://badge.fury.io/py/dotdrop)
[![AUR](https://img.shields.io/aur/version/dotdrop.svg)](https://aur.archlinux.org/packages/dotdrop)
[![Python](https://img.shields.io/pypi/pyversions/dotdrop.svg)](https://pypi.python.org/pypi/dotdrop)

*Save your dotfiles once, deploy them everywhere*

[Dotdrop](https://github.com/deadc0de6/dotdrop) makes the management of dotfiles between different hosts easy.
It allows to store your dotfiles on git and automagically deploy
different versions of the same file on different setups.

It also allows to manage different *sets* of dotfiles.
For example you can have a set of dotfiles for your home laptop and
a different set for your office desktop. Those sets may overlap and different
versions of the same dotfiles can be deployed on different predefined *profiles*.
Or you may have a main set of dotfiles for your
everyday's host and a sub-set you only need to deploy to temporary
hosts (cloud VM, etc) that may be using
a slightly different version of some of the dotfiles.

Features:

* Sync once every dotfile on git for different usages
* Allow dotfiles templating by leveraging [jinja2](http://jinja.pocoo.org/)
* Dynamically generated dotfile contents with pre-defined variables
* Comparison between deployed and stored dotfiles
* Handling multiple profiles with different sets of dotfiles
* Easy import and update dotfiles
* Handle files and directories
* Support symlink of dotfiles
* Associate an action to the deployment of specific dotfiles
* Associate transformations for storing encrypted dotfiles
* Provide different solutions for handling dotfiles containing sensitive information

Check also the [blog post](https://deadc0de.re/articles/dotfiles.html),
the [example](#example), the [wiki](https://github.com/deadc0de6/dotdrop/wiki) or
how [people are using dotdrop](https://github.com/deadc0de6/dotdrop/wiki/people-using-dotdrop)
for more.

Quick start:
```bash
mkdir dotfiles && cd dotfiles
git init
git submodule add https://github.com/deadc0de6/dotdrop.git
sudo pip3 install -r dotdrop/requirements.txt
./dotdrop/bootstrap.sh
./dotdrop.sh --help
```

A mirror of this repository is available on gitlab under <https://gitlab.com/deadc0de6/dotdrop>.

## Why dotdrop ?

There exist many tools to manage dotfiles however not
many allow to deploy different versions of the same dotfile
on different hosts. Moreover dotdrop allows to specify the
set of dotfiles that need to be deployed on a specific profile.

See the [example](#example) for a concrete example on
why [dotdrop](https://github.com/deadc0de6/dotdrop) rocks.

---

**Table of Contents**

* [Installation](#installation)
* [Getting started](#gettins-started)
* [Documentation](#documentation)
* [Example](#example)

# Installation

There are multiple ways to install and use dotdrop.
It is recommended to install dotdrop [as a submodule](#as-a-submodule)
to your dotfiles git tree. Having dotdrop as a submodule guarantees that anywhere
you are cloning your dotfiles git tree from you'll have dotdrop shipped with it.

Below instructions show how to install dotdrop as a submodule. For alternative
installation instructions (with virtualenv, pypi, aur, snap, etc), see the
[wiki installation page](https://github.com/deadc0de6/dotdrop/wiki/installation).

Dotdrop is also available on
* pypi: https://pypi.org/project/dotdrop/
* aur (stable): https://aur.archlinux.org/packages/dotdrop/
* aur (git version): https://aur.archlinux.org/packages/dotdrop-git/
* snapcraft: https://snapcraft.io/dotdrop

## As a submodule

The following will create a git repository for your dotfiles and
keep dotdrop as a submodule:
```bash
## create the repository
$ mkdir dotfiles; cd dotfiles
$ git init

## install dotdrop as a submodule
$ git submodule add https://github.com/deadc0de6/dotdrop.git
$ sudo pip3 install -r dotdrop/requirements.txt
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

For bash and zsh completion scripts see [the related doc](completion/README.md).

# Getting started

Create a new repository to store your dotfiles with dotdrop. *Init* or *clone*
that new repository and
[install dotdrop](https://github.com/deadc0de6/dotdrop/wiki/installation#as-a-submodule).

Then import any dotfiles (file or directory) you want to manage with dotdrop.
You can either use the default profile (which resolves to the *hostname* of the host
your running dotdrop on) or provide it specifically using the switch `-p --profile`.

Import dotfiles on host *hostname1*
```bash
$ dotdrop import ~/.vimrc ~/.xinitrc ~/.config/polybar
```

Dotdrop does two things:

* Copy the dotfiles in the *dotpath* directory (defined in `config.yaml`, defaults to *dotfiles*)
* Create the entries in the `config.yaml` file

Your config file will look something similar to this
```yaml
config:
  backup: true
  banner: true
  create: true
  dotpath: dotfiles
  ignoreempty: false
  keepdot: false
  link_by_default: false
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
  hostname1:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
```
For a description of the different fields and their use,
see the [config doc](https://github.com/deadc0de6/dotdrop/wiki/config).

Commit and push your changes.

Then go to another host where your dotfiles need to be managed as well,
clone the previously setup repository
and compare the local dotfiles with the ones stored by dotdrop:
```bash
$ dotdrop compare --profile=hostname1
```

Now you might want to adapt the `config.yaml` file to your likings on
that second host. Let's say for example that you only want `d_polybar` and
`f_xinitrc` to be deployed on that second host. You would then change your config
to something like this (considering that second host's hostname is *hostname2*):
```yaml
…
profiles:
  hostname1:
    dotfiles:
    - f_vimrc
    - f_xinitrc
    - d_polybar
  hostname2:
    dotfiles:
    - f_xinitrc
    - d_polybar
```

Then adapt any dotfile using the [templating](https://github.com/deadc0de6/dotdrop/wiki/templating)
feature (if needed). For example you might want different fonts sizes on polybar for the different
hosts:

`<dotpath>/config/polybar/config`
```bash
…
{%@@ if profile == "hostname1" @@%}
font0 = sans:size=10;0
{%@@ elif profile == "hostname2" @@%}
font0 = sans:size=14;0
{%@@ endif @@%}
font1 = "Material Design Icons:style=Regular:size=14;0"
font2 = "unifont:size=6;0"
…
```

When done, you can install your dotfiles using
```bash
$ dotdrop install
```
If you are unsure, you can always run `dotdrop compare` to see
how your local dotfiles would be updated by dotdrop before running
`install`.

That's it, a single repository with all your dotfiles for your different hosts.

You can then create [actions](https://github.com/deadc0de6/dotdrop/wiki/usage-actions),
use [transformations](https://github.com/deadc0de6/dotdrop/wiki/usage-transformations),
[symlink dotfiles](https://github.com/deadc0de6/dotdrop/wiki/symlinked-dotfiles),
[etc](https://github.com/deadc0de6/dotdrop/wiki).

For more options see `dotdrop --help` and the [wiki](https://github.com/deadc0de6/dotdrop/wiki).

# Documentation

Dotdrop's documentation is hosted on [its wiki](https://github.com/deadc0de6/dotdrop/wiki).

# Example

Let's consider two hosts:

* **home**: home computer with hostname *home*
* **office**: office computer with hostname *office*

The home computer is running [awesomeWM](https://awesomewm.org/)
and the office computer [bspwm](https://github.com/baskerville/bspwm).
The *.xinitrc* file will therefore be different while still sharing some lines.
Dotdrop allows to store only one single *.xinitrc* file but
to deploy different versions of it depending on where it is run from.

The following file is the dotfile stored in dotdrop containing
[jinja2](http://jinja.pocoo.org/) directives for the deployment based on the profile used.

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

The *if branch* will define which part is deployed based on the
hostname of the host on which dotdrop is run from.

And here's how the config file looks like with this setup.
Of course any combination of the dotfiles (different sets)
can be done if more dotfiles have to be deployed.

`config.yaml` file:
```yaml
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_xinitrc:
    dst: ~/.xinitrc
    src: xinitrc
profiles:
  home:
    dotfiles:
    - f_xinitrc
  office:
    dotfiles:
    - f_xinitrc
```

Installing the dotfiles (the `--profile` switch is not needed if
the hostname matches the *profile* entry in the config file):
```bash
## on home computer
$ dotdrop install --profile=home

## on office computer
$ dotdrop install --profile=office
```

Comparing the dotfiles:
```bash
$ dotdrop compare
```

For more see [the wiki](https://github.com/deadc0de6/dotdrop/wiki).

# Contribution

If you are having trouble installing or using dotdrop,
[open an issue](https://github.com/deadc0de6/dotdrop/issues).

If you want to contribute, feel free to do a PR (please follow PEP8).

# License

This project is licensed under the terms of the GPLv3 license.
