#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2018, deadc0de6

change the `link` key in all dotfiles
to a specific value

usage example:
    ./change-link.py --true ../config.yaml --ignore f_vimrc --ignore f_xinitrc
"""

import os
import io
from docopt import docopt
from ruamel.yaml import YAML as yaml

USAGE = """
change-link.py

Usage:
  change-link.py --value=<value> [--ignore=<dotfile-name>...] <config.yaml>
  change-link.py --help

Options:
  -h --help               Show this screen.

"""

KEY = 'dotfiles'
ENTRY = 'link'


def change_link(path, value, ignores):
    """change link value"""
    with open(path, 'r', encoding='utf-8') as file:
        content = yaml(typ='safe').load(file)
    for k, val in content[KEY].items():
        if k in ignores:
            continue
        val[ENTRY] = value

    output = io.StringIO()
    data = yaml()
    data.default_flow_style = False
    data.indent = 2
    data.typ = 'rt'
    data.dump(content, output)
    print(output)


def main():
    """entry point"""
    args = docopt(USAGE)
    path = os.path.expanduser(args['<config.yaml>'])
    value = args['--value']
    ignores = args['--ignore']
    change_link(path, value, ignores)


if __name__ == '__main__':
    main()
