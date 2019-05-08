"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the config parser
"""


import unittest
from unittest.mock import patch
import os
import yaml

from dotdrop.cfg_yaml import Cfg
from dotdrop.options import Options
from tests.helpers import (SubsetTestCase, _fake_args, clean,
                           create_fake_config, create_random_file,
                           create_yaml_keyval, get_tempdir,
                           populate_fake_config)


from dotdrop.cfg_yaml import CfgYaml
from dotdrop.settings import LinkTypes

NOLINK = LinkTypes.NOLINK


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
        self.assertIsSubset(imported_cfg.lnk_profiles,
                            importing_cfg.lnk_profiles)

        # test dotfiles
        self.assertIsSubset(imported_cfg.dotfiles, importing_cfg.dotfiles)

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
        self.assertIsSubset(imported_cfg.lnk_profiles,
                            importing_cfg.lnk_profiles)

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

    def test_parse_serialize_settings(self):
        """Test settings parsing in CfgYaml."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        populate_fake_config(confpath, dotfiles={})

        # parse
        config = CfgYaml.parse(confpath)

        # check members
        self.assertEqual(config.settings.backup, self.CONFIG_BACKUP)
        self.assertTrue(config.settings.banner)
        self.assertEqual(config.settings.create, self.CONFIG_CREATE)
        self.assertEqual(config.settings.dotpath, self.CONFIG_DOTPATH)
        self.assertTrue(config.settings.ignoreempty)
        self.assertEqual((), config.settings.import_actions)
        self.assertEqual((), config.settings.import_variables)
        self.assertFalse(config.settings.keepdot)
        self.assertEqual(NOLINK, config.settings.link_dotfile_default)
        self.assertEqual(NOLINK, config.settings.link_on_import)
        self.assertFalse(config.settings.longkey)
        self.assertFalse(config.settings.showdiff)
        self.assertEqual(os.path.join(tmp, 'workdir'), config.settings.workdir)

        return
        # serialize
        with open(confpath, 'w') as conf_file:
            yaml.safe_dump(config.serialize(), conf_file)

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        self.assertEqual(yaml_dict['config']['backup'], self.CONFIG_BACKUP)
        self.assertTrue(yaml_dict['config']['banner'])
        self.assertEqual(yaml_dict['config']['create'], self.CONFIG_CREATE)
        self.assertEqual(yaml_dict['config']['dotpath'], self.CONFIG_DOTPATH)
        self.assertTrue(yaml_dict['config']['ignoreempty'])
        self.assertFalse(yaml_dict['config']['keepdot'])
        self.assertEqual('nolink', yaml_dict['config']['link_dotfile_default'])
        self.assertEqual('nolink', yaml_dict['config']['link_on_import'])
        self.assertFalse(yaml_dict['config']['longkey'])
        self.assertFalse(yaml_dict['config']['showdiff'])
        self.assertEqual(os.path.join(tmp, 'workdir'),
                         yaml_dict['config']['workdir'])
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_actions']
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_variables']

        # changing a config value
        yaml_dict['config']['banner'] = False
        with open(confpath, 'w') as conf_file:
            yaml.safe_dump(yaml_dict, conf_file)

        # parse again to check serialization consistency
        # config = CfgYaml.parse(confpath)

        # check members
        self.assertEqual(config.settings.cfg, config)
        self.assertEqual(config.settings.backup, self.CONFIG_BACKUP)
        self.assertFalse(config.settings.banner)
        self.assertEqual(config.settings.create, self.CONFIG_CREATE)
        self.assertEqual(config.settings.dotpath, self.CONFIG_DOTPATH)
        self.assertTrue(config.settings.ignoreempty)
        self.assertEqual((), config.settings.import_actions)
        self.assertEqual((), config.settings.import_variables)
        self.assertFalse(config.settings.keepdot)
        self.assertEqual(NOLINK, config.settings.link_dotfile_default)
        self.assertEqual(NOLINK, config.settings.link_on_import)
        self.assertFalse(config.settings.longkey)
        self.assertFalse(config.settings.showdiff)
        self.assertEqual(os.path.join(tmp, 'workdir'), config.settings.workdir)

    def test_parse_serialize_dotfiles(self):
        """Test dotfiles parsing in CfgYaml."""
        tmp = get_tempdir()
        self.assertTrue(os.path.exists(tmp))
        self.addCleanup(clean, tmp)

        # create base config file
        confpath = create_fake_config(tmp,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        dotfile_paths = [create_random_file(tmp)[0] for _ in range(5)]
        dotfile_dicts = {
            'f_{}'.format(path): {
                'src': path,
                'dst': '~/.{}'.format(path),
            }
            for path in dotfile_paths
        }
        populate_fake_config(confpath, dotfiles=dotfile_dicts)

        # parse
        config = CfgYaml.parse(confpath)

        # check members
        for dotfile in config.dotfiles:
            dotfile_dict = dotfile_dicts.get(dotfile.key)
            self.assertIsNotNone(dotfile_dict)

            self.assertEqual({}, dotfile.actions)
            self.assertEqual((), dotfile.cmpignore)
            self.assertEqual(dotfile.dst, dotfile_dict['dst'])
            self.assertEqual(NOLINK, dotfile.link)
            self.assertFalse(dotfile.noempty)
            self.assertEqual(dotfile.src, dotfile_dict['src'])
            self.assertIsNone(dotfile.trans_r)
            self.assertIsNone(dotfile.trans_w)
            self.assertEqual((), dotfile.upignore)

        return

        # serialize
        with open(confpath, 'w') as conf_file:
            yaml.safe_dump(config.serialize(), conf_file)

        with open(confpath, 'r') as conf_file:
            yaml_dict = yaml.safe_load(conf_file)

        self.assertEqual(yaml_dict['config']['backup'], self.CONFIG_BACKUP)
        self.assertTrue(yaml_dict['config']['banner'])
        self.assertEqual(yaml_dict['config']['create'], self.CONFIG_CREATE)
        self.assertEqual(yaml_dict['config']['dotpath'], self.CONFIG_DOTPATH)
        self.assertTrue(yaml_dict['config']['ignoreempty'])
        self.assertFalse(yaml_dict['config']['keepdot'])
        self.assertEqual('nolink', yaml_dict['config']['link_dotfile_default'])
        self.assertEqual('nolink', yaml_dict['config']['link_on_import'])
        self.assertFalse(yaml_dict['config']['longkey'])
        self.assertFalse(yaml_dict['config']['showdiff'])
        self.assertEqual(os.path.join(tmp, 'workdir'),
                         yaml_dict['config']['workdir'])
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_actions']
        with self.assertRaises(KeyError):
            yaml_dict['config']['import_variables']

        # changing a config value
        yaml_dict['config']['banner'] = False
        with open(confpath, 'w') as conf_file:
            yaml.safe_dump(yaml_dict, conf_file)

        # parse again to check serialization consistency
        # config = CfgYaml.parse(confpath)

        # check members
        self.assertEqual(config.settings.cfg, config)
        self.assertEqual(config.settings.backup, self.CONFIG_BACKUP)
        self.assertFalse(config.settings.banner)
        self.assertEqual(config.settings.create, self.CONFIG_CREATE)
        self.assertEqual(config.settings.dotpath, self.CONFIG_DOTPATH)
        self.assertTrue(config.settings.ignoreempty)
        self.assertEqual((), config.settings.import_actions)
        self.assertEqual((), config.settings.import_variables)
        self.assertFalse(config.settings.keepdot)
        self.assertEqual(NOLINK, config.settings.link_dotfile_default)
        self.assertEqual(NOLINK, config.settings.link_on_import)
        self.assertFalse(config.settings.longkey)
        self.assertFalse(config.settings.showdiff)
        self.assertEqual(os.path.join(tmp, 'workdir'), config.settings.workdir)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
