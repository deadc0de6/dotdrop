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
    """test case"""

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def compare(self, opt, tmp, nbdotfiles):
        """compare"""
        dotfiles = opt.dotfiles
        self.assertEqual(len(dotfiles), nbdotfiles)
        templ = Templategen(base=opt.dotpath, debug=True)
        inst = Installer(create=opt.create, backup=opt.backup,
                         dry=opt.dry, base=opt.dotpath, debug=opt.debug)
        comp = Comparator()
        results = {}
        for dotfile in dotfiles:
            path = os.path.expanduser(dotfile.dst)
            ret, _, insttmp = inst.install_to_temp(templ, tmp, dotfile.src,
                                                   dotfile.dst)
            if not ret:
                results[path] = False
                continue
            diff = comp.compare(insttmp, dotfile.dst,
                                ignore=['whatever', 'whatelse'])
            results[path] = diff == ''
        return results

    def test_none(self):
        """test none"""
        templ = Templategen(base=self.CONFIG_DOTPATH,
                            debug=True, variables=None)
        self.assertTrue(templ is not None)

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
        df1, _ = create_random_file(fold_config)
        self.assertTrue(os.path.exists(df1))
        self.addCleanup(clean, df1)

        df2, _ = create_random_file(fold_subcfg)
        self.assertTrue(os.path.exists(df2))
        self.addCleanup(clean, df2)

        df3, _ = create_random_file(fold_tmp)
        self.assertTrue(os.path.exists(df3))
        self.addCleanup(clean, df3)

        df4, _ = create_random_file(fold_tmp, binary=True)
        self.assertTrue(os.path.exists(df4))
        self.addCleanup(clean, df4)

        df5 = get_tempdir()
        self.assertTrue(os.path.exists(df5))
        self.addCleanup(clean, df5)
        _, _ = create_random_file(df5)

        df6, _ = create_random_file(df5)
        self.assertTrue(os.path.exists(df6))

        df9 = get_tempdir()
        self.assertTrue(os.path.exists(df9))
        self.addCleanup(clean, df9)
        d9sub = os.path.join(df9, get_string(5))
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
        opt = load_options(confpath, profile)
        opt.longkey = True
        opt.debug = True
        dfiles = [df1, df2, df3, df4, df5, df9]

        # import the files
        opt.import_path = dfiles
        cmd_importer(opt)
        opt = load_options(confpath, profile)

        # compare the files
        expected = {df1: True, df2: True, df3: True, df4: True,
                    df5: True, df9: True}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertEqual(results, expected)

        # modify file
        edit_content(df1, get_string(20))
        expected = {df1: False, df2: True, df3: True, df4: True,
                    df5: True, df9: True}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify binary file
        edit_content(df4, bytes(get_string(20), 'ascii'), binary=True)
        expected = {df1: False, df2: True, df3: True, df4: False,
                    df5: True, df9: True}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # add file in directory
        df7, _ = create_random_file(df5)
        self.assertTrue(os.path.exists(df7))
        expected = {df1: False, df2: True, df3: True, df4: False,
                    df5: False, df9: True}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # modify all files
        edit_content(df2, get_string(20))
        edit_content(df3, get_string(21))
        expected = {df1: False, df2: False, df3: False, df4: False,
                    df5: False, df9: True}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # edit sub file
        edit_content(d9f1, get_string(12))
        expected = {df1: False, df2: False, df3: False, df4: False,
                    df5: False, df9: False}
        results = self.compare(opt, tmp, len(dfiles))
        self.assertTrue(results == expected)

        # test compare from dotdrop
        self.assertFalse(cmd_compare(opt, tmp))
        # test focus
        opt.compare_focus = [df4]
        self.assertFalse(cmd_compare(opt, tmp))
        opt.compare_focus = ['/tmp/fake']
        self.assertFalse(cmd_compare(opt, tmp))


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
