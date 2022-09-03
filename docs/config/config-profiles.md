# Profiles entry

The **profiles** entry (mandatory) contains a YAML object with sub-objects for the profiles for the different dotfiles that need to be managed.  The entries in the sub-objects are as follows:

Entry    | Description
-------- | -------------
`dotfiles` | The dotfiles associated with this profile
`import` | List of paths containing dotfile keys for this profile (absolute path or relative to the config file location; see [Import profile dotfiles from file](config-profiles.md#profile-import-entry)).
`include` | Include all elements (dotfiles, actions, (dyn)variables, etc) from another profile (See [Include dotfiles from another profile](config-profiles.md#profile-include-entry) and [meta profiles](../howto/group-hosts.md))
`variables` | Profile-specific variables (See [Variables](config-file.md#variables))
`dynvariables` | Profile-specific interpreted variables (See [Interpreted variables](config-dynvars.md))
`actions` | List of action keys that need to be defined in the **actions** entry below (See [actions](config-actions.md))

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