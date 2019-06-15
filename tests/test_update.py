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
        d1, c1 = create_random_file(fold_config)
        self.assertTrue(os.path.exists(d1))
        self.addCleanup(clean, d1)

        d2, c2 = create_random_file(fold_config)
        self.assertTrue(os.path.exists(d2))
        self.addCleanup(clean, d2)

        # template
        d3t, c3t = create_random_file(fold_config)
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
        f1s1, f1s1c1 = create_random_file(sub1)
        self.assertTrue(os.path.exists(f1s1))
        f1s2, f1s2c1 = create_random_file(sub2)
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
        o = load_options(confpath, profile)
        o.update_showpatch = True
        dfiles = [d1, dir1, d2, d3t, dsubstmp]

        # import the files
        o.import_path = dfiles
        cmd_importer(o)

        # get new config
        o = load_options(confpath, profile)
        o.safe = False
        o.update_showpatch = True
        o.debug = True
        trans = Transform('trans', 'cp -r {0} {1}')
        d3tb = os.path.basename(d3t)
        for dotfile in o.dotfiles:
            if os.path.basename(dotfile.dst) == d3tb:
                # patch the template
                src = os.path.join(o.dotpath, dotfile.src)
                src = os.path.expanduser(src)
                edit_content(src, '{{@@ profile @@}}')
            if os.path.basename(dotfile.dst) == dirsubs:
                # retrieve the path of the sub in the dotpath
                d1indotpath = os.path.join(o.dotpath, dotfile.src)
                d1indotpath = os.path.expanduser(d1indotpath)
            dotfile.trans_w = trans

        # update template
        o.update_path = [d3t]
        self.assertFalse(cmd_update(o))

        # update sub dirs
        gone = os.path.join(d1indotpath, dir1string)
        gone = os.path.join(gone, dir1sub1str)
        self.assertTrue(os.path.exists(gone))
        clean(sub1)  # dir1sub1str
        self.assertTrue(os.path.exists(gone))
        o.update_path = [dsubstmp]
        cmd_update(o)
        self.assertFalse(os.path.exists(gone))

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
        o.update_path = [d1, dir1]
        cmd_update(o)

        # test content
        newcontent = open(d1, 'r').read()
        self.assertTrue(newcontent == 'newcontent')
        newcontent = open(dirf1, 'r').read()
        self.assertTrue(newcontent == 'newcontent')

        edit_content(d2, 'newcontentbykey')

        # update it by key
        dfiles = o.dotfiles
        d2key = ''
        for ds in dfiles:
            t = os.path.expanduser(ds.dst)
            if t == d2:
                d2key = ds.key
                break
        self.assertTrue(d2key != '')
        o.update_path = [d2key]
        o.update_iskey = True
        cmd_update(o)

        # test content
        newcontent = open(d2, 'r').read()
        self.assertTrue(newcontent == 'newcontentbykey')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
