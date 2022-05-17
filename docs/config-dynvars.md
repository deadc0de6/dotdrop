# Dynvariables entry

The **dynvariables** entry (optional) contains an interpreted variables mapping.

```yaml
dynvariables:
  <variable-name>: <shell-oneliner>
```

Dynvariables (*dynamic* variables) will be interpreted by the shell before being substituted.

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

They have the same properties as [Variables](config-file.md#variables).