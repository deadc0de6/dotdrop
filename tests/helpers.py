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

from ruamel.yaml import YAML as yaml

from dotdrop.options import Options
from dotdrop.linktypes import LinkTypes
from dotdrop.utils import strip_home

TMPSUFFIX = '-dotdrop-tests'


class SubsetTestCase(TestCase):
    """test case"""

    def assert_is_subset(self, sub, sup):
        """ensure it's a subset"""
        for sub_key, sub_val in sub.items():
            self.assertIn(sub_key, sup)
            subvalue = sup[sub_key]

            if isinstance(sub_val, str):
                self.assertEqual(sub_val, subvalue)
                continue

            if isinstance(sub_val, dict):
                self.assert_is_subset(sub_val, subvalue)
                continue

            try:
                iter(sub_val)
                self.assertTrue(all(
                    subItem in subvalue
                    for subItem in sub_val
                ))
            except TypeError:
                self.assertEqual(sub_val, subvalue)


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
    return f'tmp.{temp}{TMPSUFFIX}'


def get_tempdir():
    """Get a temporary directory"""
    tmpdir = tempfile.mkdtemp(suffix=TMPSUFFIX)
    os.chmod(tmpdir, 0o755)
    return tmpdir


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
            content = bytes(f'{pre}{get_string(100)}\n', 'ascii')
        else:
            pre = ''
            if template:
                pre = '{{@@ header() @@}}\n'
            content = f'{pre}{get_string(100)}\n'
    path = os.path.join(directory, fname)
    # pylint: disable=W1514
    with open(path, mode) as file:
        file.write(content)
    return path, content


def edit_content(path, newcontent, binary=False):
    """edit file content"""
    mode = 'w'
    if binary:
        mode = 'wb'
    # pylint: disable=W1514
    with open(path, mode) as file:
        file.write(newcontent)


def create_dir(path):
    """Create a directory"""
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def _fake_args():
    args = {}
    args['--verbose'] = True
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
    args['--force-actions'] = False
    args['--grepable'] = False
    args['--as'] = None
    args['--file-only'] = False
    args['--workers'] = 1
    args['--preserve-mode'] = False
    args['--ignore-missing'] = False
    args['--workdir-clear'] = False
    args['--transw'] = ''
    args['--transr'] = ''
    args['--remove-existing'] = False
    # cmds
    args['profiles'] = False
    args['files'] = False
    args['install'] = False
    args['uninstall'] = False
    args['compare'] = False
    args['import'] = False
    args['update'] = False
    args['detail'] = False
    args['remove'] = False
    return args


def load_options(confpath, profile):
    """Load the config file from path"""
    # create the fake args (bypass docopt)
    args = _fake_args()
    args['--cfg'] = confpath
    args['--profile'] = profile
    args['--verbose'] = True
    # and get the options
    opt = Options(args=args)
    opt.profile = profile
    opt.dry = False
    opt.safe = False
    opt.install_diff = True
    opt.import_link = LinkTypes.NOLINK
    opt.install_showdiff = True
    opt.debug = True
    opt.dotpath = os.path.join(os.path.dirname(confpath), 'dotfiles')
    return opt


def get_path_strip_version(path):
    """Return the path of a file as stored in yaml config"""
    path = strip_home(path)
    path = path.lstrip('.' + os.sep)
    return path


def get_dotfile_from_yaml(dic, path):
    """Return the dotfile from the yaml dictionary"""
    # path is not the file in dotpath but on the FS
    dotfiles = dic['dotfiles']
    # src = get_path_strip_version(path)
    home = os.path.expanduser('~')
    if path.startswith(home):
        path = path.replace(home, '~')
    dotfile = [d for d in dotfiles.values() if d['dst'] == path]
    if dotfile:
        return dotfile[0]
    return None


def yaml_dashed_list(items, indent=0):
    """yaml dashed list"""
    ind = ' ' * indent
    return ('\n'.join(f'{ind}- {item}' for item in items)
            + '\n')


def create_fake_config(directory, configname='config.yaml',
                       dotpath='dotfiles', backup=True, create=True,
                       import_configs=(), import_actions=(),
                       import_variables=()):
    """Create a fake config file"""
    path = os.path.join(directory, configname)
    workdir = os.path.join(directory, 'workdir')
    with open(path, 'w', encoding='utf-8') as file:
        file.write('config:\n')
        file.write(f'  backup: {backup}\n')
        file.write(f'  create: {create}\n')
        file.write(f'  dotpath: {dotpath}\n')
        file.write(f'  workdir: {workdir}\n')
        if import_actions:
            file.write('  import_actions:\n')
            file.write(yaml_dashed_list(import_actions, 4))
        if import_configs:
            file.write('  import_configs:\n')
            file.write(yaml_dashed_list(import_configs, 4))
        if import_variables:
            file.write('  import_variables:\n')
            file.write(yaml_dashed_list(import_variables, 4))
        file.write('dotfiles:\n')
        file.write('profiles:\n')
        file.write('actions:\n')
    return path


def create_yaml_keyval(pairs, parent_dir=None, top_key=None):
    """create key val for yaml"""
    if top_key:
        pairs = {top_key: pairs}
    if not parent_dir:
        parent_dir = get_tempdir()

    _, file_name = tempfile.mkstemp(dir=parent_dir, suffix='.yaml', text=True)
    yaml_dump(pairs, file_name)
    return file_name


# pylint: disable=W0102
def populate_fake_config(config, dotfiles={}, profiles={}, actions={},
                         trans_install={}, trans_update={}, variables={},
                         dynvariables={}):
    """Adds some juicy content to config files"""
    is_path = isinstance(config, str)
    if is_path:
        config_path = config
        config = yaml_load(config_path)

    config['dotfiles'] = dotfiles
    config['profiles'] = profiles
    config['actions'] = actions
    config['trans_install'] = trans_install
    config['trans_update'] = trans_update
    config['variables'] = variables
    config['dynvariables'] = dynvariables

    if is_path:
        yaml_dump(config, config_path)


def file_in_yaml(yaml_file, path, link=False):
    """Return whether path is in the given yaml file as a dotfile."""
    strip = get_path_strip_version(path)

    if isinstance(yaml_file, str):
        yaml_conf = yaml_load(yaml_file)
    else:
        yaml_conf = yaml_file

    dotfiles = yaml_conf['dotfiles'].values()

    in_src = any(x['src'].endswith(strip) for x in dotfiles)
    in_dst = path in (os.path.expanduser(x['dst']) for x in dotfiles)

    if link:
        dotfile = get_dotfile_from_yaml(yaml_conf, path)
        has_link = False
        if dotfile:
            has_link = 'link' in dotfile
        else:
            return False
        return in_src and in_dst and has_link
    return in_src and in_dst


def yaml_load(path):
    """load yaml"""
    with open(path, 'r', encoding='utf-8') as file:
        content = yaml(typ='safe').load(file)
    return content


def yaml_dump(content, path):
    """dump yaml"""
    with open(path, 'w', encoding='utf-8') as file:
        cont = yaml()
        cont.default_flow_style = False
        cont.indent = 2
        cont.typ = 'safe'
        cont.dump(content, file)
