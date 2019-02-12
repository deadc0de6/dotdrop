"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the config parser
"""


import unittest
import os
import yaml

from dotdrop.config import Cfg
from tests.helpers import get_tempdir, clean, create_fake_config


class TestConfig(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    TMPSUFFIX = '.dotdrop'
    CONFIG_NAME = 'config.yaml'

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
            yaml.dump(content, f, default_flow_style=False, indent=2)

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
            yaml.dump(content, f, default_flow_style=False, indent=2)

        # do the tests
        conf = Cfg(confpath)
        self.assertTrue(conf is not None)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
