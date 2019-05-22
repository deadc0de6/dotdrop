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
from abc import ABC, abstractclassmethod
from functools import partial, wraps
from glob import iglob
from platform import python_version
from shutil import rmtree

import yaml

# local import
from dotdrop.logger import Logger

#######################################
# Variables
#######################################

LOG = Logger()


#######################################
# Functions
#######################################


def clear_none(dic):
    """Recursively delete all None values in a dictionary."""
    if not dic:
        return {}
    return {
        key: clear_none(value) if isinstance(value, dict) else value
        for key, value in dic.items()
        if value is not None
    }


def content_empty(string):
    """return True if is empty or only one CRLF"""
    if not string:
        return True
    if string == b'\n':
        return True
    return False


def destructure_keyval(func):
    """
    Decorator. Make a method taking key and value able to take them paired in
    the key.

    :param func: The method being decorated.
    :type func: (first :any, key :any, value :any, *args, **kwargs) -> any
    :return func: The same method, but it can now split key if value is not
        given.
    :type return: (first :any, key :any, value=None :any, *args, **kwargs)
        -> any
    """
    @wraps(func)
    def wrapper(first, key, value=None, *args, **kwargs):
        if value is None:
            key, value = key
        return func(first, key, value, *args, **kwargs)

    return wrapper


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
    fd, path = tempfile.mkstemp(prefix='dotdrop-')
    return path


def get_unique_tmp_name():
    """get a unique file name (not created)"""
    unique = str(uuid.uuid4())
    return os.path.join(tempfile.gettempdir(), unique)

#######################################
# Glob fallback for Python <3.5
#######################################


glob_msg_start = ('Recursive globbing is not available on Python {}: '
                  .format(python_version()))
try:
    iglob('.', recursive=True)

    # recursive keyword arg supported. Partially applying it to True
    glob = partial(iglob, recursive=True)
except TypeError:
    LOG.warn(glob_msg_start +
             'upgrade to version >3.5 if you want to use this feature.')

    def glob(glob_path):
        """Match a glob. Fail if recursive globbing (**) is used."""
        if '**' in glob_path:
            LOG.err('{}: "{}" will match nothing'
                    .format(glob_msg_start, glob_path), throw=ValueError)

        return iglob(glob_path)


def header():
    """return dotdrop header"""
    return 'This dotfile is managed using dotdrop'


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


def samefile(path1, path2):
    """return True if represent the same file"""
    if not os.path.exists(path1):
        return False
    if not os.path.exists(path2):
        return False
    return os.path.samefile(path1, path2)


def shell(cmd):
    """run a command in the shell (expects a string)"""
    return subprocess.getoutput(cmd)


def strip_home(path):
    """properly strip $HOME from path"""
    home = os.path.expanduser('~') + os.sep
    if path.startswith(home):
        path = path[len(home):]
    return path


def with_yaml_parser(funct):
    """
    Decorator. Add YAML parsing of a file, but only when no already-parsed
    dictionary is passed.

    :param func: The method being decorated.
    :type func: (first :any, yaml_dict :dict, file_name :str, *args, **kwargs)
        -> any
    :return func: The same method, but it can now parse a YAML file if the
        parsed dict is not passed.
    :type return: (first :any, yaml_dict :(dict|str), file_name=None :str,
        *args, **kwargs) -> any
    """
    @wraps(funct)
    def wrapper(first, yaml_dict, file_name=None, *args, **kwargs):
        if file_name is None:
            file_name = yaml_dict
            with open(file_name, 'r') as yaml_file:
                yaml_dict = yaml.safe_load(yaml_file)

        return funct(first, yaml_dict, file_name, *args, **kwargs)

    return wrapper


def write_to_tmpfile(content):
    """write some content to a tmp file"""
    path = get_tmpfile()
    with open(path, 'wb') as f:
        f.write(content)
    return path


#######################################
# Classes
#######################################


class DictParser(ABC):
    @property
    @abstractclassmethod
    def key_yaml(self):
        pass

    @classmethod
    def _adjust_yaml_keys(cls, yaml_dict):
        return yaml_dict

    @classmethod
    @destructure_keyval
    def parse(cls, key, value):
        value = cls._adjust_yaml_keys(value.copy())
        return cls(key=key, **value)

    @classmethod
    @with_yaml_parser
    def parse_dict(cls, yaml_dict, file_name=None):
        try:
            items = yaml_dict[cls.key_yaml]
        except KeyError:
            cls.log.err('malformed file {}: missing key "{}"'
                        .format(file_name, cls.key_yaml), throw=ValueError)

        return list(map(cls.parse, items.items()))
