"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
utilities
"""

import subprocess
import tempfile
import os
from shutil import rmtree

# local import
from dotdrop.logger import Logger


LOG = Logger()


def run(cmd, log=False, raw=True):
    """ expects a list """
    if log:
        LOG.log('cmd: \"%s\"' % (' '.join(cmd)))
    p = subprocess.Popen(cmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if raw:
        return p.stdout.readlines()
    lines = [x.decode('utf-8', 'replace') for x in p.stdout.readlines()]
    return ''.join(lines)


def diff(src, dst, log=False, raw=True):
    return run(['diff', '-r', src, dst], log=log, raw=raw)


def get_tmpdir():
    return tempfile.mkdtemp(prefix='dotdrop-')


def remove(path):
    ''' Remove a file / directory / symlink '''
    if not os.path.exists(path):
        raise OSError("File not found: %s" % path)
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        rmtree(path)
    else:
        raise OSError("Unsupported file type for deletion: %s" % path)
