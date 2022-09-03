# Uservariables entry

The **uservariables** entry (optional) contains a collection of variables
whose values are queried from the user
(See [User variables](config-variables.md)).

```yaml
uservariables:
  <variable-name>: <prompt>
```

If you want to manually enter variables' values, you can use the
`uservariables` entry. Each variable will be prompted to the user.

For example:
```yaml
uservariables:
  emailvar: "email"
```

will prompt the user to enter a value for the variable `emailvar`:
```
Please provide the value for "email":
```

And store the entered text as the value for the variable `email`.
The variable can then be used as any other [variable](config-file.md#variables).

`uservariables` are eventually saved to `uservariables.yaml` (relatively to the
config file).
This allows to use the following construct to prompt once for some specific variables and
then store them in a file. You might also want to add `uservariables.yaml` to your `.gitignore`.
```yaml
uservariables:
  emailvar: "email"
config:
  import_variables:
    - uservariables.yaml:optional
```

For an example, see [prompt user for variables](../howto/prompt-user-for-variables.md).
