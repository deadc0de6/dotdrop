# DOTDROP

[![Build Status](https://travis-ci.org/deadc0de6/dotdrop.svg?branch=master)](https://travis-ci.org/deadc0de6/dotdrop)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/deadc0de6/dotdrop/badge.svg?branch=master)](https://coveralls.io/github/deadc0de6/dotdrop?branch=master)

*Save your dotfiles once, deploy them everywhere*

Dotdrop makes the management of dotfiles between different
hosts easy.
It allows to store your dotfiles on git and automagically deploy
different versions on different setups.

For example you can have a set of dotfiles for your home laptop and
a different set for your office desktop. Those sets may overlap and different
versions of the same dotfile can be deployed on different predefined *profiles*.
Another use case is when you have a main set of dotfiles for your
everyday's host and a sub-set you only need to deploy to temporary
hosts (cloud, etc) that may be using
a slightly different version of some of the dotfiles.

Features:

* Sync once every dotfile on git for different usages
* Allow dotfiles templating by leveraging [jinja2](http://jinja.pocoo.org/)
* Comparison between local and stored dotfiles
* Handling multiple profiles with different sets of dotfiles
* Easy import dotfiles in dotdrop
* Associate an action to the deployment of a dotfile

Check the [blog post](https://deadc0de.re/articles/dotfiles.html) for more.

Quick start:
```
mkdir dotfiles && cd dotfiles
git init
git submodule add https://github.com/deadc0de6/dotdrop.git
./dotdrop/bootstrap.sh
./dotdrop.sh --help
```

---

**Table of Contents**

* [Installation](#installation)
* [Usage](#usage)
* [Template](#template)
* [Example](#example)

## Why dotdrop ?

There exist many tools to manage dotfiles however not
many allow to deploy different versions of the same dotfile
on different hosts. Moreover dotdrop allows to specify the
set of dotfiles that need to be deployed on a specific profile.

See the [example](#example) for a concrete example on
why dotdrop rocks.

These are some dotfiles related projects that
have inspired me for dotdrop:

* [https://github.com/EvanPurkhiser/dots](https://github.com/EvanPurkhiser/dots)
* [https://github.com/jaagr/dots](https://github.com/jaagr/dots)
* [https://github.com/anishathalye/dotbot](https://github.com/anishathalye/dotbot)
* [https://github.com/tomjnixon/Dotfiles](https://github.com/tomjnixon/Dotfiles)

# Installation

The following will create a repository for your dotfiles and
keep dotdrop as a submodules
```
mkdir dotfiles; cd dotfiles
git init
git submodule add https://github.com/deadc0de6/dotdrop.git
./dotdrop/bootstrap.sh
```

Then install the requirements:
```
sudo pip3 install -r dotdrop/requirements.txt
```

Finally import your dotfiles as described [below](#usage).

For MacOS users, make sure to install `realpath` through homebrew
(part of *coreutils*).

# Usage

If starting fresh, the import function of dotdrop
allows to easily and quickly get a running setup.

Install dotdrop on one of your host and then import any dotfiles you want dotdrop to
manage (be it a file or a folder)
```
$ ./dotdrop.sh import ~/.vimrc ~/.xinitrc
```

Dotdrop does two things:

* Copy the dotfiles in the *dotfiles* folder
* Create the entries in the *config.yaml* file

Commit and push your changes.

Then go to another host where your dotfiles need to be managed as well,
clone the previously setup git tree
and compare local dotfiles with the ones stored by dotdrop
```
$ ./dotdrop.sh list
$ ./dotdrop.sh compare --profile=<other-host-profile>
```

Then adapt any dotfile using the [template](#template) feature
and set a new profile for the current host by simply adding lines in
the config files, for example:

```
...
profiles:
  host1:
  - f_vimrc
  - f_xinitrc
  host2:
  - f_vimrc
...
```

When done, you can install your dotfiles using

```
$ ./dotdrop.sh install
```

That's it, a single repository with all your dotfiles for your different hosts.

For additional usage see the help:

```
$ ./dotdrop.sh --help
     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v0.4
                               |_|

Usage:
  dotdrop.py install [-fndvc <path>] [--profile=<profile>]
  dotdrop.py compare [-vc <path>] [--profile=<profile>] [--files=<files>]
  dotdrop.py import [-ldc <path>] [--profile=<profile>] <paths>...
  dotdrop.py listfiles [-c <path>] [--profile=<profile>]
  dotdrop.py list [-c <path>]
  dotdrop.py --help
  dotdrop.py --version

Options:
  --profile=<profile>     Specify the profile to use [default: thor].
  -c --cfg=<path>         Path to the config [default: /home/drits/tools/dotdrop/config.yaml].
  --files=<files>         Comma separated list of files to compare.
  -n --nodiff             Do not diff when installing.
  -l --link               Import and link.
  -f --force              Do not warn if exists.
  -v --verbose            Be verbose.
  -d --dry                Dry run.
  --version               Show version.
  -h --help               Show this screen.
```

For easy deployment the default profile used by dotdrop reflects the
hostname of the host on which it runs.

## Config file details

The config file (defaults to *config.yaml*) is a yaml file containing
the following entries:

* **config** entry: contains settings for the deployment
  * `backup`: create a backup of the dotfile in case it differs from the
    one that will be installed by dotdrop
  * `create`: create folder hierarchy when installing dotfiles if
    it doesn't exist
  * `dotpath`: path to the folder containing the dotfiles to be managed
    by dotdrop (absolute path or relative to the config file location)

* **dotfiles** entry: a list of dotfiles in the form
  * When `link` is true, dotdrop will create a link instead of copying. Template generation (as in [template](#template)) is not supported when `link` is true.
```
  <dotfile-key-name>:
    dst: <where-this-file-is-deployed>
    src: <filename-within-the-dotpath>
    # Optional
    link: <true|false>
    actions:
      - <action-key>
```

* **profiles** entry: a list of profiles with a sublist
  of dotfiles that need to be deployed for this profile

```
  <some-name-usually-the-hostname>:
    - <some-dotfile-key-name-defined-above>
    - <some-other-dotfile-key-name>
    - ...
```

* **actions** entry: a list of action available
```
  <action-key>: <command-to-execute>
```

## Installing dotfiles

Simply run
```
./dotdrop.sh install
```

Use the *--profile* switch to specify a profile if not using
the host's hostname.

## Diffing your local dotfiles with dotdrop

Compare local dotfiles with dotdrop's defined ones:
```
./dotdrop.sh compare
```

## Import new dotfiles

Dotdrop allows to import dotfiles directly from the
filesystem. It will copy the dotfile and update the
config file automatically.

For example to import *$HOME/.xinitrc*
```
$ ./dotdrop.sh import $HOME/.xinitrc

```

## List the available profiles

```
$ ./dotdrop.sh list
```

Dotdrop allows to choose which profile to use
with the *--profile* switch if you used something
else than the default (the hostname).

## List configured dotfiles

The following command lists the different dotfiles
configured for a specific profile:

```
$ ./dotdrop.sh listfiles --profile=<some-profile>
```

For example:
```
Dotfile(s) for profile "some-profile":

f_vimrc (file: "vimrc", link: False)
	-> ~/.vimrc
f_dunstrc (file: "config/dunst/dunstrc", link: False)
	-> ~/.config/dunst/dunstrc
```

## Execute an action when deploying a dotfile

It is sometimes useful to execute some kind of action
when deploying a dotfile. For example let's consider
[Vundle](https://github.com/VundleVim/Vundle.vim) is used
to manage vim's plugins, the following action could
be set to update and install the plugins when `vimrc` is
deployed:

```
actions:
  vundle: vim +VundleClean! +VundleInstall +VundleInstall! +qall
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
    actions:
      - vundle
profiles:
  home:
  - f_vimrc
```

Thus when `f_vimrc` is intalled, the command
`vim +VundleClean! +VundleInstall +VundleInstall! +qall` will
be executed.

## Update dotbot

If installed through the `bootstrap.sh` script, dotdrop is
installed as a submodule within your git tree.
You can thus simply run the following command
to update the submodule:

```
git submodule update --recursive --remote
```

# Template

Dotdrop leverage the power of [jinja2](http://jinja.pocoo.org/) to handle the
templating of dotfiles. See [jinja2 template doc](http://jinja.pocoo.org/docs/2.9/templates/)
or the [example secion](#example) for more information on how to template your dotfiles.

Note that dotdrop uses different delimiters than the
[jinja2](http://jinja.pocoo.org/) defaults:

* block start = `{%@@`
* block end = `@@%}`
* variable start = `{{@@`
* variable end = `@@}}`
* comment start = `{#@@`
* comment end = `@@#}`

# Example

Let's consider two hosts:

* **home**: home computer with hostname *home*
* **office**: office computer with hostname *office*

The home computer is running [awesomeWM](https://awesomewm.org/)
and the office computer [bspwm](https://github.com/baskerville/bspwm).
The *.xinitrc* file will therefore be different while still sharing some lines.
Dotdrop allows to store only one single *.xinitrc* but
to deploy different versions depending on where it is run from.

The following file is the dotfile stored in dotdrop containing
jinja2 directives for the deployment based on the profile used.

Dotfile `<dotpath>/xinitrc`:
```
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

And here's how the config file looks like with this setup.
Of course any combination of the dotfiles (different sets)
can be done once you have more dotfiles to deploy.

`config.yaml` file:
```
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
  - f_xinitrc
  office:
  - f_xinitrc
```

Installing the dotfiles (the `--profile` switch is not needed if
the hostname matches the entry in the config file):
```
# on home computer
./dotdrop.sh install --profile=home
# on office computer
./dotdrop.sh install --profile=office
```

Comparing the dotfiles:
```
# on home computer
./dotdrop.sh compare
# on office computer
./dotdrop.sh compare
```

# Contribution

If you are having trouble installing or using dotdrop, open an issue.

If you want to contribute, feel free to do a PR (please follow PEP8).

# License

This project is licensed under the terms of the GPLv3 license.

