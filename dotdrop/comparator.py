"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the comparison of dotfiles and local deployment
"""

import os
import shutil
import filecmp

# local imports
from dotdrop.logger import Logger
import dotdrop.utils as utils


class Comparator:

    # TODO add ignore
    def __init__(self, diffopts='', ignore=[], debug=False):
        """diff left (deployed file) and right (dotdrop dotfile)"""
        self.diffopts = diffopts
        self.ignore = [os.path.expanduser(i) for i in ignore]
        self.debug = debug
        self.log = Logger()

    def compare(self, left, right):
        """compare two files/directories"""
        left = os.path.expanduser(left)
        right = os.path.expanduser(right)
        if not os.path.isdir(left):
            return self._comp_file(left, right)
        return self._comp_dir(left, right)

    def _comp_file(self, left, right):
        """compare a file"""
        if left in self.ignore or right in self.ignore:
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        return self._diff(left, right)

    def _comp_dir(self, left, right):
        """compare a directory"""
        if left in self.ignore or right in self.ignore:
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        if self.debug:
            self.log.dbg('compare {} and {}'.format(left, right))
        ret = []
        comp = filecmp.dircmp(left, right, ignore=self.ignore)
        # handle files only in deployed file
        for i in comp.left_only:
            ret.append('Only in {}: {}'.format(left, i))
        for i in comp.right_only:
            ret.append('Only in {}: {}'.format(right, i))

        for i in comp.common_funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            diff = self._diff(lfile, rfile)
            ret.append(diff)

        for i in comp.diff_files:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            diff = self._diff(lfile, rfile)
            ret.append(diff)

        for i in comp.funny_files:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            diff = self._diff(lfile, rfile)
            ret.append(diff)

        return '\n'.join(ret)

    def _diff(self, left, right):
        """diff using the unix tool diff"""
        diff = utils.diff(left, right, raw=False,
                          opts=self.diffopts, debug=self.debug)
        return diff
