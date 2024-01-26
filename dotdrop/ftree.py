"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2024, deadc0de6

filesystem tree for directories
"""


import os

# local imports
from dotdrop.utils import must_ignore


class FTreeDir:

    def __init__(self, path, ignores=None, debug=False):
        self.path = path
        self.ignores
        self.debug = debug
        self.entries = []
        if os.path.exists(path) and os.path.isdir(path):
            self._walk()

    def _walk(self):
        for root, _, files in os.walk(self.path):
            for f in files:
                fpath = os.path.join(root, f)
                if must_ignore([fpath], ignores=self.ignores,
                               debug=self.debug):
                    continue
                self.entries.append(fpath)
        self.entries.sort()

    def compare(self, other):
        """
        compare two trees and returns
        - left_only (only in self)
        - right_only (only in other)
        - in_both (in both)
        """
        left_only = set(self.entries) - set(other.entries)
        right_only = set(other.entries) - set(self.entries)
        in_both = set(self.entries) & set(other.entries)
        return left_only, right_only, in_both
