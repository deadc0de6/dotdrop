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
import stat
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock
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
    dir_empty, get_tmpdir, _cp, mirror_file_rights, \
    adapt_workers, check_version, is_bin_in_path, \
    ignores_to_absolute
from tests.helpers import create_random_file, \
    get_tempdir, clean, edit_content


class TestUtils(unittest.TestCase):
    """test case"""

    def test_removepath(self):
        """test removepath"""
        removepath('')

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        afile, _ = create_random_file(tmpdir, content='blah')

        try:
            removepath(afile)
        except OSError:
            self.fail('must not raise OSError')
        if os.path.exists(afile):
            self.fail(f'{afile} not deleted')
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


class TestUtilsExtra(unittest.TestCase):
    """test case for additional utils coverage"""

    def test_get_tmpdir_oserror(self):
        """get_tmpdir falls back when DOTDROP_TMPDIR is invalid"""
        # point DOTDROP_TMPDIR at a file (not a dir) -> OSError -> fallback
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        afile, _ = create_random_file(tmpdir, content='x')
        with patch.dict(os.environ, {'DOTDROP_TMPDIR': afile}):
            result = get_tmpdir()
            self.assertTrue(os.path.isdir(result))

    def test_removepath_noremove_with_logger(self):
        """removepath on NOREMOVE path with logger returns False"""
        logger = MagicMock()
        self.assertFalse(removepath(os.path.expanduser('~'), logger=logger))

    def test_removepath_unsupported_filetype(self):
        """removepath on a special file (FIFO) raises/handled"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        fifo = os.path.join(tmpdir, 'myfifo')
        os.mkfifo(fifo)
        # without logger: OSError is re-raised from the unsupported branch
        with self.assertRaises(OSError):
            removepath(fifo)
        # with logger: returns False and warns
        logger = MagicMock()
        self.assertFalse(removepath(fifo, logger=logger))

    def test_cp_ignore_and_special(self):
        """_cp ignore func and special file branches"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        src, _ = create_random_file(tmpdir, content='data')
        dst = os.path.join(tmpdir, 'out', 'copied')

        # ignore_func returns True -> 0 copied
        self.assertEqual(_cp(src, dst, ignore_func=lambda _s: True), 0)

        # non-file src (a directory) with debug -> 0 copied
        sub = os.path.join(tmpdir, 'subdir')
        os.mkdir(sub)
        self.assertEqual(_cp(sub, os.path.join(tmpdir, 'x', 'y'), debug=True),
                         0)

    def test_cp_copy_fails(self):
        """_cp returns 0 when resulting file does not exist"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        src, _ = create_random_file(tmpdir, content='data')
        # patch shutil.copy2 to return a non-existing path
        with patch('dotdrop.utils.shutil.copy2', return_value='/nope'):
            self.assertEqual(_cp(src, os.path.join(tmpdir, 'out', 'c')), 0)

    def test_ignores_to_absolute_negative_absolute(self):
        """ignores_to_absolute with negative absolute pattern"""
        result = ignores_to_absolute(['!/etc/passwd'], ['/home'])
        self.assertEqual(result, ['!/etc/passwd'])

    def test_mirror_file_rights_missing(self):
        """mirror_file_rights with missing src/dst is a no-op"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        # neither exists -> returns None
        self.assertIsNone(mirror_file_rights(
            os.path.join(tmpdir, 'nope1'),
            os.path.join(tmpdir, 'nope2')))

    def test_adapt_workers(self):
        """adapt_workers reduces workers when safe or dry"""
        opts = MagicMock()
        logger = MagicMock()
        opts.safe = True
        opts.dry = False
        opts.workers = 4
        adapt_workers(opts, logger)
        self.assertEqual(opts.workers, 1)

        opts.safe = False
        opts.dry = True
        opts.workers = 4
        adapt_workers(opts, logger)
        self.assertEqual(opts.workers, 1)

        # no reduction when workers == 1
        opts.dry = False
        opts.workers = 1
        adapt_workers(opts, logger)
        self.assertEqual(opts.workers, 1)

    def test_check_version_failures(self):
        """check_version handles request failures gracefully"""
        import requests as req
        # request raises
        with patch('dotdrop.utils.requests.get',
                   side_effect=req.exceptions.RequestException):
            self.assertIsNone(check_version())
        # request returns None
        with patch('dotdrop.utils.requests.get', return_value=None):
            self.assertIsNone(check_version())
        # status code != 200
        resp = MagicMock()
        resp.status_code = 404
        with patch('dotdrop.utils.requests.get', return_value=resp):
            self.assertIsNone(check_version())
        # json decode error
        import json
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = json.decoder.JSONDecodeError('msg', 'doc', 0)
        with patch('dotdrop.utils.requests.get', return_value=resp):
            self.assertIsNone(check_version())
        # value error
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError
        with patch('dotdrop.utils.requests.get', return_value=resp):
            self.assertIsNone(check_version())
        # new version available -> warning
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'name': 'v999.999.999'}
        with patch('dotdrop.utils.requests.get', return_value=resp), \
                patch('dotdrop.utils.version.parse') as vparse:
            vparse.side_effect = lambda v: v
            check_version()

    def test_is_bin_in_path(self):
        """is_bin_in_path edge cases"""
        self.assertFalse(is_bin_in_path(''))
        self.assertFalse(is_bin_in_path(None))
        # shutil.which returns None
        with patch('dotdrop.utils.shutil.which', return_value=None):
            self.assertFalse(is_bin_in_path('somebin'))
        # shutil.which raises shutil.Error
        with patch('dotdrop.utils.shutil.which',
                   side_effect=__import__('shutil').Error):
            self.assertFalse(is_bin_in_path('somebin'))
        # normal case
        self.assertTrue(is_bin_in_path('ls'))


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

    def test_overwrite_safe_aborted(self):
        """_overwrite returns False when user says no in safe mode"""
        upd = Updater('path', {}, None, 'profile', safe=True)
        with patch('dotdrop.updater.Logger.ask', return_value=False):
            self.assertFalse(upd._overwrite('src', 'dst'))
        # not safe -> always True
        upd.safe = False
        self.assertTrue(upd._overwrite('src', 'dst'))

    def test_confirm_rm_r_safe_aborted(self):
        """_confirm_rm_r returns False when user says no in safe mode"""
        upd = Updater('path', {}, None, 'profile', safe=True)
        with patch('dotdrop.updater.Logger.ask', return_value=False):
            self.assertFalse(upd._confirm_rm_r('/some/dir'))
        # not safe -> always True
        upd.safe = False
        self.assertTrue(upd._confirm_rm_r('/some/dir'))


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

    def test_loader(self):
        """test loading template"""
        tmpl = Templategen()
        with self.assertRaises(TemplateNotFound):
            tmpl._template_loader('/abc')

    def test_is_text(self):
        """test is_text"""
        tmpl = Templategen()
        self.assertTrue(tmpl._is_text('empty'))
        self.assertTrue(tmpl._is_text('json'))
        self.assertTrue(tmpl._is_text('javascript'))
        self.assertTrue(tmpl._is_text('ecmascript'))
        self.assertTrue(tmpl._is_text('text'))
        self.assertFalse(tmpl._is_text('binary'))

    @patch.dict(os.environ, {"DOTDROP_MIME_TEXT": "application/x-wine-extension-ini"})
    def test_is_text_force(self):
        """test is_text with env var"""
        tmpl = Templategen()
        istext = tmpl._is_text("application/x-wine-extension-ini")
        self.assertTrue(istext)

    def test_handle_bin_file(self):
        """test handle binary file"""
        tmpl = Templategen()

        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        content = b'abc'
        path, _ = create_random_file(tmpdir, content=content, binary=True)

        cont = tmpl._handle_file(path)
        self.assertEqual(content, cont)

    def test_handle_bin_file_outside_base(self):
        """test _handle_bin_file with src not starting with base"""
        tmpl = Templategen()
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        content = b'binary-data'
        path, _ = create_random_file(tmpdir, content=content, binary=True)
        # call with a relative path so src does not start with base
        rel = os.path.relpath(path, os.getcwd())
        result = tmpl._handle_bin_file(rel)
        self.assertEqual(result, content)

    def test_handle_bad_encoded_text(self):
        """test _handle_text_file with non-utf8 content"""
        tmpl = Templategen()
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        # write invalid utf-8 bytes
        path, _ = create_random_file(tmpdir, content=b'\xff\xfe\x00bad',
                                     binary=True)
        # _read_bad_encoded_text decodes with replace
        data = Templategen._read_bad_encoded_text(path)
        self.assertIsInstance(data, str)
        # _handle_text_file falls back to bad-encoded path
        result = tmpl._handle_text_file(path)
        self.assertIsInstance(result, bytes)

    def test_is_template_bad_encoded(self):
        """test _is_template with non-utf8 file (UnicodeDecodeError)"""
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        path, _ = create_random_file(tmpdir, content=b'\xff\xfe\x00bad',
                                     binary=True)
        self.assertFalse(Templategen._is_template(path))

    def test_path_is_template_debug_missing(self):
        """test path_is_template with debug on missing path"""
        Templategen.path_is_template('/no/such/path', debug=True)
        self.assertFalse(Templategen.path_is_template('/no/such/path',
                                                       debug=False))

    def test_generate_dict_nested(self):
        """test generate_dict with nested dict value"""
        tmpl = Templategen()
        nested = {'outer': {'inner': 'value'}}
        result = tmpl.generate_dict(nested)
        self.assertEqual(result, {'outer': {'inner': 'value'}})

    def test_load_path_to_dic_invalid(self):
        """test _load_path_to_dic with module that cannot be loaded"""
        tmpl = Templategen()
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        # a non-python file -> get_module_from_path returns None
        path, _ = create_random_file(tmpdir, content='not python')
        # patch get_module_from_path to return None to hit the branch
        with patch('dotdrop.templategen.utils.get_module_from_path',
                   return_value=None):
            self.assertIsNone(tmpl._load_path_to_dic(path, {}))

    def test_get_filetype_relative_symlink(self):
        """test _get_filetype with a relative symlink"""
        tmpl = Templategen()
        tmpdir = get_tempdir()
        self.addCleanup(clean, tmpdir)
        target, _ = create_random_file(tmpdir, content='text content')
        link = os.path.join(tmpdir, 'alinks')
        os.symlink(os.path.basename(target), link)
        self.addCleanup(clean, link)
        # should follow the relative symlink
        ft = tmpl._get_filetype(link)
        self.assertIsInstance(ft, str)

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
