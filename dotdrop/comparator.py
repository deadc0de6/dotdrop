"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the comparison of two dotfiles
"""

import os
import filecmp

# local imports
from dotdrop.logger import Logger
import dotdrop.utils as utils


class Comparator:

    def __init__(self, diffopts='', debug=False):
        """constructor
        @diffopts: switches to pass to unix diff
        @debug: enable debug
        """
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
            if self.debug:
                self.log.dbg('is file')
            return self._comp_file(left, right, ignore)
        if self.debug:
            self.log.dbg('is directory')
        return self._comp_dir(left, right, ignore)

    def _comp_file(self, left, right, ignore):
        """compare a file"""
        if self.debug:
            self.log.dbg('compare file {} with {}'.format(left, right))
        if utils.must_ignore([left, right], ignore, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        return self._diff(left, right)

    def _comp_dir(self, left, right, ignore):
        """compare a directory"""
        if self.debug:
            self.log.dbg('compare directory {} with {}'.format(left, right))
        if not os.path.exists(right):
            return ''
        if utils.must_ignore([left, right], ignore, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        if not os.path.isdir(right):
            return '\"{}\" is a file\n'.format(right)
        if self.debug:
            self.log.dbg('compare {} and {}'.format(left, right))
        ret = []
        comp = filecmp.dircmp(left, right)

        # handle files only in deployed file
        for i in comp.left_only:
            if utils.must_ignore([os.path.join(left, i)],
                                 ignore, debug=self.debug):
                continue
            ret.append('=> \"{}\" does not exist on local\n'.format(i))

        # handle files only in dotpath file
        for i in comp.right_only:
            if utils.must_ignore([os.path.join(right, i)],
                                 ignore, debug=self.debug):
                continue
            ret.append('=> \"{}\" does not exist in dotdrop\n'.format(i))

        # same left and right but different type
        funny = comp.common_funny
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            short = os.path.basename(lfile)
            # file vs dir
            ret.append('=> different type: \"{}\"\n'.format(short))

        # content is different
        funny = comp.diff_files
        funny.extend(comp.funny_files)
        funny = list(set(funny))
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            diff = self._diff(lfile, rfile, header=True)
            ret.append(diff)

        # recursively compare subdirs
        for i in comp.common_dirs:
            subleft = os.path.join(left, i)
            subright = os.path.join(right, i)
            ret.extend(self._comp_dir(subleft, subright, ignore))

        return ''.join(ret)

    def _diff(self, left, right, header=False):
        """diff using the unix tool diff"""
        diff = utils.diff(left, right, raw=False,
                          opts=self.diffopts, debug=self.debug)
        if header:
            lshort = os.path.basename(left)
            diff = '=> diff \"{}\":\n{}'.format(lshort, diff)
        return diff
