"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the import function
"""


import unittest
import os

from dotdrop.dotdrop import cmd_importer
from dotdrop.dotdrop import cmd_list_profiles
from dotdrop.dotdrop import cmd_list_files
from dotdrop.dotdrop import cmd_update
from dotdrop.linktypes import LinkTypes

from tests.helpers import (clean, create_dir, create_fake_config,
                           create_random_file, edit_content, file_in_yaml,
                           get_path_strip_version, get_string, get_tempdir,
                           load_options, populate_fake_config,
                           yaml_load)


class TestImport(unittest.TestCase):

    CONFIG_BACKUP = False
    CONFIG_CREATE = True
    CONFIG_DOTPATH = 'dotfiles'
    CONFIG_NAME = 'config.yaml'

    def load_yaml(self, path):
        """Load yaml to dict"""
        self.assertTrue(os.path.exists(path))
        return yaml_load(path)

    def assert_file(self, path, o, profile):
        """Make sure path has been inserted in conf for profile"""
        strip = get_path_strip_version(path)
        self.assertTrue(any(x.src.endswith(strip) for x in o.dotfiles))
        dsts = (os.path.expanduser(x.dst) for x in o.dotfiles)
        self.assertTrue(path in dsts)

    def assert_in_yaml(self, path, dic, link=False):
        """Make sure "path" is in the "dic" representing the yaml file"""
        self.assertTrue(file_in_yaml(dic, path, link=link))

    def test_import(self):
        """Test the import function"""
        # on filesystem
        src = get_tempdir()
        self.assertTrue(os.path.exists(src))
        self.addCleanup(clean, src)

        # in dotdrop
        dotfilespath = get_tempdir()
        self.assertTrue(os.path.exists(dotfilespath))
        self.addCleanup(clean, dotfilespath)

        profile = get_string(10)
        confpath = create_fake_config(dotfilespath,
                                      configname=self.CONFIG_NAME,
                                      dotpath=self.CONFIG_DOTPATH,
                                      backup=self.CONFIG_BACKUP,
                                      create=self.CONFIG_CREATE)
        self.assertTrue(os.path.exists(confpath))
        o = load_options(confpath, profile)

        # create some random dotfiles
        dotfile1, content1 = create_random_file(src)
        self.addCleanup(clean, dotfile1)
        dotfile2, content2 = create_random_file(os.path.expanduser('~'))
        self.addCleanup(clean, dotfile2)
        homeconf = os.path.join(os.path.expanduser('~'), '.config')
        if not os.path.exists(homeconf):
            os.mkdir(homeconf)
            self.addCleanup(clean, homeconf)
        dotconfig = os.path.join(homeconf, get_string(5))
        create_dir(dotconfig)
        self.addCleanup(clean, dotconfig)
        dotfile3, content3 = create_random_file(dotconfig)
        dotfile4, content3 = create_random_file(homeconf)
        self.addCleanup(clean, dotfile4)

        # fake a directory containing dotfiles
        dotfile5 = get_tempdir()
        self.assertTrue(os.path.exists(dotfile5))
        self.addCleanup(clean, dotfile5)
        sub1, _ = create_random_file(dotfile5)
        sub2, _ = create_random_file(dotfile5)

        # fake a file for symlink
        dotfile6, content6 = create_random_file(dotconfig)
        self.addCleanup(clean, dotfile6)

        # fake a directory for symlink
        dotfile7 = get_tempdir()
        self.assertTrue(os.path.exists(dotfile7))
        self.addCleanup(clean, dotfile7)
        sub3, _ = create_random_file(dotfile7)
        sub4, _ = create_random_file(dotfile7)

        # import the dotfiles
        dfiles = [dotfile1, dotfile2, dotfile3, dotfile4, dotfile5]
        o.import_path = dfiles
        cmd_importer(o)
        # import symlink
        o.import_link = LinkTypes.LINK
        sfiles = [dotfile6, dotfile7]
        o.import_path = sfiles
        cmd_importer(o)
        o.import_link = LinkTypes.NOLINK

        # reload the config
        o = load_options(confpath, profile)

        # test dotfiles in config class
        self.assertTrue(profile in [p.key for p in o.profiles])
        self.assert_file(dotfile1, o, profile)
        self.assert_file(dotfile2, o, profile)
        self.assert_file(dotfile3, o, profile)
        self.assert_file(dotfile4, o, profile)
        self.assert_file(dotfile5, o, profile)
        self.assert_file(dotfile6, o, profile)
        self.assert_file(dotfile7, o, profile)

        # test dotfiles in yaml file
        y = self.load_yaml(confpath)
        self.assert_in_yaml(dotfile1, y)
        self.assert_in_yaml(dotfile2, y)
        self.assert_in_yaml(dotfile3, y)
        self.assert_in_yaml(dotfile4, y)
        self.assert_in_yaml(dotfile5, y)
        self.assert_in_yaml(dotfile6, y, link=True)
        self.assert_in_yaml(dotfile7, y, link=True)

        # test have been imported in dotdrop dotpath directory
        indt1 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile1))
        self.assertTrue(os.path.exists(indt1))
        indt2 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile2))
        self.assertTrue(os.path.exists(indt2))
        indt3 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile3))
        self.assertTrue(os.path.exists(indt3))
        indt4 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile4))
        self.assertTrue(os.path.exists(indt4))
        indt5 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile5))
        self.assertTrue(os.path.exists(indt5))
        s1 = os.path.join(dotfilespath,
                          self.CONFIG_DOTPATH,
                          get_path_strip_version(dotfile6),
                          sub1)
        self.assertTrue(os.path.exists(s1))
        s2 = os.path.join(dotfilespath,
                          self.CONFIG_DOTPATH,
                          get_path_strip_version(dotfile6),
                          sub2)
        self.assertTrue(os.path.exists(s2))
        indt6 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile6))
        self.assertTrue(os.path.exists(indt6))
        indt7 = os.path.join(dotfilespath,
                             self.CONFIG_DOTPATH,
                             get_path_strip_version(dotfile7))
        self.assertTrue(os.path.exists(indt7))
        s3 = os.path.join(dotfilespath,
                          self.CONFIG_DOTPATH,
                          get_path_strip_version(dotfile7),
                          sub3)
        self.assertTrue(os.path.exists(s3))
        s4 = os.path.join(dotfilespath,
                          self.CONFIG_DOTPATH,
                          get_path_strip_version(dotfile7),
                          sub4)
        self.assertTrue(os.path.exists(s4))

        cmd_list_profiles(o)
        cmd_list_files(o)

        # fake test update
        editcontent = 'edited'
        edit_content(dotfile1, editcontent)
        o.safe = False
        o.update_path = [dotfile1]
        o.debug = True
        cmd_update(o)
        c2 = open(indt1, 'r').read()
        self.assertTrue(editcontent == c2)

    def test_ext_config_yaml_not_mix(self):
        """Test whether the import_configs mixes yaml files upon importing."""
        # dotfiles on filesystem
        src = get_tempdir()
        self.assertTrue(os.path.exists(src))
        self.addCleanup(clean, src)

        # create some random dotfiles
        dotfiles = []
        for _ in range(3):
            dotfile, _ = create_random_file(src)
            dotfiles.append(dotfile)
            self.addCleanup(clean, dotfile)
        self.assertTrue(all(map(os.path.exists, dotfiles)))

        # create dotdrop home
        dotdrop_home = get_tempdir()
        self.assertTrue(os.path.exists(dotdrop_home))
        self.addCleanup(clean, dotdrop_home)

        dotpath_ed = 'imported'
        imported = {
            'config': {
                'dotpath': dotpath_ed,
            },
            'dotfiles': {},
            'profiles': {
                'host1': {
                    'dotfiles': [],
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
        dotpath_ing = 'importing'
        importing = {
            'config': {
                'dotpath': dotpath_ing,
            },
            'dotfiles': {},
            'profiles': {
                'host2': {
                    'dotfiles': [],
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

        dotfiles_ing, dotfiles_ed = dotfiles[:-1], dotfiles[-1:]

        # create the imported base config file
        imported_path = create_fake_config(dotdrop_home,
                                           configname='config-2.yaml',
                                           **imported['config'])
        # create the importing base config file
        importing_path = create_fake_config(dotdrop_home,
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

        # import the dotfiles
        o = load_options(imported_path, 'host1')
        o.import_path = dotfiles_ed
        cmd_importer(o)

        o = load_options(importing_path, 'host2')
        o.import_path = dotfiles_ing
        cmd_importer(o)

        # reload the config
        o = load_options(importing_path, 'host2')

        # test imported config
        y = self.load_yaml(imported_path)

        # testing dotfiles
        self.assertTrue(all(file_in_yaml(y, df)
                            for df in dotfiles_ed))
        self.assertFalse(any(file_in_yaml(y, df)
                             for df in dotfiles_ing))

        # testing profiles
        profiles = y['profiles'].keys()
        self.assertTrue('host1' in profiles)
        self.assertFalse('host2' in profiles)

        # testing actions
        actions = y['actions']['pre']
        actions.update(y['actions']['post'])
        actions.update({
            k: v
            for k, v in y['actions'].items()
            if k not in ('pre', 'post')
        })
        actions = actions.keys()
        self.assertTrue(all(a.endswith('ed') for a in actions))
        self.assertFalse(any(a.endswith('ing') for a in actions))

        # testing transformations
        transformations = y['trans_read'].keys()
        self.assertTrue(all(t.endswith('ed') for t in transformations))
        self.assertFalse(any(t.endswith('ing') for t in transformations))
        transformations = y['trans_write'].keys()
        self.assertTrue(all(t.endswith('ed') for t in transformations))
        self.assertFalse(any(t.endswith('ing') for t in transformations))

        # testing variables
        variables = self._remove_priv_vars(y['variables'].keys())
        self.assertTrue(all(v.endswith('ed') for v in variables))
        self.assertFalse(any(v.endswith('ing') for v in variables))
        dyn_variables = y['dynvariables'].keys()
        self.assertTrue(all(dv.endswith('ed') for dv in dyn_variables))
        self.assertFalse(any(dv.endswith('ing') for dv in dyn_variables))

        # test importing config
        y = self.load_yaml(importing_path)

        # testing dotfiles
        self.assertTrue(all(file_in_yaml(y, df)
                            for df in dotfiles_ing))
        self.assertFalse(any(file_in_yaml(y, df)
                             for df in dotfiles_ed))

        # testing profiles
        profiles = y['profiles'].keys()
        self.assertTrue('host2' in profiles)
        self.assertFalse('host1' in profiles)

        # testing actions
        actions = y['actions']['pre']
        actions.update(y['actions']['post'])
        actions.update({
            k: v
            for k, v in y['actions'].items()
            if k not in ('pre', 'post')
        })
        actions = actions.keys()
        self.assertTrue(all(action.endswith('ing') for action in actions))
        self.assertFalse(any(action.endswith('ed') for action in actions))

        # testing transformations
        transformations = y['trans_read'].keys()
        self.assertTrue(all(t.endswith('ing') for t in transformations))
        self.assertFalse(any(t.endswith('ed') for t in transformations))
        transformations = y['trans_write'].keys()
        self.assertTrue(all(t.endswith('ing') for t in transformations))
        self.assertFalse(any(t.endswith('ed') for t in transformations))

        # testing variables
        variables = self._remove_priv_vars(y['variables'].keys())
        self.assertTrue(all(v.endswith('ing') for v in variables))
        self.assertFalse(any(v.endswith('ed') for v in variables))
        dyn_variables = y['dynvariables'].keys()
        self.assertTrue(all(dv.endswith('ing') for dv in dyn_variables))
        self.assertFalse(any(dv.endswith('ed') for dv in dyn_variables))

    def _remove_priv_vars(self, variables_keys):
        variables = [v for v in variables_keys if not v.startswith('_')]
        if 'profile' in variables:
            variables.remove('profile')
        return variables


def main():
    unittest.main()


if __name__ == '__main__':
    main()
