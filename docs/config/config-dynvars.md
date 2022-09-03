# Dynvariables entry

The **dynvariables** entry (optional) contains an interpreted variables mapping.

```yaml
dynvariables:
  <variable-name>: <shell-oneliner>
```

You can also use multi-line (see [yaml related doc](https://yaml-multiline.info/)).
For example:
```yaml
dynvariables:
  <variable-name>: >-
    <line1>
    <line2>
    <line3>
```

For example:
```yaml
dynvariables:
  dvar1: head -1 /proc/meminfo
  dvar2: "echo 'this is some test' | rev | tr ' ' ','"
  dvar3: /tmp/my_shell_script.sh
  user: "echo $USER"
  config_file: >-
    test -f "{{@@ base_config @@}}" &&
    echo "{{@@ base_config @@}}" ||
    echo "{{@@ dfl_config @@}}"
variables:
  base_config: "profile_base.yaml"
  dfl_config: "profile_default.yaml"
```

They have the same properties as [Variables](config-variables.md).