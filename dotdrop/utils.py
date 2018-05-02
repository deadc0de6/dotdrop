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


def run(cmd, raw=True):
    ''' expects a list '''
    p = subprocess.Popen(cmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if raw:
        return p.stdout.readlines()
    lines = [x.decode('utf-8', 'replace') for x in p.stdout.readlines()]
    return ''.join(lines)


def diff(src, dst, raw=True, opts=''):
    ''' call diff to compare two files '''
    cmd = 'diff -r {} \"{}\" \"{}\"'.format(opts, src, dst)
    return run(shlex.split(cmd), raw=raw)


def get_tmpdir():
    return tempfile.mkdtemp(prefix='dotdrop-')


def get_tmpfile():
    (fd, path) = tempfile.mkstemp(prefix='dotdrop-')
    return path


def remove(path):
    ''' Remove a file / directory / symlink '''
    if not os.path.exists(path):
        raise OSError("File not found: {}".format(path))
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        rmtree(path)
    else:
        raise OSError("Unsupported file type for deletion: {}".format(path))
