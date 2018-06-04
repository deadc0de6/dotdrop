#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

transform all short dotfile keys
from the short format to the long
format

For example ~/.config/awesome/rc.lua
  short format: f_rc.lua
  long format:  f_config_awesome_rc.lua
"""

from docopt import docopt
import sys
import os
sys.path.append('../dotdrop')
try:
    from dotdrop.config import Cfg
except Exception as e:
    raise


USAGE = """
short-to-long-key.py

Usage:
  short-to-long-key.py <config.yaml>
  short-to-long-key.py --help

Options:
  -h --help               Show this screen.

"""


def main():
    args = docopt(USAGE)
    path = os.path.expanduser(args['<config.yaml>'])

    try:

        conf = Cfg(path)
    except ValueError as e:
        print('error: {}'.format(str(e)))
        return False

    conf.short_to_long()
    print(conf.dump())


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
