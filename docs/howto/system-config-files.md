# Manage system dotfiles

Dotdrop doesn't allow to handle file owernership (at least not directly). Every file operations (create/copy file/directory, create symlinks, etc) are executed with the rights of the user calling dotdrop.

Using dotdrop with `sudo` to unprivileged and privileged files in the same *session* is a bad idea as the resulting files will all have messed up owners.

It is therefore recommended to have two different config files (and thus two different *dotpath*)
for handling these two uses cases:

For example:

* one `config-user.yaml` for the local/user dotfiles (with its dedicated *dotpath*, for example `dotfiles-user`)
* one `config-root.yaml` for the system/root dotfiles (with its dedicated *dotpath*, for example `dotfiles-root`)

`config-user.yaml` is used when managing the user's dotfiles
```bash
## user config file is config-user.yaml
$ ./dotdrop.sh import --cfg config-user.yaml <some-dotfile>
$ ./dotdrop.sh install --cfg config-user.yaml
...
```

`config-root.yaml` is used when managing system's dotfiles and is to be used with `sudo` or directly by the root user
```bash
## root config file is config-root.yaml
$ sudo ./dotdrop.sh import --cfg=config-root.yaml <some-dotfile>
$ sudo ./dotdrop.sh install --cfg=config-root.yaml
...
```
