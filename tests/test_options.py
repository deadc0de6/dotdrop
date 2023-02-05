"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
basic unittest for the install function
"""

# pylint: disable=R0903
# pylint: disable=W0231
# pylint: disable=W0212

import os
import unittest
from unittest.mock import patch
from dotdrop.options import Options, Logger
from dotdrop.exceptions import YamlException


class FakeOptions(Options):
    """fake Options class"""

    def __init__(self, args):
        """init"""
        self.args = args
        self.log = Logger(debug=True)


def clean_setup():
    """clean stuff"""
    if 'DOTDROP_CONFIG' in os.environ:
        del os.environ['DOTDROP_CONFIG']
    if 'XDG_CONFIG_HOME' in os.environ:
        del os.environ['XDG_CONFIG_HOME']


def get_args(more):
    """return args dict"""
    args = {
        '--dry': False,
        '--verbose': True,
        '--cfg': '',
    }
    for k, val in more.items():
        args[k] = val
    return args


def side_effect(valid=''):
    """side effect for os.path.exists"""
    def inner(filename):
        print(f'checking if {filename} exists')
        if filename == valid:
            return True
        return False
    return inner


class TestOptions(unittest.TestCase):
    """test case"""

    def test_get_path_from_cli(self):
        """from --cli"""
        clean_setup()
        expected = 'fakepath'
        args = {}
        args['--cfg'] = expected
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    def test_get_path_from_env(self):
        """from env"""
        clean_setup()
        expected = 'envpath'
        os.environ['DOTDROP_CONFIG'] = expected
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_from_yaml(self, mock_exists):
        """from yaml"""
        clean_setup()
        mock_exists.return_value = True
        expected = 'config.yaml'
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_from_toml(self, mock_exists):
        """from toml"""
        clean_setup()
        expected = 'config.toml'
        args = get_args({'--cfg': ''})
        mock_exists.side_effect = side_effect(valid=expected)
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_xdg_yaml(self, mock_exists):
        """from xdg"""
        clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        os.environ['XDG_CONFIG_HOME'] = home
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_xdg_toml(self, mock_exists):
        """from xdg toml"""
        clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        os.environ['XDG_CONFIG_HOME'] = home
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_xdg_yaml(self, mock_exists):
        """from fs yaml"""
        clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_xdg_etc_yaml(self, mock_exists):
        """from fs xdg"""
        clean_setup()
        home = os.path.expanduser('/etc/xdg')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_etc_dotdrop_yaml(self, mock_exists):
        """from fs etc"""
        clean_setup()
        home = os.path.expanduser('/etc')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_etc_xdg_yaml(self, mock_exists):
        """from fs etc/xdg"""
        clean_setup()
        home = os.path.expanduser('/etc/xdg')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_xdg_toml(self, mock_exists):
        """from fs toml"""
        clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_xdg_etc_toml(self, mock_exists):
        """from fs xdg"""
        clean_setup()
        home = os.path.expanduser('/etc/xdg')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_etc_dotdrop_toml(self, mock_exists):
        """from fs etc"""
        clean_setup()
        home = os.path.expanduser('/etc')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_etc_xdg_toml(self, mock_exists):
        """from fs etc/xdg"""
        clean_setup()
        home = os.path.expanduser('/etc/xdg')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = side_effect(valid=expected)
        args = get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_none(self, mock_exists):
        """path is none"""
        clean_setup()
        mock_exists.return_value = False
        args = get_args({})
        fake = FakeOptions(args)
        self.assertEqual(None, fake._get_config_path())

    @patch('os.path.exists')
    def test_options_debug(self, mock_exists):
        """test debug"""
        mock_exists.return_value = False
        args = {
            '--verbose': True,
            '--dry': False,
            '--cfg': 'path',
            '--profile': 'profile',
        }
        with self.assertRaises(YamlException):
            Options(args)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
