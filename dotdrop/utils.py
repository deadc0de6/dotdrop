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
import fnmatch
from shutil import rmtree

# local import
from dotdrop.logger import Logger

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


def write_to_tmpfile(content):
    """write some content to a tmp file"""
    path = get_tmpfile()
    with open(path, 'wb') as f:
        f.write(content)
    return path


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


def strip_home(path):
    """properly strip $HOME from path"""
    home = os.path.expanduser('~') + os.sep
    if path.startswith(home):
        path = path[len(home):]
    return path


def must_ignore(paths, ignores, debug=False):
    """return true if any paths in list matches any ignore patterns"""
    if not ignores:
        return False
    for p in paths:
        for i in ignores:
            if fnmatch.fnmatch(p, i):
                if debug:
                    LOG.dbg('ignore \"{}\" match: {}'.format(i, p))
                return True
    return False


def is_dict(obj):
    return isinstance(obj, dict)


def is_not_magic(name):
    return (name[0:2], name[-2:]) != ('__', '__')
