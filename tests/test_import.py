"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the import function
"""


import unittest
import os
import yaml

from dotdrop.dotdrop import importer
from dotdrop.config import Cfg

from tests.helpers import *


class TestImport(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def load_yaml(self, path):
        '''Load yaml to dict'''
        self.assertTrue(os.path.exists(path))
        content = ''
        with open(path, 'r') as f:
            content = yaml.load(f)
        return content

    def assert_file(self, path, conf, profile):
        '''Make sure "path" has been inserted in "conf" for "profile"'''
        strip = get_path_strip_version(path)
        self.assertTrue(strip in [x.src for x in conf.get_dotfiles(profile)])
        dsts = [os.path.expanduser(x.dst) for x in conf.get_dotfiles(profile)]
        self.assertTrue(path in dsts)

    def assert_in_yaml(self, path, dic, link=False):
        '''Make sure "path" is in the "dic" representing the yaml file'''
        strip = get_path_strip_version(path)
        self.assertTrue(strip in [x['src'] for x in dic['dotfiles'].values()])
        dsts = [os.path.expanduser(x['dst']) for x in dic['dotfiles'].values()]
        if link:
            self.assertTrue(get_dotfile_from_yaml(dic, path)['link'])
        self.assertTrue(path in dsts)

    def test_import(self):
        '''Test the import function'''
        src = get_tempfolder()
        self.assertTrue(os.path.exists(src))
        self.addCleanup(clean, src)

        dotfilespath = get_tempfolder()
        self.assertTrue(os.path.exists(dotfilespath))
        self.addCleanup(clean, dotfilespath)

        profile = get_string(10)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        conf, opts = load_config(confpath, profile)

        # create some random dotfiles
        dotfile1, content1 = create_random_file(src)
        self.addCleanup(clean, dotfile1)
        dotfile2, content2 = create_random_file(os.path.expanduser('~'))
        self.addCleanup(clean, dotfile2)
        homeconf = os.path.join(os.path.expanduser('~'), '.config')
        if not os.path.exists(homeconf):
            os.mkdir(homeconf)
            self.addCleanup(clean, homeconf)
        dotconfig = os.path.join(homeconf, get_string(5))
        create_dir(dotconfig)
        self.addCleanup(clean, dotconfig)
        dotfile3, content3 = create_random_file(dotconfig)
        dotfile4, content3 = create_random_file(homeconf)
        self.addCleanup(clean, dotfile4)

        # fake a folder containing dotfiles
        dotfile5 = get_tempfolder()
        self.assertTrue(os.path.exists(dotfile5))
        self.addCleanup(clean, dotfile5)
        sub1, _ = create_random_file(dotfile5)
        sub2, _ = create_random_file(dotfile5)

        # fake a file for symlink
        # TODO
        dotfile6, content6 = create_random_file(dotconfig)
        self.addCleanup(clean, dotfile6)

        # fake a folder for symlink
        # TODO
        dotfile7 = get_tempfolder()
        self.assertTrue(os.path.exists(dotfile7))
        self.addCleanup(clean, dotfile7)
        sub1, _ = create_random_file(dotfile7)
        sub2, _ = create_random_file(dotfile7)

        # import the dotfiles
        dfiles = [dotfile1, dotfile2, dotfile3, dotfile4, dotfile5]
        importer(opts, conf, dfiles)
        # import symlink
        # TODO
        opts[Cfg.key_dotfiles_link] = True
        sfiles = [dotfile6, dotfile7]
        importer(opts, conf, sfiles)
        opts[Cfg.key_dotfiles_link] = False

        # reload the config
        conf, opts = load_config(confpath, profile)

        # test dotfiles in config class
        self.assertTrue(profile in conf.get_profiles())
        self.assert_file(dotfile1, conf, profile)
        self.assert_file(dotfile2, conf, profile)
        self.assert_file(dotfile3, conf, profile)
        self.assert_file(dotfile4, conf, profile)
        self.assert_file(dotfile5, conf, profile)
        self.assert_file(dotfile6, conf, profile)
        self.assert_file(dotfile7, conf, profile)

        # test dotfiles in yaml file
        y = self.load_yaml(confpath)
        self.assert_in_yaml(dotfile1, y)
        self.assert_in_yaml(dotfile2, y)
        self.assert_in_yaml(dotfile3, y)
        self.assert_in_yaml(dotfile4, y)
        self.assert_in_yaml(dotfile5, y)
        self.assert_in_yaml(dotfile6, y, link=True)
        self.assert_in_yaml(dotfile7, y, link=True)

        # test dotfiles on filesystem
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile1)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile2)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile3)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile4)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile5)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath,
                                                    dotfile5, sub1)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath,
                                                    dotfile5, sub2)))

        # test symlink on filesystem
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile6)))
        self.assertTrue(os.path.islink(dotfile6))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile7)))
        self.assertTrue(os.path.islink(dotfile7))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
