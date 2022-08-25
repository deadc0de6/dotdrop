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
    """compare dotfiles helper"""

    def __init__(self, diff_cmd='', debug=False,
                 ignore_missing_in_dotdrop=False):
        """constructor
        @diff_cmd: diff command to use
        @debug: enable debug
        """
        self.diff_cmd = diff_cmd
        self.debug = debug
        self.log = Logger(debug=self.debug)
        self.ignore_missing_in_dotdrop = ignore_missing_in_dotdrop

    def compare(self, local_path, deployed_path, ignore=None, mode=None):
        """
        diff local_path (dotdrop dotfile) and
        deployed_path (destination file)
        If mode is None, rights will be read from local_path
        """
        if not ignore:
            ignore = []
        local_path = os.path.expanduser(local_path)
        deployed_path = os.path.expanduser(deployed_path)
        self.log.dbg(f'comparing {local_path} and {deployed_path}')
        self.log.dbg(f'ignore pattern(s): {ignore}')

        # test type of file
        if os.path.isdir(local_path) and not os.path.isdir(deployed_path):
            ret = f'\"{local_path}\" is a dir'
            ret += f' while \"{deployed_path}\" is a file\n'
            return ret
        if not os.path.isdir(local_path) and os.path.isdir(deployed_path):
            ret = f'\"{local_path}\" is a file'
            ret += f' while \"{deployed_path}\" is a dir\n'
            return ret

        # test content
        if not os.path.isdir(local_path):
            self.log.dbg(f'{local_path} is a file')
            ret = self._comp_file(local_path, deployed_path, ignore)
            if not ret:
                ret = self._comp_mode(local_path, deployed_path, mode=mode)
            return ret

        self.log.dbg(f'{local_path} is a directory')

        ret = self._comp_dir(local_path, deployed_path, ignore)
        if not ret:
            ret = self._comp_mode(local_path, deployed_path, mode=mode)
        return ret

    def _comp_mode(self, local_path, deployed_path, mode=None):
        """
        compare mode
        If mode is None, rights will be read on local_path
        """
        local_mode = mode
        if not local_mode:
            local_mode = get_file_perm(local_path)
        deployed_mode = get_file_perm(deployed_path)
        if local_mode == deployed_mode:
            return ''
        msg = f'mode differ {local_path} ({local_mode:o}) '
        msg += f'and {deployed_path} ({deployed_mode:o})'
        self.log.dbg(msg)
        ret = f'modes differ for {deployed_path} '
        ret += f'({deployed_mode:o}) vs {local_mode:o}\n'
        return ret

    def _comp_file(self, local_path, deployed_path, ignore):
        """compare a file"""
        self.log.dbg(f'compare file {local_path} with {deployed_path}')
        if (self.ignore_missing_in_dotdrop and not
                os.path.exists(local_path)) \
                or must_ignore([local_path, deployed_path], ignore,
                               debug=self.debug):
            self.log.dbg(f'ignoring diff {local_path} and {deployed_path}')
            return ''
        return self._diff(local_path, deployed_path)

    def _comp_dir(self, local_path, deployed_path, ignore):
        """compare a directory"""
        self.log.dbg(f'compare directory {local_path} with {deployed_path}')
        if not os.path.exists(deployed_path):
            return ''
        if (self.ignore_missing_in_dotdrop and not
                os.path.exists(local_path)) \
                or must_ignore([local_path, deployed_path], ignore,
                               debug=self.debug):
            self.log.dbg(f'ignoring diff {local_path} and {deployed_path}')
            return ''
        if not os.path.isdir(deployed_path):
            return f'\"{deployed_path}\" is a file\n'

        return self._compare_dirs(local_path, deployed_path, ignore)

    def _compare_dirs(self, local_path, deployed_path, ignore):
        """compare directories"""
        self.log.dbg(f'compare {local_path} and {deployed_path}')
        ret = []
        comp = filecmp.dircmp(local_path, deployed_path)

        # handle files only in deployed dir
        self.log.dbg(f'files only in deployed dir: {comp.left_only}')
        for i in comp.left_only:
            if self.ignore_missing_in_dotdrop or \
               must_ignore([os.path.join(local_path, i)],
                           ignore, debug=self.debug):
                continue
            ret.append(f'=> \"{i}\" does not exist on destination\n')

        # handle files only in dotpath dir
        self.log.dbg(f'files only in dotpath dir: {comp.right_only}')
        for i in comp.right_only:
            if must_ignore([os.path.join(deployed_path, i)],
                           ignore, debug=self.debug):
                continue

            if not self.ignore_missing_in_dotdrop:
                ret.append(f'=> \"{i}\" does not exist in dotdrop\n')

        # same local_path and deployed_path but different type
        funny = comp.common_funny
        self.log.dbg(f'files with different types: {funny}')
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
            ret.append(f'=> different type: \"{short}\"\n')

        # content is different
        funny = comp.diff_files
        funny.extend(comp.funny_files)
        funny = uniq_list(funny)
        self.log.dbg(f'files with different content: {funny}')
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
            out = f'=> diff \"{lshort}\":\n{out}'
        return out
