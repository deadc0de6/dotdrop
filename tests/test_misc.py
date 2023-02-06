"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6
basic unittest for misc stuff
"""

# pylint: disable=R0903
# pylint: disable=W0231
# pylint: disable=W0212

import unittest
from dotdrop.profile import Profile
from dotdrop.linktypes import LinkTypes


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
