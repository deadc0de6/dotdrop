# Usage

Run `dotdrop --help` to see all available options.

## Profile

The default profile used by dotdrop is the *hostname* of the host you are running dotdrop on.

It can be changed:

* Using the command line switch `-p`/`--profile=<profile>`
* By defining it in the env variable `DOTDROP_PROFILE`

## List profiles

The `profiles` command lists the profiles defined in the config file.
```bash
$ dotdrop profiles
```

Dotdrop allows to choose which profile to use
with the `--profile` switch if you use something
other than the default (the hostname).

The default profile can also be changed by defining the
`DOTDROP_PROFILE` environment variable.

## Import dotfiles

The `import` command imports dotfiles to be managed by dotdrop.
It copies the dotfile to your `dotpath` and updates the config file with the new entry.

Dotdrop will ask whether to dereference symlinks on import unless `-f`/`--force` is used.

For example, to import `~/.xinitrc`:
```bash
$ dotdrop import ~/.xinitrc
	-> "/home/user/.xinitrc" imported

1 file(s) imported.
```

You can control how the dotfile key is generated in the config file
with the following [config entries](config/config-config.md):

* `longkey`
    * `false` (default): take the shortest unique path
    * `true` take the full path
* `key_prefix`: defines if the key is prefixed with `f<key_separator>` for file and `d<key_separator>` for directory
* `key_separator`: defines the separator to use (defaults to `_`)

For example, `~/.config/awesome/rc.lua` gives:

* `f_rc.lua` in the short format
* `f_config_awesome_rc.lua` in the long format

Importing `~/.mutt/colors` and then `~/.vim/colors` will result in:

* `d_colors` and `d_vim_colors` in the short format
* `d_mutt_colors` and `d_vim_colors` in the long format

It is possible to import a dotfile while pretending it was at a different
path with the use of `--as` what will effectively modify the `src` path
of the generated dotfile entry in the config as well as the location of the file
in the *dotpath*.
The argument to `--as` is expected to be an absolute path and will be made
absolute in case it isn't (specifying `--as test` will result in something like
`--as <current-working-directory>/test`). It is however recommended
to use [templating](template/templating.md) to avoid duplicates and optimize
dotfile management instead of using `--as`.
```bash
# imported to <dotpath>/zshrc.test
$ dotdrop import ~/.zshrc --as=~/.zshrc.test
```
see [issue #220](https://github.com/deadc0de6/dotdrop/issues/220) and [issue #368](https://github.com/deadc0de6/dotdrop/issues/368).

By importing a path using the profile special keyword `ALL`, a dotfile will be created
in the config but won't be associated to any profile.

To ignore specific patterns during import, see [the ignore patterns](config/config-file.md#ignore-patterns).

For more options, see the usage with `dotdrop --help`.

## Install dotfiles

The `install` command installs/deploys dotfiles managed by dotdrop from the `dotpath` to their destinations.
```bash
$ dotdrop install
```

A dotfile will be installed only if it differs from the version already present at its destination.

Some available options:

* `-t`/`--temp`: Install the dotfile(s) to a temporary directory for review (helping to debug templating issues, for example).
  Note that actions are not executed in this mode.
* `-a`/`--force-actions`: Force the execution of actions even if the dotfiles are not installed (see [Fake dotfile and actions](config/config-actions.md#fake-dotfile-and-actions) as an alternative)
* `-f`/`--force`: Do not ask for any confirmation
* `-W`/`--workdir-clear`: Clear the `workdir` before installing dotfiles (see [the config entry](config/config-config.md) `clear_workdir`)
* `-R`/`remove-existing`: Applies to directory dotfiles only (`nolink`) and will remove files not managed by dotdrop in the destination directory

To ignore specific patterns during installation, see [the ignore patterns](config/config-file.md#ignore-patterns).

For more options, see the usage with `dotdrop --help`.

## Compare dotfiles

The `compare` command compares dotfiles at their destinations with the ones stored in your `dotpath`.
```bash
$ dotdrop compare
```

The diffing is done with the UNIX tool `diff` as the backend; one can provide a specific
diff command using [the config entry](config/config-config.md) `diff_command`.

You can specify against which destination file to compare:
```bash
$ dotdrop compare -C ~/.vimrc
```

To ignore specific patterns, see [the ignore patterns](config/config-file.md#ignore-patterns).

To completely ignore all files not present in `dotpath` see [Ignore missing](config/config-file.md#ignore-missing).

If you want to get notified on files present in the `workdir` but not tracked
by dotdrop see the [compare_workdir](config/config-config.md).

For more options, see the usage with `dotdrop --help`.

## List dotfiles

The `files` command lists the dotfiles declared for a specific profile.
```bash
$ dotdrop files --profile=some-profile
f_xinitrc
	-> dst: /home/user/.xinitrc
	-> src: /home/user/dotdrop/dotfiles/xinitrc
	-> link: nolink
```

By using the `-T`/`--template` switch, only the dotfiles that
are using [templating](template/templating.md) are listed.

It is also possible to list all the files related to each dotfile entry
by invoking the `detail` command, for example:
```bash
$ dotdrop detail
dotfiles details for profile "some-profile":
f_xinitrc (dst: "/home/user/.xinitrc", link: nolink)
	-> /home/user/dotdrop/dotfiles/xinitrc (template:no)
```

This is especially useful when the dotfile entry is a directory
and one wants to have information on the different files it contains
(does a specific file uses templating, etc.).

For more options, see the usage with `dotdrop --help`.

## Update dotfiles

The `update` command updates a dotfile managed by dotdrop by copying the dotfile
from the filesystem to the `dotpath`. Only dotfiles that have differences with the stored version are updated.
A confirmation is requested from the user before any overwrite/update unless the `-f`/`--force` switch is used.

Either provide the path of the file containing the new version of the dotfile or
provide the dotfile key to update (as found in the config file) along with the `-k`/`--key` switch.
When using the `-k`/`--key` switch and no key is provided, all dotfiles for that profile are updated.
```bash
## update by path
$ dotdrop update ~/.vimrc

## update by key with the --key switch
$ dotdrop update --key f_vimrc
```

If not argument is provided, all dotfiles for the selected profile are updated.

To ignore specific patterns, see [the dedicated page](config/config-file.md#ignore-patterns).

To completely ignore all files not present in `dotpath`, see [Ignore missing](config/config-file.md#ignore-missing).

There are two cases when updating a dotfile:

* [The dotfile does not use templating](#the-dotfile-does-not-use-templating)
* [The dotfile uses templating](#the-dotfile-uses-templating)

### The dotfile does not use [templating](template/templating.md)

The new version of the dotfile is copied to the *dotpath* directory and overwrites
the old version. If Git is used to version the dotfiles stored by dotdrop, the Git command
`diff` can be used to view the changes.

```bash
$ dotdrop update ~/.vimrc
$ git diff
```

### The dotfile uses [templating](template/templating.md)

The dotfile must be manually updated; three solutions can be used to identify the
changes to apply to the template:

* Use the `compare` command:
```bash
## use compare to identify change(s)
$ dotdrop compare --file=~/.vimrc
```

* Call `update` with the `-P`/`--show-patch` switch, which provides an ad-hoc solution
  to manually patch the template file using a temporary generated version of the template.
  (This isn't a bullet-proof solution and might need manual checking.)
```bash
## get an ad-hoc solution to manually patch the template
$ dotdrop update --show-patch ~/.vimrc
[WARN] /home/user/dotfiles/vimrc uses template, update manually
[WARN] try patching with: "diff -u /tmp/dotdrop-sbx6hw0r /home/user/.vimrc | patch /home/user/dotfiles/vimrc"
```

* Install the dotfiles to a temporary directory (using the `install` command and the
  `-t` switch) and compare the generated dotfile with the local one:
```bash
## use install to identify change(s)
$ dotdrop install -t -t f_vimrc
Installed to tmp /tmp/dotdrop-6ajz7565
$ diff ~/.vimrc /tmp/dotdrop-6ajz7565/home/user/.vimrc
```

## Remove dotfiles

The command `remove` allows to stop managing a specific dotfile with
dotdrop. It will:

* remove the entry from the config file (under `dotfiles` and `profile`)
* delete the file from the `dotpath`

For more options, see the usage with `dotdrop --help`.

## Uninstall dotfiles

The `uninstall` command removes dotfiles installed by dotdrop
```bash
$ dotdrop uninstall
```

It will remove the installed dotfiles related to the provided key
(or all dotfiles if not provided) of the selected profile.

If a backup exists ([backup entry](config/config-config.md#backup-entry)),
the file will be restored.

For more options, see the usage with `dotdrop --help`.

## Concurrency

The command line switch `-w`/`--workers`, if set to a value greater than one, enables the use
of multiple concurrent workers to execute an operation. It can be applied to the following
commands:

* `install`
* `compare`
* `update`

It should be set to a maximum of the number of cores available (usually returned
on linux by the command `nproc`).

It may speed up the operation but cannot be used interactively (it needs `-f`/`--force` to be set
except for `compare`) and cannot be used with `-d`/`--dry`. Also, information printed to stdout/stderr
will probably be messed up.

**WARNING:** This feature hasn't been extensively tested and is to be used at your own risk.
If you try it out and find any issues, please [report them](https://github.com/deadc0de6/dotdrop/issues).
Also, if you find it useful and have been able to successfully speed up your operation when using
`-w`/`--workers`, do please also report it [in an issue](https://github.com/deadc0de6/dotdrop/issues).

## Environment variables

The following environment variables can be used to specify different CLI options.
Note that CLI switches take precedence over environment variables (except for `DOTDROP_FORCE_NODEBUG`)

* `DOTDROP_PROFILE`: `-p`/`--profile`
```bash
export DOTDROP_PROFILE="my-fancy-profile"
```
* `DOTDROP_CONFIG`: `-c`/`--cfg`
```bash
export DOTDROP_CONFIG="/home/user/dotdrop/config.yaml"
```
* `DOTDROP_NOBANNER`: `-b`/`--no-banner`
```bash
export DOTDROP_NOBANNER=
```
* `DOTDROP_DEBUG`: `-V`/`--verbose`
```bash
export DOTDROP_DEBUG=
```
* `DOTDROP_FORCE_NODEBUG`: disable debug output even if `-V`/`--verbose` is provided or `DOTDROP_DEBUG` is set
```bash
export DOTDROP_FORCE_NODEBUG=
```
* `DOTDROP_TMPDIR`: defines a temporary directory for dotdrop to use for its operations instead of using a system generated one
```bash
export DOTDROP_TMPDIR="/tmp/dotdrop-tmp"
```
* `DOTDROP_WORKDIR`: overwrite the `workdir` defined in the config
```bash
export DOTDROP_WORKDIR="/tmp/dotdrop-workdir"
```
* `DOTDROP_WORKERS`: overwrite the `-w`/`--workers` cli argument
```bash
export DOTDROP_WORKERS="10"
```
