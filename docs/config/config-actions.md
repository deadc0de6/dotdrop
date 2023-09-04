# Actions entry

The **actions** entry (optional) contains an actions mapping.

```yaml
actions:
  <action-key>: <command-to-execute>
```

*pre* actions:
```yaml
actions:
  pre:
    <action-key>: <command-to-execute>
```

*post* actions:
```yaml
actions:
  post:
    <action-key>: <command-to-execute>
```

Actions can be either `post` or `pre`.

* `post` action will be executed after the dotfile deployment.
* `pre` action will be executed before the dotfile deployment.

If you don't specify either `post` or `pre`, the action will be executed
after the dotfile deployment (which is equivalent to `post`).
Actions cannot obviously be named `pre` or `post`.

Four types of actions can be defined:

* [Dotfiles actions](config-dotfiles.md#dotfile-actions)
* [Default actions](config-config.md#default_actions-entry)
* [Profile actions](config-profiles.md#profile-actions-entry)
* [Fake dotfiles and actions](config-actions.md#fake-dotfile-and-actions)

**Notes**:

* Any action with a key starting with an underscore (`_`) won't be shown in output. This can be useful when working with sensitive data containing passwords, for example.
* Make sure to quote your actions to avoid bad surprises
* Actions are executed using the default shell (`$SHELL`)
* To use shell variables in your actions, you need to escape the curly brackets (`${HOME}` becomes `${{HOME}}`)

## Fake dotfile and actions

*Fake* dotfile can be created by specifying no `dst` and no `src` (see [Fake dotfiles and actions](config-actions.md#fake-dotfile-and-actions)).
By binding an action to such a *fake* dotfile, you make sure the action is always executed since
*fake* dotfile are always considered installed.

```yaml
actions:
  always_action: 'date > ~/.dotdrop.log'
dotfiles:
  fake:
    src:
    dst:
    actions:
    - always_action
```

## Dynamic actions

Variables ([config variables and dynvariables](config-file.md#variables)
and [template variables](../template/template-variables.md)) can be used
in actions for more advanced use-cases.

Actions accept arguments in the form `{<arg-num>}` which specifies which
argument to replace in the action.

For example
```yaml
dotfiles:
  f_test:
    dst: ~/.test
    src: test
    actions:
      - cookie_mv_somewhere "/tmp/moved-cookie"
variables:
  cookie_dir_available: (test -d /tmp/cookiedir || mkdir -p /tmp/cookiedir)
  cookie_header: "{{@@ cookie_dir_available @@}} && echo 'header' > /tmp/cookiedir/cookie"
  cookie_mv: "{{@@ cookie_header @@}} && mv /tmp/cookiedir/cookie"
actions:
  cookie_mv_somewhere: "{{@@ cookie_mv @@}} {0}"
```

or even something like this:
```yaml
actions:
  log: "echo {0} >> {1}"
config:
  default_actions:
  - log '{{@@ _dotfile_key @@}} installed' "/tmp/log"
...
```

Make sure to quote the actions using variables.
