"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6
basic unittest for jhelpers
"""

import os
import unittest

from dotdrop.cfg_aggregator import CfgAggregator as Cfg
from tests.helpers import (clean,
                           create_random_file, get_string, get_tempdir,
                           load_options)
from dotdrop.dotfile import Dotfile
from dotdrop.dotdrop import cmd_install


class TestJhelpers(unittest.TestCase):

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

    def fake_config(self, path, dotfile, profile, dotpath):
        """Create a fake config file"""
        with open(path, 'w') as f:
            f.write('config:\n')
            f.write('  backup: true\n')
            f.write('  create: true\n')
            f.write('  dotpath: {}\n'.format(dotpath))
            f.write('dotfiles:\n')
            f.write('  {}:\n'.format(dotfile.key))
            f.write('    dst: {}\n'.format(dotfile.dst))
            f.write('    src: {}\n'.format(dotfile.src))
            f.write('profiles:\n')
            f.write('  {}:\n'.format(profile))
            f.write('    dotfiles:\n')
            f.write('    - {}\n'.format(dotfile.key))
        return path

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
        f1, c1 = create_random_file(tmp)
        with open(f1, 'w') as f:
            f.write(self.TEMPLATE)
        dst1 = os.path.join(dst, get_string(6))
        d1 = Dotfile(get_string(5), dst1, os.path.basename(f1))

        # generate the config and stuff
        profile = get_string(5)
        confpath = os.path.join(tmp, self.CONFIG_NAME)
        self.fake_config(confpath, d1, profile, tmp)
        conf = Cfg(confpath, profile, debug=True)
        self.assertTrue(conf is not None)

        # install them
        o = load_options(confpath, profile)
        o.safe = False
        o.install_showdiff = True
        o.variables = {}
        o.debug = True
        cmd_install(o)

        # now compare the generated files
        self.assertTrue(os.path.exists(dst1))
        f1content = open(dst1, 'r').read()
        self.assertTrue(f1content == self.RESULT)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
