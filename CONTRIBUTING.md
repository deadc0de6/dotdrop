Thanks for helping out!

Feature requests, bug reports and PRs are always welcome!

This file provides a few pointers on how to contribute to dotdrop
and where to find information. For any question, feel free to open an issue.

For PR adding new features, I'd be very thankful if you could add either
a unittest testing the added feature or a bash script test, thanks!

# Code base

Dotdrop's code base is located in the [dotdrop directory](/dotdrop).

Here's an overview of the different files and their role:

* **action.py**: represent the actions and transformations
* **comparator.py**: the class handling the comparison for `compare`
* **config.py**: the config file (*config.yaml*) parser
* **dotdrop.py**: the entry point and where the different cli commands are executed
* **dotfile.py**: represent a dotfile
* **installer.py**: the class handling the installation of dotfile for `install`
* **jhelpers.py**: list of methods available in templates with jinja2
* **linktypes.py**: enum for the three types of linking (none, symlink, children)
* **logger.py**: the custom logger
* **options.py**: the class embedding all the different options across dotdrop
* **templategen.py**: the jinja2 templating class
* **updater.py**: the class handling the update of dotfiles for `update`
* **utils.py**: some useful methods

# Testing

Dotdrop is tested with the use of the [tests.sh](/tests.sh) script.

* test for PEP8 compliance with `pycodestyle` and `pyflakes`
* run the unittest available in [tests directory](/tests)
* run the bash script tests in [tests-ng directory](tests-ng)

## How to implement unittest

**TODO**

## How to implement bash script tests

**TODO**

# Documentation

Most of dotdrop documentation is hosted in [its wiki](https://github.com/deadc0de6/dotdrop/wiki)
