"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the install function
"""

import os
import unittest
from unittest.mock import MagicMock
import filecmp
from tests.helpers import (clean, create_dir, create_fake_config,
                           create_random_file, get_string, get_tempdir,
                           load_options, populate_fake_config)
from dotdrop.cfg_aggregator import CfgAggregator as Cfg
from dotdrop.dotfile import Dotfile
from dotdrop.installer import Installer
from dotdrop.action import Action
from dotdrop.dotdrop import cmd_install
from dotdrop.options import BACKUP_SUFFIX
from dotdrop.utils import header
from dotdrop.linktypes import LinkTypes


def fake_config(path, dotfiles, profile,
                dotpath, actions, transs):
    """Create a fake config file"""
    with open(path, 'w', encoding='utf-8') as file:
        file.write('actions:\n')
        for action in actions:
            file.write(f'  {action.key}: {action.action}\n')
        file.write('trans_install:\n')
        for trans in transs:
            file.write(f'  {trans.key}: {trans.action}\n')
        file.write('config:\n')
        file.write('  backup: true\n')
        file.write('  create: true\n')
        file.write(f'  dotpath: {dotpath}\n')
        file.write('dotfiles:\n')
        for dotfile in dotfiles:
            linkval = dotfile.link.name.lower()
            file.write(f'  {dotfile.key}:\n')
            file.write(f'    dst: {dotfile.dst}\n')
            file.write(f'    src: {dotfile.src}\n')
            file.write(f'    link: {linkval}\n')
            if len(dotfile.actions) > 0:
                file.write('    actions:\n')
                for action in dotfile.actions:
                    file.write(f'      - {action.key}\n')
            if dotfile.trans_install:
                for trans in dotfile.trans_install:
                    file.write(f'    trans_install: {trans.key}\n')
        file.write('profiles:\n')
        file.write(f'  {profile}:\n')
        file.write('    dotfiles:\n')
        for dotfile in dotfiles:
            file.write(f'    - {dotfile.key}\n')
    return path


class TestInstall(unittest.TestCase):
    """test case"""

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
        fcontent1, _ = create_random_file(tmp)
        dst1 = os.path.join(dst, get_string(6))
        dotfile1 = Dotfile(get_string(5), dst1, os.path.basename(fcontent1))
        # fake a __str__
        self.assertTrue(str(dotfile1) != '')
        fcontent2, _ = create_random_file(tmp)
        dst2 = os.path.join(dst, get_string(6))
        dotfile2 = Dotfile(get_string(5), dst2, os.path.basename(fcontent2))
        with open(fcontent2, 'w', encoding='utf-8') as file:
            file.write(self.TEMPLATE)
        fcontent3, _ = create_random_file(tmp, binary=True)
        dst3 = os.path.join(dst, get_string(6))
        dotfile3 = Dotfile(get_string(5), dst3, os.path.basename(fcontent3))

        # create a directory dotfile
        dir1 = os.path.join(tmp, 'somedir')
        create_dir(dir1)
        fildfd, _ = create_random_file(dir1)
        dstd = os.path.join(dst, get_string(6))
        ddot = Dotfile(get_string(5), dstd, os.path.basename(dir1))

        # to test backup
        fcontent4, _ = create_random_file(tmp)
        dst4 = os.path.join(dst, get_string(6))
        dotfile4 = Dotfile(key=get_string(6),
                           dst=dst4,
                           src=os.path.basename(fcontent4))
        with open(dst4, 'w',
                  encoding='utf-8') as file:
            file.write(get_string(16))

        # to test link
        fcontent5, _ = create_random_file(tmp)
        dst5 = os.path.join(dst, get_string(6))
        self.addCleanup(clean, dst5)
        dotfile5 = Dotfile(get_string(6), dst5,
                           os.path.basename(fcontent5), link=LinkTypes.LINK)

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
        dotfile6 = Dotfile(get_string(6), dst6, os.path.basename(dir1))

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
        dotfile7 = Dotfile(get_string(6), dst7,
                           os.path.basename(dir2), link=LinkTypes.LINK)

        # to test actions
        value = get_string(12)
        fact = '/tmp/action'
        self.addCleanup(clean, fact)
        act1 = Action('testaction', 'post', f'echo "{value}" > {fact}')
        fcontent8, _ = create_random_file(tmp)
        dst8 = os.path.join(dst, get_string(6))
        dotfile8 = Dotfile(get_string(6), dst8, os.path.basename(fcontent8),
                           actions=[act1])

        # to test transformations
        trans1 = 'trans1'
        trans2 = 'trans2'
        # pylint: disable=C0209
        cmd = 'cat {0} | sed \'s/%s/%s/g\' > {1}' % (trans1, trans2)
        self.addCleanup(clean, trans2)
        the_trans = Action('testtrans', 'post', cmd)
        fcontent9, _ = create_random_file(tmp, content=trans1)
        dst9 = os.path.join(dst, get_string(6))
        dotfile9 = Dotfile(get_string(6), dst9, os.path.basename(fcontent9),
                           trans_install=[the_trans])

        # to test template
        f10, _ = create_random_file(tmp, content='{{@@ header() @@}}')
        dst10 = os.path.join(dst, get_string(6))
        dotfile10 = Dotfile(get_string(6), dst10, os.path.basename(f10))

        # generate the config and stuff
        profile = get_string(5)
        confpath = os.path.join(tmp, self.CONFIG_NAME)
        dotfiles = [dotfile1, dotfile2, dotfile3, dotfile4,
                    dotfile5, dotfile6, dotfile7, dotfile8,
                    dotfile9, dotfile10, ddot]
        fake_config(confpath, dotfiles,
                    profile, tmp, [act1], [the_trans])
        conf = Cfg(confpath, profile, debug=True)
        self.assertTrue(conf is not None)

        # install them
        opt = load_options(confpath, profile)
        opt.safe = False
        opt.install_showdiff = True
        cmd_install(opt)

        # now compare the generated files
        self.assertTrue(os.path.exists(dst1))
        self.assertTrue(os.path.exists(dst2))
        self.assertTrue(os.path.exists(dst3))
        self.assertTrue(os.path.exists(dst5))
        self.assertTrue(os.path.exists(dst6))
        self.assertTrue(os.path.exists(dst7))
        self.assertTrue(os.path.exists(dst8))
        self.assertTrue(os.path.exists(dst10))
        self.assertTrue(os.path.exists(fildfd))

        # check if 'dst5' is a link whose target is 'f5'
        self.assertTrue(os.path.islink(dst5))
        self.assertTrue(os.path.realpath(dst5) == os.path.realpath(fcontent5))

        # check if 'dst7' is a link whose target is 'dir2'
        self.assertTrue(os.path.islink(dst7))
        self.assertTrue(os.path.realpath(dst7) == os.path.realpath(dir2))

        # make sure backup is there
        backupf = dst4 + BACKUP_SUFFIX
        self.assertTrue(os.path.exists(backupf))

        self.assertTrue(filecmp.cmp(fcontent1, dst1, shallow=True))
        f2content = ''
        with open(dst2, 'r', encoding='utf-8') as file:
            f2content = file.read()
        self.assertTrue(f2content == self.RESULT)
        self.assertTrue(filecmp.cmp(fcontent3, dst3, shallow=True))

        # test action has been executed
        self.assertTrue(os.path.exists(fact))
        self.assertTrue(str(act1) != '')
        actcontent = ''
        with open(fact, 'r', encoding='utf-8') as file:
            actcontent = file.read().rstrip()
        self.assertTrue(actcontent == value)

        # test transformation has been done
        self.assertTrue(os.path.exists(dst9))
        transcontent = ''
        with open(dst9, 'r', encoding='utf-8') as file:
            transcontent = file.read().rstrip()
        self.assertTrue(transcontent == trans2)

        # test template has been remplaced
        self.assertTrue(os.path.exists(dst10))
        tempcontent = ''
        with open(dst10, 'r', encoding='utf-8') as file:
            tempcontent = file.read().rstrip()
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
            'key': f'f_{imported_dotfile}',
            'name': imported_dotfile,
            'src': os.path.join(tmp, 'imported', imported_dotfile),
        }
        importing_dotfile, _ = \
            create_random_file(os.path.join(tmp, 'importing'))
        importing_dotfile = {
            'dst': os.path.join(dst, importing_dotfile),
            'key': f'f_{importing_dotfile}',
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
        opt = load_options(importing_path, 'host2')
        opt.safe = False
        opt.install_showdiff = True
        opt.variables = {}
        cmd_install(opt)

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
        installer.install(templater=MagicMock(), src=src_dir,
                          dst=dst_dir, linktype=LinkTypes.LINK_CHILDREN,
                          actionexec=None)

        # Ensure all destination files point to source
        for src in srcs:
            xyz = os.path.join(dst_dir, src)
            self.assertEqual(os.path.realpath(xyz), os.path.realpath(src))

    def test_fails_without_src(self):
        """test fails without src"""
        src = '/some/non/existant/file'

        installer = Installer()
        # logger = MagicMock()
        # installer.log.err = logger

        res, err = installer.install(templater=MagicMock(), src=src,
                                     dst='/dev/null',
                                     linktype=LinkTypes.LINK_CHILDREN,
                                     actionexec=None)

        self.assertFalse(res)
        exp = f'source dotfile does not exist: {src}'
        self.assertEqual(err, exp)

    def test_fails_when_src_file(self):
        """test fails when src file"""
        # create source dir
        src_dir = get_tempdir()
        self.assertTrue(os.path.exists(src_dir))
        self.addCleanup(clean, src_dir)

        src = create_random_file(src_dir)[0]

        # logger = MagicMock()
        templater = MagicMock()
        installer = Installer()
        # installer.log.err = logger

        # pass src file not src dir
        res, err = installer.install(templater=templater, src=src,
                                     dst='/dev/null',
                                     linktype=LinkTypes.LINK_CHILDREN,
                                     actionexec=None)

        # ensure nothing performed
        self.assertFalse(res)
        exp = f'source dotfile is not a directory: {src}'
        self.assertEqual(err, exp)

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
        installer.install(templater=MagicMock(), src=src_dir,
                          dst=dst_dir, linktype=LinkTypes.LINK_CHILDREN,
                          actionexec=None)

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
        with open(dst, 'w', encoding='utf=8'):
            pass
        self.assertTrue(os.path.isfile(dst))

        # setup mocks
        ask = MagicMock()
        ask.return_value = True

        # setup installer
        installer = Installer()
        installer.safe = True
        installer.log.ask = ask

        installer.install(templater=MagicMock(), src=src_dir,
                          dst=dst, linktype=LinkTypes.LINK_CHILDREN,
                          actionexec=None)

        # ensure destination now a directory
        self.assertTrue(os.path.isdir(dst))

        # ensure prompted
        ask.assert_called_with(
            f'Remove regular file {dst} and replace with empty directory?')

    def test_runs_templater(self):
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

        installer.install(templater=templater, src=src_dir, dst=dst_dir,
                          linktype=LinkTypes.LINK_CHILDREN, actionexec=None)

        for src in srcs:
            xyz = os.path.join(dst_dir, os.path.basename(src))

            # ensure dst is link
            self.assertTrue(os.path.islink(xyz))
            # ensure dst not directly linked to src
            self.assertNotEqual(os.path.realpath(xyz), src)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
