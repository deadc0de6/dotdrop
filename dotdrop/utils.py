"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
utilities
"""

import subprocess
import tempfile
import os
import os.path
import shlex
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


def diff(src, dst, log=False, raw=True, opts=''):
    cmd = 'diff -r %s \"%s\" \"%s\"' % (opts, src, dst)
    return run(shlex.split(cmd), log=log, raw=raw)


def get_tmpdir():
    return tempfile.mkdtemp(prefix='dotdrop-')


def get_tmpfile():
    (fd, path) = tempfile.mkstemp(prefix='dotdrop-')
    return path


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

        
def relative_path_from_base(base, path):
    ''' Return `path' relative to `base'.
    
    >>> relative_path_from_base('base/dir', 'base/dir/some/file')
    'some/file'
    '''
    head, tail = path, ''
    while head != base:
        head, new_tail = os.path.split(head)
        tail = os.path.join(new_tail, tail) if tail else new_tail
        if not head:
            raise ValueError('Path "%s" not under "%s"' % (path, base))
    return tail
