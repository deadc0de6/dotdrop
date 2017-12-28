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
    '''Delete file or folder.'''
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


def get_tempfolder():
    '''Get a temporary folder'''
    return tempfile.mkdtemp(suffix=TMPSUFFIX)


def create_random_file(folder, content=None, binary=False):
    '''Create a new file in folder with random content.'''
    fname = get_string(8)
    mode = 'w'
    if binary:
        mode = 'wb'
    if content is None:
        if binary:
            content = bytes(get_string(100), 'ascii')
        else:
            content = get_string(100)
    path = os.path.join(folder, fname)
    with open(path, mode) as f:
        f.write(content)
    return path, content


def create_dir(path):
    '''Create a folder'''
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def load_config(confpath, profile):
    '''Load the config file from path'''
    conf = Cfg(confpath)
    opts = conf.get_configs()
    opts['dry'] = False
    opts['profile'] = profile
    opts['safe'] = True
    opts['installdiff'] = True
    opts['link'] = False
    opts['quiet'] = True
    opts['dopts'] = ''
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


def create_fake_config(folder, configname='config.yaml',
                       dotpath='dotfiles', backup=True, create=True):
    '''Create a fake config file'''
    path = os.path.join(folder, configname)
    with open(path, 'w') as f:
        f.write('config:\n')
        f.write('  backup: %s\n' % (str(backup)))
        f.write('  create: %s\n' % (str(create)))
        f.write('  dotpath: %s\n' % (dotpath))
        f.write('dotfiles:\n')
        f.write('profiles:\n')
        f.write('actions:\n')
    return path
