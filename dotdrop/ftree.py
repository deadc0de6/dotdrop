"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2024, deadc0de6

filesystem tree for directories
"""


import os

# local imports
from dotdrop.utils import must_ignore, dir_empty
from dotdrop.logger import Logger


class FTreeDir:
    """
    directory tree for comparison
    """

    def __init__(self, path, ignores=None, debug=False):
        self.path = path
        self.ignores = ignores
        self.debug = debug
        self.entries = []
        self.log = Logger(debug=self.debug)
        if os.path.exists(path) and os.path.isdir(path):
            self._walk()

    def _walk(self):
        """
        index directory
        ignore empty directory
        test for ignore pattern
        """
        for root, dirs, files in os.walk(self.path, followlinks=True):
            for file in files:
                fpath = os.path.join(root, file)
                if must_ignore([fpath], ignores=self.ignores,
                               debug=self.debug, strict=True):
                    self.log.dbg(f'ignoring file {fpath}')
                    continue
                self.log.dbg(f'added file to list of {self.path}: {fpath}')
                self.entries.append(fpath)
            for dname in dirs:
                dpath = os.path.join(root, dname)
                if dir_empty(dpath):
                    # ignore empty directory
                    self.log.dbg(f'ignoring empty dir {dpath}')
                    continue
                # appending "/" allows to ensure pattern
                # like "*/dir/*" will match the content of the directory
                # but also the directory itself
                dpath += os.path.sep
                if must_ignore([dpath], ignores=self.ignores,
                               debug=self.debug, strict=True):
                    self.log.dbg(f'ignoring dir {dpath}')
                    continue
                self.log.dbg(f'added dir to list of {self.path}: {dpath}')
                self.entries.append(dpath)

    def get_entries(self):
        """return all entries"""
        return self.entries

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
