# Manage dconf settings

Here is an example (thanks [@gmvelencoso](https://github.com/gmvelencoso)) 
using dotdrop to manage dconf settings:

```yaml
actions:
  dconf_load: dconf load "{0}" < "{{@@ _dotfile_abs_src @@}}"
trans_update:
  dconf_dump: dconf dump "{2}" > "{1}"
dconf_tilix:
    src: config/tilix/tilix.dconf
    dst: /tmp/tilix.dconf 
    actions:
      - dconf_load /com/gexperts/Tilix/
    trans_update: dconf_dump /com/gexperts/Tilix/
    link: nolink
````

On `install`/`compare`, the [action](../config/config-actions.md) `dconf_load` will call `dconf` to load
the configuration from the file stored in the *dotpath* under `config/tilix/tilix.dconf`.

On `update`, the [transformation](../config/config-transformations.md) `trans_update` will dump the configuration
entry and use it to update the file in the *dotpath*.
