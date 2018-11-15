"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the comparison of dotfiles and local deployment
"""

import os
import filecmp
import fnmatch

# local imports
from dotdrop.logger import Logger
import dotdrop.utils as utils


class Comparator:

    def __init__(self, diffopts='', debug=False):
        self.diffopts = diffopts
        self.debug = debug
        self.log = Logger()

    def compare(self, left, right, ignore=[]):
        """diff left (dotdrop dotfile) and right (deployed file)"""
        left = os.path.expanduser(left)
        right = os.path.expanduser(right)
        if self.debug:
            self.log.dbg('comparing {} and {}'.format(left, right))
            self.log.dbg('ignore pattern(s): {}'.format(ignore))
        if not os.path.isdir(left):
            return self._comp_file(left, right, ignore)
        return self._comp_dir(left, right, ignore)

    def _comp_file(self, left, right, ignore):
        """compare a file"""
        if self._ignore([left, right], ignore):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        return self._diff(left, right)

    def _comp_dir(self, left, right, ignore):
        """compare a directory"""
        if not os.path.exists(right):
            return ''
        if self._ignore([left, right], ignore):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        if self.debug:
            self.log.dbg('compare {} and {}'.format(left, right))
        ret = []
        comp = filecmp.dircmp(left, right)
        # handle files only in deployed file
        for i in comp.left_only:
            if self._ignore([os.path.join(left, i)], ignore):
                continue
            ret.append('only in left: \"{}\"\n'.format(i))
        for i in comp.right_only:
            if self._ignore([os.path.join(right, i)], ignore):
                continue
            ret.append('only in right: \"{}\"\n'.format(i))

        # same left and right but different type
        funny = comp.common_funny
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            short = os.path.basename(lfile)
            # file vs dir
            ret.append('different type: \"{}\"\n'.format(short))

        # content is different
        funny = comp.diff_files
        funny.extend(comp.funny_files)
        funny = list(set(funny))
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            diff = self._diff(lfile, rfile, header=True)
            ret.append(diff)

        return ''.join(ret)

    def _diff(self, left, right, header=False):
        """diff using the unix tool diff"""
        diff = utils.diff(left, right, raw=False,
                          opts=self.diffopts, debug=self.debug)
        if header:
            lshort = os.path.basename(left)
            rshort = os.path.basename(right)
            diff = 'diff \"{}\":\n{}'.format(lshort, diff)
        return diff

    def _ignore(self, paths, ignore):
        '''return True if any paths is ignored - not very efficient'''
        if not ignore:
            return False
        for p in paths:
            for i in ignore:
                if fnmatch.fnmatch(p, i):
                    if self.debug:
                        self.log.dbg('ignore match {}'.format(p))
                    return True
        return False
