# Manage system dotfiles

Dotdrop doesn't allow to handle file owernership (at least not directly). Every file operation (create/copy file/directory, create symlinks, etc.) is executed with the rights of the user calling dotdrop.

Using dotdrop with `sudo` to manage unprivileged and privileged files in the same *session* is a bad idea as the resulting files will all have messed-up owners.

It is therefore recommended to have two different config files (and thus two different *dotpath*s)
for handling these two uses cases:

For example:

* One `config-user.yaml` for the local/user dotfiles (with its dedicated *dotpath*, for example `dotfiles-user`)
* One `config-root.yaml` for the system/root dotfiles (with its dedicated *dotpath*, for example `dotfiles-root`)

`config-user.yaml` is used when managing the user's dotfiles:
```bash
## user config file is config-user.yaml
$ dotdrop import --cfg config-user.yaml <some-dotfile>
$ dotdrop install --cfg config-user.yaml
...
```

`config-root.yaml` is used when managing the system's dotfiles and is to be used with `sudo` or directly by the root user:
```bash
## root config file is config-root.yaml
$ sudo dotdrop import --cfg=config-root.yaml <some-dotfile>
$ sudo dotdrop install --cfg=config-root.yaml
...
```

When commiting the local and system wide changes git will complain about permission. To fix that run:
```
$ sudo chown -R <user>:<user> <system-wide-dotfiles>
```
