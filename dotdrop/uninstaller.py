"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

handle the un-installation of dotfiles
"""

import os
from dotdrop.logger import Logger
from dotdrop.utils import removepath, dir_empty


class Uninstaller:
    """dotfile uninstaller"""

    def __init__(self, base='.', workdir='~/.config/dotdrop',
                 dry=False, safe=True, debug=False,
                 backup_suffix='.dotdropbak'):
        """
        @base: directory path where to search for templates
        @workdir: where to install template before symlinking
        @dry: just simulate
        @debug: enable debug
        @backup_suffix: suffix for dotfile backup file
        @safe: ask for any action
        """
        base = os.path.expanduser(base)
        base = os.path.normpath(base)
        self.base = base
        workdir = os.path.expanduser(workdir)
        workdir = os.path.normpath(workdir)
        self.workdir = workdir
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.backup_suffix = backup_suffix
        self.log = Logger(debug=self.debug)

    def uninstall(self, src, dst, linktype):
        """
        uninstall dst
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @linktype: linktypes.LinkTypes

        return
        - True, None        : success
        - False, error_msg  : error
        """
        if not src or not dst:
            self.log.dbg(f'cannot uninstall empty {src} or {dst}')
            return True, None

        # ensure exists
        path = os.path.expanduser(dst)
        path = os.path.normpath(path)
        path = path.rstrip(os.sep)

        if not os.path.isfile(path) and not os.path.isdir(path):
            msg = f'cannot uninstall special file {path}'
            return False, msg

        if not os.path.exists(path):
            self.log.dbg(f'cannot uninstall non existing {path}')
            return True, None

        msg = f'uninstalling \"{path}\" (link: {linktype})'
        self.log.dbg(msg)
        ret, msg = self._remove(path)
        if ret:
            if not self.dry:
                self.log.sub(f'uninstall {dst}')
        return ret, msg

    def _descend(self, dirpath):
        ret = True
        self.log.dbg(f'recursively uninstall {dirpath}')
        for sub in os.listdir(dirpath):
            subpath = os.path.join(dirpath, sub)
            if os.path.isdir(subpath):
                self.log.dbg(f'under {dirpath} uninstall dir {subpath}')
                self._descend(subpath)
            else:
                self.log.dbg(f'under {dirpath} uninstall file {subpath}')
                subret, _ = self._remove(subpath)
                if not subret:
                    ret = False

        if dir_empty(dirpath):
            # empty
            self.log.dbg(f'remove empty dir {dirpath}')
            if self.dry:
                self.log.dry(f'would \"rm -r {dirpath}\"')
                return True, ''
            return self._remove_path(dirpath)
        self.log.dbg(f'not removing non-empty dir {dirpath}')
        return ret, ''

    def _remove_path(self, path):
        """remove a file"""
        try:
            removepath(path, self.log)
        except OSError as exc:
            err = f'removing \"{path}\" failed: {exc}'
            return False, err
        return True, ''

    def _remove(self, path):
        """remove path"""
        self.log.dbg(f'handling uninstall of {path}')
        if path.endswith(self.backup_suffix):
            self.log.dbg(f'skip {path} ignored')
            return True, ''
        backup = f'{path}{self.backup_suffix}'
        if os.path.exists(backup):
            self.log.dbg(f'backup exists for {path}: {backup}')
            return self._replace(path, backup)
        self.log.dbg(f'no backup file for {path}')

        if os.path.isdir(path):
            self.log.dbg(f'{path} is a directory')
            return self._descend(path)

        if self.dry:
            self.log.dry(f'would \"rm {path}\"')
            return True, ''

        msg = f'Remove {path}?'
        if self.safe and not self.log.ask(msg):
            return False, 'user refused'
        self.log.dbg(f'removing {path}')
        return self._remove_path(path)

    def _replace(self, path, backup):
        """replace path by backup"""
        if self.dry:
            self.log.dry(f'would \"mv {backup} {path}\"')
            return True, ''

        msg = f'Restore {path} from {backup}?'
        if self.safe and not self.log.ask(msg):
            return False, 'user refused'

        try:
            self.log.dbg(f'mv {backup} {path}')
            os.replace(backup, path)
        except OSError as exc:
            err = f'replacing \"{path}\" by \"{backup}\" failed: {exc}'
            return False, err
        return True, ''
