* [Use transformations](#use-transformations)
* [Arguments and templating](#arguments-and-templating)
* [Examples](#examples)

---

**Note**: any transformation with a key starting with an underscore (`_`) won't be shown in output.
This can be useful when working with sensitive data containing passwords for example.

# Use transformations

There are two types of transformations available:

* **read transformations**: used to transform dotfiles before they are installed ([Config](config.md) key `trans_read`)
    * Used for commands `install` and `compare`
    * They have two arguments:
        * **{0}** will be replaced with the dotfile to process
        * **{1}** will be replaced with a temporary file to store the result of the transformation
    * Happens **before** the dotfile is templated with jinja2 (see [templating](../template/templating.md))

* **write transformations**: used to transform files before updating a dotfile ([Config](config.md) key `trans_write`)
    * Used for command `update`
    * They have two arguments:
        * **{0}** will be replaced with the file path to update the dotfile with
        * **{1}** will be replaced with a temporary file to store the result of the transformation

A typical use-case for transformations is when dotfiles need to be
stored encrypted or compressed. For more see below [examples](#examples).

Note that transformations cannot be used if the dotfiles is to be linked (when `link: link` or `link: link_children`).

# Arguments and templating

Transformations also support additional positional arguments that must start from 2 (since `{0}` and `{1}` are added automatically). The transformations itself as well as its arguments can also be templated.

For example
```yaml
trans_read:
  targ: echo "$(basename {0}); {{@@ _dotfile_key @@}}; {2}; {3}" > {1}
dotfiles:
  f_abc:
    dst: /tmp/abc
    src: abc
    trans_read: targ "{{@@ profile @@}}" lastarg
profiles:
  p1:
    dotfiles:
    - f_abc
```

will result in `abc; f_abc; p1; lastarg`

# Examples

See

* [Store compressed directories](../howto/store-compressed-directories.md)
* [Sensitive dotfiles](../howto/sensitive-dotfiles.md)
