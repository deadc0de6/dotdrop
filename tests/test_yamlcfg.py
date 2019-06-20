"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the config parser
"""


import unittest
from unittest.mock import patch
import os

from dotdrop.cfg_yaml import CfgYaml as Cfg
from dotdrop.options import Options
from dotdrop.linktypes import LinkTypes
from tests.helpers import (SubsetTestCase, _fake_args, clean,
                           create_fake_config, create_yaml_keyval, get_tempdir,
                           populate_fake_config, yaml_load, yaml_dump)


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
        conf = Cfg(confpath, debug=True)
        self.assertTrue(conf is not None)

        opts = conf.settings
        self.assertTrue(opts is not None)
        self.assertTrue(opts != {})
        self.assertTrue(opts['backup'] == self.CONFIG_BACKUP)
        self.assertTrue(opts['create'] == self.CONFIG_CREATE)
        dpath = os.path.basename(opts['dotpath'])
        self.assertTrue(dpath == self.CONFIG_DOTPATH)
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
        args['--verbose'] = True
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
        args['--verbose'] = True

        with self.assertRaises(ValueError):
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
        content = yaml_load(confpath)

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
        yaml_dump(content, confpath)

        # do the tests
        conf = Cfg(confpath, debug=True)
        self.assertTrue(conf is not None)

        # test profile
        profiles = conf.profiles
        self.assertTrue(pf1key in profiles)
        self.assertTrue(pf2key in profiles)

        # test dotfiles
        dotfiles = conf.profiles[pf1key]['dotfiles']
        self.assertTrue(df1key in dotfiles)
        self.assertTrue(df2key in dotfiles)
        dotfiles = conf.profiles[pf2key]['dotfiles']
        self.assertTrue(df1key in dotfiles)
        self.assertFalse(df2key in dotfiles)

        # test not existing included profile
        # edit the config
        content = yaml_load(confpath)
        content['profiles'] = {
                pf1key: {'dotfiles': [df2key], 'include': ['host2']},
                pf2key: {'dotfiles': [df1key], 'include': ['host3']}
                }

        # save the new config
        yaml_dump(content, confpath)

        # do the tests
        conf = Cfg(confpath, debug=True)
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
            'actions': {
                'pre': {
                    'a_pre_action_ed': 'echo pre 22',
                },
                'post': {
                    'a_post_action_ed': 'echo post 22',
                },
                'a_action_ed': 'echo 22',
            }
        }
        actions_ing = {
            'actions': {
                'pre': {
                    'a_pre_action_ing': 'echo pre aa',
                },
                'post': {
                    'a_post_action_ing': 'echo post aa',
                },
                'a_action_ing': 'echo aa',
            }
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
                                            import_configs=[
                                                self.CONFIG_NAME_2
                                            ],
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
        importing_cfg = Cfg(importing_path, debug=True)
        imported_cfg = Cfg(imported_path, debug=True)
        self.assertIsNotNone(importing_cfg)
        self.assertIsNotNone(imported_cfg)

        # test profiles
        self.assertIsSubset(imported_cfg.profiles,
                            importing_cfg.profiles)

        # test dotfiles
        self.assertIsSubset(imported_cfg.dotfiles, importing_cfg.dotfiles)

        # test actions
        pre_ed = post_ed = pre_ing = post_ing = {}
        for k, v in imported_cfg.actions.items():
            kind, _ = v
            if kind == 'pre':
                pre_ed[k] = v
            elif kind == 'post':
                post_ed[k] = v
        for k, v in importing_cfg.actions.items():
            kind, _ = v
            if kind == 'pre':
                pre_ing[k] = v
            elif kind == 'post':
                post_ing[k] = v
        self.assertIsSubset(pre_ed, pre_ing)
        self.assertIsSubset(post_ed, post_ing)

        # test transactions
        self.assertIsSubset(imported_cfg.trans_r, importing_cfg.trans_r)
        self.assertIsSubset(imported_cfg.trans_w, importing_cfg.trans_w)

        # test variables
        imported_vars = {
            k: v
            for k, v in imported_cfg.variables.items()
            if not k.startswith('_')
        }
        importing_vars = {
            k: v
            for k, v in importing_cfg.variables.items()
            if not k.startswith('_')
        }
        self.assertIsSubset(imported_vars, importing_vars)

        # test prodots
        self.assertIsSubset(imported_cfg.profiles, importing_cfg.profiles)

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
            'actions': {
                'pre': {
                    'a_pre_action': 'echo pre 22',
                },
                'post': {
                    'a_post_action': 'echo post 22',
                },
                'a_action': 'echo 22',
            }
        }
        actions_ing = {
            'actions': {
                'pre': {
                    'a_pre_action': 'echo pre aa',
                },
                'post': {
                    'a_post_action': 'echo post aa',
                },
                'a_action': 'echo aa',
            }
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
        importing_cfg = Cfg(importing_path, debug=True)
        imported_cfg = Cfg(imported_path, debug=True)
        self.assertIsNotNone(importing_cfg)
        self.assertIsNotNone(imported_cfg)

        # test profiles
        self.assertIsSubset(imported_cfg.profiles,
                            importing_cfg.profiles)

        # test dotfiles
        self.assertEqual(importing_cfg.dotfiles['f_vimrc'],
                         imported_cfg.dotfiles['f_vimrc'])
        self.assertNotEqual(importing_cfg.dotfiles['f_xinitrc'],
                            imported_cfg.dotfiles['f_xinitrc'])

        # test actions
        self.assertFalse(any(
            (imported_cfg.actions[key]
                == importing_cfg.actions[key])
            for key in imported_cfg.actions
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
        # since variables get merged they are
        # the same in both configs
        imported_vars = imported_cfg.variables
        self.assertFalse(any(
            imported_vars[k] != v
            for k, v in importing_cfg.variables.items()
            if not k.startswith('_')
        ))

        # test profiles dotfiles
        self.assertEqual(imported_cfg.profiles['host1']['dotfiles'],
                         importing_cfg.profiles['host1']['dotfiles'])
        self.assertNotEqual(imported_cfg.profiles['host2']['dotfiles'],
                            importing_cfg.profiles['host2']['dotfiles'])
        self.assertTrue(set(imported_cfg.profiles['host1']['dotfiles'])
                        < set(importing_cfg.profiles['host2']['dotfiles']))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
