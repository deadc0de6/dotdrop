"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the update function
"""


import unittest
import os
import yaml

from dotdrop.config import Cfg
from dotdrop.dotdrop import cmd_update
from dotdrop.dotdrop import cmd_importer
from dotdrop.dotfile import Dotfile

from tests.helpers import *


class TestUpdate(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def test_update(self):
        '''Test the update function'''
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

        # create the directory to test
        dpath = os.path.join(fold_config, get_string(5))
        dir1 = create_dir(dpath)
        dirf1, _ = create_random_file(dpath)

        # create the config file
        profile = get_string(5)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        conf, opts = load_config(confpath, profile)
        dfiles = [d1, dir1]

        # import the files
        cmd_importer(opts, conf, dfiles)
        conf, opts = load_config(confpath, profile)

        # edit the files
        edit_content(d1, 'newcontent')
        edit_content(dirf1, 'newcontent')

        # add more file
        dirf2, _ = create_random_file(dpath)

        # add more dirs
        dpath = os.path.join(dpath, get_string(5))
        create_dir(dpath)
        create_random_file(dpath)

        # update it
        opts['safe'] = False
        opts['debug'] = True
        cmd_update(opts, conf, [d1, dir1])

        # test content
        newcontent = open(d1, 'r').read()
        self.assertTrue(newcontent == 'newcontent')
        newcontent = open(dirf1, 'r').read()
        self.assertTrue(newcontent == 'newcontent')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
