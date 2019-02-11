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

from dotdrop.options import Options
from dotdrop.linktypes import LinkTypes
from dotdrop.utils import strip_home

TMPSUFFIX = '.dotdrop'


def clean(path):
    """Delete file or directory"""
    if not os.path.exists(path):
        return
    if os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def get_string(length):
    """Get a random string of length 'length'"""
    alpha = string.ascii_uppercase + string.digits
    temp = ''.join(random.choice(alpha) for _ in range(length))
    return 'dotdrop-tests-{}'.format(temp)


def get_tempdir():
    """Get a temporary directory"""
    return tempfile.mkdtemp(prefix='dotdrop-tests-')


def create_random_file(directory, content=None,
                       binary=False, template=False):
    """Create a new file in directory with random content"""
    fname = get_string(8)
    mode = 'w'
    if binary:
        mode = 'wb'
    if content is None:
        if binary:
            pre = bytes()
            if template:
                pre = bytes('{{@@ header() @@}}\n', 'ascii')
            content = bytes('{}{}\n'.format(pre, get_string(100)), 'ascii')
        else:
            pre = ''
            if template:
                pre = '{{@@ header() @@}}\n'
            content = '{}{}\n'.format(pre, get_string(100))
    path = os.path.join(directory, fname)
    with open(path, mode) as f:
        f.write(content)
    return path, content


def edit_content(path, newcontent, binary=False):
    """edit file content"""
    mode = 'w'
    if binary:
        mode = 'wb'
    with open(path, mode) as f:
        f.write(newcontent)


def create_dir(path):
    """Create a directory"""
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def _fake_args():
    args = {}
    args['--verbose'] = False
    args['--no-banner'] = False
    args['--dry'] = False
    args['--force'] = False
    args['--nodiff'] = False
    args['--showdiff'] = True
    args['--inv-link'] = False
    args['--template'] = False
    args['--temp'] = False
    args['<key>'] = []
    args['--dopts'] = ''
    args['--file'] = []
    args['--ignore'] = []
    args['<path>'] = []
    args['--key'] = False
    args['--ignore'] = []
    args['--show-patch'] = False
    # cmds
    args['list'] = False
    args['listfiles'] = False
    args['install'] = False
    args['compare'] = False
    args['import'] = False
    args['update'] = False
    args['detail'] = False
    return args


def load_options(confpath, profile):
    """Load the config file from path"""
    # create the fake args (bypass docopt)
    args = _fake_args()
    args['--cfg'] = confpath
    args['--profile'] = profile
    # and get the options
    # TODO need to patch options
    o = Options(args=args)
    o.profile = profile
    o.dry = False
    o.profile = profile
    o.safe = True
    o.installdiff = True
    o.link = LinkTypes.NOLINK.value
    o.showdiff = True
    o.debug = True
    o.dopts = ''
    o.variables = {}
    return o


def get_path_strip_version(path):
    """Return the path of a file as stored in yaml config"""
    path = strip_home(path)
    path = path.lstrip('.' + os.sep)
    return path


def get_dotfile_from_yaml(dic, path):
    """Return the dotfile from the yaml dictionary"""
    # path is not the file in dotpath but on the FS
    dotfiles = dic['dotfiles']
    src = get_path_strip_version(path)
    return [d for d in dotfiles.values() if d['src'] == src][0]


def create_fake_config(directory, configname='config.yaml',
                       dotpath='dotfiles', backup=True, create=True):
    """Create a fake config file"""
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
