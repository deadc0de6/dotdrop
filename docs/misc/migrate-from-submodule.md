**WARNING**

Only do the following if you are using dotdrop version `< 0.7.1` or if you encounter an issue when running dotdrop that redirects you here.

---

Initially dotdrop was only available as a submodule directly in the
dotfiles git tree. When updated to work with PyPI, some code changed
that brought some issues to older versions.

If you want to keep it as a submodule (recommended), simply do the following:
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

Otherwise, simply install it from PyPI as shown below:

* Move to the dotfiles directory where dotdrop is used as a submodule
```bash
$ cd <dotfiles-repository>
```
* Remove the entire `submodule "dotdrop"` section in `.gitmodules`
* Stage the changes
```bash
$ git add .gitmodules
```
* Remove the entire `submodule "dotdrop"` section in `.git/config`
* Remove the submodule
```bash
$ git rm --cached dotdrop
```
* Remove the submodule from .git
```bash
$ rm -rf .git/modules/dotdrop
```
* Commit the changes
```bash
$ git commit -m 'removing dotdrop submodule'
```
* Remove any remaining files from the dotdrop submodule
```bash
$ rm -rf dotdrop
```
* Remove `dotdrop.sh`
```bash
$ git rm dotdrop.sh
$ git commit -m 'remove dotdrop.sh script'
```
* Push upstream
```bash
$ git push
```
