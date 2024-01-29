"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the comparison of two dotfiles
"""

import os

# local imports
from dotdrop.logger import Logger
from dotdrop.ftree import FTreeDir
from dotdrop.utils import must_ignore, diff, \
    get_file_perm


class Comparator:
    """compare dotfiles helper"""

    def __init__(self, diff_cmd='', debug=False,
                 ignore_missing_in_dotdrop=False):
        """constructor
        @diff_cmd: diff command to use
        @debug: enable debug
        @ignore_missing_in_dotdrop: ignore missing files in dotdrop
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

        self.log.dbg(f'comparing \"{local_path}\" and \"{deployed_path}\"')
        self.log.dbg(f'ignore pattern(s): {ignore}')

        return self._compare(local_path, deployed_path,
                             ignore=ignore, mode=mode,
                             recurse=True)

    def _compare(self, local_path, deployed_path,
                 ignore=None, mode=None,
                 recurse=False):
        if not ignore:
            ignore = []

        # test existence
        if not os.path.exists(local_path):
            return f'=> \"{local_path}\" does not exist on destination\n'
        if not self.ignore_missing_in_dotdrop:
            if not os.path.exists(deployed_path):
                return f'=> \"{deployed_path}\" does not exist in dotdrop\n'

        # test type of file
        if os.path.isdir(local_path) and not os.path.isdir(deployed_path):
            ret = f'\"{local_path}\" is a dir'
            ret += f' while \"{deployed_path}\" is a file\n'
            return ret
        if not os.path.isdir(local_path) and os.path.isdir(deployed_path):
            ret = f'\"{local_path}\" is a file'
            ret += f' while \"{deployed_path}\" is a dir\n'
            return ret

        # is a file
        if not os.path.isdir(local_path):
            self.log.dbg(f'{local_path} is a file')
            ret = self._comp_file(local_path, deployed_path, ignore)
            if not ret:
                ret = self._comp_mode(local_path, deployed_path, mode=mode)
            return ret

        # is a directory
        self.log.dbg(f'\"{local_path}\" is a directory')
        ret = ''
        if recurse:
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
        return self._diff(local_path, deployed_path, header=True)

    def _comp_dir(self, local_path, deployed_path, ignore):
        """compare a directory"""
        self.log.dbg(f'compare directory {local_path} with {deployed_path}')
        if not os.path.exists(deployed_path):
            return ''
        ign_missing = self.ignore_missing_in_dotdrop and not \
            os.path.exists(local_path)
        paths = [local_path, deployed_path]
        must_ign = must_ignore(paths,
                               ignore,
                               debug=self.debug)
        if ign_missing or must_ign:
            self.log.dbg(f'ignoring diff {local_path} and {deployed_path}')
            return ''
        if not os.path.isdir(deployed_path):
            return f'\"{deployed_path}\" is a file\n'

        return self._compare_dirs2(local_path, deployed_path, ignore)

    def _compare_dirs2(self, local_path, deployed_path, ignore):
        """compare directories"""
        self.log.dbg(f'compare dirs {local_path} and {deployed_path}')
        ret = []

        local_tree = FTreeDir(local_path, ignores=ignore, debug=self.debug)
        deploy_tree = FTreeDir(deployed_path, ignores=ignore, debug=self.debug)
        lonly, ronly, common = local_tree.compare(deploy_tree)

        for i in lonly:
            path = os.path.join(local_path, i)
            if os.path.isdir(path):
                # ignore dir
                continue
            ret.append(f'=> \"{path}\" does not exist on destination\n')
        if not self.ignore_missing_in_dotdrop:
            for i in ronly:
                path = os.path.join(deployed_path, i)
                if os.path.isdir(path):
                    # ignore dir
                    continue
                ret.append(f'=> \"{path}\" does not exist in dotdrop\n')

        # test for content difference
        # and mode difference
        self.log.dbg(f'common files {common}')
        for i in common:
            source_file = os.path.join(local_path, i)
            deployed_file = os.path.join(deployed_path, i)
            subret = self._compare(source_file, deployed_file,
                                   ignore=None, mode=None,
                                   recurse=False)
            ret.extend(subret)

        return ''.join(ret)

    def _diff(self, local_path, deployed_path, header=False):
        """diff two files"""
        out = diff(modified=local_path, original=deployed_path,
                   diff_cmd=self.diff_cmd, debug=self.debug)
        if header and out:
            lshort = os.path.basename(local_path)
            out = f'=> diff \"{lshort}\":\n{out}'
        return out
