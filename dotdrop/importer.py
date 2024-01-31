"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2020, deadc0de6

handle import of dotfiles
"""

import os
import shutil

# local imports
from dotdrop.logger import Logger
from dotdrop.ftree import FTreeDir
from dotdrop.utils import strip_home, get_default_file_perms, \
    get_file_perm, get_umask, must_ignore, \
    get_unique_tmp_name, removepath
from dotdrop.linktypes import LinkTypes
from dotdrop.comparator import Comparator
from dotdrop.templategen import Templategen
from dotdrop.exceptions import UndefinedException


class Importer:
    """dotfile importer"""

    def __init__(self, profile, conf, dotpath, diff_cmd,
                 variables, dry=False, safe=True, debug=False,
                 keepdot=True, ignore=None):
        """constructor
        @profile: the selected profile
        @conf: configuration manager
        @dotpath: dotfiles dotpath
        @diff_cmd: diff command to use
        @variables: dictionary of variables for the templates
        @dry: simulate
        @safe: ask for overwrite if True
        @debug: enable debug
        @keepdot: keep dot prefix
        @ignore: patterns to ignore when importing
        This may raise UndefinedException
        """
        self.profile = profile
        if not self.profile:
            raise UndefinedException("profile is undefined")
        self.conf = conf
        self.dotpath = dotpath
        self.diff_cmd = diff_cmd
        self.variables = variables
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.keepdot = keepdot
        self.ignore = []
        self.log = Logger(debug=self.debug)

        # patch ignore patterns
        if ignore:
            for ign in ignore:
                if ign.startswith('!'):
                    self.ignore.append(ign)
                    continue
                if ign.startswith('*/'):
                    self.ignore.append(ign)
                    continue
                newign = f'*/{ign}'
                self.log.dbg(f'patching ignore {ign} to {newign}')
                self.ignore.append(newign)

        self.templater = Templategen(variables=self.variables,
                                     base=self.dotpath,
                                     debug=self.debug)

        self.umask = get_umask()

    def import_path(self, path, import_as=None,
                    import_link=LinkTypes.NOLINK,
                    import_mode=False,
                    trans_install="",
                    trans_update=""):
        """
        import a dotfile pointed by path
        returns:
            1: 1 dotfile imported
            0: ignored
            -1: error
        """
        path = os.path.abspath(path)
        self.log.dbg(f'import {path}')
        if not os.path.exists(path):
            self.log.err(f'\"{path}\" does not exist, ignored!')
            return -1

        # check trans_update if any
        tinstall = None
        tupdate = None
        if trans_install:
            tinstall = self.conf.get_trans_install(trans_install)
        if trans_update:
            tupdate = self.conf.get_trans_update(trans_update)

        return self._import(path, import_as=import_as,
                            import_link=import_link,
                            import_mode=import_mode,
                            trans_update=tupdate,
                            trans_install=tinstall)

    def _import(self, path, import_as=None,
                import_link=LinkTypes.NOLINK,
                import_mode=False,
                trans_install=None,
                trans_update=None):
        """
        import path
        returns:
            1: 1 dotfile imported
            0: ignored
            -1: error
        """

        # normalize path
        infspath = path.rstrip(os.sep)
        infspath = os.path.abspath(infspath)

        # test if must be ignored
        if self._ignore(infspath):
            return 0

        # ask confirmation for symlinks
        if self.safe:
            realdst = os.path.realpath(infspath)
            if infspath != realdst:
                msg = f'\"{infspath}\" is a symlink, '
                msg += 'dereference it and continue?'
                if not self.log.ask(msg):
                    return 0

        # create src path
        indotpath = strip_home(infspath)
        if import_as:
            # handle import as
            indotpath = os.path.expanduser(import_as)
            indotpath = indotpath.rstrip(os.sep)
            indotpath = os.path.abspath(indotpath)
            indotpath = strip_home(indotpath)
            self.log.dbg(f'import src for {infspath} as {indotpath}')
        # with or without dot prefix
        strip = '.' + os.sep
        if self.keepdot:
            strip = os.sep
        indotpath = indotpath.lstrip(strip)

        # get the permission
        perm = get_file_perm(infspath)

        # get the link attribute
        linktype = import_link
        if linktype == LinkTypes.LINK_CHILDREN and \
                not os.path.isdir(path):
            self.log.err(f'importing \"{path}\" failed!')
            return -1

        if self._already_exists(indotpath, infspath):
            return -1

        self.log.dbg(f'import dotfile: src:{indotpath} dst:{infspath}')
        if not self._import_to_dotpath(indotpath,
                                       infspath,
                                       trans_update=trans_update):
            self.log.dbg('import files failed')
            return -1

        return self._import_in_config(path, indotpath,
                                      infspath, perm, linktype,
                                      import_mode,
                                      trans_update=trans_update,
                                      trans_install=trans_install)

    def _import_in_config(self, path, src, dst, perm,
                          linktype, import_mode,
                          trans_install=None,
                          trans_update=None):
        """
        import path
        returns:
            1: 1 dotfile imported
            0: ignored
        """
        # handle file mode
        chmod = None
        dflperm = get_default_file_perms(dst, self.umask)
        self.log.dbg(f'import chmod: {import_mode}')
        if import_mode or perm != dflperm:
            msg = f'adopt mode {perm:o} (umask {dflperm:o})'
            self.log.dbg(msg)
            chmod = perm

        # add file to config file
        retconf = self.conf.new_dotfile(src, dst, linktype, chmod=chmod,
                                        trans_install=trans_install,
                                        trans_update=trans_update)
        if not retconf:
            self.log.warn(f'\"{path}\" ignored during import')
            return 0

        self.log.sub(f'\"{path}\" imported')
        return 1

    def _check_existing_dotfile(self, src, dst):
        """
        check if a dotfile file in the dotpath
        already exists for this src
        """
        if not os.path.exists(src):
            return True
        if not self.safe:
            return True
        cmp = Comparator(debug=self.debug,
                         diff_cmd=self.diff_cmd)
        diff = cmp.compare(src, dst)
        if diff != '':
            # files are different, dunno what to do
            self.log.log(f'diff \"{dst}\" VS \"{src}\"')
            self.log.emph(diff)
            # ask user
            msg = f'Dotfile \"{src}\" already exists, overwrite?'
            if not self.log.ask(msg):
                return False
            self.log.dbg('will overwrite existing file')
        return True

    def _import_to_dotpath(self, in_dotpath, in_fs, trans_update=None):
        """
        copy files to dotpath
        """
        in_dotpath_abs = os.path.join(self.dotpath, in_dotpath)

        # check we are not overwritting
        if not self._check_existing_dotfile(in_dotpath_abs, in_fs):
            self.log.dbg(f'{in_dotpath_abs} exits already')
            return False

        # import the file
        if self.dry:
            self.log.dry(f'would copy {in_fs} to {in_dotpath_abs}')
            return True

        # apply trans_update
        in_fs = self._apply_trans_update(in_fs, trans_update)
        if not in_fs:
            # transformation failed
            self.log.dbg(f"trans failed: {in_fs}")
            return False

        if not os.path.isdir(in_fs):
            # handle file
            self._import_file_to_dotpath(in_fs, in_dotpath_abs)

        # handle dir and get a list of all files to import
        fstree = FTreeDir(in_fs,
                          ignores=self.ignore,
                          debug=self.debug)

        self.log.dbg(f'{len(fstree.get_entries())} files to import')
        for entry in fstree.get_entries():
            self.log.dbg(f"importing {entry}...")
            src = os.path.join(in_fs, entry)
            rel_src = os.path.relpath(entry, in_fs)
            dst = os.path.join(in_dotpath_abs, rel_src)
            if os.path.isdir(src):
                # we do not care about directory
                # these are created based on files
                continue
            self._import_file_to_dotpath(src, dst)

        return os.path.exists(in_dotpath_abs)

    def _import_file_to_dotpath(self, src, dst):
        self.log.dbg(f'importing {src} to {dst}')
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        except IOError as exc:
            self.log.err(f'importing \"{src}\" failed: {exc}')
            return False
        return True

    def _already_exists(self, src, dst):
        """
        test no other dotfile exists with same
        dst for this profile but different src
        """
        dfs = self.conf.get_dotfile_by_dst(dst, profile_key=self.profile)
        if not dfs:
            return False
        for dotfile in dfs:
            profiles = self.conf.get_profiles_by_dotfile_key(dotfile.key)
            profiles = [x.key for x in profiles]
            if self.profile in profiles and \
                    not self.conf.get_dotfile_by_src_dst(src, dst):
                # same profile
                # different src
                msg = f'duplicate dotfile: {dotfile.key}'
                self.log.err(msg)
                return True
        return False

    def _ignore(self, path):
        if must_ignore([path], self.ignore, debug=self.debug):
            self.log.dbg(f'ignoring import of {path}')
            self.log.warn(f'{path} ignored')
            return True
        return False

    def _apply_trans_update(self, path, trans):
        """
        apply transformation to path on filesystem)
        returns
        - the new path (tmp file) if trans
        - original path if no trans
        - None/empty string if error
        """
        if not trans:
            return path
        self.log.dbg(f'executing write transformation {trans}')
        tmp = get_unique_tmp_name()
        if not trans.transform(path, tmp, debug=self.debug,
                               templater=self.templater):
            msg = f'transformation \"{trans.key}\" failed for {path}'
            self.log.err(msg)
            if os.path.exists(tmp):
                removepath(tmp, logger=self.log)
            return None
        return tmp
