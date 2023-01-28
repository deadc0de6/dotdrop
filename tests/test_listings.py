"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the compare function
"""


import unittest
import os

from dotdrop.dotdrop import cmd_list_profiles
from dotdrop.dotdrop import cmd_files
from dotdrop.dotdrop import cmd_detail
from dotdrop.dotdrop import cmd_importer

from tests.helpers import create_dir, get_string, get_tempdir, \
                          create_random_file, load_options, \
                          create_fake_config, clean


class TestListings(unittest.TestCase):
    """listing test"""

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
        file1, _ = create_random_file(fold_config)
        self.assertTrue(os.path.exists(file1))
        self.addCleanup(clean, file1)
        file2, _ = create_random_file(fold_subcfg)
        self.assertTrue(os.path.exists(file2))
        self.addCleanup(clean, file2)
        file3, _ = create_random_file(fold_tmp)
        self.assertTrue(os.path.exists(file3))
        self.addCleanup(clean, file3)
        file4, _ = create_random_file(fold_tmp, binary=True)
        self.assertTrue(os.path.exists(file4))
        self.addCleanup(clean, file4)
        file5 = get_tempdir()
        self.assertTrue(os.path.exists(file5))
        self.addCleanup(clean, file5)
        file6, _ = create_random_file(file5)
        self.assertTrue(os.path.exists(file6))

        # create the config file
        profile = get_string(5)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        opt = load_options(confpath, profile)
        dfiles = [file1, file2, file3, file4, file5]

        # import the files
        opt.import_path = dfiles
        cmd_importer(opt)
        opt = load_options(confpath, profile)

        # files
        cmd_list_profiles(opt)

        # list files
        opt.files_templateonly = False
        cmd_files(opt)
        opt.files_templateonly = True
        cmd_files(opt)

        # details
        opt.detail_keys = None
        cmd_detail(opt)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
