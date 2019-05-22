"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the config parser
"""


import unittest
import os
from unittest.mock import patch

import yaml

from dotdrop.options import Options
from tests.helpers import (SubsetTestCase, _fake_args, clean, create_dir,
                           create_fake_config, create_random_file,
                           create_yaml_keyval, get_string, get_tempdir,
                           populate_fake_config)


from dotdrop.cfg_aggregator import CfgAggregator as Cfg
from dotdrop.cfg_yaml import CfgYaml
from dotdrop.dotfile import Dotfile
from dotdrop.profile import Profile
from dotdrop.settings import LinkTypes, Settings


class TestConfig(SubsetTestCase):

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

    @patch('dotdrop.cfg_yaml.open', create=True)
    @patch('dotdrop.cfg_yaml.os.path.exists', create=True)
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

    @patch('dotdrop.cfg_yaml.open', create=True)
    @patch('dotdrop.cfg_yaml.os.path.exists', create=True)
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
            content = yaml.safe_load(f)

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
            content = yaml.safe_load(f)
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

    def test_import_configs_merge(self):
        """Test import_configs when all config keys merge."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        vars_ed = {
            'variables': {
                'a_var_ed': '33',
            },
            'dynvariables': {
                'a_dynvar_ed': 'echo 33',
            },
        }
        vars_ing = {
            'variables': {
                'a_var_ing': 'dd',
            },
            'dynvariables': {
                'a_dynvar_ing': 'echo dd',
            },
        }
        vars_ed_file = create_yaml_keyval(vars_ed, tmp)
        vars_ing_file = create_yaml_keyval(vars_ing, tmp)

        actions_ed = {
            'pre': {
                'a_pre_action_ed': 'echo pre 22',
            },
            'post': {
                'a_post_action_ed': 'echo post 22',
            },
            'a_action_ed': 'echo 22',
        }
        actions_ing = {
            'pre': {
                'a_pre_action_ing': 'echo pre aa',
            },
            'post': {
                'a_post_action_ing': 'echo post aa',
            },
            'a_action_ing': 'echo aa',
        }
        actions_ed_file = create_yaml_keyval(actions_ed, tmp)
        actions_ing_file = create_yaml_keyval(actions_ing, tmp)

        imported = {
            'config': {
                'dotpath': 'importing',
                'import_variables': [vars_ed_file],
                'import_actions': [actions_ed_file],
            },
            'dotfiles': {
                'f_vimrc': {'dst': '~/.vimrc', 'src': 'vimrc'},
            },
            'profiles': {
                'host1': {
                    'dotfiles': ['f_vimrc'],
                },
            },
            'actions': {
                'pre': {
                    'a_pre_log_ed': 'echo pre 2',
                },
                'post': {
                    'a_post_log_ed': 'echo post 2',
                },
                'a_log_ed': 'echo 2',
            },
            'trans': {
                't_log_ed': 'echo 3',
            },
            'trans_write': {
                'tw_log_ed': 'echo 4',
            },
            'variables': {
                'v_log_ed': '42',
            },
            'dynvariables': {
                'dv_log_ed': 'echo 5',
            },
        }
        importing = {
            'config': {
                'dotpath': 'importing',
                'import_variables': [vars_ing_file],
                'import_actions': [actions_ing_file],
            },
            'dotfiles': {
                'f_xinitrc': {'dst': '~/.xinitrc', 'src': 'xinitrc'},
            },
            'profiles': {
                'host2': {
                    'dotfiles': ['f_xinitrc'],
                    'include': ['host1'],
                },
            },
            'actions': {
                'pre': {
                    'a_pre_log_ing': 'echo pre a',
                },
                'post': {
                    'a_post_log_ing': 'echo post a',
                },
                'a_log_ing': 'echo a',
            },
            'trans': {
                't_log_ing': 'echo b',
            },
            'trans_write': {
                'tw_log_ing': 'echo c',
            },
            'variables': {
                'v_log_ing': 'd',
            },
            'dynvariables': {
                'dv_log_ing': 'echo e',
            },
        }

        # create the imported base config file
        imported_path = create_fake_config(tmp,
                                           configname=self.CONFIG_NAME_2,
                                           **imported['config'])
        # create the importing base config file
        importing_path = create_fake_config(tmp,
                                            configname=self.CONFIG_NAME,
                                            import_configs=('config-*.yaml',),
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

        # do the tests
        importing_cfg = Cfg(importing_path)
        imported_cfg = Cfg(imported_path)
        self.assertIsNotNone(importing_cfg)
        self.assertIsNotNone(imported_cfg)

        # test profiles
        self.assertIsSubset(imported_cfg.get_profiles(),
                            importing_cfg.get_profiles())

        # test dotfiles
        self.assertIsSubset(imported_cfg.get_dotfiles, importing_cfg.dotfiles)

        # test actions
        self.assertIsSubset(imported_cfg.actions['pre'],
                            importing_cfg.actions['pre'])
        self.assertIsSubset(imported_cfg.actions['post'],
                            importing_cfg.actions['post'])

        # test transactions
        self.assertIsSubset(imported_cfg.trans_r, importing_cfg.trans_r)
        self.assertIsSubset(imported_cfg.trans_w, importing_cfg.trans_w)

        # test variables
        imported_vars = {
            k: v
            for k, v in imported_cfg.get_variables(None).items()
            if not k.startswith('_')
        }
        importing_vars = {
            k: v
            for k, v in importing_cfg.get_variables(None).items()
            if not k.startswith('_')
        }
        self.assertIsSubset(imported_vars, importing_vars)

        # test prodots
        self.assertIsSubset(imported_cfg.prodots, importing_cfg.prodots)

    def test_import_configs_override(self):
        """Test import_configs when some config keys overlap."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        vars_ed = {
            'variables': {
                'a_var': '33',
            },
            'dynvariables': {
                'a_dynvar': 'echo 33',
            },
        }
        vars_ing = {
            'variables': {
                'a_var': 'dd',
            },
            'dynvariables': {
                'a_dynvar': 'echo dd',
            },
        }
        vars_ed_file = create_yaml_keyval(vars_ed, tmp)
        vars_ing_file = create_yaml_keyval(vars_ing, tmp)

        actions_ed = {
            'pre': {
                'a_pre_action': 'echo pre 22',
            },
            'post': {
                'a_post_action': 'echo post 22',
            },
            'a_action': 'echo 22',
        }
        actions_ing = {
            'pre': {
                'a_pre_action': 'echo pre aa',
            },
            'post': {
                'a_post_action': 'echo post aa',
            },
            'a_action': 'echo aa',
        }
        actions_ed_file = create_yaml_keyval(actions_ed, tmp)
        actions_ing_file = create_yaml_keyval(actions_ing, tmp)

        imported = {
            'config': {
                'dotpath': 'imported',
                'backup': False,
                'import_variables': [vars_ed_file],
                'import_actions': [actions_ed_file],
            },
            'dotfiles': {
                'f_vimrc': {'dst': '~/.vimrc', 'src': 'vimrc'},
                'f_xinitrc': {'dst': '~/.xinitrc', 'src': 'xinitrc',
                              'link': 'link'},
            },
            'profiles': {
                'host1': {
                    'dotfiles': ['f_vimrc'],
                },
                'host2': {
                    'dotfiles': ['f_xinitrc'],
                },
            },
            'actions': {
                'pre': {
                    'a_pre_log': 'echo pre 2',
                },
                'post': {
                    'a_post_log': 'echo post 2',
                },
                'a_log': 'echo 2',
            },
            'trans': {
                't_log': 'echo 3',
            },
            'trans_write': {
                'tw_log': 'echo 4',
            },
            'variables': {
                'v_log': '42',
            },
            'dynvariables': {
                'dv_log': 'echo 5',
            },
        }
        importing = {
            'config': {
                'dotpath': 'importing',
                'backup': True,
                'import_variables': [vars_ing_file],
                'import_actions': [actions_ing_file],
            },
            'dotfiles': {
                'f_xinitrc': {'dst': '~/.xinitrc', 'src': 'xinitrc'},
            },
            'profiles': {
                'host2': {
                    'dotfiles': ['f_xinitrc'],
                    'include': ['host1'],
                },
            },
            'actions': {
                'pre': {
                    'a_pre_log': 'echo pre a',
                },
                'post': {
                    'a_post_log': 'echo post a',
                },
                'a_log': 'echo a',
            },
            'trans': {
                't_log': 'echo b',
            },
            'trans_write': {
                'tw_log': 'echo c',
            },
            'variables': {
                'v_log': 'd',
            },
            'dynvariables': {
                'dv_log': 'echo e',
            },
        }

        # create the imported base config file
        imported_path = create_fake_config(tmp,
                                           configname=self.CONFIG_NAME_2,
                                           **imported['config'])
        # create the importing base config file
        importing_path = create_fake_config(tmp,
                                            configname=self.CONFIG_NAME,
                                            import_configs=(imported_path,),
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

        # do the tests
        importing_cfg = Cfg(importing_path)
        imported_cfg = Cfg(imported_path)
        self.assertIsNotNone(importing_cfg)
        self.assertIsNotNone(imported_cfg)

        # test profiles
        self.assertIsSubset(imported_cfg.get_profiles(),
                            importing_cfg.get_profiles())

        # test dotfiles
        self.assertEqual(importing_cfg.dotfiles['f_vimrc'],
                         imported_cfg.dotfiles['f_vimrc'])
        self.assertNotEqual(importing_cfg.dotfiles['f_xinitrc'],
                            imported_cfg.dotfiles['f_xinitrc'])

        # test actions
        self.assertFalse(any(
            (imported_cfg.actions['pre'][key]
                == importing_cfg.actions['pre'][key])
            for key in imported_cfg.actions['pre']
        ))
        self.assertFalse(any(
            (imported_cfg.actions['post'][key]
                == importing_cfg.actions['post'][key])
            for key in imported_cfg.actions['post']
        ))

        # test transactions
        self.assertFalse(any(
            imported_cfg.trans_r[key] == importing_cfg.trans_r[key]
            for key in imported_cfg.trans_r
        ))
        self.assertFalse(any(
            imported_cfg.trans_w[key] == importing_cfg.trans_w[key]
            for key in imported_cfg.trans_w
        ))

        # test variables
        imported_vars = imported_cfg.get_variables(None)
        self.assertFalse(any(
            imported_vars[k] == v
            for k, v in importing_cfg.get_variables(None).items()
            if not k.startswith('_')
        ))

        # test prodots
        self.assertEqual(imported_cfg.prodots['host1'],
                         importing_cfg.prodots['host1'])
        self.assertNotEqual(imported_cfg.prodots['host2'],
                            importing_cfg.prodots['host2'])
        self.assertTrue(set(imported_cfg.prodots['host1'])
                        < set(importing_cfg.prodots['host2']))


class TestCfgYaml(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    TMPSUFFIX = '.dotdrop'
    CONFIG_NAME = 'config.yaml'
    CONFIG_NAME_2 = 'config-2.yaml'

    def test_parse_serialize_settings(self):
        """Test settings parsing in CfgYaml."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)
        workdir = os.path.join(tmp, 'workdir')
        default_settings = Settings()

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)

        # parse
        config = CfgYaml(confpath)

        # check members
        self.assertEqual(config.settings.backup, self.CONFIG_BACKUP)
        self.assertEqual(config.settings.banner, default_settings.banner)
        self.assertEqual(config.settings.cmpignore, default_settings.cmpignore)
        self.assertEqual(config.settings.create, self.CONFIG_CREATE)
        self.assertEqual(config.settings.default_actions,
                         default_settings.default_actions)
        self.assertEqual(config.settings.dotpath, self.CONFIG_DOTPATH)
        self.assertEqual(config.settings.ignoreempty,
                         default_settings.ignoreempty)
        self.assertEqual(config.settings.import_actions,
                         default_settings.import_actions)
        self.assertEqual(config.settings.import_configs,
                         default_settings.import_configs)
        self.assertEqual(config.settings.import_variables,
                         default_settings.import_variables)
        self.assertEqual(config.settings.keepdot, default_settings.keepdot)
        self.assertEqual(config.settings.link_dotfile_default,
                         default_settings.link_dotfile_default)
        self.assertEqual(config.settings.link_on_import,
                         default_settings.link_on_import)
        self.assertEqual(config.settings.longkey, default_settings.longkey)
        self.assertEqual(config.settings.showdiff, default_settings.showdiff)
        self.assertEqual(config.settings.workdir, workdir)
        self.assertEqual(config.settings.upignore, default_settings.upignore)

        # serialize
        config.save(force=True)

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        self.assertEqual(yaml_dict['config']['backup'], self.CONFIG_BACKUP)
        self.assertEqual(yaml_dict['config']['banner'],
                         default_settings.banner)
        self.assertEqual(yaml_dict['config']['create'], self.CONFIG_CREATE)
        self.assertEqual(yaml_dict['config']['dotpath'], self.CONFIG_DOTPATH)
        self.assertTrue(yaml_dict['config']['ignoreempty'],
                        default_settings.ignoreempty)
        self.assertFalse(yaml_dict['config']['keepdot'],
                         default_settings.keepdot)
        self.assertEqual(yaml_dict['config']['link_dotfile_default'],
                         str(default_settings.link_dotfile_default))
        self.assertEqual('nolink', yaml_dict['config']['link_on_import'],
                         str(default_settings.link_on_import))
        self.assertFalse(yaml_dict['config']['longkey'],
                         default_settings.longkey)
        self.assertFalse(yaml_dict['config']['showdiff'],
                         default_settings.showdiff)
        self.assertEqual(yaml_dict['config']['workdir'], workdir)
        with self.assertRaises(KeyError):
            yaml_dict['config']['cmpignore']
        with self.assertRaises(KeyError):
            yaml_dict['config']['default_actions']
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_actions']
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_config']
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_variables']
        with self.assertRaises(KeyError):
            yaml_dict['config']['upignore']

        # changing a config value
        yaml_dict['config']['banner'] = False
        with open(confpath, 'w') as conf_file:
            yaml.safe_dump(yaml_dict, conf_file)

        # parse again to check serialization consistency
        config = CfgYaml(confpath)

        # check members
        self.assertEqual(config.settings.backup, self.CONFIG_BACKUP)
        self.assertFalse(config.settings.banner)
        self.assertEqual(config.settings.cmpignore, default_settings.cmpignore)
        self.assertEqual(config.settings.create, self.CONFIG_CREATE)
        self.assertEqual(config.settings.default_actions,
                         default_settings.default_actions)
        self.assertEqual(config.settings.dotpath, self.CONFIG_DOTPATH)
        self.assertEqual(config.settings.ignoreempty,
                         default_settings.ignoreempty)
        self.assertEqual(config.settings.import_actions,
                         default_settings.import_actions)
        self.assertEqual(config.settings.import_configs,
                         default_settings.import_configs)
        self.assertEqual(config.settings.import_variables,
                         default_settings.import_variables)
        self.assertEqual(config.settings.keepdot, default_settings.keepdot)
        self.assertEqual(config.settings.link_dotfile_default,
                         default_settings.link_dotfile_default)
        self.assertEqual(config.settings.link_on_import,
                         default_settings.link_on_import)
        self.assertEqual(config.settings.longkey, default_settings.longkey)
        self.assertEqual(config.settings.showdiff, default_settings.showdiff)
        self.assertEqual(config.settings.workdir, workdir)
        self.assertEqual(config.settings.upignore, default_settings.upignore)

    def test_parse_serialize_dotfiles(self):
        """Test dotfiles parsing in CfgYaml."""
        tmp = get_tempdir()
        profile_name = 'profiletest'
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)
        default_dotfile = Dotfile(key=None, src=None, dst=None)

        # creating dotfiles
        dotfiles_start = {
            'f_{}'.format(path): {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        }
        dotfiles_added = [
            {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        ]

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, dotfiles=dotfiles_start)

        # parse
        config = CfgYaml(confpath)

        # check members
        for dotfile in config.dotfiles:
            dotfile_dict = dotfiles_start.get(dotfile.key)
            self.assertIsNotNone(dotfile_dict)

            self.assertEqual(dotfile.actions, default_dotfile.actions)
            self.assertEqual(dotfile.cmpignore, default_dotfile.cmpignore)
            self.assertEqual(dotfile.dst, dotfile_dict['dst'])
            self.assertEqual(dotfile.link, default_dotfile.link)
            self.assertEqual(dotfile.noempty, default_dotfile.noempty)
            self.assertEqual(dotfile.src, dotfile_dict['src'])
            self.assertEqual(dotfile.trans_r, default_dotfile.trans_r)
            self.assertEqual(dotfile.trans_w, default_dotfile.trans_w)
            self.assertEqual(dotfile.upignore, default_dotfile.upignore)

        # serialize
        config.save(force=True)

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        for key, dotfile_dict in dotfiles_start.items():
            config_dotfile = yaml_dict['dotfiles'].get(key)
            self.assertIsNotNone(config_dotfile)
            self.assertEqual(config_dotfile, dotfile_dict)

        # modify
        for dotfile_args in dotfiles_added:
            config.new_dotfile(dotfile_args, profile_name)
        config.save()

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        for key, dotfile_dict in dotfiles_start.items():
            config_dotfile = yaml_dict['dotfiles'].get(key)
            self.assertIsNotNone(config_dotfile)
            self.assertEqual(config_dotfile, dotfile_dict)

        for dotfile_args in dotfiles_added:
            config_dotfile = next(
                dotfile_dict
                for dotfile_dict in yaml_dict['dotfiles'].values()
                if dotfile_args['dst'] == dotfile_dict['dst']
            )
            self.assertEqual(dotfile_args, config_dotfile)

    def test_parse_serialize_profiles(self):
        """Test profiles parsing in CfgYaml."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)
        default_profile = Profile(key=None)

        # creating dotfiles
        dotfiles_start = {
            'f_{}'.format(path): {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        }
        dotfiles_added = [
            {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        ]

        # creating profiles
        profiles = {
            'host1': {
                'dotfiles': list(dotfiles_start.keys()),
            },
        }

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, dotfiles=dotfiles_start,
                             profiles=profiles)

        # parse
        config = CfgYaml(confpath)

        # check members
        for profile in config.profiles:
            profile_dict = profiles.get(profile.key)
            self.assertIsNotNone(profile_dict)

            self.assertEqual(profile.actions, default_profile.actions)
            self.assertEqual(profile_dict['dotfiles'], profile.dotfiles)
            self.assertEqual(profile.imported_dotfiles,
                             default_profile.imported_dotfiles)
            self.assertEqual(profile.included_profiles,
                             default_profile.included_profiles)
            self.assertEqual(profile.variables, default_profile.variables)
            self.assertEqual(profile.dynvariables,
                             default_profile.dynvariables)

        # serialize
        config.save(force=True)

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        for key, profile_dict in profiles.items():
            config_profile = yaml_dict['profiles'].get(key)
            self.assertIsNotNone(config_profile)
            self.assertEqual(config_profile, profile_dict)

        # modify
        modified_profile = config.profiles[0]
        for dotfile_args in dotfiles_added:
            config.new_dotfile(dotfile_args, modified_profile.key)
        config.save()

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        modified_profile_dict = yaml_dict['profiles'][modified_profile.key]
        self.assertIsNotNone(modified_profile_dict)

        for dotfile_key in dotfiles_start.keys():
            self.assertIn(dotfile_key, modified_profile_dict['dotfiles'])
            self.assertIn(dotfile_key, modified_profile.dotfiles)

        for dotfile_args in dotfiles_added:
            dotfile_key = next(
                dotfile_key
                for dotfile_key, dotfile_dict in yaml_dict['dotfiles'].items()
                if dotfile_args['dst'] == dotfile_dict['dst']
            )
            self.assertIn(dotfile_key, modified_profile_dict['dotfiles'])
            self.assertIn(dotfile_key, modified_profile.dotfiles)

    def test_get_dotfile(self):
        """Test CfgYaml:get_dotfile method."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # creating profiles
        dotfiles = {
            'test-dotfile': {
                'src': 'dotfile',
                'dst': '~/.dotfile',
            }
        }

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, dotfiles=dotfiles)

        # parse
        config = CfgYaml(confpath)

        ###################################################
        # dotfile not found
        ###################################################

        missing_dotfile = 'missing'
        found_dotfile = config.get_dotfile(missing_dotfile)
        self.assertIsNone(found_dotfile)

        ###################################################
        # profile found
        ###################################################

        searched_dotfile = config.dotfiles[0]
        found_dotfile = config.get_dotfile(searched_dotfile.dst)
        self.assertIs(searched_dotfile, found_dotfile)

    def test_get_profile(self):
        """Test CfgYaml:get_profile method."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # creating profiles
        profiles = {
            'test-profile': {
                'dotfiles': [],
            }
        }

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, profiles=profiles)

        # parse
        config = CfgYaml(confpath)

        ###################################################
        # profile not found
        ###################################################

        missing_profile = 'missing'
        found_profile = config.get_profile(missing_profile)
        self.assertIsNone(found_profile)

        ###################################################
        # profile found
        ###################################################

        searched_profile = config.profiles[0]
        found_profile = config.get_profile(searched_profile.key)
        self.assertIs(searched_profile, found_profile)

    def test_new_dotfile(self):
        """Test CfgYaml:new_dotfile() corner cases."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # creating dotfiles
        dotfiles_start = {
            'f_{}'.format(path): {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        }
        dotfiles_added = [
            {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in (create_random_file(tmp)[0] for _ in range(5))
        ]

        # creating profiles
        profile_name = 'host1'
        profiles = {
            profile_name: {
                'dotfiles': list(dotfiles_start.keys()),
            },
        }

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, dotfiles=dotfiles_start,
                             profiles=profiles)

        # parse
        config = CfgYaml(confpath)

        ###################################################
        # dotfile already exists
        ###################################################

        existing_dotfile = dotfiles_start[next(iter(dotfiles_start.keys()))]
        prev_dotfiles = config.dotfiles
        config.new_dotfile(existing_dotfile, profile_name)

        # model-layer test
        self.assertEqual(prev_dotfiles, config.dotfiles)

        # filesystem test
        config.save(force=True)
        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)
        self.assertEqual(yaml_dict['dotfiles'], dotfiles_start)

        ###################################################
        # new dotfile
        ###################################################

        new_dotfile_args = dotfiles_added[0]
        _, new_dotfile = config.new_dotfile(new_dotfile_args, profile_name)

        # model-layer test
        self.assertIn(new_dotfile, config.dotfiles)

        # filesystem test
        config.save()
        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)
        self.assertEqual(yaml_dict['dotfiles'][new_dotfile.key],
                         new_dotfile_args)

        ###################################################
        # profile found
        ###################################################

        existing_profile = config.profiles[0]
        _, existing_dotfile_obj = config.new_dotfile(existing_dotfile,
                                                     existing_profile.key)

        # model-layer test
        self.assertIn(existing_dotfile_obj.key, existing_profile.dotfiles)

        # filesystem test
        config.save()
        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)
        existing_profile_dict = yaml_dict['profiles'][existing_profile.key]
        self.assertIn(existing_dotfile_obj.key,
                      existing_profile_dict['dotfiles'])

        ###################################################
        # profile not found
        ###################################################

        new_profile = 'new-profile'
        config.new_dotfile(existing_dotfile, new_profile)
        new_profile = config.get_profile(new_profile)

        # model-layer test
        self.assertIn(existing_dotfile_obj.key, new_profile.dotfiles)

        # filesystem test
        config.save()
        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)
        new_profile_dict = yaml_dict['profiles'][new_profile.key]
        self.assertIn(existing_dotfile_obj.key, new_profile_dict['dotfiles'])

    def test_new_dotfile_keys(self):
        """Test new dotfile key creation in CfgYaml:new_dotfile()."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        inner_tmp = create_dir(os.path.join(tmp, get_string(5)))
        self.assertTrue(os.path.exists(inner_tmp))
        self.addCleanup(clean, tmp)

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        config = CfgYaml(confpath)
        profile_name = 'testprofile'

        ###################################################
        # Brand new key (empty dotfiles)
        ###################################################

        dst0, _ = create_random_file(tmp)
        src0 = os.path.relpath(dst0, start=tmp)
        dotfile0 = {'src': src0, 'dst': dst0, }
        expected_key = 'f_{}'.format(src0.replace(os.path.sep, '_').lower())

        _, new_dotfile0 = config.new_dotfile(dotfile0, profile_name)
        self.assertEqual(expected_key, new_dotfile0.key)

        ###################################################
        # No key suffix
        ###################################################

        dst1, _ = create_random_file(tmp)
        src1 = os.path.relpath(dst1, start=tmp)
        dotfile1 = {'src': src1, 'dst': dst1, }
        expected_key = 'f_{}'.format(src1.replace(os.path.sep, '_').lower())

        _, new_dotfile1 = config.new_dotfile(dotfile1, profile_name)
        self.assertEqual(expected_key, new_dotfile1.key)

        ###################################################
        # Common key suffix
        ###################################################

        dst2 = os.path.join(inner_tmp, os.path.basename(dotfile0['dst']))
        with open(dst2, 'w') as dst_file:
            dst_file.write('aaaaa')
        src2 = os.path.relpath(dst2, start=tmp)
        dotfile2 = {'src': src2, 'dst': dst2, }
        expected_key = 'f_{}'.format(src2.replace(os.path.sep, '_').lower())

        _, new_dotfile2 = config.new_dotfile(dotfile2, profile_name)
        self.assertEqual(expected_key, new_dotfile2.key)

        ###################################################
        # Unique key
        ###################################################

        base_dir = os.path.expanduser('~')
        dst3_dir = create_dir(os.path.join(base_dir, '.dotdrop-test'))
        dst3, _ = create_random_file(dst3_dir)
        dst4 = os.path.normpath(os.path.join(dst3_dir, '..',
                                             os.path.basename(dst3)))
        with open(dst4, 'w') as dst_file:
            dst_file.write('aaaaa')
        self.addCleanup(clean, dst3_dir)
        self.addCleanup(clean, dst4)
        src3 = os.path.basename(dst3)
        src4 = os.path.relpath(dst4, start=base_dir)
        dotfile3 = {'src': src3, 'dst': dst3, }
        dotfile4 = {'src': src4, 'dst': dst4, }
        expected_key3 = 'f_{}'.format(src3.replace(os.path.sep, '_').lower())
        expected_key4 = 'f_{}_1'.format(src4.replace(os.path.sep, '_').lower())

        _, new_dotfile3 = config.new_dotfile(dotfile3, profile_name)
        _, new_dotfile4 = config.new_dotfile(dotfile4, profile_name)
        self.assertEqual(expected_key3, new_dotfile3.key)
        self.assertEqual(expected_key4, new_dotfile4.key)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
