"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6
basic unittest for misc stuff
"""

# pylint: disable=R0903
# pylint: disable=W0231
# pylint: disable=W0212

import unittest
from unittest.mock import patch
from dotdrop.profile import Profile
from dotdrop.linktypes import LinkTypes
from dotdrop.templategen import Templategen
from dotdrop.exceptions import UndefinedException
from jinja2 import TemplateNotFound
from tests.helpers import create_random_file, \
    get_tempdir, clean


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
