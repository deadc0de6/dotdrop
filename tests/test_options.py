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


class FakeOptions(Options):
    """fake Options class"""

    def __init__(self, args):
        """init"""
        self.args = args
        self.log = Logger(debug=True)


class TestOptions(unittest.TestCase):
    """test case"""

    def clean_setup(self):
        """clean stuff"""
        if 'DOTDROP_CONFIG' in os.environ:
            del os.environ['DOTDROP_CONFIG']
        if 'XDG_CONFIG_HOME' in os.environ:
            del os.environ['XDG_CONFIG_HOME']

    def _get_args(self, more):
        args = {
            '--dry': False,
            '--verbose': True,
            '--cfg': '',
        }
        for k, val in more.items():
            args[k] = val
        return args

    def side_effect(self, valid=''):
        """side effect for os.path.exists"""
        def inner(filename):
            print(f'checking if {filename} exists')
            if filename == valid:
                return True
            return False
        return inner

    def test_get_path_from_cli(self):
        """from --cli"""
        self.clean_setup()
        expected = 'fakepath'
        args = {}
        args['--cfg'] = expected
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    def test_get_path_from_env(self):
        """from env"""
        self.clean_setup()
        expected = 'envpath'
        os.environ['DOTDROP_CONFIG'] = expected
        args = self._get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_from_yaml(self, mock_exists):
        """from yaml"""
        self.clean_setup()
        mock_exists.return_value = True
        expected = 'config.yaml'
        args = self._get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_from_toml(self, mock_exists):
        """from toml"""
        self.clean_setup()
        expected = 'config.toml'
        args = self._get_args({'--cfg': ''})
        mock_exists.side_effect = self.side_effect(valid=expected)
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_xdg_yaml(self, mock_exists):
        """from xdg"""
        self.clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.yaml'
        mock_exists.side_effect = self.side_effect(valid=expected)
        log = Logger(debug=True)
        log.dbg(f'expected: {expected}')
        args = self._get_args({'--cfg': ''})
        os.environ['XDG_CONFIG_HOME'] = home
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_xdg_toml(self, mock_exists):
        """from xdg toml"""
        self.clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = self.side_effect(valid=expected)
        log = Logger(debug=True)
        log.dbg(f'expected: {expected}')
        args = self._get_args({'--cfg': ''})
        os.environ['XDG_CONFIG_HOME'] = home
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_yaml(self, mock_exists):
        """from fs yaml"""
        self.clean_setup()
        home = os.path.expanduser('~/.config')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = self.side_effect(valid=expected)
        log = Logger(debug=True)
        log.dbg(f'expected: {expected}')
        args = self._get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_xdg(self, mock_exists):
        """from fs xdg"""
        self.clean_setup()
        home = os.path.expanduser('/etc/xdg')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = self.side_effect(valid=expected)
        log = Logger(debug=True)
        log.dbg(f'expected: {expected}')
        args = self._get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)

    @patch('os.path.exists')
    def test_get_path_fs_etc(self, mock_exists):
        """from fs etc"""
        self.clean_setup()
        home = os.path.expanduser('/etc')
        expected = f'{home}/dotdrop/config.toml'
        mock_exists.side_effect = self.side_effect(valid=expected)
        log = Logger(debug=True)
        log.dbg(f'expected: {expected}')
        args = self._get_args({'--cfg': ''})
        fake = FakeOptions(args)
        self.assertEqual(fake._get_config_path(), expected)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
