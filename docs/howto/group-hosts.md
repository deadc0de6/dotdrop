# Group hosts in config and meta profiles

Let's consider the situation where you have multiple hosts from different distros and you
want an easy way to structure your config file nicely but also simplify the use
of templates (since multiple hosts in the same distro would share the same configs parts -
or if branch in templates).

You define two types of profiles:

* **Meta profiles**: for example for distros it would be something like `os_arch`, `os_debian` and so on.
  These are never directly used for installing dotfiles but instead included by other profiles.
* **Host profiles** (defaults to hostnames): the usual `home`, `office`, etc

Each *Host profile* would include a *meta profile* and inherit all its dotfiles as well as
it variables. For example in the *meta profile* you would define variables like `distro: debian`
that you could use in your templates with `{%@@ if distro == "debian" @@%}` to target all
profiles that inherit from the same *meta profile*.

Meta profiles can be clearly separated from host profiles
using the [group](../config/config-profiles.md#profile-group-entry)
entry and by naming meta profiles with a leading underscore
([hidden profiles](../config/config-profiles.md#hidden-profiles)):
meta profiles get a dedicated group and are hidden, so that
`dotdrop profiles` only shows the host profiles (and `dotdrop install -p`
on a meta profile results in an error unless `--force` is used).

```yaml
profiles:
  _meta_base:
    group: meta
    description: base dotfiles for all distros
    dotfiles:
    - f_zshrc
  _os_arch:
    group: meta
    variables:
      distro: arch
    include:
    - _meta_base
  _os_debian:
    group: meta
    variables:
      distro: debian
    include:
    - _meta_base
  home:
    group: hosts
    include:
    - _os_arch
    dotfiles:
    - f_vimrc
  office:
    group: hosts
    include:
    - _os_debian
    dotfiles:
    - f_something
```

You then have the opportunity in your templates to do the following
that would select the if branch for all profiles inheriting from
a specific *meta profile*.
```
# zsh-syntax-highlighting
# https://github.com/zsh-users/zsh-syntax-highlighting
{%@@ if distro == "arch" @@%}
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
{%@@ elif distro == "debian" @@%}
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
{%@@ endif @@%}
```