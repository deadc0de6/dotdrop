"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

utilities
"""

import subprocess
import tempfile
import os
import shlex
from shutil import rmtree

# local import
from dotdrop.logger import Logger
from dotdrop.version import __version__ as VERSION

LOG = Logger()


def run(cmd, raw=True, debug=False):
    """run a command in the shell (expects a list)"""
    if debug:
        LOG.dbg('exec: {}'.format(' '.join(cmd)))
    p = subprocess.Popen(cmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if raw:
        return p.stdout.readlines()
    lines = [x.decode('utf-8', 'replace') for x in p.stdout.readlines()]
    return ''.join(lines)


def diff(src, dst, raw=True, opts='', debug=False):
    """call unix diff to compare two files"""
    cmd = 'diff -r {} \"{}\" \"{}\"'.format(opts, src, dst)
    return run(shlex.split(cmd), raw=raw, debug=debug)


def get_tmpdir():
    """create a temporary directory"""
    return tempfile.mkdtemp(prefix='dotdrop-')


def get_tmpfile():
    """create a temporary file"""
    (fd, path) = tempfile.mkstemp(prefix='dotdrop-')
    return path


def remove(path):
    """remove a file/directory/symlink"""
    if not os.path.lexists(path):
        raise OSError("File not found: {}".format(path))
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        rmtree(path)
    else:
        raise OSError("Unsupported file type for deletion: {}".format(path))


def samefile(path1, path2):
    """return True if represent the same file"""
    if not os.path.exists(path1):
        return False
    if not os.path.exists(path2):
        return False
    return os.path.samefile(path1, path2)


def header():
    return 'This dotfile is managed using dotdrop'
