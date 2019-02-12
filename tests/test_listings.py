"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the compare function
"""


import unittest
import os

from dotdrop.dotdrop import cmd_list_profiles
from dotdrop.dotdrop import cmd_list_files
from dotdrop.dotdrop import cmd_detail
from dotdrop.dotdrop import cmd_importer

from tests.helpers import create_dir, get_string, get_tempdir, \
                          create_random_file, load_options, \
                          create_fake_config, clean


class TestListings(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def test_listings(self):
        """Test the compare function"""
        # setup some directories
        fold_config = os.path.join(os.path.expanduser('~'), '.config')
        create_dir(fold_config)
        fold_subcfg = os.path.join(os.path.expanduser('~'), '.config',
                                   get_string(5))
        create_dir(fold_subcfg)
        self.addCleanup(clean, fold_subcfg)
        fold_tmp = get_tempdir()
        create_dir(fold_tmp)
        self.addCleanup(clean, fold_tmp)

        # create the directories
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        dotfilespath = get_tempdir()
        self.assertTrue(os.path.exists(dotfilespath))
        self.addCleanup(clean, dotfilespath)

        # create the dotfiles to test
        d1, c1 = create_random_file(fold_config)
        self.assertTrue(os.path.exists(d1))
        self.addCleanup(clean, d1)
        d2, c2 = create_random_file(fold_subcfg)
        self.assertTrue(os.path.exists(d2))
        self.addCleanup(clean, d2)
        d3, c3 = create_random_file(fold_tmp)
        self.assertTrue(os.path.exists(d3))
        self.addCleanup(clean, d3)
        d4, c4 = create_random_file(fold_tmp, binary=True)
        self.assertTrue(os.path.exists(d4))
        self.addCleanup(clean, d4)
        d5 = get_tempdir()
        self.assertTrue(os.path.exists(d5))
        self.addCleanup(clean, d5)
        d6, _ = create_random_file(d5)
        self.assertTrue(os.path.exists(d6))

        # create the config file
        profile = get_string(5)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        o = load_options(confpath, profile)
        dfiles = [d1, d2, d3, d4, d5]

        # import the files
        o.import_path = dfiles
        cmd_importer(o)
        o = load_options(confpath, profile)

        # listfiles
        cmd_list_profiles(o)

        # list files
        o.listfiles_templateonly = False
        cmd_list_files(o)
        o.listfiles_templateonly = True
        cmd_list_files(o)

        # details
        o.detail_keys = None
        cmd_detail(o)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
