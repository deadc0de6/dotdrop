# Welcome to the dotdrop wiki!

The idea of dotdrop is to have the ability to store each dotfile only once and deploy them with a different content on different hosts/setups. To achieve this, it uses [jinja2](http://jinja.pocoo.org/) which is a templating engine that allows to specify, during the dotfile installation with dotdrop, based on a selected profile, how (with what content) each dotfile will be installed.

Most information on using dotdrop are described in this wiki and in the [readme](https://github.com/deadc0de6/dotdrop/blob/master/README.md). For more check

* [a quick overview of dotdrop features](https://deadc0de.re/dotdrop/)
* [the blogpost on dotdrop](https://deadc0de.re/articles/dotfiles.html)
* [an example](https://github.com/deadc0de6/dotdrop#getting-started)
* [how people are using dotdrop](people-using-dotdrop)

For more examples of config file, [search github](https://github.com/search?q=filename%3Aconfig.yaml+dotdrop&type=Code).

# Wiki pages

* Documentation
    * [Installation](installation)
    * [Usage](usage)
    * [Config file format](config)
    * [Templating](templating)
* How To
    * [Use actions](usage-actions)
    * [Use transformations](usage-transformations)
    * [Store secrets](sensitive-dotfiles)
    * [Symlink dotfiles](symlinked-dotfiles)
    * [Store compressed directories](store-compressed-directories)
    * [Merge files when installing](merge-files-when-installing)
    * [Append to a dotfile](append)
    * [Manage system/global config files](global-config-files)
    * [Handle special chars](special-chars)
    * [Share content across dotfiles](sharing-content)
    * [Ignore patterns](ignore-pattern)
    * [Create special files](create-special-files)
* [Related projects](related-projects)
* [Troubleshooting](troubleshooting)
