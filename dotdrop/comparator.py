"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the comparison of two dotfiles
"""

import os
import filecmp

# local imports
from dotdrop.logger import Logger
from dotdrop.utils import must_ignore, uniq_list, diff, \
    get_file_perm


class Comparator:

    def __init__(self, diff_cmd='', debug=False, ignore_missing_in_dotdrop=False):
        """constructor
        @diff_cmd: diff command to use
        @debug: enable debug
        """
        self.diff_cmd = diff_cmd
        self.debug = debug
        self.log = Logger()
        self.ignore_missing_in_dotdrop = ignore_missing_in_dotdrop

    def compare(self, left, right, ignore=[]):
        """diff left (dotdrop dotfile) and right (deployed file)"""
        left = os.path.expanduser(left)
        right = os.path.expanduser(right)
        if self.debug:
            self.log.dbg('comparing {} and {}'.format(left, right))
            self.log.dbg('ignore pattern(s): {}'.format(ignore))

        # test type of file
        if os.path.isdir(left) and not os.path.isdir(right):
            return '\"{}\" is a dir while \"{}\" is a file\n'.format(left,
                                                                     right)
        if not os.path.isdir(left) and os.path.isdir(right):
            return '\"{}\" is a file while \"{}\" is a dir\n'.format(left,
                                                                     right)

        # test content
        if not os.path.isdir(left):
            if self.debug:
                self.log.dbg('{} is a file'.format(left))
            if self.debug:
                self.log.dbg('is file')
            ret = self._comp_file(left, right, ignore)
            if not ret:
                ret = self._comp_mode(left, right)
            return ret

        if self.debug:
            self.log.dbg('{} is a directory'.format(left))

        ret = self._comp_dir(left, right, ignore)
        if not ret:
            ret = self._comp_mode(left, right)
        return ret

    def _comp_mode(self, left, right):
        """compare mode"""
        left_mode = get_file_perm(left)
        right_mode = get_file_perm(right)
        if left_mode == right_mode:
            return ''
        if self.debug:
            msg = 'mode differ {} ({:o}) and {} ({:o})'
            self.log.dbg(msg.format(left, left_mode, right, right_mode))
        ret = 'modes differ for {} ({:o}) vs {:o}\n'
        return ret.format(right, right_mode, left_mode)

    def _comp_file(self, left, right, ignore):
        """compare a file"""
        if self.debug:
            self.log.dbg('compare file {} with {}'.format(left, right))
        if must_ignore([left, right], ignore, debug=self.debug):
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
        if must_ignore([left, right], ignore, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(left, right))
            return ''
        if not os.path.isdir(right):
            return '\"{}\" is a file\n'.format(right)
        if self.debug:
            self.log.dbg('compare {} and {}'.format(left, right))
        ret = []
        comp = filecmp.dircmp(left, right)

        # handle files only in deployed dir
        for i in comp.left_only:
            if must_ignore([os.path.join(left, i)],
                           ignore, debug=self.debug):
                continue
            ret.append('=> \"{}\" does not exist on destination\n'.format(i))

        # handle files only in dotpath dir
        for i in comp.right_only:
            if must_ignore([os.path.join(right, i)],
                           ignore, debug=self.debug):
                continue

            if not self.ignore_missing_in_dotdrop:
                ret.append('=> \"{}\" does not exist in dotdrop\n'.format(i))

        # same left and right but different type
        funny = comp.common_funny
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            if must_ignore([lfile, rfile],
                           ignore, debug=self.debug):
                continue
            short = os.path.basename(lfile)
            # file vs dir
            ret.append('=> different type: \"{}\"\n'.format(short))

        # content is different
        funny = comp.diff_files
        funny.extend(comp.funny_files)
        funny = uniq_list(funny)
        for i in funny:
            lfile = os.path.join(left, i)
            rfile = os.path.join(right, i)
            if must_ignore([lfile, rfile],
                           ignore, debug=self.debug):
                continue
            diff = self._diff(lfile, rfile, header=True)
            ret.append(diff)

        # recursively compare subdirs
        for i in comp.common_dirs:
            subleft = os.path.join(left, i)
            subright = os.path.join(right, i)
            ret.extend(self._comp_dir(subleft, subright, ignore))

        return ''.join(ret)

    def _diff(self, left, right, header=False):
        """diff two files"""
        out = diff(modified=left, original=right,
                   diff_cmd=self.diff_cmd, debug=self.debug)
        if header:
            lshort = os.path.basename(left)
            out = '=> diff \"{}\":\n{}'.format(lshort, out)
        return out
