"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the compare function
"""


import unittest
import os
import yaml

from dotdrop.config import Cfg
from dotdrop.dotdrop import importer
from dotdrop.dotfile import Dotfile
from dotdrop.installer import Installer
from dotdrop.templategen import Templategen

from tests.helpers import *


class TestCompare(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def compare(self, opts, conf, tmp, nbdotfiles):
        dotfiles = conf.get_dotfiles(opts['profile'])
        self.assertTrue(len(dotfiles) == nbdotfiles)
        t = Templategen(base=opts['dotpath'])
        inst = Installer(create=opts['create'], backup=opts['backup'],
                         dry=opts['dry'], base=opts['dotpath'], quiet=True)
        results = {}
        for dotfile in dotfiles:
            diffval = inst.compare(t, tmp, opts['profile'],
                                   dotfile.src, dotfile.dst)
            path = os.path.expanduser(dotfile.dst)
            results[path] = diffval
        return results

    def edit_content(self, path, newcontent, binary=False):
        mode = 'w'
        if binary:
            mode = 'wb'
        with open(path, mode) as f:
            f.write(newcontent)

    def test_compare(self):
        '''Test the compare function'''
        # setup some folders
        fold_config = os.path.join(os.path.expanduser('~'), '.config')
        create_dir(fold_config)
        fold_subcfg = os.path.join(os.path.expanduser('~'), '.config',
                                   get_string(5))
        create_dir(fold_subcfg)
        self.addCleanup(clean, fold_subcfg)
        fold_tmp = get_tempfolder()
        create_dir(fold_tmp)
        self.addCleanup(clean, fold_tmp)

        # create the folders
        tmp = get_tempfolder()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        dotfilespath = get_tempfolder()
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
        d5 = get_tempfolder()
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
        conf, opts = load_config(confpath, self.CONFIG_DOTPATH, profile)
        dfiles = [d1, d2, d3, d4, d5]

        # import the files
        importer(opts, conf, dfiles)
        conf, opts = load_config(confpath, self.CONFIG_DOTPATH, profile)

        # compare the files
        expected = {d1: True, d2: True, d3: True, d4: True, d5: True}
        results = self.compare(opts, conf, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify file
        self.edit_content(d1, get_string(20))
        expected = {d1: False, d2: True, d3: True, d4: True, d5: True}
        results = self.compare(opts, conf, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify binary file
        self.edit_content(d4, bytes(get_string(20), 'ascii'), binary=True)
        expected = {d1: False, d2: True, d3: True, d4: False, d5: True}
        results = self.compare(opts, conf, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # add file in folder
        d7, _ = create_random_file(d5)
        self.assertTrue(os.path.exists(d7))
        expected = {d1: False, d2: True, d3: True, d4: False, d5: False}
        results = self.compare(opts, conf, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify all files
        self.edit_content(d2, get_string(20))
        self.edit_content(d3, get_string(21))
        expected = {d1: False, d2: False, d3: False, d4: False, d5: False}
        results = self.compare(opts, conf, tmp, len(dfiles))
        self.assertTrue(results == expected)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
