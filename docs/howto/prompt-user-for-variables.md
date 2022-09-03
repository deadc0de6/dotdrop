# Prompt user for variables

With the use of [uservariables](../config/config-uservars.md),
one can define specific variables that need to be initially filled in manually
by the user on first run.

The provided values are then automatically saved by dotdrop to `uservariables.yaml`,
which can be included in the main config as a file from which variables are imported
using [import_variables](../config/config-config.md).

Let's say, for example, that you want to manually provide the email value
on new hosts you deploy your dotfiles to.

You'd add the following elements to your config:
```yaml
uservariables:
  emailvar: "email"
config:
  import_variables:
    - uservariables.yaml:optional
```

On first run, the `emailvar` is prompted to the user and then saved
to `uservariables.yaml`. Since this file is imported, the value for
`emailvar` will automatically be filled in without prompting the
user on subsequent calls.
