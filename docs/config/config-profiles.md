# Profiles entry

The mandatory `profiles` entry contains a YAML object with sub-objects defining
each profile and its related dotfiles, variables, actions, and other configurations.

A profile whose name starts with an underscore is a *hidden profile*:
it is not displayed by the `profiles` command and cannot be installed
directly without `--force` (See [hidden profiles](config-profiles.md#hidden-profiles)).

The entries in the sub-objects are as follows:

Entry    | Description
-------- | -------------
`dotfiles` | The dotfiles associated with this profile
`import` | List of paths containing dotfile keys for this profile (absolute path or relative to the config file location; see [Import profile dotfiles from file](config-profiles.md#profile-import-entry)).
`include` | Include all elements (dotfiles, actions, (dyn)variables, etc) from another profile (See [Include dotfiles from another profile](config-profiles.md#profile-include-entry) and [meta profiles](../howto/group-hosts.md))
`variables` | Profile-specific variables (See [Variables](config-file.md#variables))
`dynvariables` | Profile-specific interpreted variables (See [Interpreted variables](config-dynvars.md))
`actions` | List of action keys defined in the [actions](config-actions.md) entry (See [actions](config-actions.md))
`description` | *Optional*, one-liner description of this profile, displayed by `dotdrop profiles` (See [Profile description entry](config-profiles.md#profile-description-entry))
`group` | *Optional*, group this profile belongs to, `dotdrop profiles` regroups profiles by group (See [Profile group entry](config-profiles.md#profile-group-entry))

```yaml
<some-profile-name-usually-the-hostname>:
  dotfiles:
  - <some-dotfile-key-name-defined-above>
  - <some-other-dotfile-key-name>
  - ...
  ## Optional
  include:
  - <some-other-profile>
  - ...
  variables:
    <name>: <value>
  dynvariables:
    <name>: <value>
  actions:
  - <some-action>
  - ...
  import:
  - <some-path>
  - ...
  description: <some one-liner describing this profile>
  group: <some group name>
```

## Profile include entry

If one profile is using the entire set of another profile, one can use
the `include` entry to avoid redundancy.

Note that everything from the included profile is made available
(actions, variables/dynvariables, etc). See also an example in
[meta profiles](../howto/group-hosts.md).

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

For more advanced use-cases, variables
([variables](config-variables.md) and [dynvariables](config-dynvars.md))
can be used to specify the profile to include in a profile:

For example:
```yaml
variables:
  var1: "john"
dynvariables:
  d_user: "echo $USER"
profiles:
  profile_john:
    dotfiles:
    - f_john_dotfile
  profile_bill:
    dotfiles:
    - f_bill_dotfile
  p1:
    include:
    - "profile_{{@@ d_user @@}}"
  p2:
    include:
    - "profile_{{@@ var1 @@}}"
```

Note that profiles cannot include other profiles defined above in
the import tree (for example, when a profile exists in another file and is imported using `import_configs`).

## Profile import entry

A profile's dotfiles list can be loaded from external files
by specifying their paths in the config entry `import` under the specific profile.

The paths can be absolute or relative to the config file location.

`config.yaml`
```yaml
dotfiles:
  f_abc:
    dst: ~/.abc
    src: abc
  f_def:
    dst: ~/.def
    src: def
  f_xyz:
    dst: ~/.xyz
    src: xyz
profiles:
  p1:
    dotfiles:
    - f_abc
    import:
    - somedotfiles.yaml
```

`somedotfiles.yaml`
```
dotfiles:
  - f_def
  - f_xyz
```

Variables can be used in `import`, what allows to do something like:
```yaml
import:
- profiles.d/{{@@ profile @@}}.yaml
```

## Profile variables entry

Profile variables will take precedence over globally defined variables.
This means that you could do something like this:
```yaml
variables:
  git_email: home@email.com
dotfiles:
  f_gitconfig:
    dst: ~/.gitconfig
    src: gitconfig
profiles:
  work:
    dotfiles:
    - f_gitconfig
    variables:
      git_email: work@email.com
  private:
    dotfiles:
    - f_gitconfig
```

## Profile actions entry

A profile action can be either a `pre` or `post` action (see [actions](config-actions.md)).
These are executed before any dotfile installation (for `pre`) and after all dotfile installations (for `post`)
only if at least one dotfile has been installed.

## Profile description entry

A profile can optionally be given a one-liner description that will be
displayed next to the profile by the `profiles` command.

This is useful to document the purpose of a profile (for example a
[meta profile](../howto/group-hosts.md)):

```yaml
profiles:
  base:
    description: base set of dotfiles shared by all hosts
    dotfiles:
    - f_gitconfig
  home:
    description: home workstation
    include:
    - base
```

Running `dotdrop profiles` gives:

```
Available profile(s):
	-> base (1 dotfiles) - base set of dotfiles shared by all hosts
	-> home (1 dotfiles) - home workstation
```

## Profile group entry

A profile can be assigned to a group to make it easier to
structure a large number of profiles, for example to clearly separate
[meta profiles](../howto/group-hosts.md) from host profiles.

The `profiles` command displays profiles regrouped by their group
(groups are displayed in the order in which they are encountered):

```yaml
profiles:
  zsh:
    group: meta
    dotfiles:
    - f_zshrc
  base:
    group: meta
    description: base set of dotfiles shared by all hosts
    dotfiles:
    - f_gitconfig
  home:
    group: hosts
    include:
    - base
  office:
    group: hosts
    dotfiles:
    - f_something
```

Running `dotdrop profiles` gives:

```
Available profile(s):
group "meta":
	-> zsh (1 dotfiles)
	-> base (1 dotfiles) - base set of dotfiles shared by all hosts
group "hosts":
	-> home (1 dotfiles)
	-> office (1 dotfiles)
```

The `group` entry is optional. Profiles without a `group` entry belong
to the unnamed top group: they are displayed on top, without a group header.

## Hidden profiles

A profile whose name starts with an underscore is *hidden*:
it is not displayed by the `profiles` command.
This is handy for [meta profiles](../howto/group-hosts.md)
that exist only to be included by other profiles.

A hidden profile cannot be directly installed,
`dotdrop install -p <profile>` will result in an error unless
`--force` is used. However, hidden profiles can still be included
by other profiles, which can then be installed normally:

```yaml
profiles:
  _base:
    dotfiles:
    - f_gitconfig
  home:
    include:
    - _base
```