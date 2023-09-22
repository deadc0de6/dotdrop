# Handle compressed directories

This is an example of how to use transformations (`trans_install` and `trans_update`) to store
compressed directories and deploy them with dotdrop.

Start by defining the transformations:
```yaml
trans_install:
  uncompress: "mkdir -p {1} && tar -xf {0} -C {1}"
trans_update:
  compress: "tar -cf {1} -C {0} ."
```

Then import the directory by specifying which transformations to apply/associate:
```bash
dotdrop import --transw=compress --transr=uncompress ~/.somedir
```

The *read* transformation `uncompress` is used to execute the below command before installing/comparing the dotfile (where `{0}` is the source and `{1}` the destination):
```bash
mkdir -p {1} && tar -xf {0} -C {1}
```

And the *write* transformation `compress` is run when updating the dotfile directory by compressing it (where `{0}` is the source and `{1}` the destination):
```bash
tar -cf {1} -C {0} .
```

See [transformations](../config/config-transformations.md).