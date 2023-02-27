# Test latest dotdrop

If you installed dotdrop from a package but want to test
you current setup with the latest version from git
(or from a specific branch), you can do the following

```bash
$ cd /tmp/
$ git clone https://github.com/deadc0de6/dotdrop.git
$ cd dotdrop
## switch to a specific branch if needed
$ git checkout <branch-name>
$ ./dotdrop.sh --cfg <path-to-your-config-file.yaml>
```