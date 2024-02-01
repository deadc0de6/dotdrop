"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

utilities
"""

import subprocess
import tempfile
import os
import uuid
import fnmatch
import inspect
import importlib
import filecmp
import itertools
import shutil
import json
import sys
import requests
from packaging import version

# local import
from dotdrop.logger import Logger
from dotdrop.exceptions import UnmetDependency
from dotdrop.version import __version__ as VERSION

LOG = Logger()
STAR = '*'
# the environment variable for temporary
ENV_TEMP = 'DOTDROP_TMPDIR'
# the temporary directory
TMPDIR = None

# files dotdrop refuses to remove
DONOTDELETE = [
    os.path.expanduser('~'),
    os.path.expanduser('~/.config'),
]
NOREMOVE = [os.path.normpath(p) for p in DONOTDELETE]


def run(cmd, debug=False):
    """run a command (expects a list)"""
    if debug:
        fcmd = ' '.join(cmd)
        LOG.dbg(f'exec: {fcmd}', force=True)
    with subprocess.Popen(cmd, shell=False,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT) as proc:
        out, _ = proc.communicate()
        ret = proc.returncode
    out = out.splitlines(keepends=True)
    lines = ''.join([x.decode('utf-8', 'replace') for x in out])
    return ret == 0, lines


def write_to_tmpfile(content):
    """write some content to a tmp file"""
    path = get_tmpfile()
    with open(path, 'wb') as file:
        file.write(content)
    return path


def shellrun(cmd, debug=False):
    """
    run a command in the shell (expects a string)
    returns True|False, output
    """
    if debug:
        LOG.dbg(f'shell exec: \"{cmd}\"', force=True)
    ret, out = subprocess.getstatusoutput(cmd)
    if debug:
        LOG.dbg(f'shell result ({ret}): {out}', force=True)
    return ret == 0, out


def userinput(prompt, debug=False):
    """
    get user input
    return user input
    """
    if debug:
        LOG.dbg(f'get user input for \"{prompt}\"', force=True)
    pre = f'Please provide the value for \"{prompt}\": '
    res = input(pre)
    if debug:
        LOG.dbg(f'user input result: {res}', force=True)
    return res


def fastdiff(left, right):
    """fast compare files and returns True if different"""
    return not filecmp.cmp(left, right, shallow=False)


def diff(original, modified,
         diff_cmd='', debug=False):
    """compare two files, returns '' if same"""
    if not diff_cmd:
        diff_cmd = 'diff -r -u {0} {1}'

    replacements = {
        "{0}": original,
        "{original}": original,
        "{1}": modified,
        "{modified}": modified,
    }
    cmd = [replacements.get(x, x) for x in diff_cmd.split()]
    _, out = run(cmd, debug=debug)
    return out


def get_tmpdir():
    """create and return the temporary directory"""
# pylint: disable=W0603
    global TMPDIR
# pylint: enable=W0603
    if TMPDIR:
        return TMPDIR
    tmp = _get_tmpdir()
    TMPDIR = tmp
    return tmp


def _get_tmpdir():
    """create the tmpdir"""
    try:
        if ENV_TEMP in os.environ:
            tmp = os.environ[ENV_TEMP]
            tmp = os.path.expanduser(tmp)
            tmp = os.path.abspath(tmp)
            tmp = os.path.normpath(tmp)
            os.makedirs(tmp, exist_ok=True)
            return tmp
    except OSError:
        pass
    return tempfile.mkdtemp(prefix='dotdrop-')


def get_tmpfile():
    """create a temporary file"""
    tmpdir = get_tmpdir()
    return tempfile.NamedTemporaryFile(prefix='dotdrop-',
                                       dir=tmpdir, delete=False).name


def get_unique_tmp_name():
    """get a unique file name (not created)"""
    unique = str(uuid.uuid4())
    tmpdir = get_tmpdir()
    return os.path.join(tmpdir, unique)


def removepath(path, logger=None):
    """
    remove a file/directory/symlink
    if logger is defined, OSError are catched
    and printed to logger.warn instead of being forwarded
    as OSError
    """
    if not path:
        return
    if not os.path.lexists(path):
        err = f'File not found: {path}'
        if logger:
            logger.warn(err)
            return
        raise OSError(err)
    if os.path.normpath(os.path.expanduser(path)) in NOREMOVE:
        err = f'Dotdrop refuses to remove {path}'
        if logger:
            logger.warn(err)
            return
        LOG.err(err)
        raise OSError(err)
    if logger:
        logger.dbg(f'removing {path}')
    try:
        if os.path.islink(path) or os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            err = f'Unsupported file type for deletion: {path}'
            raise OSError(err)
    except Exception as exc:
        err = str(exc)
        if logger:
            logger.warn(err)
            return
        raise OSError(err) from exc


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


def _match_ignore_pattern(path, pattern, debug=False):
    """
    returns true if path matches the pattern
    we test the entire path but also
    any parent directory recursively to
    be able to match pattern like "*/dir"
    """
    subpath = path
    while subpath != os.path.sep:
        # if debug:
        #     msg = f'fnmatch \"{subpath}\" against {pattern}'
        #     LOG.dbg(msg, force=True)
        ret = fnmatch.fnmatch(subpath, pattern)
        if ret:
            if debug:
                LOG.dbg(f'ignore \"{pattern}\" match: {subpath} ({path})',
                        force=True)
            return ret
        subpath = os.path.dirname(subpath)
    # if debug:
    #     LOG.dbg(f'NOT ignore \"{pattern}\" match: {path}',
    #             force=True)
    return False


def _must_ignore(path, ignores, neg_ignores,
                 debug=False, strict=False):
    """
    return true if path matches any ignore patterns
    """
    # if debug:
    #     msg = f'path to check for ignore: {path}'
    #     LOG.dbg(msg, force=True)
    #     msg = f'ignore pattern: {ignores}'
    #     LOG.dbg(msg, force=True)
    #     msg = f'neg ignore pattern: {neg_ignores}'
    #     LOG.dbg(msg, force=True)
    match_ignore_pattern = []
    # test for ignore pattern
    for pattern in ignores:
        if _match_ignore_pattern(path, pattern, debug=debug):
            match_ignore_pattern.append(path)

    # remove negative match
    neg_ignore_cnt = 0
    for pattern in neg_ignores:
        # remove '!'
        pattern = pattern[1:]
        neg_ignore_cnt += 1
        if not _match_ignore_pattern(path, pattern, debug=debug):
            if debug:
                msg = f'NO MATCH negative ignore \"{pattern}\" against {path}'
                LOG.dbg(msg, force=True)
            continue

        if debug:
            msg = f'MATCH negative ignore \"{pattern}\" against {path}'
            LOG.dbg(msg, force=True)

        # remove from the list
        try:
            match_ignore_pattern.remove(path)
        except ValueError:
            warn = 'no files that are currently being '
            warn += f'ignored match \"{pattern}\". In order '
            warn += 'for a negative ignore pattern '
            warn += 'to work, it must match a file '
            warn += 'that is being ignored by a '
            warn += 'previous ignore pattern.'
            LOG.warn(warn)

    if len(match_ignore_pattern) < 1:
        # if debug:
        #     LOG.dbg(f'NOT ignoring \"{path}\"', force=True)
        return False
    if not strict and (
        os.path.isdir(path) or not os.path.exists(path)
    ) and neg_ignore_cnt > 0:
        # this ensures whoever calls this function will
        # descend into the directory to explore the possiblity
        # of a file matching the non-ignore pattern
        if debug:
            msg = '[!!] ignore would have match but neg ignores'
            msg += ' present and is a dir or does not exist: '
            msg += f'\"{path}\" -> not ignored!'
            LOG.dbg(msg, force=True)
        return False
    # if debug:
    #     LOG.dbg(f'effectively ignoring \"{path}\"', force=True)
    return True


def must_ignore(paths, ignores, debug=False,
                strict=False):
    """
    return true if any paths in list matches any ignore patterns
    """
    if not ignores:
        return False
    if debug:
        LOG.dbg(f'[IGN] IGNORE? \"{paths}\" against {ignores}',
                force=True)
    nign, ign = categorize(
        lambda ign: ign.startswith('!'), ignores)
    for path in paths:
        if _must_ignore(path, ign, nign,
                        debug=debug, strict=strict):
            if debug:
                LOG.dbg(f'[IGN] IGNORING \"{paths}\"', force=True)
            return True
    if debug:
        LOG.dbg(f'[IGN] NOT IGNORING \"{paths}\"', force=True)
    return False


def _cp(src, dst, ignore_func=None, debug=False):
    """
    the copy function for copytree
    returns the numb of files copied
    """
    if ignore_func and ignore_func(src):
        return 0
    if not os.path.isfile(src):
        # ignore special files
        if debug:
            LOG.dbg(f'ignore special file \"{src}\"',
                    force=True)
        return 0
    dstdir = os.path.dirname(dst)
    if debug:
        LOG.dbg(f'mkdir \"{dstdir}\"',
                force=True)
    os.makedirs(dstdir, exist_ok=True)
    if debug:
        LOG.dbg(f'cp {src} {dst}',
                force=True)
    path = shutil.copy2(src, dst)
    if os.path.exists(path):
        return 1
    return 0


def copyfile(src, dst, debug=False):
    """
    copy file from src to dst
    no dir expected!
    returns True if file was copied
    """
    return _cp(src, dst, debug=debug) == 1


def uniq_list(a_list):
    """unique elements of a list while preserving order"""
    new = []
    if not a_list:
        return new
    for elem in a_list:
        if elem not in new:
            new.append(elem)
    return new


def ignores_to_absolute(ignores, prefixes, debug=False):
    """allow relative ignore pattern"""
    new = []
    LOG.dbg(f'ignores before patching: {ignores}', force=debug)
    for ignore in ignores:
        negative = ignore.startswith('!')
        if negative:
            ignore = ignore[1:]

        if os.path.isabs(ignore):
            # is absolute
            if negative:
                new.append('!' + ignore)
            else:
                new.append(ignore)
            continue
        if STAR in ignore:
            if ignore.startswith(STAR) or ignore.startswith(os.sep):
                # is glob
                if negative:
                    new.append('!' + ignore)
                else:
                    new.append(ignore)
                continue
        # patch ignore
        for prefix in prefixes:
            path = os.path.join(prefix, ignore)
            if negative:
                new.append('!' + path)
            else:
                new.append(path)
    LOG.dbg(f'ignores after patching: {new}', force=debug)
    return new


def get_module_functions(mod):
    """return a list of fonction from a module"""
    funcs = []
    for memb in inspect.getmembers(mod):
        name, func = memb
        if not inspect.isfunction(func):
            continue
        funcs.append((name, func))
    return funcs


def get_module_from_path(path):
    """get module from path"""
    if not path or not os.path.exists(path):
        return None
    module_name = os.path.basename(path).rstrip('.py')
    # allow any type of files
    importlib.machinery.SOURCE_SUFFIXES.append('')
    # import module
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dependencies_met():
    """make sure all dependencies are met"""
    # check unix tools deps
    # diff command is checked in settings.py
    deps = ['file']

    for dep in deps:
        if not shutil.which(dep):
            err = f'The tool \"{dep}\" was not found in the PATH!'
            raise UnmetDependency(err)

    # check python deps
# pylint: disable=C0415

    # python-magic
    name = 'python-magic'
    err = f'missing python module \"{name}\"'
    try:
        import magic
        assert magic
        if not hasattr(magic, 'from_file'):
            LOG.warn(err)
    except ImportError:
        LOG.warn(err)

    # docopt
    name = 'docopt'
    err = f'missing python module \"{name}\"'
    try:
        from docopt import docopt
        assert docopt
    except ImportError as exc:
        raise UnmetDependency(err) from exc

    # jinja2
    name = 'jinja2'
    err = f'missing python module \"{name}\"'
    try:
        import jinja2
        assert jinja2
    except ImportError as exc:
        raise UnmetDependency(err) from exc

    # ruamel.yaml
    name = 'ruamel.yaml'
    err = f'missing python module \"{name}\"'
    try:
        from ruamel.yaml import YAML
        assert YAML
    except ImportError as exc:
        raise UnmetDependency(err) from exc

    # tomli
    if sys.version_info < (3, 11):
        name = 'tomli'
        err = f'missing python module \"{name}\"'
        try:
            import tomli
            assert tomli
        except ImportError as exc:
            raise UnmetDependency(err) from exc

    # tomli_w
    name = 'tomli_w'
    err = f'missing python module \"{name}\"'
    try:
        import tomli_w
        assert tomli_w
    except ImportError as exc:
        raise UnmetDependency(err) from exc

    # distro
    name = 'distro'
    err = f'missing python module \"{name}\"'
    try:
        import distro
        assert distro
    except ImportError as exc:
        raise UnmetDependency(err) from exc

# pylint: enable=C0415


def mirror_file_rights(src, dst):
    """mirror file rights of src to dst (can rise exc)"""
    if not os.path.exists(src) or not os.path.exists(dst):
        return
    rights = get_file_perm(src)
    os.chmod(dst, rights)


def get_umask():
    """return current umask value"""
    cur = os.umask(0)
    os.umask(cur)
    # return 0o777 - cur
    return cur


def get_default_file_perms(path, umask):
    """get default rights for a file"""
    base = 0o666
    if os.path.isdir(path):
        base = 0o777
    return base - umask


def get_file_perm(path):
    """return file permission"""
    if not os.path.exists(path):
        return 0o777
    return os.stat(path, follow_symlinks=True).st_mode & 0o777


def chmod(path, mode, debug=False):
    """change mode of file"""
    if debug:
        LOG.dbg(f'chmod {mode:o} {path}', force=True)
    os.chmod(path, mode)
    return get_file_perm(path) == mode


def adapt_workers(options, logger):
    """adapt number of workers if safe/dry"""
    if options.safe and options.workers > 1:
        logger.warn('workers set to 1 when --force is not used')
        options.workers = 1
    if options.dry and options.workers > 1:
        logger.warn('workers set to 1 when --dry is used')
        options.workers = 1


def categorize(function, iterable):
    """separate an iterable into elements for which
    function(element) is true for each element and
    for which function(element) is false for each
    element"""
    return (tuple(filter(function, iterable)),
            tuple(itertools.filterfalse(function, iterable)))


def debug_list(title, elems, debug):
    """pretty print list"""
    if not debug:
        return
    LOG.dbg(f'{title}:', force=debug)
    for elem in elems:
        LOG.dbg(f'\t- {elem}', force=debug)


def debug_dict(title, elems, debug):
    """pretty print dict"""
    if not debug:
        return
    LOG.dbg(f'{title}:', force=debug)
    for k, val in elems.items():
        if isinstance(val, list):
            LOG.dbg(f'\t- \"{k}\":', force=debug)
            for i in val:
                LOG.dbg(f'\t\t- {i}', force=debug)
        else:
            LOG.dbg(f'\t- \"{k}\": {val}', force=debug)


def check_version():
    """
    get dotdrop latest version on github
    compare with "version"
    and emit warning in case new version is available
    """
    url = 'https://api.github.com/repos/deadc0de6/dotdrop/releases/latest'
    try:
        req = requests.get(url, timeout=1)
    except requests.exceptions.RequestException:
        # request failed
        return
    if not req:
        # request failed
        return
    if req.status_code != 200:
        # request failed
        return
    # get json
    try:
        latest = req.json()['name']
    except json.decoder.JSONDecodeError:
        return
    except ValueError:
        return
    # compare
    if latest.startswith('v'):
        latest = latest[1:]
    if version.parse(VERSION) < version.parse(latest):
        msg = f'A new version of dotdrop is available ({latest})'
        LOG.warn(msg)


def pivot_path(path, newdir, striphome=False, logger=None):
    """change path to be under newdir"""
    if logger:
        logger.dbg(f'pivot new dir: \"{newdir}\"')
        logger.dbg(f'strip home: {striphome}')
    if striphome:
        path = strip_home(path)
    sub = path.lstrip(os.sep)
    new = os.path.join(newdir, sub)
    if logger:
        logger.dbg(f'pivot \"{path}\" to \"{new}\"')
    return new


def dir_empty(path):
    """return true if directory is empty"""
    if not os.path.exists(path) or not os.path.isdir(path):
        return True
    return len(os.listdir(path)) < 1


def is_bin_in_path(command):
    """
    check binary from command is in path
    """
    bpath = ""
    if not command:
        return False
    try:
        binary = command.split(" ")[0]
    except ValueError:
        return False
    if not binary:
        return False
    try:
        bpath = shutil.which(binary)
    except shutil.Error:
        return False
    if not bpath:
        return False
    return os.path.exists(bpath)
