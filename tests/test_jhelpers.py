"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6
basic unittest for jhelpers
"""

import os
import unittest
from tests.helpers import (clean,
                           create_random_file, get_string, get_tempdir,
                           load_options)
from dotdrop.cfg_aggregator import CfgAggregator
from dotdrop.dotfile import Dotfile
from dotdrop.dotdrop import cmd_install


def fake_config(path, dotfile, profile, dotpath):
    """Create a fake config file"""
    with open(path, 'w', encoding='utf-8') as file:
        file.write('config:\n')
        file.write('  backup: true\n')
        file.write('  create: true\n')
        file.write(f'  dotpath: {dotpath}\n')
        file.write('dotfiles:\n')
        file.write(f'  {dotfile.key}:\n')
        file.write(f'    dst: {dotfile.dst}\n')
        file.write(f'    src: {dotfile.src}\n')
        file.write('profiles:\n')
        file.write(f'  {profile}:\n')
        file.write('    dotfiles:\n')
        file.write(f'    - {dotfile.key}\n')
    return path


class TestJhelpers(unittest.TestCase):
    """test case"""

    CONFIG_NAME = 'config.yaml'

    TEMPLATE = '''
{%@@ if exists('/dev/null') @@%}
it does not exist
{%@@ endif @@%}

{%@@ if exists('/tmp') @@%}
it does exist
{%@@ endif @@%}

{%@@ if exists_in_path('ls') @@%}
ls exists
{%@@ endif @@%}

{%@@ if not exists_in_path('itdoesnotexist') @@%}
itdoesnotexist does not exist
{%@@ endif @@%}

{%@@ set the_basename = basename('/tmp/a/b/c') @@%}
basename: {{@@ the_basename @@}}

{%@@ set the_dirname = dirname('/tmp/a/b/c') @@%}
dirname: {{@@ the_dirname @@}}
'''
    RESULT = '''
it does not exist

it does exist

ls exists

itdoesnotexist does not exist

basename: c

dirname: /tmp/a/b
'''

    def test_jhelpers(self):
        """Test the install function"""

        # dotpath location
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # where dotfiles will be installed
        dst = get_tempdir()
        self.assertTrue(os.path.exists(dst))
        self.addCleanup(clean, dst)

        # create the dotfile in dotdrop
        file1, _ = create_random_file(tmp)
        with open(file1, 'w', encoding='utf-8') as file:
            file.write(self.TEMPLATE)
        dst1 = os.path.join(dst, get_string(6))
        dotfile1 = Dotfile(get_string(5), dst1, os.path.basename(file1))

        # generate the config and stuff
        profile = get_string(5)
        confpath = os.path.join(tmp, self.CONFIG_NAME)
        fake_config(confpath, dotfile1, profile, tmp)
        conf = CfgAggregator(confpath, profile, debug=True)
        self.assertTrue(conf is not None)

        # install them
        opt = load_options(confpath, profile)
        opt.safe = False
        opt.install_showdiff = True
        opt.variables = {}
        opt.debug = True
        cmd_install(opt)

        # now compare the generated files
        self.assertTrue(os.path.exists(dst1))
        f1content = ''
        with open(dst1, 'r', encoding='utf-8') as file:
            f1content = file.read()
        self.assertTrue(f1content == self.RESULT)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
