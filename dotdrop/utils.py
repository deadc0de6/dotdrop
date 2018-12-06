"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

utilities
"""

import subprocess
import tempfile
import os
import uuid
import shlex
from shutil import rmtree

# local import
from dotdrop.logger import Logger
from dotdrop.version import __version__ as VERSION

LOG = Logger()


def run(cmd, raw=True, debug=False, checkerr=False):
    """run a command (expects a list)"""
    if debug:
        LOG.dbg('exec: {}'.format(' '.join(cmd)))
    p = subprocess.Popen(cmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    ret = p.returncode
    out = p.stdout.readlines()
    lines = ''.join([x.decode('utf-8', 'replace') for x in out])
    if checkerr and ret != 0:
        c = ' '.join(cmd)
        errl = lines.rstrip()
        m = '\"{}\" returned non zero ({}): {}'.format(c, ret, errl)
        LOG.err(m)
    if raw:
        return ret == 0, out
    return ret == 0, lines


def shell(cmd):
    """run a command in the shell (expects a string)"""
    return subprocess.getoutput(cmd)


def diff(src, dst, raw=True, opts='', debug=False):
    """call unix diff to compare two files"""
    cmd = 'diff -r {} \"{}\" \"{}\"'.format(opts, src, dst)
    _, out = run(shlex.split(cmd), raw=raw, debug=debug)
    return out


def get_tmpdir():
    """create a temporary directory"""
    return tempfile.mkdtemp(prefix='dotdrop-')


def get_tmpfile():
    """create a temporary file"""
    (fd, path) = tempfile.mkstemp(prefix='dotdrop-')
    return path


def get_unique_tmp_name():
    """get a unique file name (not created)"""
    unique = str(uuid.uuid4())
    return os.path.join(tempfile.gettempdir(), unique)


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
    """return dotdrop header"""
    return 'This dotfile is managed using dotdrop'


def content_empty(string):
    """return True if is empty or only one CRLF"""
    if not string:
        return True
    if string == b'\n':
        return True
    return False
