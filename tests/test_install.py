"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the install function
"""

import os
import unittest
from unittest.mock import MagicMock, patch
import filecmp

from dotdrop.cfg_aggregator import CfgAggregator as Cfg
from tests.helpers import (clean, create_dir, create_fake_config,
                           create_random_file, get_string, get_tempdir,
                           load_options, populate_fake_config)
from dotdrop.dotfile import Dotfile
from dotdrop.installer import Installer
from dotdrop.action import Action
from dotdrop.dotdrop import cmd_install
from dotdrop.options import BACKUP_SUFFIX
from dotdrop.utils import header
from dotdrop.linktypes import LinkTypes


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
        """Create a fake config file"""
        with open(path, 'w') as f:
            f.write('actions:\n')
            for action in actions:
                f.write('  {}: {}\n'.format(action.key, action.action))
            f.write('trans:\n')
            for tr in trans:
                f.write('  {}: {}\n'.format(tr.key, tr.action))
            f.write('config:\n')
            f.write('  backup: true\n')
            f.write('  create: true\n')
            f.write('  dotpath: {}\n'.format(dotpath))
            f.write('dotfiles:\n')
            for d in dotfiles:
                f.write('  {}:\n'.format(d.key))
                f.write('    dst: {}\n'.format(d.dst))
                f.write('    src: {}\n'.format(d.src))
                f.write('    link: {}\n'.format(d.link.name.lower()))
                if len(d.actions) > 0:
                    f.write('    actions:\n')
                    for action in d.actions:
                        f.write('      - {}\n'.format(action.key))
                if d.trans_r:
                    for tr in d.trans_r:
                        f.write('    trans_read: {}\n'.format(tr.key))
            f.write('profiles:\n')
            f.write('  {}:\n'.format(profile))
            f.write('    dotfiles:\n')
            for d in dotfiles:
                f.write('    - {}\n'.format(d.key))
        return path

    def test_install(self):
        """Test the install function"""

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
        # fake a __str__
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
        d4 = Dotfile(key=get_string(6), dst=dst4, src=os.path.basename(f4))
        with open(dst4, 'w') as f:
            f.write(get_string(16))

        # to test link
        f5, c5 = create_random_file(tmp)
        dst5 = os.path.join(dst, get_string(6))
        self.addCleanup(clean, dst5)
        d5 = Dotfile(get_string(6), dst5,
                     os.path.basename(f5), link=LinkTypes.LINK)

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
        d7 = Dotfile(get_string(6), dst7,
                     os.path.basename(dir2), link=LinkTypes.LINK)

        # to test actions
        value = get_string(12)
        fact = '/tmp/action'
        self.addCleanup(clean, fact)
        act1 = Action('testaction', 'post', 'echo "{}" > {}'.format(value,
                                                                    fact))
        f8, c8 = create_random_file(tmp)
        dst8 = os.path.join(dst, get_string(6))
        d8 = Dotfile(get_string(6), dst8, os.path.basename(f8), actions=[act1])

        # to test transformations
        trans1 = 'trans1'
        trans2 = 'trans2'
        cmd = 'cat {0} | sed \'s/%s/%s/g\' > {1}' % (trans1, trans2)
        tr = Action('testtrans', 'post', cmd)
        f9, c9 = create_random_file(tmp, content=trans1)
        dst9 = os.path.join(dst, get_string(6))
        d9 = Dotfile(get_string(6), dst9, os.path.basename(f9), trans_r=[tr])

        # to test template
        f10, _ = create_random_file(tmp, content='{{@@ header() @@}}')
        dst10 = os.path.join(dst, get_string(6))
        d10 = Dotfile(get_string(6), dst10, os.path.basename(f10))

        # generate the config and stuff
        profile = get_string(5)
        confpath = os.path.join(tmp, self.CONFIG_NAME)
        dotfiles = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, ddot]
        self.fake_config(confpath, dotfiles,
                         profile, tmp, [act1], [tr])
        conf = Cfg(confpath, profile, debug=True)
        self.assertTrue(conf is not None)

        # install them
        o = load_options(confpath, profile)
        o.safe = False
        o.install_showdiff = True
        o.variables = {}
        cmd_install(o)

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
        b = dst4 + BACKUP_SUFFIX
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
        self.assertTrue(tempcontent == header())

    def test_install_import_configs(self):
        """Test the install function with imported configs"""
        # dotpath location
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        os.mkdir(os.path.join(tmp, 'importing'))
        os.mkdir(os.path.join(tmp, 'imported'))

        # where dotfiles will be installed
        dst = get_tempdir()
        self.assertTrue(os.path.exists(dst))
        self.addCleanup(clean, dst)

        # creating random dotfiles
        imported_dotfile, _ = create_random_file(os.path.join(tmp, 'imported'))
        imported_dotfile = {
            'dst': os.path.join(dst, imported_dotfile),
            'key': 'f_{}'.format(imported_dotfile),
            'name': imported_dotfile,
            'src': os.path.join(tmp, 'imported', imported_dotfile),
        }
        importing_dotfile, _ = \
            create_random_file(os.path.join(tmp, 'importing'))
        importing_dotfile = {
            'dst': os.path.join(dst, importing_dotfile),
            'key': 'f_{}'.format(importing_dotfile),
            'name': importing_dotfile,
            'src': os.path.join(tmp, 'imported', importing_dotfile),
        }

        imported = {
            'config': {
                'dotpath': 'imported',
            },
            'dotfiles': {
                imported_dotfile['key']: {
                    'dst': imported_dotfile['dst'],
                    'src': imported_dotfile['name'],
                },
            },
            'profiles': {
                'host1': {
                    'dotfiles': [imported_dotfile['key']],
                },
            },
        }
        importing = {
            'config': {
                'dotpath': 'importing',
            },
            'dotfiles': {
                importing_dotfile['key']: {
                    'dst': importing_dotfile['dst'],
                    'src': importing_dotfile['src'],
                },
            },
            'profiles': {
                'host2': {
                    'dotfiles': [importing_dotfile['key']],
                    'include': ['host1'],
                },
            },
        }

        # create the imported base config file
        imported_path = create_fake_config(tmp,
                                           configname='config-2.yaml',
                                           **imported['config'])
        # create the importing base config file
        importing_path = create_fake_config(tmp,
                                            configname='config.yaml',
                                            import_configs=['config-2.yaml'],
                                            **importing['config'])

        # edit the imported config
        populate_fake_config(imported_path, **{
            k: v
            for k, v in imported.items()
            if k != 'config'
        })

        # edit the importing config
        populate_fake_config(importing_path, **{
            k: v
            for k, v in importing.items()
            if k != 'config'
        })

        # install them
        o = load_options(importing_path, 'host2')
        o.safe = False
        o.install_showdiff = True
        o.variables = {}
        cmd_install(o)

        # now compare the generated files
        self.assertTrue(os.path.exists(importing_dotfile['dst']))
        self.assertTrue(os.path.exists(imported_dotfile['dst']))

    def test_link_children(self):
        """test the link children"""
        # create source dir
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        # where dotfiles will be installed
        dst_dir = get_tempdir()
        self.assertTrue(os.path.exists(dst_dir))
        self.addCleanup(clean, dst_dir)

        # create 3 random files in source
        srcs = [create_random_file(src_dir)[0] for _ in range(3)]

        installer = Installer()
        installer.link_children(templater=MagicMock(), src=src_dir,
                                dst=dst_dir, actionexec=None)

        # Ensure all destination files point to source
        for src in srcs:
            dst = os.path.join(dst_dir, src)
            self.assertEqual(os.path.realpath(dst), src)

    def test_fails_without_src(self):
        """test fails without src"""
        src = '/some/non/existant/file'

        installer = Installer()
        logger = MagicMock()
        installer.log.err = logger

        res, err = installer.link_children(templater=MagicMock(), src=src,
                                           dst='/dev/null', actionexec=None)

        self.assertFalse(res)
        e = 'source dotfile does not exist: {}'.format(src)
        self.assertEqual(err, e)

    def test_fails_when_src_file(self):
        """test fails when src file"""
        # create source dir
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        src = create_random_file(src_dir)[0]

        logger = MagicMock()
        templater = MagicMock()
        installer = Installer()
        installer.log.err = logger

        # pass src file not src dir
        res, err = installer.link_children(templater=templater, src=src,
                                           dst='/dev/null', actionexec=None)

        # ensure nothing performed
        self.assertFalse(res)
        e = 'source dotfile is not a directory: {}'.format(src)
        self.assertEqual(err, e)

    def test_creates_dst(self):
        """test creates dst"""
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        # where dotfiles will be installed
        dst_dir = get_tempdir()
        self.addCleanup(clean, dst_dir)

        # move dst dir to new (uncreated) dir in dst
        dst_dir = os.path.join(dst_dir, get_string(6))
        self.assertFalse(os.path.exists(dst_dir))

        installer = Installer()
        installer.link_children(templater=MagicMock(), src=src_dir,
                                dst=dst_dir, actionexec=None)

        # ensure dst dir created
        self.assertTrue(os.path.exists(dst_dir))

    def test_prompts_to_replace_dst(self):
        """test prompts to replace dst"""
        # create source dir
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        # where dotfiles will be installed
        dst_dir = get_tempdir()
        self.addCleanup(clean, dst_dir)

        # Create destination file to be replaced
        dst = os.path.join(dst_dir, get_string(6))
        with open(dst, 'w'):
            pass
        self.assertTrue(os.path.isfile(dst))

        # setup mocks
        ask = MagicMock()
        ask.return_value = True

        # setup installer
        installer = Installer()
        installer.safe = True
        installer.log.ask = ask

        installer.link_children(templater=MagicMock(), src=src_dir, dst=dst,
                                actionexec=None)

        # ensure destination now a directory
        self.assertTrue(os.path.isdir(dst))

        # ensure prompted
        ask.assert_called_with(
            'Remove regular file {} and replace with empty directory?'
            .format(dst))

    @patch('dotdrop.installer.Templategen')
    def test_runs_templater(self, mocked_templategen):
        """test runs templater"""
        # create source dir
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        # where dotfiles will be installed
        dst_dir = get_tempdir()
        self.assertTrue(os.path.exists(dst_dir))
        self.addCleanup(clean, dst_dir)

        # create 3 random files in source
        srcs = [create_random_file(src_dir)[0] for _ in range(3)]

        # setup installer and mocks
        installer = Installer()
        templater = MagicMock()
        templater.generate.return_value = b'content'
        # make templategen treat everything as a template
        mocked_templategen.is_template.return_value = True

        installer.link_children(templater=templater, src=src_dir, dst=dst_dir,
                                actionexec=None)

        for src in srcs:
            dst = os.path.join(dst_dir, os.path.basename(src))

            # ensure dst is link
            self.assertTrue(os.path.islink(dst))
            # ensure dst not directly linked to src
            self.assertNotEqual(os.path.realpath(dst), src)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
