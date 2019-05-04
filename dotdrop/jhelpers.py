"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2018, deadc0de6

jinja2 helper methods
"""

import os
import shutil


def exists(path):
    """return true when path exists"""
    return os.path.exists(os.path.expandvars(path))


def exists_in_path(name, path=None):
    """return true when executable exists in os path"""
    return shutil.which(name, os.F_OK | os.X_OK, path) is not None


def basename(path):
    """return basename"""
    return os.path.basename(path)


def dirname(path):
    """return dirname"""
    return os.path.dirname(path)
