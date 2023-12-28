Contents

* [Code base](#code-base)
* [Config parsing](#config-parsing)
  * [Lower layer](#lower-layer)
  * [Higher layer](#higher-layer)
  * [Precedence](#precedence)
  * [Variable resolution](#variable-resolution)
  * [Rules](#rules)
  * [Ignore pattern](#ignore-pattern)
* [Testing](#testing)
  * [Testing with unittest](#testing-with-unittest)
  * [Testing with bash scripts](#testing-with-bash-scripts)
* [Documentation](#documentation)

Thanks for helping out!

Feature requests, bug reports, and PRs are always welcome!

This file provides a few pointers on how to contribute to dotdrop
and where to find information. For any questions, feel free to open an issue.

For PRs adding new features, I'd be very thankful if you could add either
a unittest for the added feature or a bash script test (see [testing](#testing)), thanks!

# Code base

Dotdrop's code base is located in the [dotdrop directory](/dotdrop).

Here's an overview of the different files and their roles:

* **action.py**: represents the actions and transformations
* **cfg_yaml.py**: the lower level config parser (see [lower layer](#lower-layer))
* **cfg_aggregator.py**: the higher level config parser (see [higher layer](#higher-layer))
* **comparator.py**: the class handling the comparison for `compare`
* **dictparser.py**: abstract class for parsing dictionaries
* **dotdrop.py**: the entry point and where the different CLI commands are executed
* **dotfile.py**: represent a dotfile
* **installer.py**: the class handling the installation of dotfile for `install`
* **jhelpers.py**: list of methods available in templates with Jinja2
* **linktypes.py**: enum for the three types of linking (none, symlink, children)
* **logger.py**: the custom logger
* **options.py**: the class embedding all the different options across dotdrop
* **profile.py**: represents a profile
* **settings.py**: represents the config settings
* **templategen.py**: the Jinja2 templating class
* **updater.py**: the class handling the update of dotfiles for `update`
* **utils.py**: some useful methods used across the code base

# Config parsing

The configuration file (YAML) is parsed using two layers:

  * First in the lower layer in [cfg_yaml.py](/dotdrop/cfg_yaml.py)
  * Then in the higher layer in [cfg_aggregator.py](/dotdrop/cfg_aggregator.py)

Only the higher layer is accessible to other classes of dotdrop.

## Lower layer

This is done in [cfg_yaml.py](/dotdrop/cfg_yaml.py).

The lower layer part only takes care of basic types
and does the following:
  * Normalize all config entries
    * Resolve paths (dotfiles src, dotpath, etc)
    * Refactor actions/transformations to a common format
    * Etc.
  * Import any data from external files (configs, variables, etc)
  * Apply variable substitutions
  * Complete any data if needed (add the "profile" variable, etc)
  * Execute intrepreted variables through the shell
  * Write new entries (dotfile, profile) into the dictionary and save it to a file
  * Fix any deprecated entries (link_by_default, etc)
  * Clear empty entries

In the end, it builds a cleaned and normalized dictionary to be accessed by the higher layer.

## Higher layer

This is done in [cfg_aggregator.py](/dotdrop/cfg_aggregator.py).

The higher layer will transform the dictionary parsed by the lower layer
into objects (profiles, dotfiles, actions, transformations, etc).
The higher layer has no notion of inclusion (profile included, for example) or
file importing (import actions etc.) or even interpreted variables
(it only sees variables that have already been interpreted).

It does the following:
  * Transform dictionaries into objects
  * Patch lists of keys with their corresponding objects (For example, dotfile's actions)
  * Provide getters for every dotdrop class that needs to access elements

Note that any changes to the YAML dictionary (adding a new profile or a new dotfile for
example) won't be *seen* by the higher layer until the config is reloaded. Consider the
`dirty` flag as a sign the file needs to be written and its representation in higher
levels in not accurate anymore.

## Precedence

* `dynvariables` > `variables`
* Profile `(dyn)variables` > any other `(dyn)variables`
* Profile `(dyn)variables` > profile's included `(dyn)variables`
* Imported `variables`/`dynvariables` > `(dyn)variables`

## Variable resolution

How variables are resolved (through Jinja2's
templating) in the config file.

* Resolve main config file variables
  * Merge `variables` and `dynvariables` (allowing cyclic references)
  * Recursively template merged `variables` and `dynvariables`
  * `dynvariables` are executed
  * Profile's `variables` and `dynvariables` are merged
* Resolve *included* entries (see below)
  * Paths and entries are templated
    (allows using something like `include {{@@ os @@}}.variables.yaml`)
* *included* entries are processed
  * dyn-/variables are all resolved in their own file

Potential *included* entries:

* Entry *import_actions*
* Entry *import_configs*
* Entry *import_variables*
* Profile's *import*
* Profile's *include*

Variables are then used to resolve different elements in the config file:
see [this](docs/config/config-file.md#variables).

## Rules

* `dynvariables` are executed in their own config file
* Since `variables` and `dynvariables` are templated before the `dynvariables`
  are executed, this means that `dynvariables` can safely reference `variables`; however,
  `variables` referencing `dynvariables` will result in the *not-executed* value of the
  referenced `dynvariables` (see examples below).
* Profiles cannot include profiles defined above in the import tree
* Config files do not have access to variables defined above in the import tree
* Actions/transformations using variables are resolved at runtime
  (when the action/transformation is executed) and not when loading the config
* The same config file cannot be imported twice

This will result in `dvar0 = "test"` and `var0 = "echo test"` (**not** `var0 = test`):
```yaml
variables:
  var0: "{{@@ dvar0 @@}}"
dynvariables:
  dvar0: "echo test"
```

This will result in `dvar0 = "test"` and `var0 = "test"`:
```yaml
variables:
  var0: "test"
dynvariables:
  dvar0: "echo {{@@ var0 @@}}"
```

## Ignore pattern

Officially only `*/file` and `*/dir/*` should be used for ignore pattern.
However we still recursively process each path components to ensure
that pattern like `*/dir` are matched (see `_match_ignore_pattern`
in `utils.py`).

We also append a separator to directory before checking
for a match with the ignore patterns.

**compare**

* for files, match with ignore directly
* uses `filecmp.dircmp` to compare directories
* will then match each file that is different
  within the directory against the ignore patterns
  before printing
* patterns are matched against both files
  (in dotpath and in filesystem)

**import**

* for files, match with ignore directly
* uses `shutil.copytree` with a callback
  that will match each path against the ignore pattern
* the pattern (and negative pattern) will be matched
  against the path that is being imported
  (and not against its destination in the dotpath)

**install**

* recursively process each files and
  match against the ignore pattern
* patterns are matched against both files
  (in dotpath and in filesystem)

**update**

* for files, match with ignore directly
* uses `filecmp.dircmp` to compare directories
* will then match each file that is different
  within the directory against the ignore patterns
  before printing
* patterns are matched against both files
  (in dotpath and in filesystem)

# Testing

Dotdrop is tested with the use of the [tests.sh](/tests.sh) script.

* Test for PEP8 compliance with `pylint`, `pycodestyle` and `pyflakes` (see [check-syntax.sh](/scripts/test-syntax.sh))
* Test the documentation and links (see [check-doc.sh](/scripts/check-doc.sh))
* Run the unittests in [tests directory](/tests) with pytest (see [check-unittest.sh](/scripts/check-unittests.sh))
* Run the blackbox bash script tests in [tests-ng directory](/tests-ng) (see [check-tests-ng.sh](/scripts/check-tests-ng.sh))

## Testing with unittest

All unittests are available in [the tests directory](/tests)
and use [Python's unittest](https://docs.python.org/3/library/unittest.html).
Those are run with the help of [pytest](https://docs.pytest.org/).

The file [helpers.py](/tests/helpers.py) provides different helper methods
for the tests.

## Testing with bash scripts

The bash scripts are available in [tests-ng directory](/tests-ng).
These scripts test entire workflows by simulating the use of dotdrop with a blackbox approach
for different use-cases (usually described in their filename or in the file header).

Each script starts with the same boilerplate code that you can paste at the
start of your new test (see the head of the file down to `# this is the test`).

To run the tests on OSX, install following tools with homebrew
```bash
brew install coreutils gnu-sed
```

# Documentation

Dotdrop documentation is available under [https://dotdrop.readthedocs.io/](https://dotdrop.readthedocs.io/).
