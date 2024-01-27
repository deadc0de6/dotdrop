"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2024, deadc0de6

filesystem tree for directories
"""


import os

# local imports
from dotdrop.utils import must_ignore


class FTreeDir:
    """
    directory tree for comparison
    """

    def __init__(self, path, ignores=None, debug=False):
        self.path = path
        self.ignores = ignores
        self.debug = debug
        self.entries = []
        if os.path.exists(path) and os.path.isdir(path):
            self._walk()

    def _walk(self):
        """
        index directory
        ignore empty directory
        test for ignore pattern
        """
        for root, dirs, files in os.walk(self.path):
            for file in files:
                fpath = os.path.join(root, file)
                if must_ignore([fpath], ignores=self.ignores,
                               debug=self.debug):
                    continue
                self.entries.append(fpath)
            for dname in dirs:
                dpath = os.path.join(root, dname)
                if len(os.listdir(dpath)) < 1:
                    # ignore empty directory
                    continue
                if must_ignore([dpath], ignores=self.ignores,
                               debug=self.debug):
                    continue
                self.entries.append(dpath)

    def compare(self, other):
        """
        compare two trees and returns
        - left_only (only in self)
        - right_only (only in other)
        - in_both (in both)
        the relative path are returned
        """
        left = [os.path.relpath(entry, self.path) for entry in self.entries]
        right = [os.path.relpath(entry, other.path) for entry in other.entries]
        left_only = set(left) - set(right)
        right_only = set(right) - set(left)
        in_both = set(left) & set(right)
        return list(left_only), list(right_only), list(in_both)
