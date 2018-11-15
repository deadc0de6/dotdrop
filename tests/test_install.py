"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the install function
"""

import unittest
import filecmp

from tests.helpers import *
from dotdrop.dotfile import Dotfile
from dotdrop.installer import Installer
from dotdrop.action import Action
from dotdrop.dotdrop import cmd_install


class TestInstall(unittest.TestCase):

    CONFIG_NAME = 'config.yaml'

    TEMPLATE = '''
# launch the wm
{%@@ if profile == "home" @@%}
exec awesome
{%@@ else @@%}
exec bspwm
{%@@ endif @@%}
'''
    RESULT = '''
# launch the wm
exec bspwm
'''

    def fake_config(self, path, dotfiles, profile,
                    dotpath, actions, trans):
        '''Create a fake config file'''
        with open(path, 'w') as f:
            f.write('actions:\n')
            for action in actions:
                f.write('  {}: {}\n'.format(action.key, action.action))
            f.write('trans:\n')
            for action in trans:
                f.write('  {}: {}\n'.format(action.key, action.action))
            f.write('config:\n')
            f.write('  backup: true\n')
            f.write('  create: true\n')
            f.write('  dotpath: {}\n'.format(dotpath))
            f.write('dotfiles:\n')
            for d in dotfiles:
                f.write('  {}:\n'.format(d.key))
                f.write('    dst: {}\n'.format(d.dst))
                f.write('    src: {}\n'.format(d.src))
                f.write('    link: {}\n'.format(str(d.link).lower()))
                if len(d.actions) > 0:
                    f.write('    actions:\n')
                    for action in d.actions:
                        f.write('      - {}\n'.format(action.key))
                if len(d.trans) > 0:
                    f.write('    trans:\n')
                    for action in d.trans:
                        f.write('      - {}\n'.format(action.key))
            f.write('profiles:\n')
            f.write('  {}:\n'.format(profile))
            for d in dotfiles:
                f.write('  - {}\n'.format(d.key))
        return path

    def test_install(self):
        '''Test the install function'''

        # dotpath location
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # where dotfiles will be installed
        dst = get_tempdir()
        self.assertTrue(os.path.exists(dst))
        self.addCleanup(clean, dst)

        # create the dotfile in dotdrop
        f1, c1 = create_random_file(tmp)
        dst1 = os.path.join(dst, get_string(6))
        d1 = Dotfile(get_string(5), dst1, os.path.basename(f1))
        # fake a print
        self.assertTrue(str(d1) != '')
        f2, c2 = create_random_file(tmp)
        dst2 = os.path.join(dst, get_string(6))
        d2 = Dotfile(get_string(5), dst2, os.path.basename(f2))
        with open(f2, 'w') as f:
            f.write(self.TEMPLATE)
        f3, _ = create_random_file(tmp, binary=True)
        dst3 = os.path.join(dst, get_string(6))
        d3 = Dotfile(get_string(5), dst3, os.path.basename(f3))

        # create a directory dotfile
        dir1 = os.path.join(tmp, 'somedir')
        create_dir(dir1)
        fd, _ = create_random_file(dir1)
        dstd = os.path.join(dst, get_string(6))
        ddot = Dotfile(get_string(5), dstd, os.path.basename(dir1))

        # to test backup
        f4, c4 = create_random_file(tmp)
        dst4 = os.path.join(dst, get_string(6))
        d4 = Dotfile(get_string(6), dst4, os.path.basename(f4))
        with open(dst4, 'w') as f:
            f.write(get_string(16))

        # to test link
        f5, c5 = create_random_file(tmp)
        dst5 = os.path.join(dst, get_string(6))
        self.addCleanup(clean, dst5)
        d5 = Dotfile(get_string(6), dst5, os.path.basename(f5), link=True)

        # create the dotfile directories in dotdrop
        dir1 = create_dir(os.path.join(tmp, get_string(6)))
        self.assertTrue(os.path.exists(dir1))
        self.addCleanup(clean, dir1)
        dst6 = os.path.join(dst, get_string(6))
        # fill with files
        sub1, _ = create_random_file(dir1, template=True)
        self.assertTrue(os.path.exists(sub1))
        sub2, _ = create_random_file(dir1)
        self.assertTrue(os.path.exists(sub2))
        # make up the dotfile
        d6 = Dotfile(get_string(6), dst6, os.path.basename(dir1))

        # to test symlink directories
        dir2 = create_dir(os.path.join(tmp, get_string(6)))
        self.assertTrue(os.path.exists(dir2))
        self.addCleanup(clean, dir2)
        dst7 = os.path.join(dst, get_string(6))
        # fill with files
        sub3, _ = create_random_file(dir2)
        self.assertTrue(os.path.exists(sub3))
        sub4, _ = create_random_file(dir2)
        self.assertTrue(os.path.exists(sub4))
        # make up the dotfile
        d7 = Dotfile(get_string(6), dst7, os.path.basename(dir2), link=True)

        # to test actions
        value = get_string(12)
        fact = '/tmp/action'
        act1 = Action('testaction', 'echo "{}" > {}'.format(value, fact))
        f8, c8 = create_random_file(tmp)
        dst8 = os.path.join(dst, get_string(6))
        d8 = Dotfile(get_string(6), dst8, os.path.basename(f8), actions=[act1])

        # to test transformations
        trans1 = 'trans1'
        trans2 = 'trans2'
        cmd = 'cat {0} | sed \'s/%s/%s/g\' > {1}' % (trans1, trans2)
        tr = Action('testtrans', cmd)
        f9, c9 = create_random_file(tmp, content=trans1)
        dst9 = os.path.join(dst, get_string(6))
        d9 = Dotfile(get_string(6), dst9, os.path.basename(f9), trans=[tr])

        # to test template
        f10, _ = create_random_file(tmp, content='{{@@ profile @@}}')
        dst10 = os.path.join(dst, get_string(6))
        d10 = Dotfile(get_string(6), dst10, os.path.basename(f10))

        # generate the config and stuff
        profile = get_string(5)
        confpath = os.path.join(tmp, self.CONFIG_NAME)
        dotfiles = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, ddot]
        self.fake_config(confpath, dotfiles,
                         profile, tmp, [act1], [tr])
        conf = Cfg(confpath)
        self.assertTrue(conf is not None)

        # install them
        conf, opts = load_config(confpath, profile)
        opts['safe'] = False
        opts['debug'] = True
        opts['showdiff'] = True
        opts['variables'] = {}
        cmd_install(opts, conf)

        # now compare the generated files
        self.assertTrue(os.path.exists(dst1))
        self.assertTrue(os.path.exists(dst2))
        self.assertTrue(os.path.exists(dst3))
        self.assertTrue(os.path.exists(dst5))
        self.assertTrue(os.path.exists(dst6))
        self.assertTrue(os.path.exists(dst7))
        self.assertTrue(os.path.exists(dst8))
        self.assertTrue(os.path.exists(dst10))
        self.assertTrue(os.path.exists(fd))

        # check if 'dst5' is a link whose target is 'f5'
        self.assertTrue(os.path.islink(dst5))
        self.assertTrue(os.path.realpath(dst5) == os.path.realpath(f5))

        # check if 'dst7' is a link whose target is 'dir2'
        self.assertTrue(os.path.islink(dst7))
        self.assertTrue(os.path.realpath(dst7) == os.path.realpath(dir2))

        # make sure backup is there
        b = dst4 + Installer.BACKUP_SUFFIX
        self.assertTrue(os.path.exists(b))

        self.assertTrue(filecmp.cmp(f1, dst1, shallow=True))
        f2content = open(dst2, 'r').read()
        self.assertTrue(f2content == self.RESULT)
        self.assertTrue(filecmp.cmp(f3, dst3, shallow=True))

        # test action has been executed
        self.assertTrue(os.path.exists(fact))
        self.assertTrue(str(act1) != '')
        actcontent = open(fact, 'r').read().rstrip()
        self.assertTrue(actcontent == value)

        # test transformation has been done
        self.assertTrue(os.path.exists(dst9))
        transcontent = open(dst9, 'r').read().rstrip()
        self.assertTrue(transcontent == trans2)

        # test template has been remplaced
        self.assertTrue(os.path.exists(dst10))
        tempcontent = open(dst10, 'r').read().rstrip()
        self.assertTrue(tempcontent == profile)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
