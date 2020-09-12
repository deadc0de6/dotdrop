# Config variables

* [Config available variables](available-variables)
    * [Variables entry](#variables-entry)
    * [Profile variables](#profile-variables)
    * [Config variables in templates](#config-variables-in-templates)
    * [Interpreted variables entry](#interpreted-variables-entry)

---

# Config available variables

Multiple variables can be used within the config file to
parametrize following elements of the config:

* dotfiles `src` and `dst` paths (see [Dynamic dotfile paths](config#dynamic-dotfile-paths))
* external path specifications
  * `import_variables`
  * `import_actions`
  * `import_configs`
  * profiles's `import`

`actions` and `transformations` also support the use of variables
but those are resolved when the action/transformation is executed
(see [Dynamic actions](config#dynamic-actions),
[Dynamic transformations](config#dynamic-transformations) and [Templating](templating)).

Following variables are available in the config files:

* [variables defined in the config](#variables-entry)
* [interpreted variables defined in the config](#interpreted-variables-entry)
* [profile variables defined in the config](#profile-variables)
* environment variables: `{{@@ env['MY_VAR'] @@}}`
* dotdrop header: `{{@@ header() @@}}` (see [Dotdrop header](templating#dotdrop-header))

As well as all template methods (see [Available methods](templating#available-methods))

# Variables entry

Variables defined in the `variables` entry are made available within the config file.

Config variables are recursively evaluated what means that
a config like the below
```yaml
variables:
  var1: "var1"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
dynvariables:
  dvar1: "echo dvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
```

will result in the following available variables:
* var1: `var1`
* var2: `var1 var2`
* var3: `var1 var2 var3`
* var4: `echo var1 var2 var3`
* dvar1: `dvar1`
* dvar2: `dvar1 dvar2`
* dvar3: `dvar1 dvar2 dvar3`
* dvar4: `var1 var2 var3`

# Profile variables

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

# Config variables in templates

`variables` and `dynvariables` are also made available in templates
(see [Template variables](templating#template-variables)).

Variables in the config file
```yaml
variables:
  var1: some variable content
  var2: some other content
```

Can be used in any templates like this
```
var1 value is: {{@@ var1 @@}}
```

# Interpreted variables entry

It is also possible to have *dynamic* variables in the sense that their
content will be interpreted by the shell before being substituted.

These need to be defined in the config file under the entry `dynvariables`.

For example:
```yaml
dynvariables:
  dvar1: head -1 /proc/meminfo
  dvar2: "echo 'this is some test' | rev | tr ' ' ','"
  dvar3: /tmp/my_shell_script.sh
  user: "echo $USER"
  config_file: test -f "{{@@ user_config @@}}" && echo "{{@@ user_config @@}}" || echo "{{@@ dfl_config @@}}"
variables:
  user_config: "profile_{{@@ user @@}}_uid.yaml"
  dfl_config: "profile_default.yaml"
```

They have the same properties as [Variables](#variables-entry).
