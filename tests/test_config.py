"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the config parser
"""


import unittest
from unittest.mock import patch
import os
import yaml

from dotdrop.config import Cfg
from dotdrop.options import Options
from dotdrop.linktypes import LinkTypes
from tests.helpers import get_tempdir, clean, \
        create_fake_config, _fake_args, populate_fake_config


class TestConfig(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    TMPSUFFIX = '.dotdrop'
    CONFIG_NAME = 'config.yaml'
    CONFIG_NAME_2 = 'config-2.yaml'

    def test_config(self):
        """Test the config class"""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        conf = Cfg(confpath)
        self.assertTrue(conf is not None)

        opts = conf.get_settings()
        self.assertTrue(opts is not None)
        self.assertTrue(opts != {})
        self.assertTrue(opts['backup'] == self.CONFIG_BACKUP)
        self.assertTrue(opts['create'] == self.CONFIG_CREATE)
        dotpath = os.path.join(tmp, self.CONFIG_DOTPATH)
        self.assertTrue(opts['dotpath'] == dotpath)
        self.assertTrue(conf._is_valid())
        self.assertTrue(conf.dump() != '')

    def test_def_link(self):
        self._test_link_import('nolink', LinkTypes.LINK, 'link')
        self._test_link_import('nolink', LinkTypes.NOLINK, 'nolink')
        self._test_link_import('nolink',
                               LinkTypes.LINK_CHILDREN,
                               'link_children')
        self._test_link_import('link', LinkTypes.LINK, 'link')
        self._test_link_import('link', LinkTypes.NOLINK, 'nolink')
        self._test_link_import('link',
                               LinkTypes.LINK_CHILDREN,
                               'link_children')
        self._test_link_import('link_children', LinkTypes.LINK, 'link')
        self._test_link_import('link_children', LinkTypes.NOLINK, 'nolink')
        self._test_link_import('link_children', LinkTypes.LINK_CHILDREN,
                               'link_children')
        self._test_link_import_fail('whatever')

    @patch('dotdrop.config.open', create=True)
    @patch('dotdrop.config.os.path.exists', create=True)
    def _test_link_import(self, cfgstring, expected,
                          cliargs, mock_exists, mock_open):
        data = '''
config:
  backup: true
  create: true
  dotpath: dotfiles
  banner: true
  longkey: false
  keepdot: false
  link_on_import: {}
  link_dotfile_default: nolink
dotfiles:
profiles:
        '''.format(cfgstring)

        mock_open.side_effect = [
                unittest.mock.mock_open(read_data=data).return_value
                ]
        mock_exists.return_value = True

        args = _fake_args()
        args['--profile'] = 'p1'
        args['--cfg'] = 'mocked'
        args['--link'] = cliargs
        o = Options(args=args)

        self.assertTrue(o.import_link == expected)

    @patch('dotdrop.config.open', create=True)
    @patch('dotdrop.config.os.path.exists', create=True)
    def _test_link_import_fail(self, value, mock_exists, mock_open):
        data = '''
config:
  backup: true
  create: true
  dotpath: dotfiles
  banner: true
  longkey: false
  keepdot: false
  link_on_import: {}
  link_dotfile_default: nolink
dotfiles:
profiles:
        '''.format(value)

        mock_open.side_effect = [
                unittest.mock.mock_open(read_data=data).return_value
                ]
        mock_exists.return_value = True

        args = _fake_args()
        args['--profile'] = 'p1'
        args['--cfg'] = 'mocked'

        with self.assertRaisesRegex(ValueError, 'config is not valid'):
            o = Options(args=args)
            print(o.import_link)

    def test_include(self):
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # create a base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)

        # edit the config
        with open(confpath, 'r') as f:
            content = yaml.load(f)

        # adding dotfiles
        df1key = 'f_vimrc'
        df2key = 'f_xinitrc'
        content['dotfiles'] = {
                df1key: {'dst': '~/.vimrc', 'src': 'vimrc'},
                df2key: {'dst': '~/.xinitrc', 'src': 'xinitrc'}
                }

        # adding profiles
        pf1key = 'host1'
        pf2key = 'host2'
        content['profiles'] = {
                pf1key: {'dotfiles': [df2key], 'include': ['host2']},
                pf2key: {'dotfiles': [df1key]}
                }

        # save the new config
        with open(confpath, 'w') as f:
            yaml.safe_dump(content, f, default_flow_style=False,
                           indent=2)

        # do the tests
        conf = Cfg(confpath)
        self.assertTrue(conf is not None)

        # test profile
        profiles = conf.get_profiles()
        self.assertTrue(pf1key in profiles)
        self.assertTrue(pf2key in profiles)

        # test dotfiles
        dotfiles = conf._get_dotfiles(pf1key)
        self.assertTrue(df1key in [x.key for x in dotfiles])
        self.assertTrue(df2key in [x.key for x in dotfiles])
        dotfiles = conf._get_dotfiles(pf2key)
        self.assertTrue(df1key in [x.key for x in dotfiles])
        self.assertFalse(df2key in [x.key for x in dotfiles])

        # test not existing included profile
        # edit the config
        with open(confpath, 'r') as f:
            content = yaml.load(f)
        content['profiles'] = {
                pf1key: {'dotfiles': [df2key], 'include': ['host2']},
                pf2key: {'dotfiles': [df1key], 'include': ['host3']}
                }

        # save the new config
        with open(confpath, 'w') as f:
            yaml.safe_dump(content, f, default_flow_style=False,
                           indent=2)

        # do the tests
        conf = Cfg(confpath)
        self.assertTrue(conf is not None)

    def test_include_profiles(self):
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # create the imported base config file
        imported = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME_2,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        # create the importing base config file
        importing = create_fake_config(tmp,
                                       configname=self.CONFIG_NAME,
                                       dotpath=self.CONFIG_DOTPATH,
                                       backup=self.CONFIG_BACKUP,
                                       create=self.CONFIG_CREATE,
                                       import_profiles=(imported,))

        # keys
        keys = {
            'dotfile1': 'f_vimrc',
            'dotfile2': 'f_xinitrc',
            'profile1': 'host1',
            'profile2': 'host2',
            }

        # edit the imported config
        dotfiles_imported = {
                keys['dotfile1']: {'dst': '~/.vimrc', 'src': 'vimrc'},
                }
        profiles_imported = {
            keys['profile1']: {'dotfiles': [keys['dotfile1']]},
        }
        populate_fake_config(imported,
                             dotfiles=dotfiles_imported,
                             profiles=profiles_imported)

        # edit the importing config
        dotfiles_importing = {
                keys['dotfile2']: {'dst': '~/.vimrc', 'src': 'vimrc'},
                }
        profiles_importing = {
                keys['profile2']: {
                    'dotfiles': [keys['dotfile2']],
                    'include': [keys['profile1']],
                    }
                }
        populate_fake_config(importing,
                             dotfiles=dotfiles_importing,
                             profiles=profiles_importing)

        # do the tests
        importing_cfg = Cfg(importing)
        self.assertIsNotNone(importing_cfg)

        # test profile
        profiles = importing_cfg.get_profiles()
        self.assertIn(keys['profile2'], profiles)

        # test dotfiles
        importing_cfg_dotfiles = [
            (dotfile.key, {'src': dotfile.src, 'dst': dotfile.dst})
            for dotfile in importing_cfg.prodots[keys['profile2']]
            ]

        self.assertIn(
            (keys['dotfile2'], dotfiles_importing[keys['dotfile2']]),
            importing_cfg_dotfiles)
        self.assertIn(
            (keys['dotfile1'], dotfiles_imported[keys['dotfile1']]),
            importing_cfg_dotfiles)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
