"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the update function
"""


import unittest
import os

from dotdrop.dotdrop import cmd_update
from dotdrop.dotdrop import cmd_importer
from dotdrop.action import Transform

from tests.helpers import create_dir, get_string, get_tempdir, clean, \
    create_random_file, create_fake_config, load_options, edit_content


class TestUpdate(unittest.TestCase):
    """unit test"""

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def test_update(self):
        """Test the update function"""
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
        dotfilefile1, _ = create_random_file(fold_config)
        self.assertTrue(os.path.exists(dotfilefile1))
        self.addCleanup(clean, dotfilefile1)

        dotfilefile2, _ = create_random_file(fold_config)
        self.assertTrue(os.path.exists(dotfilefile2))
        self.addCleanup(clean, dotfilefile2)

        # template
        d3t, _ = create_random_file(fold_config)
        self.assertTrue(os.path.exists(d3t))
        self.addCleanup(clean, d3t)

        # sub dirs
        dsubstmp = get_tempdir()
        self.assertTrue(os.path.exists(dsubstmp))
        self.addCleanup(clean, dsubstmp)
        dirsubs = os.path.basename(dsubstmp)

        dir1string = 'somedir'
        dir1 = os.path.join(dsubstmp, dir1string)
        create_dir(dir1)
        dir1sub1str = 'sub1'
        sub1 = os.path.join(dir1, dir1sub1str)
        create_dir(sub1)
        dir1sub2str = 'sub2'
        sub2 = os.path.join(dir1, dir1sub2str)
        create_dir(sub2)
        f1s1, _ = create_random_file(sub1)
        self.assertTrue(os.path.exists(f1s1))
        f1s2, _ = create_random_file(sub2)
        self.assertTrue(os.path.exists(f1s2))

        # create the directory to test
        dpath = os.path.join(fold_config, get_string(5))
        dir1 = create_dir(dpath)
        dirf1, _ = create_random_file(dpath)
        self.addCleanup(clean, dir1)

        # create the config file
        profile = get_string(5)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        opt = load_options(confpath, profile)
        opt.update_showpatch = True
        dfiles = [dotfilefile1, dir1, dotfilefile2, d3t, dsubstmp]

        # import the files
        opt.import_path = dfiles
        cmd_importer(opt)

        # get new config
        opt = load_options(confpath, profile)
        opt.safe = False
        opt.update_showpatch = True
        opt.debug = True
        trans = Transform('trans', 'cp -r {0} {1}')
        d3tb = os.path.basename(d3t)
        for dotfile in opt.dotfiles:
            if os.path.basename(dotfile.dst) == d3tb:
                # patch the template
                src = os.path.join(opt.dotpath, dotfile.src)
                src = os.path.expanduser(src)
                edit_content(src, '{{@@ profile @@}}')
            left = os.path.realpath(os.path.basename(dotfile.dst))
            right = os.path.realpath(dirsubs)
            if left == right:
                # retrieve the path of the sub in the dotpath
                d1indotpath = os.path.join(opt.dotpath, dotfile.src)
                d1indotpath = os.path.expanduser(d1indotpath)
            dotfile.trans_update = trans

        # update template
        opt.update_path = [d3t]
        self.assertFalse(cmd_update(opt))

        # update sub dirs
        gone = os.path.join(d1indotpath, dir1string)
        gone = os.path.join(gone, dir1sub1str)
        self.assertTrue(os.path.exists(gone))
        clean(sub1)  # dir1sub1str
        self.assertTrue(os.path.exists(gone))
        opt.update_path = [dsubstmp]
        cmd_update(opt)
        self.assertFalse(os.path.exists(gone))

        # edit the files
        edit_content(dotfilefile1, 'newcontent')
        edit_content(dirf1, 'newcontent')

        # add more file
        _, _ = create_random_file(dpath)

        # add more dirs
        dpath = os.path.join(dpath, get_string(5))
        create_dir(dpath)
        create_random_file(dpath)

        # update it
        opt.update_path = [dotfilefile1, dir1]
        cmd_update(opt)

        # test content
        newcontent = ''
        with open(dotfilefile1, 'r', encoding='utf-8') as file:
            newcontent = file.read()
        self.assertTrue(newcontent == 'newcontent')
        newcontent = ''
        with open(dirf1, 'r', encoding='utf-8') as file:
            newcontent = file.read()
        self.assertTrue(newcontent == 'newcontent')

        edit_content(dotfilefile2, 'newcontentbykey')

        # update it by key
        dfiles = opt.dotfiles
        d2key = ''
        for dotfile in dfiles:
            src = os.path.expanduser(dotfile.dst)
            if src == dotfilefile2:
                d2key = dotfile.key
                break
        self.assertTrue(d2key != '')
        opt.update_path = [d2key]
        opt.update_iskey = True
        cmd_update(opt)

        # test content
        newcontent = ''
        with open(dotfilefile2, 'r', encoding='utf-8') as file:
            newcontent = file.read()
        self.assertTrue(newcontent == 'newcontentbykey')


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
