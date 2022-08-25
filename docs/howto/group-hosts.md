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

```yaml
profiles:
  meta_base:
    dotfiles:
    - f_zshrc
    - f_zshrc
  os_arch:
    variables:
      distro: arch
    include:
    - meta-base
  os_debian:
    variables:
      distro: debian
    include:
    - meta-base
  home:
    include:
    - os_arch
    dotfiles:
    - f_vimrc
  office:
    include:
    - os_debian
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