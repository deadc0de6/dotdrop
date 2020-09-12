# Welcome to the dotdrop wiki!

The idea of dotdrop is to have the ability to store each dotfile only once and deploy them with a different content on different hosts/setups. To achieve this, it uses [jinja2](http://jinja.pocoo.org/) which is a templating engine that allows to specify, during the dotfile installation with dotdrop, based on a selected profile, how (with what content) each dotfile will be installed.

Most information on using dotdrop are described in this wiki and in the [readme](https://github.com/deadc0de6/dotdrop/blob/master/README.md). For more check

* [a quick overview of dotdrop features](https://deadc0de.re/dotdrop/)
* [the blogpost on dotdrop](https://deadc0de.re/articles/dotfiles.html)
* [an example](https://github.com/deadc0de6/dotdrop#getting-started)
* [how people are using dotdrop](meta/people-using-dotdrop.md)

For more examples of config file, [search github](https://github.com/search?q=filename%3Aconfig.yaml+dotdrop&type=Code).

# Wiki pages

* [Installation](installation.md)
* [Usage](usage.md)
* [Config file format](config/config.md)
    * [Use actions](config/usage-actions.md)
    * [Use transformations](config/usage-transformations.md)
    * [Manage system/global config files](howto/global-config-files.md)
    * [Ignore patterns](config/ignore-pattern.md)
* [Templating](template/templating.md)
* HowTo
    * [Store secrets](howto/sensitive-dotfiles.md)
    * [Symlink dotfiles](howto/symlinked-dotfiles.md)
    * [Store compressed directories](howto/store-compressed-directories.md)
    * [Merge files when installing](howto/merge-files-when-installing.md)
    * [Append to a dotfile](howto/append.md)
    * [Handle special chars](howto/special-chars.md)
    * [Share content across dotfiles](howto/sharing-content.md)
    * [Create special files](howto/create-special-files.md)
