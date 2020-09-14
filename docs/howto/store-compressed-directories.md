# Handle compressed directories

This is an example on how to use transformations (`trans_read` and `trans_write`) to store
compressed directories and deploy them with dotdrop.

Config file:
```yaml
trans_read:
  uncompress: "mkdir -p {1} && tar -xf {0} -C {1}"
trans_write:
  compress: "tar -cf {1} -C {0} ."
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_somedir:
    dst: ~/.somedir
    src: somedir
    trans_read: uncompress
    trans_write: compress
profiles:
  p1:
    dotfiles:
    - d_somedir
```

The *read* transformation `uncompress` is used to execute below command before deploying the dotfile (where `{0}` is the source and `{1}` the destination)
```
mkdir -p {1} && tar -xf {0} -C {1}
```

And the *write* transformation `compress` is run when updating the dotfile directory by compressing it (where `{0}` is the source and `{1}` the destination)
```
tar -cf {1} -C {0} .
```