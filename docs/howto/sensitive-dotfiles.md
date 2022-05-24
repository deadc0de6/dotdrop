# Handle secrets

Two solutions exist, the first one using an unversioned file (see [Environment variables](../templating.md#environment-variables))
and the second using transformations (see [Store encrypted dotfiles](#store-encrypted-dotfiles)).

* [Store encrypted dotfiles](#store-encrypted-dotfiles)
* [Load passphrase from file](#load-passphrase-from-file)

## Store encrypted dotfiles

Here's an example of part of a config file to use gpg encrypted dotfiles:
```yaml
dotfiles:
  f_secret:
    dst: ~/.secret
    src: secret
    trans_read: _gpg
trans_read:
  _gpg: gpg2 -q --for-your-eyes-only --no-tty -d {0} > {1}
```

The above config allows to store the dotfile `~/.secret` encrypted in the *dotpath*
directory and uses gpg to decrypt it when `install` is run.

Here's how to deploy the above solution:

* Import the clear dotfile (what creates the correct entries in the config file):

```bash
$ dotdrop import ~/.secret
```

* Encrypt the original dotfile:

```bash
$ <some-gpg-command> ~/.secret
```

* Overwrite the dotfile with the encrypted version:

```bash
$ cp <encrypted-version-of-secret> dotfiles/secret
```

* Edit the config file and add the transformation to the dotfile
  (as shown in the example above)

* Commit and push the changes

See [transformations](../config-transformations.md).

## Load passphrase from file

Passphrase is retrieved using a script:
```yaml
variables:
  gpg_password: "./get-password.sh"
trans_read:
  _gpg: "gpg2 --batch --yes --passphrase-file <({{@@ gpg_password @@}}) -q --for-your-eyes-only --no-tty -d {0} > {1}"
```

Passphrase is stored in a file directly:
```yaml
variables:
  gpg_password_file: "/tmp/the-password"
trans_read:
  _gpg: "gpg2 --batch --yes --passphrase-file <(cat {{@@ gpg_password_file @@}}) -q --for-your-eyes-only --no-tty -d {0} > {1}"
```

See [transformations](../config-transformations.md).
