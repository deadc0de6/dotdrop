"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6
basic unittest for the remove function
"""

import unittest
import os

# local imports
from dotdrop.dotdrop import cmd_remove
from tests.helpers import (clean, create_dir,
                           create_random_file, load_options,
                           get_tempdir, yaml_load, yaml_dump)


class TestRemove(unittest.TestCase):

    def load_yaml(self, path):
        """Load yaml to dict"""
        self.assertTrue(os.path.exists(path))
        return yaml_load(path)

    def test_remove(self):
        """test the remove command"""

        # dotfiles in dotpath
        dotdrop_home = get_tempdir()
        self.assertTrue(os.path.exists(dotdrop_home))
        self.addCleanup(clean, dotdrop_home)

        dotfilespath = os.path.join(dotdrop_home, 'dotfiles')
        confpath = os.path.join(dotdrop_home, 'config.yaml')
        create_dir(dotfilespath)

        df1, _ = create_random_file(dotfilespath)
        df2, _ = create_random_file(dotfilespath)
        df3, _ = create_random_file(dotfilespath)
        configdic = {
            'config': {
                'dotpath': 'dotfiles',
            },
            'dotfiles': {
                'f_test1': {
                    'src': df1,
                    'dst': '/dev/null'
                },
                'f_test2': {
                    'src': df2,
                    'dst': '/dev/null'
                },
                'f_test3': {
                    'src': df3,
                    'dst': '/tmp/some-fake-path'
                },
            },
            'profiles': {
                'host1': {
                    'dotfiles': ['f_test1', 'f_test2', 'f_test3'],
                },
                'host2': {
                    'dotfiles': ['f_test1'],
                },
                'host3': {
                    'dotfiles': ['f_test2'],
                },
            },
        }

        yaml_dump(configdic, confpath)
        o = load_options(confpath, 'host1')
        o.remove_path = ['f_test1']
        o.remove_iskey = True
        o.debug = True
        o.safe = False
        # by key
        cmd_remove(o)

        # ensure file is deleted
        self.assertFalse(os.path.exists(df1))
        self.assertTrue(os.path.exists(df2))
        self.assertTrue(os.path.exists(df3))

        # load dict
        y = yaml_load(confpath)

        # ensure not present
        self.assertTrue('f_test1' not in y['dotfiles'])
        self.assertTrue('f_test1' not in y['profiles']['host1']['dotfiles'])
        self.assertTrue('host2' not in y['profiles'])

        # assert rest is intact
        self.assertTrue('f_test2' in y['dotfiles'].keys())
        self.assertTrue('f_test3' in y['dotfiles'].keys())
        self.assertTrue('f_test2' in y['profiles']['host1']['dotfiles'])
        self.assertTrue('f_test3' in y['profiles']['host1']['dotfiles'])
        self.assertTrue(y['profiles']['host3']['dotfiles'] == ['f_test2'])

        o = load_options(confpath, 'host1')
        o.remove_path = ['/tmp/some-fake-path']
        o.remove_iskey = False
        o.debug = True
        o.safe = False
        # by path
        cmd_remove(o)

        # ensure file is deleted
        self.assertTrue(os.path.exists(df2))
        self.assertFalse(os.path.exists(df3))

        # load dict
        y = yaml_load(confpath)

        # ensure not present
        self.assertTrue('f_test3' not in y['dotfiles'])
        self.assertTrue('f_test3' not in y['profiles']['host1']['dotfiles'])

        # assert rest is intact
        self.assertTrue('host1' in y['profiles'].keys())
        self.assertFalse('host2' in y['profiles'].keys())
        self.assertTrue('host3' in y['profiles'].keys())
        self.assertTrue(y['profiles']['host1']['dotfiles'] == ['f_test2'])
        self.assertTrue(y['profiles']['host3']['dotfiles'] == ['f_test2'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
