"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the compare function
"""


import unittest
import os

from dotdrop.dotdrop import cmd_importer
from dotdrop.dotdrop import cmd_compare
from dotdrop.installer import Installer
from dotdrop.comparator import Comparator
from dotdrop.templategen import Templategen

# from tests.helpers import *
from tests.helpers import create_dir, get_string, get_tempdir, clean, \
    create_random_file, create_fake_config, load_options, edit_content


class TestCompare(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def compare(self, o, tmp, nbdotfiles):
        dotfiles = o.dotfiles
        self.assertTrue(len(dotfiles) == nbdotfiles)
        t = Templategen(base=o.dotpath, debug=True)
        inst = Installer(create=o.create, backup=o.backup,
                         dry=o.dry, base=o.dotpath, debug=o.debug)
        comp = Comparator()
        results = {}
        for dotfile in dotfiles:
            path = os.path.expanduser(dotfile.dst)
            ret, insttmp = inst.install_to_temp(t, tmp, dotfile.src,
                                                dotfile.dst)
            if not ret:
                results[path] = False
                continue
            diff = comp.compare(insttmp, dotfile.dst,
                                ignore=['whatever', 'whatelse'])
            results[path] = diff == ''
        return results

    def test_none(self):
        t = Templategen(base=self.CONFIG_DOTPATH,
                        debug=True, variables=None)
        self.assertTrue(t is not None)

    def test_compare(self):
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

        d9 = get_tempdir()
        self.assertTrue(os.path.exists(d9))
        self.addCleanup(clean, d9)
        d9sub = os.path.join(d9, get_string(5))
        create_dir(d9sub)
        d9f1, _ = create_random_file(d9sub)

        # create the config file
        profile = get_string(5)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        o = load_options(confpath, profile)
        o.longkey = True
        o.debug = True
        dfiles = [d1, d2, d3, d4, d5, d9]

        # import the files
        o.import_path = dfiles
        cmd_importer(o)
        o = load_options(confpath, profile)

        # compare the files
        expected = {d1: True, d2: True, d3: True, d4: True,
                    d5: True, d9: True}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify file
        edit_content(d1, get_string(20))
        expected = {d1: False, d2: True, d3: True, d4: True,
                    d5: True, d9: True}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify binary file
        edit_content(d4, bytes(get_string(20), 'ascii'), binary=True)
        expected = {d1: False, d2: True, d3: True, d4: False,
                    d5: True, d9: True}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # add file in directory
        d7, _ = create_random_file(d5)
        self.assertTrue(os.path.exists(d7))
        expected = {d1: False, d2: True, d3: True, d4: False,
                    d5: False, d9: True}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify all files
        edit_content(d2, get_string(20))
        edit_content(d3, get_string(21))
        expected = {d1: False, d2: False, d3: False, d4: False,
                    d5: False, d9: True}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # edit sub file
        edit_content(d9f1, get_string(12))
        expected = {d1: False, d2: False, d3: False, d4: False,
                    d5: False, d9: False}
        results = self.compare(o, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # test compare from dotdrop
        self.assertFalse(cmd_compare(o, tmp))
        # test focus
        o.compare_focus = [d4]
        self.assertFalse(cmd_compare(o, tmp))
        o.compare_focus = ['/tmp/fake']
        self.assertFalse(cmd_compare(o, tmp))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
