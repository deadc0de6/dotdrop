#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2018, deadc0de6

change the `link` key in all dotfiles
to a specific value

usage example:
    ./change-link.py --true ../config.yaml --ignore f_vimrc --ignore f_xinitrc
"""

from docopt import docopt
import sys
import os
from ruamel.yaml import YAML as yaml

USAGE = """
change-link.py

Usage:
  change-link.py (--true | --false) [--ignore=<dotfile-name>...] <config.yaml>
  change-link.py --help

Options:
  -h --help               Show this screen.

"""

key = 'dotfiles'
entry = 'link'


def main():
    args = docopt(USAGE)
    path = os.path.expanduser(args['<config.yaml>'])
    if args['--true']:
        value = True
    if args['--false']:
        value = False

    ignores = args['--ignore']

    with open(path, 'r') as f:
        content = yaml(typ='safe').load(f)
    for k, v in content[key].items():
        if k in ignores:
            continue
        v[entry] = value

    ret = yaml.dump(content, default_flow_style=False, indent=2)
    print(ret)


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
