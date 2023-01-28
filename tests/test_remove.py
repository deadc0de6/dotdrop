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
    """test case"""

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
        opt = load_options(confpath, 'host1')
        opt.remove_path = ['f_test1']
        opt.remove_iskey = True
        opt.debug = True
        opt.safe = False
        # by key
        cmd_remove(opt)

        # ensure file is deleted
        self.assertFalse(os.path.exists(df1))
        self.assertTrue(os.path.exists(df2))
        self.assertTrue(os.path.exists(df3))

        # load dict
        cont = yaml_load(confpath)

        # ensure not present
        self.assertTrue('f_test1' not in cont['dotfiles'])
        self.assertTrue('f_test1' not in cont['profiles']['host1']['dotfiles'])
        self.assertTrue('host2' not in cont['profiles'])

        # assert rest is intact
        self.assertTrue('f_test2' in cont['dotfiles'].keys())
        self.assertTrue('f_test3' in cont['dotfiles'].keys())
        self.assertTrue('f_test2' in cont['profiles']['host1']['dotfiles'])
        self.assertTrue('f_test3' in cont['profiles']['host1']['dotfiles'])
        self.assertTrue(cont['profiles']['host3']['dotfiles'] == ['f_test2'])

        opt = load_options(confpath, 'host1')
        opt.remove_path = ['/tmp/some-fake-path']
        opt.remove_iskey = False
        opt.debug = True
        opt.safe = False
        # by path
        cmd_remove(opt)

        # ensure file is deleted
        self.assertTrue(os.path.exists(df2))
        self.assertFalse(os.path.exists(df3))

        # load dict
        cont = yaml_load(confpath)

        # ensure not present
        self.assertTrue('f_test3' not in cont['dotfiles'])
        self.assertTrue('f_test3' not in cont['profiles']['host1']['dotfiles'])

        # assert rest is intact
        self.assertTrue('host1' in cont['profiles'].keys())
        self.assertFalse('host2' in cont['profiles'].keys())
        self.assertTrue('host3' in cont['profiles'].keys())
        self.assertTrue(cont['profiles']['host1']['dotfiles'] == ['f_test2'])
        self.assertTrue(cont['profiles']['host3']['dotfiles'] == ['f_test2'])


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
