# Handle secrets

* [Using environment variables](#using-environment-variables)
* [Store encrypted dotfiles using GPG](#store-encrypted-dotfiles-using-gpg)
* [GPG examples](#gpg-examples)

## Using environment variables

For example, you can have an `.env` file in the directory where your `config.yaml` lies:
```bash
## Some secrets
pass="verysecurepassword"
```

If this file contains secrets that should not be tracked by Git,
put it in your `.gitignore`.

You can then invoke dotdrop with the help of an alias
```bash
# when dotdrop is installed as a submodule
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) ~/dotfiles/dotdrop.sh'

# when dotdrop is installed from package
alias dotdrop='eval $(grep -v "^#" ~/dotfiles/.env) /usr/bin/dotdrop --cfg=~/dotfiles/config.yaml'
```

The above aliases load all the variables from `~/dotfiles/.env`
(while omitting lines starting with `#`) before calling dotdrop.
Defined variables can then be used [in the config](../config/config-file.md#template-config-entries)
or [for templating dotfiles](../template/templating.md)

For more see [the doc on environment variables](../template/template-variables.md#environment-variables).

## Store encrypted dotfiles using GPG

First you need to define the encryption/decryption methods, for example
```yaml
variables:
  keyid: "11223344"
trans_install:
  _decrypt: "gpg -q --for-your-eyes-only--no-tty -d {0} > {1}"
trans_update:
  _encrypt: "gpg -q -r {{@@ keyid @@}} --armor --no-tty -o {1} -e {0}"
```

You can then import your dotfile and specify the transformations to apply/associate.
```bash
dotdrop import --transw=_encrypt --transr=_decrypt ~/.secret
```

Now whenever you install/compare your dotfile, the `_decrypt` transformation will be executed
to get the clear version of the file.
When updating the `_encrypt` transformation will transform the file to store it encrypted.

See [transformations](../config/config-transformations.md).

## gpg examples

Using GPG keys:
```yaml
variables:
  keyid: "11223344"
trans_install:
  _decrypt: "gpg -q --for-your-eyes-only--no-tty -d {0} > {1}"
trans_update:
  _encrypt: "gpg -q -r {{@@ keyid @@}} --armor --no-tty -o {1} -e {0}"
```

Passphrase is stored in an environment variable:
```yaml
trans_install:
  _decrypt: "echo {{@@ env['THE_KEY'] @@}} | gpg -q --batch --yes --for-your-eyes-only --passphrase-fd 0 --no-tty -d {0} > {1}"
trans_update:
  _encrypt: "echo {{@@ env['THE_KEY'] @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -o {1} -c {0}"
```

Passphrase is stored as a variable:
```yaml
variables:
  gpg_password: "some password"
trans_install:
  _decrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --for-your-eyes-only --passphrase-fd 0 --no-tty -d {0} > {1}"
trans_update:
  _encrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -o {1} -c {0}"
```

Passphrase is retrieved using a script:
```yaml
dynvariables:
  gpg_password: "./get-password.sh"
trans_install:
  _decrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --for-your-eyes-only --passphrase-fd 0 --no-tty -d {0} > {1}"
trans_update:
  _encrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -o {1} -c {0}"
```

Passphrase is stored in a file:
```yaml
variables:
  gpg_password_file: "/tmp/the-password"
dynvariables:
  gpg_password: "cat {{@@ gpg_password_file @@}}"
trans_install:
  _decrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --for-your-eyes-only --passphrase-fd 0 --no-tty -d {0} > {1}"
trans_update:
  _encrypt: "echo {{@@ gpg_password @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -o {1} -c {0}"
```

See also [transformations](../config/config-transformations.md).
