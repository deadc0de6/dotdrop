"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2020, deadc0de6

handle import of dotfiles
"""

import os
import shutil

# local imports
from dotdrop.logger import Logger
from dotdrop.utils import strip_home, get_default_file_perms, \
    get_file_perm, get_umask, must_ignore
from dotdrop.linktypes import LinkTypes
from dotdrop.comparator import Comparator


class Importer:
    """dotfile importer"""

    def __init__(self, profile, conf, dotpath, diff_cmd,
                 dry=False, safe=True, debug=False,
                 keepdot=True, ignore=None):
        """constructor
        @profile: the selected profile
        @conf: configuration manager
        @dotpath: dotfiles dotpath
        @diff_cmd: diff command to use
        @dry: simulate
        @safe: ask for overwrite if True
        @debug: enable debug
        @keepdot: keep dot prefix
        @ignore: patterns to ignore when importing
        """
        self.profile = profile
        self.conf = conf
        self.dotpath = dotpath
        self.diff_cmd = diff_cmd
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.keepdot = keepdot
        if not ignore:
            ignore = []
        self.ignore = ignore

        self.umask = get_umask()
        self.log = Logger()

    def import_path(self, path, import_as=None,
                    import_link=LinkTypes.NOLINK, import_mode=False):
        """
        import a dotfile pointed by path
        returns:
            1: 1 dotfile imported
            0: ignored
            -1: error
        """
        if self.debug:
            self.log.dbg('import {}'.format(path))
        if not os.path.exists(path):
            self.log.err('\"{}\" does not exist, ignored!'.format(path))
            return -1

        return self._import(path, import_as=import_as,
                            import_link=import_link, import_mode=import_mode)

    def _import(self, path, import_as=None,
                import_link=LinkTypes.NOLINK, import_mode=False):
        """
        import path
        returns:
            1: 1 dotfile imported
            0: ignored
            -1: error
        """

        # normalize path
        dst = path.rstrip(os.sep)
        dst = os.path.abspath(dst)

        # test if must be ignored
        if self._ignore(dst):
            return 0

        # ask confirmation for symlinks
        if self.safe:
            realdst = os.path.realpath(dst)
            if dst != realdst:
                msg = '\"{}\" is a symlink, dereference it and continue?'
                if not self.log.ask(msg.format(dst)):
                    return 0

        # create src path
        src = strip_home(dst)
        if import_as:
            # handle import as
            src = os.path.expanduser(import_as)
            src = src.rstrip(os.sep)
            src = os.path.abspath(src)
            src = strip_home(src)
            if self.debug:
                self.log.dbg('import src for {} as {}'.format(dst, src))
        # with or without dot prefix
        strip = '.' + os.sep
        if self.keepdot:
            strip = os.sep
        src = src.lstrip(strip)

        # get the permission
        perm = get_file_perm(dst)

        # get the link attribute
        linktype = import_link
        if linktype == LinkTypes.LINK_CHILDREN and \
                not os.path.isdir(path):
            self.log.err('importing \"{}\" failed!'.format(path))
            return -1

        if self._already_exists(src, dst):
            return -1

        if self.debug:
            self.log.dbg('import dotfile: src:{} dst:{}'.format(src, dst))

        if not self._prepare_hierarchy(src, dst):
            return -1

        return self._import_it(path, src, dst, perm, linktype, import_mode)

    def _import_it(self, path, src, dst, perm, linktype, import_mode):
        """
        import path
        returns:
            1: 1 dotfile imported
            0: ignored
        """

        # handle file mode
        chmod = None
        dflperm = get_default_file_perms(dst, self.umask)
        if self.debug:
            self.log.dbg('import mode: {}'.format(import_mode))
        if import_mode or perm != dflperm:
            if self.debug:
                msg = 'adopt mode {:o} (umask {:o})'
                self.log.dbg(msg.format(perm, dflperm))
            chmod = perm

        # add file to config file
        retconf = self.conf.new_dotfile(src, dst, linktype, chmod=chmod)
        if not retconf:
            self.log.warn('\"{}\" ignored during import'.format(path))
            return 0

        self.log.sub('\"{}\" imported'.format(path))
        return 1

    def _prepare_hierarchy(self, src, dst):
        """prepare hierarchy for dotfile"""
        srcf = os.path.join(self.dotpath, src)
        srcfd = os.path.dirname(srcf)
        if self._ignore(srcf) or self._ignore(srcfd):
            return False

        # a dotfile in dotpath already exists at that spot
        if os.path.exists(srcf):
            if self.safe:
                cmp = Comparator(debug=self.debug,
                               diff_cmd=self.diff_cmd)
                diff = cmp.compare(srcf, dst)
                if diff != '':
                    # files are different, dunno what to do
                    self.log.log('diff \"{}\" VS \"{}\"'.format(dst, srcf))
                    self.log.emph(diff)
                    # ask user
                    msg = 'Dotfile \"{}\" already exists, overwrite?'
                    if not self.log.ask(msg.format(srcf)):
                        return False
                    if self.debug:
                        self.log.dbg('will overwrite existing file')

        # create directory hierarchy
        if self.dry:
            cmd = 'mkdir -p {}'.format(srcfd)
            self.log.dry('would run: {}'.format(cmd))
        else:
            try:
                os.makedirs(srcfd, exist_ok=True)
            except OSError:
                self.log.err('importing \"{}\" failed!'.format(dst))
                return False

        if self.dry:
            self.log.dry('would copy {} to {}'.format(dst, srcf))
        else:
            # copy the file to the dotpath
            try:
                if os.path.isdir(dst):
                    if os.path.exists(srcf):
                        shutil.rmtree(srcf)
                    ign = shutil.ignore_patterns(*self.ignore)
                    shutil.copytree(dst, srcf,
                                    copy_function=self._cp,
                                    ignore=ign)
                else:
                    shutil.copy2(dst, srcf)
            except shutil.Error as exc:
                src = exc.args[0][0][0]
                why = exc.args[0][0][2]
                self.log.err('importing \"{}\" failed: {}'.format(src, why))

        return True

    def _cp(self, src, dst):
        """the copy function for copytree"""
        # test if must be ignored
        if self._ignore(src):
            return
        shutil.copy2(src, dst)

    def _already_exists(self, src, dst):
        """
        test no other dotfile exists with same
        dst for this profile but different src
        """
        dfs = self.conf.get_dotfile_by_dst(dst)
        if not dfs:
            return False
        for dotfile in dfs:
            profiles = self.conf.get_profiles_by_dotfile_key(dotfile.key)
            profiles = [x.key for x in profiles]
            if self.profile in profiles and \
                    not self.conf.get_dotfile_by_src_dst(src, dst):
                # same profile
                # different src
                self.log.err('duplicate dotfile for this profile')
                return True
        return False

    def _ignore(self, path):
        if must_ignore([path], self.ignore, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring import of {}'.format(path))
            self.log.warn('{} ignored'.format(path))
            return True
        return False
