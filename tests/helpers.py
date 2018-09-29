"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
helpers for the unittests
"""

import os
import shutil
import string
import random
import tempfile

from dotdrop.config import Cfg

TMPSUFFIX = '.dotdrop'


def clean(path):
    '''Delete file or directory.'''
    if not os.path.exists(path):
        return
    if os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def get_string(length):
    '''Get a random string of length "length".'''
    alpha = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alpha) for _ in range(length))


def get_tempdir():
    '''Get a temporary directory'''
    return tempfile.mkdtemp(suffix=TMPSUFFIX)


def create_random_file(directory, content=None, binary=False):
    '''Create a new file in directory with random content.'''
    fname = get_string(8)
    mode = 'w'
    if binary:
        mode = 'wb'
    if content is None:
        if binary:
            content = bytes(get_string(100), 'ascii')
        else:
            content = get_string(100)
    path = os.path.join(directory, fname)
    with open(path, mode) as f:
        f.write(content)
    return path, content


def edit_content(path, newcontent, binary=False):
    '''edit file content'''
    mode = 'w'
    if binary:
        mode = 'wb'
    with open(path, mode) as f:
        f.write(newcontent)


def create_dir(path):
    '''Create a directory'''
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def load_config(confpath, profile):
    '''Load the config file from path'''
    conf = Cfg(confpath)
    opts = conf.get_settings()
    opts['dry'] = False
    opts['profile'] = profile
    opts['safe'] = True
    opts['installdiff'] = True
    opts['link'] = False
    opts['showdiff'] = True
    opts['debug'] = True
    opts['dopts'] = ''
    opts['variables'] = {}
    return conf, opts


def get_path_strip_version(path):
    '''Return the path of a file as stored in yaml config'''
    strip = path
    home = os.path.expanduser('~')
    if strip.startswith(home):
        strip = strip[len(home):]
    return strip.lstrip('.' + os.sep)


def get_dotfile_from_yaml(dic, path):
    '''Return the dotfile from the yaml dictionary'''
    # path is not the file in dotpath but on the FS
    dotfiles = dic['dotfiles']
    src = get_path_strip_version(path)
    return [d for d in dotfiles.values() if d['src'] == src][0]


def create_fake_config(directory, configname='config.yaml',
                       dotpath='dotfiles', backup=True, create=True):
    '''Create a fake config file'''
    path = os.path.join(directory, configname)
    workdir = os.path.join(directory, 'workdir')
    with open(path, 'w') as f:
        f.write('config:\n')
        f.write('  backup: {}\n'.format(str(backup)))
        f.write('  create: {}\n'.format(str(create)))
        f.write('  dotpath: {}\n'.format(dotpath))
        f.write('  workdir: {}\n'.format(workdir))
        f.write('dotfiles:\n')
        f.write('profiles:\n')
        f.write('actions:\n')
    return path
