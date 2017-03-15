"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the import function
"""


import unittest
import os
import yaml

from dotdrop.config import Cfg
from dotdrop.dotdrop import importer

from tests.helpers import *


class TestImport(unittest.TestCase):

    CONFIG_BACKUP = True
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def load_config(self, confpath, profile):
        '''Load the config file from path'''
        conf = Cfg(confpath, self.CONFIG_DOTPATH)
        self.assertTrue(conf is not None)
        opts = conf.get_configs()
        opts['dry'] = False
        opts['profile'] = profile
        opts['safe'] = True
        opts['installdiff'] = True
        return conf, opts

    def load_yaml(self, path):
        '''Load yaml to dict'''
        self.assertTrue(os.path.exists(path))
        content = ''
        with open(path, 'r') as f:
            content = yaml.load(f)
        return content

    def get_path_strip_version(self, path):
        '''Strip a file path for conf tests'''
        self.assertTrue(os.path.exists(path))
        strip = path
        home = os.path.expanduser('~')
        if strip.startswith(home):
            strip = strip[len(home):]
        strip = strip.lstrip('.' + os.sep)
        return strip

    def assert_file(self, path, conf, profile):
        '''Make sure "path" has been inserted in "conf" for "profile"'''
        strip = self.get_path_strip_version(path)
        self.assertTrue(strip in [x.src for x in conf.get_dotfiles(profile)])
        dsts = [os.path.expanduser(x.dst) for x in conf.get_dotfiles(profile)]
        self.assertTrue(path in dsts)

    def assert_in_yaml(self, path, dic):
        '''Make sure "path" is in the "dic" representing the yaml file'''
        strip = self.get_path_strip_version(path)
        self.assertTrue(strip in [x['src'] for x in dic['dotfiles'].values()])
        dsts = [os.path.expanduser(x['dst']) for x in dic['dotfiles'].values()]
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
        conf, opts = self.load_config(confpath, profile)

        # create some random dotfiles
        dotfile1, content1 = create_random_file(src)
        self.addCleanup(clean, dotfile1)
        dotfile2, content2 = create_random_file(os.path.expanduser('~'))
        self.addCleanup(clean, dotfile2)
        homeconf = os.path.join(os.path.expanduser('~'), '.config')
        os.mkdir(homeconf)
        dotconfig = os.path.join(homeconf, get_string(5))
        create_dir(dotconfig)
        self.addCleanup(clean, dotconfig)
        dotfile3, content3 = create_random_file(dotconfig)
        dotfile4, content3 = create_random_file(homeconf)
        self.addCleanup(clean, dotfile4)

        # import the dotfiles
        importer(opts, conf, [dotfile1, dotfile2, dotfile3])

        # reload the config
        conf, opts = self.load_config(confpath, profile)

        # test dotfiles in config class
        self.assertTrue(profile in conf.get_profiles())
        self.assert_file(dotfile1, conf, profile)
        self.assert_file(dotfile2, conf, profile)
        self.assert_file(dotfile3, conf, profile)

        # test dotfiles in yaml file
        y = self.load_yaml(confpath)
        self.assert_in_yaml(dotfile1, y)
        self.assert_in_yaml(dotfile2, y)
        self.assert_in_yaml(dotfile3, y)

        # test dotfiles on filesystem
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile1)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile2)))
        self.assertTrue(os.path.exists(os.path.join(dotfilespath, dotfile3)))


def main():
    unittest.main()

if __name__ == '__main__':
    main()
