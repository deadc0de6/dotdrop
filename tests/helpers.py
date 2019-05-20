"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
helpers for the unittests
"""

import os
import random
import shutil
import string
import tempfile
from unittest import TestCase

import yaml

from dotdrop.options import Options, ENV_NODEBUG
from dotdrop.linktypes import LinkTypes
from dotdrop.utils import strip_home

TMPSUFFIX = '-dotdrop-tests'


class SubsetTestCase(TestCase):
    def assertIsSubset(self, sub, sup):
        for subKey, subValue in sub.items():
            self.assertIn(subKey, sup)
            supValue = sup[subKey]

            if isinstance(subValue, str):
                self.assertEqual(subValue, supValue)
                continue

            if isinstance(subValue, dict):
                self.assertIsSubset(subValue, supValue)
                continue

            try:
                iter(subValue)
                self.assertTrue(all(
                    subItem in supValue
                    for subItem in subValue
                ))
            except TypeError:
                self.assertEqual(subValue, supValue)


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
    return 'tmp.{}{}'.format(temp, TMPSUFFIX)


def get_tempdir():
    """Get a temporary directory"""
    return tempfile.mkdtemp(suffix=TMPSUFFIX)


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
    args['--link'] = 'nolink'
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
    o = Options(args=args)
    o.profile = profile
    o.dry = False
    o.safe = True
    o.install_diff = True
    o.import_link = LinkTypes.NOLINK
    o.install_showdiff = True
    o.debug = True
    if ENV_NODEBUG in os.environ:
        o.debug = False
    o.compare_dopts = ''
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


def yaml_dashed_list(items, indent=0):
    return ('\n'.join('{}- {}'.format(' ' * indent, item) for item in items)
            + '\n')


def create_fake_config(directory, configname='config.yaml',
                       dotpath='dotfiles', backup=True, create=True,
                       import_configs=(), import_actions=(),
                       import_variables=()):
    """Create a fake config file"""
    path = os.path.join(directory, configname)
    workdir = os.path.join(directory, 'workdir')
    with open(path, 'w') as f:
        f.write('config:\n')
        f.write('  backup: {}\n'.format(str(backup)))
        f.write('  create: {}\n'.format(str(create)))
        f.write('  dotpath: {}\n'.format(dotpath))
        f.write('  workdir: {}\n'.format(workdir))
        if import_actions:
            f.write('  import_actions:\n')
            f.write(yaml_dashed_list(import_actions, 4))
        if import_configs:
            f.write('  import_configs:\n')
            f.write(yaml_dashed_list(import_configs, 4))
        if import_variables:
            f.write('  import_variables:\n')
            f.write(yaml_dashed_list(import_variables, 4))
        f.write('dotfiles:\n')
        f.write('profiles:\n')
        f.write('actions:\n')
    return path


def create_yaml_keyval(pairs, parent_dir=None, top_key=None):
    if top_key:
        pairs = {top_key: pairs}
    if not parent_dir:
        parent_dir = get_tempdir()

    fd, file_name = tempfile.mkstemp(dir=parent_dir, suffix='.yaml', text=True)
    with os.fdopen(fd, 'w') as f:
        yaml.safe_dump(pairs, f)
    return file_name


def populate_fake_config(config, dotfiles={}, profiles={}, actions={},
                         trans={}, trans_write={}, variables={},
                         dynvariables={}):
    """Add some juicy content to config files"""
    is_path = isinstance(config, str)
    if is_path:
        config_path = config
        with open(config_path) as config_file:
            config = yaml.safe_load(config_file)

    config['dotfiles'] = dotfiles
    config['profiles'] = profiles
    config['actions'] = actions
    config['trans'] = trans
    config['trans_write'] = trans_write
    config['variables'] = variables
    config['dynvariables'] = dynvariables

    if is_path:
        with open(config_path, 'w') as config_file:
            yaml.safe_dump(config, config_file, default_flow_style=False,
                           indent=2)


def file_in_yaml(yaml_file, path, link=False):
    """Return whether path is in the given yaml file as a dotfile."""
    strip = get_path_strip_version(path)

    if isinstance(yaml_file, str):
        with open(yaml_file) as f:
            yaml_conf = yaml.safe_load(f)
    else:
        yaml_conf = yaml_file

    dotfiles = yaml_conf['dotfiles'].values()

    in_src = strip in (x['src'] for x in dotfiles)
    in_dst = path in (os.path.expanduser(x['dst']) for x in dotfiles)

    if link:
        has_link = get_dotfile_from_yaml(yaml_conf, path)['link']
        return in_src and in_dst and has_link
    return in_src and in_dst
