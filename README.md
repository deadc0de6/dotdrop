# DOTDROP

[![Build Status](https://travis-ci.org/deadc0de6/dotdrop.svg?branch=master)](https://travis-ci.org/deadc0de6/dotdrop)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/deadc0de6/dotdrop/badge.svg?branch=master)](https://coveralls.io/github/deadc0de6/dotdrop?branch=master)
[![PyPI version](https://badge.fury.io/py/dotdrop.svg)](https://badge.fury.io/py/dotdrop)
[![AUR](https://img.shields.io/aur/version/dotdrop.svg)](https://aur.archlinux.org/packages/dotdrop)
[![Python](https://img.shields.io/pypi/pyversions/dotdrop.svg)](https://pypi.python.org/pypi/dotdrop)

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
hosts (cloud VM, etc) that may be using
a slightly different version of some of the dotfiles.

Features:

* Sync once every dotfile on git for different usages
* Allow dotfiles templating by leveraging [jinja2](http://jinja.pocoo.org/)
* Comparison between local and stored dotfiles
* Handling multiple profiles with different sets of dotfiles
* Easy import dotfiles
* Handle files and directories
* Associate an action to the deployment of specific dotfiles
* Associate transformations that allow to store encrypted dotfiles

Check the [blog post](https://deadc0de.re/articles/dotfiles.html) and
and the [example](#example) for more.

Quick start:
```bash
mkdir dotfiles && cd dotfiles
git init
git submodule add https://github.com/deadc0de6/dotdrop.git
./dotdrop/bootstrap.sh
./dotdrop.sh --help
```

## Why dotdrop ?

There exist many tools to manage dotfiles however not
many allow to deploy different versions of the same dotfile
on different hosts. Moreover dotdrop allows to specify the
set of dotfiles that need to be deployed on a specific profile.

See the [example](#example) for a concrete example on
why dotdrop rocks.

---

**Table of Contents**

* [Installation](#installation)
* [Usage](#usage)
* How to

  * [Install dotfiles](#install-dotfiles)
  * [Compare dotfiles](#compare-dotfiles)
  * [Import dotfiles](#import-dotfiles)
  * [List profiles](#list-profiles)
  * [List dotfiles](#list-dotfiles)
  * [Use actions](#use-actions)
  * [Use transformations](#use-transformations)
  * [Update dotdrop](#update-dotdrop)
  * [Update dotfiles](#update-dotfiles)
  * [Store sensitive dotfiles](#store-sensitive-dotfiles)

* [Config](#config)
* [Template](#template)
* [Example](#example)
* [People using dotdrop](#people-using-dotdrop)

# Installation

There's two ways of installing and using dotdrop, either [as a submodule](#as-a-submodule)
to your dotfiles git tree or system-wide [with pypi](#with-pypi).

Having dotdrop as a submodule guarantees that anywhere your are cloning your dotfiles git tree
from you'll have dotdrop shipped with it. It is the recommended way.

Dotdrop is also available on aur: https://aur.archlinux.org/packages/dotdrop/

## As a submodule

The following will create a repository for your dotfiles and
keep dotdrop as a submodules:
```bash
$ mkdir dotfiles; cd dotfiles
$ git init
$ git submodule add https://github.com/deadc0de6/dotdrop.git
$ sudo pip3 install -r dotdrop/requirements.txt
$ ./dotdrop/bootstrap.sh
$ ./dotdrop.sh --help
```

Install the requirements with:
```bash
$ sudo pip3 install -r dotdrop/requirements.txt
```

For MacOS users, make sure to install `realpath` through homebrew
(part of *coreutils*).

Using this solution will need you to work with dotdrop by
using the generated script `dotdrop.sh` at the root
of your dotfiles repository.

Finally import your dotfiles as described [below](#usage).

## With pypi

Start by installing dotdrop
```bash
$ sudo pip3 install dotdrop
```

And then create a repository for your dotfiles
```bash
$ mkdir dotfiles; cd dotfiles
$ git init
```

To avoid the need to provide the config file path to dotdrop each time it
is called, you can create an alias:
```
alias dotdrop='dotdrop --cfg=<path-to-your-config.yaml>'
```

Replace any call to `dotdrop.sh` in the documentation below
by `dotdrop` if using the pypi solution.

Finally import your dotfiles as described [below](#usage).

# Usage

If starting fresh, the `import` command of dotdrop
allows to easily and quickly get a running setup.

Install dotdrop on one of your host and then import any dotfiles you want dotdrop to
manage (be it a file or a directory):
```bash
$ dotdrop.sh import ~/.vimrc ~/.xinitrc
```

Dotdrop does two things:

* Copy the dotfiles in the *dotfiles* directory
* Create the entries in the *config.yaml* file

Commit and push your changes.

Then go to another host where your dotfiles need to be managed as well,
clone the previously setup git tree
and compare local dotfiles with the ones stored by dotdrop:
```bash
$ dotdrop.sh list
$ dotdrop.sh compare --profile=<other-host-profile>
```

Then adapt any dotfile using the [template](#template) feature
and set a new profile for the current host by simply adding lines in
the config files, for example:

```yaml
...
profiles:
  host1:
    dotfiles:
    - f_vimrc
    - f_xinitrc
  host2:
    dotfiles:
    - f_vimrc
...
```

When done, you can install your dotfiles using

```bash
$ dotdrop.sh install
```

That's it, a single repository with all your dotfiles for your different hosts.

For additional usage see the help:

```
$ dotdrop.sh --help

     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/ 
                               |_|

Usage:
  dotdrop install   [-fndV] [-c <path>] [-p <profile>]
  dotdrop import    [-ldV]  [-c <path>] [-p <profile>] <paths>...
  dotdrop compare   [-V]    [-c <path>] [-p <profile>]
                            [-o <opts>] [--files=<files>]
  dotdrop update    [-fdV]  [-c <path>] <path>
  dotdrop listfiles [-V]    [-c <path>] [-p <profile>]
  dotdrop list      [-V]    [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -p --profile=<profile>  Specify the profile to use [default: carbon].
  -c --cfg=<path>         Path to the config [default: config.yaml].
  --files=<files>         Comma separated list of files to compare.
  -o --dopts=<opts>       Diff options [default: ].
  -n --nodiff             Do not diff when installing.
  -l --link               Import and link.
  -f --force              Do not warn if exists.
  -V --verbose            Be verbose.
  -d --dry                Dry run.
  -v --version            Show version.
  -h --help               Show this screen.
```

For easy deployment the default profile used by dotdrop reflects the
hostname of the host on which it runs.

## Install dotfiles

Simply run
```bash
$ dotdrop.sh install
```

Use the `--profile` switch to specify a profile if not using
the host's hostname.

## Compare dotfiles

Compare local dotfiles with dotdrop's defined ones:
```bash
$ dotdrop.sh compare
```

The diffing is done by diff in the backend, one can provide specific
options to diff using the `-o` switch.

## Import dotfiles

Dotdrop allows to import dotfiles directly from the
filesystem. It will copy the dotfile and update the
config file automatically.

For example to import `~/.xinitrc`
```bash
$ dotdrop.sh import ~/.xinitrc
```

## List profiles

```bash
$ dotdrop.sh list
```

Dotdrop allows to choose which profile to use
with the *--profile* switch if you use something
else than the default (the hostname).

## List dotfiles

The following command lists the different dotfiles
configured for a specific profile:

```bash
$ dotdrop.sh listfiles --profile=<some-profile>
```

For example:
```
Dotfile(s) for profile "some-profile":

f_vimrc (file: "vimrc", link: False)
	-> ~/.vimrc
f_dunstrc (file: "config/dunst/dunstrc", link: False)
	-> ~/.config/dunst/dunstrc
```

## Use actions

It is sometimes useful to execute some kind of action
when deploying a dotfile. For example let's consider
[Vundle](https://github.com/VundleVim/Vundle.vim) is used
to manage vim's plugins, the following action could
be set to update and install the plugins when `vimrc` is
deployed:

```yaml
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
    dotfiles:
    - f_vimrc
```

Thus when `f_vimrc` is installed, the command
`vim +VundleClean! +VundleInstall +VundleInstall! +qall` will
be executed.

## Use transformations

Transformation actions are used to transform a dotfile before it is
installed. They work like [actions](#use-actions) but are executed before the
dotfile is installed to transform the source.

Transformation commands have two arguments:

* **{0}** will be replaced with the dotfile to process
* **{1}** will be replaced with a temporary file to store the result of the transformation

A typical use-case for transformations is when the dotfile needs to be
stored encrypted.

Here's an example of part of a config file to use gpg encrypted dotfiles:
```
dotfiles:
  f_secret:
    dst: ~/.secret
    src: secret
    trans:
      - gpg
trans:
  gpg: gpg2 -q --for-your-eyes-only --no-tty -d {0} > {1}
```

The above config allows to store the dotfile `~/.secret` encrypted in the *dotfiles*
directory and uses gpg to decrypt it when install is run.

Here's how to deploy the above solution:

* import the clear dotfile (creates the correct entries in the config file)
```
./dotdrop.sh import ~/.secret
```
* encrypt the original dotfile 
```
<some-gpg-command> ~/.secret
```
* overwrite the dotfile with the encrypted version
```
cp <encrypted-version-of-secret> dotfiles/secret
```
* edit the config file and add the transformation to the dotfile
* commit and push the changes

Note that transformations cannot be used if the dotfiles is to be linked (`link: true`)
and `compare` won't work on dotfiles using transformations.

## Update dotdrop

If used as a submodule, update it with
```bash
$ git submodule foreach git pull origin master
$ git add dotdrop
$ git commit -m 'update dotdrop'
$ git push
```

Through pypi:
```bash
$ sudo pip3 install dotdrop --upgrade
```

## Update dotfiles

Dotfiles managed by dotdrop can be updated using the `update` command.
There are two cases:

  * the dotfile doesn't use [templating](#template): the new version of the dotfile is copied to the
    *dotfiles* directory and overwrites the old version. If git is used to version the dotfiles stored
    by dotdrop, the git command `diff` can be used to view the changes.
  * the dotfile uses [templating](#template): the dotfile must be manually updated, the use of
    the dotdrop command `compare` can be helpful to identify the changes to apply to the template.

```
$ dotdrop.sh update ~/.vimrc
```

## Store sensitive dotfiles

Two solutions exist, the first one using an unversioned file (see [Environment variables](#environment-variables))
and the second using transformations (see [Transformations](#use-transformations)).

# Config

The config file (defaults to *config.yaml*) is a yaml file containing
the following entries:

* **config** entry: contains settings for the deployment
  * `backup`: create a backup of the dotfile in case it differs from the
    one that will be installed by dotdrop
  * `create`: create directory hierarchy when installing dotfiles if
    it doesn't exist
  * `dotpath`: path to the directory containing the dotfiles to be managed
    by dotdrop (absolute path or relative to the config file location)

* **dotfiles** entry: a list of dotfiles
  * When `link` is true, dotdrop will create a symlink instead of copying. Template generation (as in [template](#template)) is not supported when `link` is true.
  * `actions` contains a list of action keys that need to be defined in the **actions** entry below.
  * `trans` contains a list of transformation keys that need to be defined in the **trans** entry below.
```
  <dotfile-key-name>:
    dst: <where-this-file-is-deployed>
    src: <filename-within-the-dotpath>
    # Optional
    link: <true|false>
    actions:
      - <action-key>
    trans:
      - <transformation-key>
```

* **profiles** entry: a list of profiles with the different dotfiles that
  need to be managed
  * `dotfiles`: the dotfiles associated to this profile
  * `include`: include all dotfiles from another profile (optional)

```
  <some-name-usually-the-hostname>:
    dotfiles:
    - <some-dotfile-key-name-defined-above>
    - <some-other-dotfile-key-name>
    - ...
    # Optional
    include:
    - <some-other-profile>
    - ...
```

* **actions** entry: a list of action
```
  <action-key>: <command-to-execute>
```

* **trans** entry: a list of transformations
```
  <trans-key>: <command-to-execute>
```

## All dotfiles for a profile

To use all defined dotfiles for a profile, simply use
the keyword `ALL`.

For example:
```yaml
dotfiles:
  f_xinitrc:
    dst: ~/.xinitrc
    src: xinitrc
  f_vimrc:
    dst: ~/.vimrc
    src: vimrc
profiles:
  host1:
    dotfiles:
    - ALL
  host2:
    dotfiles:
    - f_vimrc
```

## Include dotfiles from another profile

If one profile is using the entire set of another profile, one can use
the `include` entry to avoid redundancy.

For example:
```yaml
profiles:
  host1:
      dotfiles:
        - f_xinitrc
      include:
        - host2
  host2:
      dotfiles:
        - f_vimrc
```
Here profile *host1* contains all the dotfiles defined for *host2* plus `f_xinitrc`.

# Template

Dotdrop leverage the power of [jinja2](http://jinja.pocoo.org/) to handle the
templating of dotfiles. See [jinja2 template doc](http://jinja.pocoo.org/docs/2.9/templates/)
or the [example section](#example) for more information on how to template your dotfiles.

Note that dotdrop uses different delimiters than
[jinja2](http://jinja.pocoo.org/)'s defaults:

* block start = `{%@@`
* block end = `@@%}`
* variable start = `{{@@`
* variable end = `@@}}`
* comment start = `{#@@`
* comment end = `@@#}`

## Available variables

* `{{@@ profile @@}}` contains the profile provided to dotdrop.
* `{{@@ env['MY_VAR'] @@}}` contains environment variables (see [Environment variables](#environment-variables))

## Environment variables

It's possible to access environment variables inside the templates. This feature can be used like this:

```
{{@@ env['MY_VAR'] @@}}
```

This allows for storing host-specific properties and/or secrets in environment variables.

You can have an `.env` file in the directory where your `config.yaml` lies:

```
## My variables for this host
var1="some value"
var2="some other value"

## Some secrets
pass="verysecurepassword"
```
Of course, this file should not be tracked by git (put it in your `.gitignore`).

Then you can invoke dotdrop with the help of an alias like that:
```
## when using dotdrop as a submodule
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) ~/dotfiles/dotdrop.sh'

## when using dotdrop from pypi
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) dotdrop --cfg=~/dotfiles/config.yaml'
```
This loads all the variables from `.env` (while omitting lines starting with `#`) before calling dotdrop.

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
the hostname matches the entry in the config file):
```bash
# on home computer
$ dotdrop.sh install --profile=home

# on office computer
$ dotdrop.sh install --profile=office
```

Comparing the dotfiles:
```bash
# on home computer
$ dotdrop.sh compare

# on office computer
$ dotdrop.sh compare
```

# People using dotdrop

For more examples, see how people are using dotdrop:

* [https://github.com/open-dynaMIX/dotfiles](https://github.com/open-dynaMIX/dotfiles)
* [https://github.com/moyiz/dotfiles](https://github.com/moyiz/dotfiles)
* [https://github.com/japorized/dotfiles](https://github.com/japorized/dotfiles)

# Related projects

These are some dotfiles related projects that
have inspired me for dotdrop:

* [https://github.com/EvanPurkhiser/dots](https://github.com/EvanPurkhiser/dots)
* [https://github.com/jaagr/dots](https://github.com/jaagr/dots)
* [https://github.com/anishathalye/dotbot](https://github.com/anishathalye/dotbot)
* [https://github.com/tomjnixon/Dotfiles](https://github.com/tomjnixon/Dotfiles)

See also [github does dotfiles](https://dotfiles.github.io/)

# Migrate from submodule

Initially dotdrop was used as a submodule directly in the
dotfiles git tree. That solution allows your dotfiles to be shipped along
with the tool able to handle them. Dotdrop is however also directly available
on pypi.

If you want to keep it as a submodule (recommended), simply do the following
```bash
$ cd <dotfiles-directory>

## get latest version of the submodule
$ git submodule foreach git pull origin master

## and stage the changes
$ git add dotdrop
$ git commit -m 'update dotdrop'

## update the bash script wrapper
$ ./dotdrop/bootstrap.sh

## and stage the change to the dotdrop.sh script
$ git add dotdrop.sh
$ git commit -m 'update dotdrop.sh'

## and finally push the changes upstream
$ git push
```

Otherwise, simply install it from pypi as explained [above](#with-pypi)
and get rid of the submodule as shown below:

* move to the dotfiles directory where dotdrop is used as a submodule
```bash
$ cd <dotfiles-repository>
```
* remove the entire `submodule "dotdrop"` section in `.gitmodules`
* stage the changes
```bash
$ git add .gitmodules
```
* remove the entire `submodule "dotdrop"` section in `.git/config`
* remove the submodule
```bash
$ git rm --cached dotdrop
```
* remove the submodule from .git
```bash
$ rm -rf .git/modules/dotdrop
```
* commit the changes
```bash
$ git commit -m 'removing dotdrop submodule'
```
* remove any remaining files from the dotdrop submodule
```bash
$ rm -rf dotdrop
```
* remove `dotdrop.sh`
```bash
$ git rm dotdrop.sh
$ git commit -m 'remove dotdrop.sh script'
```
* push upstream
```bash
$ git push
```

# Contribution

If you are having trouble installing or using dotdrop, open an issue.

If you want to contribute, feel free to do a PR (please follow PEP8).

# License

This project is licensed under the terms of the GPLv3 license.

