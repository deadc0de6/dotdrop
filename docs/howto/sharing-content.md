# Share content across dotfiles

There are cases in which two or more dotfiles are very similar. For example,
two files exporting environment variables for two projects built with the same
technology (eg. two node.js web servers deployed on AWS). In these cases it's
nice to share as much code as possible across the dotfiles by leveraging
templating and merging them into the same dotfile in dotdrop's `dotpath`. Here
are a few suggestions about how to achieve this:

* [Brute force templating](#brute-force-templating)
* [Profile variables](#profile-variables)
* [Jinja macros](#jinja-macros)

## Brute force templating

The first approach is sheer use of templating and variables.
In order to do this, we need to:

1. Create the merged dotfile with an arbitrary name somewhere in `dotpath`.
2. Create two `dotfile` entries in `config.yaml`, both having the merged
  dotfile as `src`, but their own `dst`.

Here we have an example:

The merged dotfile in `dotpath` (`dotpath/projects/env`):
```bash
# .env

{%@@ if _dotfile_key == 'server0-env' @@%}
    {%@@set aws_db_host = 'super-duper.host' @@%}
    {%@@set aws_db_port = 4521 @@%}
{%@@ elif _dotfile_key == 'server1-env' @@%}
    {%@@set aws_db_host = 'cheaper.host' @@%}
    {%@@set aws_db_host = 9632 @@%}
{%@@ endif @@%}

export DB_HOST='{{@@ aws_db_host @@}}'
export DB_PORT='{{@@ aws_db_port @@}}'
```

Part of dotdrop `config.yaml` file:
```yaml
# config.yaml

dotfiles:
  server0-env:
    src: projects/env
    dst: ~/projects/server0/.env
  server1-env:
    src: projects/env
    dst: ~/projects/server1/.env
```

Installing the dotfile `server0-env` will create an environment file in
`~/projects/server0/.env` with the following content:

```bash
# .env

export DB_HOST='super-duper.host'
export DB_PORT='4521'
```

## Profile variables

The previous method, albeit flexible, is a bit cumbersome for some use cases.
For example, when the dotfiles belong to different profiles, the cleanest
solution consists of using
[profile variables](../config/config-profiles.md#profile-variables-entry). This is achieved by:

1. Creating the merged dotfile with an arbitrary name somewhere in `dotpath`.
2. Adding some variables in the merged dotfile via templating.
3. Overriding them with different values in each profile via profile variables.
4. Typically, making the dotfile `dst` dynamic, as different profiles need
    usually to deploy the dotfiles in different locations.

**NOTE**: This technique does *not* require two different `dotfiles` entry in
`config.yaml`.

An example:

The merged dotfile (`dotpath/projects/env`):
```bash
# .env

export DB_HOST='{{@@ aws_db_host @@}}'
export DB_PORT='{{@@ aws_db_port @@}}'
```

Part of dotdrop `config.yaml` file:
```yaml
# config.yaml

dotfiles:
  env:
    src: projects/env
    dst: '{{@@ server_path @@}}/.env'

profiles:
  server0:
    dotfiles:
    - env
  variables:
    aws_db_host: super-duper.host
    aws_db_port: 4521
    server_path: ~/projects/server0

  server1:
    dotfiles:
    - env
  variables:
    aws_db_host: cheaper.host
    aws_db_port: 9632
    server_path: ~/projects/server1
```

With this setup, installing the `server1` profile will create an environment
file in `~/projects/server1/.env` with the following content:

```bash
# .env

export DB_HOST='cheaper.host'
export DB_PORT='9632'
```

## Jinja macros

Even though it has cleaner dotfiles, the profile-variable-based procedure can't
be used in two scenarios: when the dotfiles belong to the same profile, and
when variable values require some complex computations. In both cases, the brute
force templating approach can be used, but in the latter one it also makes the
dotfiles bloated with "bookkeeping" logic, thus hard to read.

A solution for this relies in leveraging Jinja macros. This method is a
variation of the brute force templating one where the merged dotfile is
included from many different dotfiles in `dotpath` via Jinja macros rather
than via many `dotfile` entries with the same `src` attribute. This way, the
merged original dotfiles stays clean as in the profile variables solution
because computations are in other files.

The steps to achieve this are:

1. Creating the merged dotfile with an arbitrary name somewhere in `dotpath`.
2. Wrapping the whole content of the merged dotfile in a Jinja macro with the
    necessary parameters.
3. Calling the macro in each original dotfile, computing the parameters there.

**NOTE**: The merged dotfile will be empty, as it only contains a Jinja macro.
    If it needs to not be deployed, the `ignoreempty` entry can be set to
    `true` in `config.yaml`.

As usual, an example:

The merged dotfile in `dotpath` (`dotpath/projects/env`):
```bash
{%@@ macro env(db_host, db_port) @@%}
# .env

export DB_HOST='{{@@ db_host @@}}'
export DB_PORT='{{@@ db_port @@}}'
{%@@ endmacro @@%}
```

Server0's environment file (`projects/server0/.env`):
```jinja2
{%@@ from projects/env import env @@%}

{%@@ set keyPieces = _dotfile_key.split('-') @@%}
{%@@ if keyPieces[-1] == 'dbg' @@%}
    {%@@ set isLocal = keyPieces[-2] == 'local' @@%}
    {%@@ set remote_host = 'super-duper-dbg.host'
        if not isLocal
        else 'localhost' @@%}
    {%@@set aws_db_port = 3333 @@%}

{%@@ elif keyPieces[-1] == 'dev' @@%}
    {%@@set aws_db_host = 'localhost' @@%}
    {%@@set aws_db_host = 4521 @@%}
{%@@ endif @@%}

{{@@ env(db_host, db_port) @@}}
```

Server1's environment file (`projects/server1/.env`):
```jinja2
{%@@ from projects/env import env @@%}

{{@@ env('average-host.com', 9632) @@}}
```

Part of dotdrop `config.yaml` file:
```yaml
# config.yaml

dotfiles:
  server0-env-remote-dbg:
    src: projects/server0/.env
    dst: ~/projects/server0/.env.remote.dbg
  server0-env-local-dbg:
    src: projects/server0/.env
    dst: ~/projects/server0/.env.local.dbg
  server1-env:
    src: projects/server1/.env
    dst: ~/projects/server1/.env
```

With this configuration, installing the dotfile `server0-env-local-dbg` will
create an environment file in `~/projects/server0/.env.local.dbg` with the
following content:

```bash
# .env

export DB_HOST='localhost'
export DB_PORT='3333'
```
