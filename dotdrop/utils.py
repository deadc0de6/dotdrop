"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

utilities
"""

import fnmatch
import os
import shlex
import subprocess
import tempfile
import uuid
from functools import partial, wraps
from glob import iglob
from platform import python_version
from shutil import rmtree

import yaml

# local import
from .logger import Logger

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


def with_yaml_parser(funct):
    @wraps(funct)
    def wrapper(first, yaml_dict, file_name=None, *args, **kwargs):
        if file_name is None:
            file_name = yaml_dict
            with open(file_name, 'r') as yaml_file:
                yaml_dict = yaml.safe_load(yaml_file)

        return funct(first, yaml_dict, file_name, *args, **kwargs)

    return wrapper


glob_msg_start = ('Recursive globbing is not available on Python {}: '
                  .format(python_version()))
try:
    iglob('.', recursive=True)
    glob = partial(iglob, recursive=True)
except TypeError:
    LOG.warn(glob_msg_start +
             'upgrade to version >3.5 if you want to use this feature.')

    def glob(glob_path):
        if '**' in glob_path:
            LOG.err('{}: "{}" will match nothing'
                    .format(glob_msg_start, glob_path), throw=ValueError)

        return iglob(glob_path)
