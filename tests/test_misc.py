"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6
basic unittest for misc stuff
"""

# pylint: disable=R0903
# pylint: disable=W0231
# pylint: disable=W0212

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch
from jinja2 import TemplateNotFound
from dotdrop.profile import Profile
from dotdrop.importer import Importer
from dotdrop.linktypes import LinkTypes
from dotdrop.action import Cmd, Transform
from dotdrop.dotfile import Dotfile
from dotdrop.installer import Installer
from dotdrop.updater import Updater
from dotdrop.uninstaller import Uninstaller
from dotdrop.templategen import Templategen
from dotdrop.exceptions import UndefinedException, \
    UnmetDependency
from dotdrop.dotdrop import apply_install_trans
from dotdrop.utils import removepath, samefile, \
    content_empty, _match_ignore_pattern, \
    get_module_from_path, dependencies_met, \
    dir_empty
from tests.helpers import create_random_file, \
    get_tempdir, clean, edit_content


class TestUtils(unittest.TestCase):
    """test case"""

    def test_removepath(self):
        """test removepath"""
        removepath('')
        with self.assertRaises(OSError):
            removepath('/abc')
        with self.assertRaises(OSError):
            removepath(os.path.expanduser('~'))

    def test_dirempty(self):
        """dir_empty"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)

        self.assertTrue(dir_empty('/a/b/c/d/e'))
        self.assertTrue(dir_empty(tmpdir))
        path1, _ = create_random_file(tmpdir, content='left')
        self.assertTrue(dir_empty(path1))

    def test_misc(self):
        """misc test"""
        self.assertFalse(samefile('', ''))
        self.assertTrue(content_empty(b'\n'))
        self.assertTrue(_match_ignore_pattern('', '', debug=True))
        self.assertEqual(get_module_from_path(None), None)

    def test_dependencies_met(self):
        """dependencies met"""
        oimport = __import__

        def prepare_import_mock(keywords):
            def import_mock(name, *args):
                if name in keywords:
                    raise ImportError
                return oimport(name, *args)
            return import_mock

        # with self.assertRaises(UnmetDependency):
        #     with patch('builtins.__import__',
        #                side_effect=prepare_import_mock(
        #                    ['magic', 'python-magic'])
        #                ):
        #         dependencies_met()

        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['docopt'])):
                dependencies_met()

        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['jinja2'])):
                dependencies_met()

        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['ruamel.yaml'])):
                dependencies_met()

        orig = sys.version_info
        sys.version_info = (3, 10)
        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['tomli'])):
                dependencies_met()
        sys.version_info = orig

        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['tomli_w'])):
                dependencies_met()

        with self.assertRaises(UnmetDependency):
            with patch('builtins.__import__',
                       side_effect=prepare_import_mock(['distro'])):
                dependencies_met()


class TestDotdropDotdrop(unittest.TestCase):
    """test case"""

    def test_apply_install_trans(self):
        """ensure transformation fails if destination exists"""
        dotpath = get_tempdir()
        self.addCleanup(clean, dotpath)

        src, _ = create_random_file(dotpath, content='left')
        dst, _ = create_random_file(dotpath, content='left')
        new_src = f'{src}.trans'
        edit_content(new_src, 'some_content')

        trans = Transform('somekey', 'echo')
        dotf = Dotfile('key', dst, os.path.relpath(src, dotpath))
        dotf.trans_install = trans
        self.assertIsNone(apply_install_trans(
            dotpath,
            dotf,
            templater=None,
            debug=True,
        ))


class TestUpdater(unittest.TestCase):
    """test case"""

    def test_update_path(self):
        """coverage for update_path"""
        upd = Updater('path', {}, None, 'profile')
        self.assertFalse(upd.update_path('/a/b/c/d'))


class TestInstaller(unittest.TestCase):
    """test case"""

    def test_show_diff_before_write(self):
        """coverage for _show_diff_before_write"""
        inst = Installer()

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)

        path1, _ = create_random_file(tmpdir, content='left')
        path2, _ = create_random_file(tmpdir, content='right')
        self.assertIsNotNone(inst._show_diff_before_write(
            path1,
            path2,
            content=b'blah'
        ))

        path3, _ = create_random_file(tmpdir, content='left')
        path4, _ = create_random_file(tmpdir, content='left')
        self.assertEqual(inst._show_diff_before_write(
            path3,
            path4,
        ), '')

    def test_show_diff(self):
        """coverage for _print_diff"""
        inst = Installer()
        self.assertIsNone(inst._print_diff(
            "left",
            "right",
            "diff",
        ))

    def test_check_paths(self):
        """coverage for _check_paths"""
        inst = Installer()
        ret1, ret2, ret3, ret4 = inst._check_paths(None, None)
        self.assertIsNone(ret1)
        self.assertIsNone(ret2)
        self.assertFalse(ret3)
        self.assertIsNotNone(ret4)


class TestUninstaller(unittest.TestCase):
    """test case"""

    def test_uninstall(self):
        """coverage for uninstall()"""
        uninst = Uninstaller()
        ret1, ret2 = uninst.uninstall(None, None, None)
        self.assertTrue(ret1)
        self.assertIsNone(ret2)

        ret1, ret2 = uninst.uninstall('a/b/c', 'd/e/f', None)
        self.assertFalse(ret1)
        self.assertIsNotNone(ret2)

        ret1, ret2 = uninst._remove_path('a/b/c')
        self.assertTrue(ret1)
        self.assertIsNotNone(ret2)


class TestImporter(unittest.TestCase):
    """test case"""

    @patch('sys.stdin', StringIO('y\n'))
    def test_generic(self):
        """test importer"""
        with self.assertRaises(UndefinedException):
            Importer('', None, '', '', {})

        imp = Importer('profile', None, '', '', {})
        self.assertEqual(imp.import_path('/abc'), -1)

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        path1, _ = create_random_file(tmpdir, content='left')
        path2, _ = create_random_file(tmpdir, content='right')
        imp.safe = True
        self.assertTrue(imp._check_existing_dotfile(path1, path2))
        path2, _ = create_random_file(tmpdir, content='left')
        self.assertTrue(imp._check_existing_dotfile(path1, path2))

    def test_apply_trans(self):
        """test apply_trans"""
        trans = Transform('key', 'value')
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        path, _ = create_random_file(tmpdir)

        imp = Importer('profile', None, '', '', {})
        self.assertEqual(imp._apply_trans_update(path, trans), None)


class TestActions(unittest.TestCase):
    """test case"""

    def test_cmd(self):
        """test action"""
        badstring = '{{@@ non-existing-var @@}}'
        cmd = Cmd('key', badstring)
        tmpl = Templategen()
        self.assertFalse(cmd._get_action(tmpl, False))

        cmd.args = [badstring]
        self.assertFalse(cmd._get_args(tmpl))

    def test_args(self):
        """test arg parameters"""
        cmd = Cmd('key', '{0} {1}')
        cmd.args = ['arg1']
        self.assertFalse(cmd.execute())

        cmd = Cmd('key', '{0}')
        cmd.args = ['arg1', 'arg2']
        self.assertFalse(cmd.execute())

    def test_trans(self):
        """test trans"""
        trans = Transform('key', 'value')
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        path, _ = create_random_file(tmpdir)
        self.assertFalse(trans.transform('', path))


class TestTemplateGen(unittest.TestCase):
    """test case"""

    def test_misc(self):
        """test misc"""
        tmpl = Templategen()
        self.assertFalse(tmpl.path_is_template('/abc'))
        self.assertFalse(tmpl._is_template('/abc'))
        tmpl._debug_dict('a', 'b')

    def test_lodaer(self):
        """test loading template"""
        tmpl = Templategen()
        with self.assertRaises(TemplateNotFound):
            tmpl._template_loader('/abc')

    def test_is_text(self):
        """test is_text"""
        self.assertTrue(Templategen._is_text('empty'))
        self.assertTrue(Templategen._is_text('json'))
        self.assertTrue(Templategen._is_text('javascript'))
        self.assertTrue(Templategen._is_text('ecmascript'))
        self.assertTrue(Templategen._is_text('text'))
        self.assertFalse(Templategen._is_text('binary'))

    def test_handle_bin_file(self):
        """test handle binary file"""
        tmpl = Templategen()

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        content = b'abc'
        path, _ = create_random_file(tmpdir, content=content, binary=True)

        cont = tmpl._handle_file(path)
        self.assertEqual(content, cont)

    def test_filetype(self):
        """test using file instead of magic"""
        oimport = __import__

        def import_mock(name, *args):
            if name == 'magic':
                raise ImportError
            return oimport(name, *args)

        with patch('builtins.__import__',
                   side_effect=import_mock):
            tmpdir = get_tempdir()
            self.addCleanup(clean, tmpdir)
            content = 'abc'
            path, _ = create_random_file(tmpdir, content=content)

            tmpl = Templategen()
            self.assertTrue('text' in tmpl._get_filetype(path))

    def test_generate(self):
        """test generate"""
        tmpl = Templategen()
        self.assertEqual(tmpl.generate('/abc'), '')

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        content = '{{@@ non-existing-var @@}}'
        path, _ = create_random_file(tmpdir, content=content)
        with self.assertRaises(UndefinedException):
            tmpl.generate(path)

        fakestring = None
        self.assertEqual(tmpl.generate_string(fakestring), '')
        fakestring = '{{@@ non-existing-var @@}}'
        with self.assertRaises(UndefinedException):
            tmpl.generate_string(fakestring)

        fakedict = None
        self.assertEqual(tmpl.generate_dict(fakedict), None)
        fakedict = {'key': {
            'subkey', fakestring,
        }}
        tmpl.generate_dict(fakedict)

        with self.assertRaises(UndefinedException):
            tmpl.generate_string_or_dict(2)

        tmpdir2 = get_tempdir()
        self.addCleanup(clean, tmpdir2)
        adic = {}
        path, _ = create_random_file(tmpdir, content='blah')
        with self.assertRaises(NameError):
            tmpl._load_path_to_dic(path, adic)

        tmpl._load_funcs_to_dic(None, None)


class TestLinkTypes(unittest.TestCase):
    """test case"""

    def test_exc(self):
        """test exception"""
        with self.assertRaises(ValueError):
            LinkTypes.get('whatever')
        with self.assertRaises(ValueError):
            LinkTypes.get('whatever', default="something-else")


class TestProfile(unittest.TestCase):
    """test case"""

    def test_hash(self):
        """test profile hash"""
        pro = Profile('some-profile')
        self.assertIsNotNone(hash(pro))

    def test_repr(self):
        """test profile repr"""
        name = 'profile-name'
        pro = Profile(name)
        expected = f'profile(key:"{name}")'
        self.assertEqual(repr(pro), expected)

    def test_eq(self):
        """test profile eq"""
        p1_name = 'profile-1'
        pro1 = Profile(p1_name, dotfiles=['abc'])
        p2_name = 'profile-2'
        pro2 = Profile(p2_name)
        p3_name = p1_name
        pro3 = Profile(p3_name, dotfiles=['abc'])
        p4_name = p1_name
        pro4 = Profile(p4_name, dotfiles=['ab'])
        self.assertNotEqual(pro1, pro2)
        self.assertEqual(pro1, pro3)
        self.assertNotEqual(pro1, pro4)
        self.assertNotEqual(pro3, pro4)


def main():
    """entry point"""
    unittest.main()


if __name__ == '__main__':
    main()
