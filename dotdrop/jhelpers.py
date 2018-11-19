"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2018, deadc0de6

jinja2 helper methods
"""

import os


def exists(path):
    '''return true when path exists'''
    return os.path.exists(path)
