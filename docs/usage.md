# Usage

Run `dotdrop --help` to see all available options.

## Basic usage

The basic use of dotdrop is

* import a file/directory to manage (this will copy the files from the filesystem to your `dotpath`): `dotdrop import <somefile>`
* install the dotfiles (will *copy/link* those from your `dotpath` to the filesystem): `dotdrop install`

Then if you happen to update the file/directory directly on the filesystem (add new file/dir, edit content, etc) you can use `update` to mirror back those changes in dotdrop.

For more advanced uses:

* `dotdrop --help` for more options.
* [the example](https://github.com/deadc0de6/dotdrop#getting-started)

## Install dotfiles

Simply run
```bash
$ dotdrop install
```

some available options

* `-t --temp`: install the dotfile(s) to a temporary directory for review (it helps to debug templating issues for example). Note that actions are not executed in that mode.
* `-a --force-actions`: force the execution of actions even if the dotfiles are not installed

For more detail, see the usage with `dotdrop --help`

To ignore specific pattern during installation see [the ignore patterns](config.md#ignore-patterns)

## Compare dotfiles

Compare local dotfiles with the ones stored in dotdrop:
```bash
$ dotdrop compare
```

The diffing is done by `diff` in the backend, one can provide its specific
diff command using the config option `diff_command`.

To ignore specific pattern,
see [the ignore patterns](config.md#ignore-patterns)

It is also possible to install all dotfiles for a specific profile
in a temporary directory in order to manually compare them with
the local version by using `install` and the `-t` switch.

## Import dotfiles

Dotdrop allows to import dotfiles directly from the
filesystem. It will copy the dotfile and update the
config file automatically.

Note that dotdrop will dereference all symlinks
when importing a file or directory.

For example to import `~/.xinitrc`
```bash
$ dotdrop import ~/.xinitrc
```

You can control how the dotfile key is generated in the config file
with the option `longkey` (per default to *false*).

Two formats are available:

* *short format* (default): take the shortest unique path
* *long format*: take the full path

For example `~/.config/awesome/rc.lua` gives

* `f_rc.lua` in the short format
* `f_config_awesome_rc.lua` in the long format

Importing `~/.mutt/colors` and then `~/.vim/colors` will result in

* `d_colors` and `d_vim_colors` in the short format
* `d_mutt_colors` and `d_vim_colors` in the long format

Dotfile can be imported as a different file with the use
of the command line switch `--as` (effectively selecting the `src` part
of the dotfile in the config). It is however recommended
to use [templating](templating.md) to avoid duplicates and optimize
dotfiles management.
```bash
$ dotdrop import ~/.zshrc --as=~/.zshrc.test
```

## List profiles

```bash
$ dotdrop profiles
```

Dotdrop allows to choose which profile to use
with the `--profile` switch if you use something
else than the default (the hostname).

The default profile can also be changed by defining the
`DOTDROP_PROFILE` environment variable.

## List dotfiles

The following command lists the different dotfiles
configured for a specific profile:

```bash
$ dotdrop files --profile=<some-profile>
```

For example:
```
Dotfile(s) for profile "some-profile":
f_vimrc (file: "vimrc", link: nolink)
	-> ~/.vimrc
f_dunstrc (file: "config/dunst/dunstrc", link: nolink)
	-> ~/.config/dunst/dunstrc
```

By using the `-T --template` switch, only the dotfiles that
are using [jinja2](https://palletsprojects.com/p/jinja/) directives are listed.

It is also possible to list all files related to each dotfile entries
by invoking the `detail` command, for example:
```bash
$ dotdrop detail
dotfiles details for profile "some-profile":
f_tmux.conf (dst: "~/.tmux.conf", link: nolink)
        -> /home/user/dotfiles/tmux.conf (template:no)
f_vimrc (dst: "~/.vimrc", link: nolink)
        -> /home/user/dotfiles/vimrc (template:no)
```

This is especially useful when the dotfile entry is a directory
and one wants to have information on the different files (is it
a templated file, etc).

## Update dotfiles

Dotfiles managed by dotdrop can be updated using the `update` command. When updating, only
dotfiles that have differences with the stored version are updated.
A confirmation is requested from the user before any overwrite/update unless the
`-f --force` switch is used.

Either provide the path of the file containing the new version of the dotfile or
provide the dotfile key to update (as found in the config file) along with the `-k --key` switch.
When using the `-k --key` switch and no key is provided, all dotfiles for that profile are updated.
```bash
# update by path
$ dotdrop update ~/.vimrc

# update by key with the --key switch
$ dotdrop update --key f_vimrc
```

If not argument is provided, all dotfiles for the selected profile are updated.

To ignore specific pattern,
see [the dedicated page](config.md#ignore-patterns)

There are two cases when updating a dotfile:

### The dotfile doesn't use [templating](templating.md)

The new version of the dotfile is copied to the *dotpath* directory and overwrites
the old version. If git is used to version the dotfiles stored by dotdrop, the git command
`diff` can be used to view the changes.

```bash
$ dotdrop update ~/.vimrc
$ git diff
```

### The dotfile uses [templating](templating.md)

The dotfile must be manually updated, three solutions can be used to identify the
changes to apply to the template:

* Use dotdrop's `compare` command
```bash
# use compare to identify change(s)
$ dotdrop compare --file=~/.vimrc
```

* Call `update` with the `-P --show-patch` switch that will provide with an ad-hoc solution
  to manually patch the template file using a temporary generated version of the template
  (this isn't a bullet proof solution and might need manual checking)
```bash
# get an ad-hoc solution to manually patch the template
$ dotdrop update --show-patch ~/.vimrc
[WARN] /home/user/dotfiles/vimrc uses template, update manually
[WARN] try patching with: "diff -u /tmp/dotdrop-sbx6hw0r /home/user/.vimrc | patch /home/user/dotfiles/vimrc"
```

* Install the dotfiles to a temporary directory (using the `install` command and the
  `-t` switch) and compare the generated dotfile with the local one.
```bash
# use install to identify change(s)
$ dotdrop install -t
Installed to tmp /tmp/dotdrop-6ajz7565
$ diff ~/.vimrc /tmp/dotdrop-6ajz7565/home/user/.vimrc
```

It is also possible to install only specific dotfiles by providing their keys
in the command line. For example for a dotfile having a key `f_zshrc` in the config file.
```bash
$ dotdrop install -t f_zshrc
```

## Remove dotfiles

The command `remove` allows to stop managing a specific dotfile with
dotdrop. It will:

* remove the entry in the config file (under `dotfiles` and `profile`)
* remove the file from the `dotpath`

## Environment variables

Following environment variables can be used to specify different CLI options.
Note that CLI switches take precedence over environment variables (except for `DOTDROP_FORCE_NODEBUG`)

* `DOTDROP_PROFILE`: `-p --profile`
```bash
export DOTDROP_PROFILE="my-fancy-profile"
```
* `DOTDROP_CONFIG`: `-c --cfg`
```bash
export DOTDROP_CONFIG="/home/user/dotdrop/config.yaml"
```
* `DOTDROP_NOBANNER`: `-b --no-banner`
```bash
export DOTDROP_NOBANNER=
```
* `DOTDROP_DEBUG`: `-V --verbose`
```bash
export DOTDROP_DEBUG=
```
* `DOTDROP_FORCE_NODEBUG`: disable debug outputs even if `-V --verbose` is provided or `DOTDROP_DEBUG` is set
```bash
export DOTDROP_FORCE_NODEBUG=
```
