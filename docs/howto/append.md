# Append text on install

Sometimes it might be useful to be able to append some text to a
file. Dotdrop is able to do that with the help of
[actions](../config/config-actions.md) and a temporary file.

Below is a config example to append to a file:
```yaml
dynvariables:
  tmpfile: mktemp
variables:
  somefile_final: ~/.somefile
dotfiles:
  f_somefile:
    dst: "{{@@ tmpfile @@}}"
    src: somefile
    actions:
      - strip "{{@@ somefile_final @@}}"
      - append "{{@@ tmpfile @@}}" "{{@@ somefile_final @@}}"
actions:
  pre:
    strip: "sed -i '/^# my pattern$/,$d' {0}"
  post:
    append: "cat {0} >> {1}; rm -f {0}"
```
During installation, the `strip` action is executed before the installation, and it strips everything from the pattern `# my pattern` to the end of the file. Then the dotfile `somefile` is installed in a temporary location (here `tmpfile`) and finally the post action `append` will append the contents of the `tmpfile` to the final dotfile pointed to by `somefile_final`.

Obviously, the dotfile in the dotpath should start with a unique pattern (here `# my pattern`):
```
# my pattern
this is the end
```
