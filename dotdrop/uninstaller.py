"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

handle the un-installation of dotfiles
"""

import os
from dotdrop.logger import Logger
from dotdrop.utils import removepath


class Uninstaller:
    """dotfile uninstaller"""

    def __init__(self, base='.', workdir='~/.config/dotdrop',
                 dry=False, debug=False, backup_suffix='.dotdropbak'):
        """
        @base: directory path where to search for templates
        @workdir: where to install template before symlinking
        @dry: just simulate
        @debug: enable debug
        @backup_suffix: suffix for dotfile backup file
        """
        base = os.path.expanduser(base)
        base = os.path.normpath(base)
        self.base = base
        workdir = os.path.expanduser(workdir)
        workdir = os.path.normpath(workdir)
        self.workdir = workdir
        self.dry = dry
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

        if not os.path.exists(path):
            self.log.dbg(f'cannot uninstall non existing {path}')
            return True, None

        msg = f'uninstalling \"{path}\" (link: {linktype})'
        self.log.dbg(msg)
        self._remove(path)

    def _remove(self, path):
        """remove path"""
        # TODO handle symlink
        backup = f'{path}{self.backup_suffix}'
        if os.path.exists(backup):
            return self._replace(path, backup)
        try:
            removepath(path, self.log)
        except OSError as exc:
            err = f'removing \"{path}\" failed: {exc}'
            return False, err

    def _replace(self, path, backup):
        """replace path by backup"""
        if os.path.isdir(path):
            # TODO
            return False, 'TODO'
        try:
            os.replace(path, backup)
        except OSError as exc:
            err = f'replacing \"{path}\" by \"{backup}\" failed: {exc}'
            return False, err
