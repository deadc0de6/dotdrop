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

    def __init__(self, diff_cmd='', debug=False,
                 ignore_missing_in_dotdrop=False):
        """constructor
        @diff_cmd: diff command to use
        @debug: enable debug
        """
        self.diff_cmd = diff_cmd
        self.debug = debug
        self.log = Logger()
        self.ignore_missing_in_dotdrop = ignore_missing_in_dotdrop

    def compare(self, local_path, deployed_path, ignore=[]):
        """diff local_path (dotdrop dotfile) and
        deployed_path (destination file)"""
        local_path = os.path.expanduser(local_path)
        deployed_path = os.path.expanduser(deployed_path)
        if self.debug:
            self.log.dbg('comparing {} and {}'.format(
                local_path,
                deployed_path,
            ))
            self.log.dbg('ignore pattern(s): {}'.format(ignore))

        # test type of file
        if os.path.isdir(local_path) and not os.path.isdir(deployed_path):
            return '\"{}\" is a dir while \"{}\" is a file\n'.format(
                local_path,
                deployed_path,
            )
        if not os.path.isdir(local_path) and os.path.isdir(deployed_path):
            return '\"{}\" is a file while \"{}\" is a dir\n'.format(
                local_path,
                deployed_path,
            )

        # test content
        if not os.path.isdir(local_path):
            if self.debug:
                self.log.dbg('{} is a file'.format(local_path))
            if self.debug:
                self.log.dbg('is file')
            ret = self._comp_file(local_path, deployed_path, ignore)
            if not ret:
                ret = self._comp_mode(local_path, deployed_path)
            return ret

        if self.debug:
            self.log.dbg('{} is a directory'.format(local_path))

        ret = self._comp_dir(local_path, deployed_path, ignore)
        if not ret:
            ret = self._comp_mode(local_path, deployed_path)
        return ret

    def _comp_mode(self, local_path, deployed_path):
        """compare mode"""
        local_mode = get_file_perm(local_path)
        deployed_mode = get_file_perm(deployed_path)
        if local_mode == deployed_mode:
            return ''
        if self.debug:
            msg = 'mode differ {} ({:o}) and {} ({:o})'
            self.log.dbg(msg.format(local_path, local_mode, deployed_path,
                                    deployed_mode))
        ret = 'modes differ for {} ({:o}) vs {:o}\n'
        return ret.format(deployed_path, deployed_mode, local_mode)

    def _comp_file(self, local_path, deployed_path, ignore):
        """compare a file"""
        if self.debug:
            self.log.dbg('compare file {} with {}'.format(
                local_path,
                deployed_path,
            ))
        if (self.ignore_missing_in_dotdrop and not os.path.exists(local_path)) \
                or must_ignore([local_path, deployed_path], ignore,
                               debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(
                    local_path,
                    deployed_path,
                ))
            return ''
        return self._diff(local_path, deployed_path)

    def _comp_dir(self, local_path, deployed_path, ignore):
        """compare a directory"""
        if self.debug:
            self.log.dbg('compare directory {} with {}'.format(
                local_path,
                deployed_path,
            ))
        if not os.path.exists(deployed_path):
            return ''
        if (self.ignore_missing_in_dotdrop and not os.path.exists(local_path)) \
                or must_ignore([local_path, deployed_path], ignore,
                               debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring diff {} and {}'.format(
                    local_path,
                    deployed_path,
                ))
            return ''
        if not os.path.isdir(deployed_path):
            return '\"{}\" is a file\n'.format(deployed_path)
        if self.debug:
            self.log.dbg('compare {} and {}'.format(local_path, deployed_path))
        ret = []
        comp = filecmp.dircmp(local_path, deployed_path)

        # handle files only in deployed dir
        for i in comp.left_only:
            if self.ignore_missing_in_dotdrop:
                continue
            if must_ignore([os.path.join(local_path, i)],
                           ignore, debug=self.debug):
                continue
            ret.append('=> \"{}\" does not exist on destination\n'.format(i))

        # handle files only in dotpath dir
        for i in comp.right_only:
            if must_ignore([os.path.join(deployed_path, i)],
                           ignore, debug=self.debug):
                continue

            if not self.ignore_missing_in_dotdrop:
                ret.append('=> \"{}\" does not exist in dotdrop\n'.format(i))

        # same local_path and deployed_path but different type
        funny = comp.common_funny
        for i in funny:
            source_file = os.path.join(local_path, i)
            deployed_file = os.path.join(deployed_path, i)
            if self.ignore_missing_in_dotdrop and \
                    not os.path.exists(source_file):
                continue
            if must_ignore([source_file, deployed_file],
                           ignore, debug=self.debug):
                continue
            short = os.path.basename(source_file)
            # file vs dir
            ret.append('=> different type: \"{}\"\n'.format(short))

        # content is different
        funny = comp.diff_files
        funny.extend(comp.funny_files)
        funny = uniq_list(funny)
        for i in funny:
            source_file = os.path.join(local_path, i)
            deployed_file = os.path.join(deployed_path, i)
            if self.ignore_missing_in_dotdrop and \
                    not os.path.exists(source_file):
                continue
            if must_ignore([source_file, deployed_file],
                           ignore, debug=self.debug):
                continue
            ret.append(self._diff(source_file, deployed_file, header=True))

        # recursively compare subdirs
        for i in comp.common_dirs:
            sublocal_path = os.path.join(local_path, i)
            subdeployed_path = os.path.join(deployed_path, i)
            ret.extend(self._comp_dir(sublocal_path, subdeployed_path, ignore))

        return ''.join(ret)

    def _diff(self, local_path, deployed_path, header=False):
        """diff two files"""
        out = diff(modified=local_path, original=deployed_path,
                   diff_cmd=self.diff_cmd, debug=self.debug)
        if header:
            lshort = os.path.basename(local_path)
            out = '=> diff \"{}\":\n{}'.format(lshort, out)
        return out
