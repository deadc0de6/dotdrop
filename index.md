---
layout: default
---

[Dotdrop](https://github.com/deadc0de6/dotdrop) is a dotfile manager written in Python3
that helps you to manage your dotfiles and deploy them anywhere.

If you work on multiple hosts then you are probably struggling to keep all your
dotfiles syncronized across multiple devices and be able to easily manage those.

# Why dotdrop

Why should you use [dotdrop](https://github.com/deadc0de6/dotdrop)?
Check the features

* **versioned**
  be it on github, gitlab, gitolite or your own git solution, it makes
  sure you are able to keep a history of your changes
* **quick import**
  import a new dotfile easily
* **no duplicates, efficiency**
  each dotfile is stored only once, dotdrop allows to template those
  such that the same dotfile is customized when deployed on the host you're working on
* **multiple devices**
  different profiles can be defined that allows for a fine-grained control over which
  dotfiles has to be installed on different hosts (home, work, vps, etc)
* **different sets of dotfiles for different profiles**
  some hosts will have all your dotfiles installed while others might just
  need a subset of the dotfiles
* **symlink or no symlink**
  you can choose for each dotfile if you want it to be symlinked or
  directly copied to its final destination
* **fine grained control**
  each dotfile is unique and thus each may have specific settings
  linked to it when installed
* **post deployment action**
  action can be executed each time a specific dotfile is installed, for
  example to install a package, setup some directories, call a tool to update, etc
* **handle sensitive dotfiles**
  multiple solutions are available to handle dotfiles containing sensitive information
  as well as full encrypted dotfiles/rc files
* **compare**
  quickly compare your local dotfiles with the managed ones

… and many more …

Go check [dotdrop](https://github.com/deadc0de6/dotdrop), it does all that!

For more check

* [The readme](https://github.com/deadc0de6/dotdrop/blob/master/README.md).
* [A small example](https://github.com/deadc0de6/dotdrop#example)
* [How people are using dotdrop](https://github.com/deadc0de6/dotdrop#people-using-dotdrop)
* [The blog post](https://deadc0de.re/articles/dotfiles.html)

