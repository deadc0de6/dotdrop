# Manage system dotfiles

Dotdrop doesn't allow to handle file rights and permissions (at least not directly). Every operations (`mkdir`, `cp`, `mv`, `ln`, file creation) are executed with the rights of the user calling dotdrop. The rights of the stored dotfile are mirrored on the deployed dotfile (`chmod` like). It works well for local/user dotfiles but doesn't allow to manage global/system config files (`/etc` or `/var` for example) directly.

Using dotdrop with `sudo` to handle local **and** global dotfiles in the same *session* is a bad idea as the resulting files will all have messed up owners.

It is therefore recommended to have two different config files (and thus two different *dotpath*) for handling these two uses cases:

* one `config.yaml` for the local/user dotfiles (with its dedicated *dotpath*)
* another config file for the global/system dotfiles (with its dedicated *dotpath*)

The default config file (`config.yaml`) is used when installing the user dotfiles as usual
```bash
# default config file is config.yaml
$ ./dotdrop.sh import <some-dotfile>
$ ./dotdrop.sh install
...
```

A different config file (for example `global-config.yaml` and its associated *dotpath*) is used when installing/managing global dotfiles and is to be used with `sudo` or directly by the root user
```bash
# specifying explicitly the config file with the --cfg switch
$ sudo ./dotdrop.sh import --cfg=global-config.yaml <some-dotfile>
$ sudo ./dotdrop.sh install --cfg=global-config.yaml
...
```