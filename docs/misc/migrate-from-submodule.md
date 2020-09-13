**WARNING**

Only do the following if you are using dotdrop version `< 0.7.1` or if you encounter an issue when running dotdrop that redirects you here.

---

Initially dotdrop was only available as a submodule directly in the
dotfiles git tree. When updated to work with pypi, some code changed
that brought some issues to older versions.

If you want to keep it as a submodule (recommended), simply do the following
```bash
$ cd <dotfiles-directory>

## get latest version of the submodule
$ git submodule foreach git pull origin master

## and stage the changes
$ git add dotdrop
$ git commit -m 'update dotdrop'

## update the bash script wrapper
$ ./dotdrop/bootstrap.sh

## and stage the change to the dotdrop.sh script
$ git add dotdrop.sh
$ git commit -m 'update dotdrop.sh'

## and finally push the changes upstream
$ git push
```

Otherwise, simply install it from pypi as shown below:

* move to the dotfiles directory where dotdrop is used as a submodule
```bash
$ cd <dotfiles-repository>
```
* remove the entire `submodule "dotdrop"` section in `.gitmodules`
* stage the changes
```bash
$ git add .gitmodules
```
* remove the entire `submodule "dotdrop"` section in `.git/config`
* remove the submodule
```bash
$ git rm --cached dotdrop
```
* remove the submodule from .git
```bash
$ rm -rf .git/modules/dotdrop
```
* commit the changes
```bash
$ git commit -m 'removing dotdrop submodule'
```
* remove any remaining files from the dotdrop submodule
```bash
$ rm -rf dotdrop
```
* remove `dotdrop.sh`
```bash
$ git rm dotdrop.sh
$ git commit -m 'remove dotdrop.sh script'
```
* push upstream
```bash
$ git push
```
