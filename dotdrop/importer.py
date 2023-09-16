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
    get_file_perm, get_umask, must_ignore, \
    get_unique_tmp_name, removepath, copytree_with_ign, \
    copyfile
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
        for ign in ignore:
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
                    import_transw="",
                    import_transr=""):
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

        # check transw if any
        trans_write = None
        trans_read = None
        if import_transw:
            trans_write = self.conf.get_trans_w(import_transw)
        if import_transr:
            trans_read = self.conf.get_trans_r(import_transr)

        return self._import(path, import_as=import_as,
                            import_link=import_link,
                            import_mode=import_mode,
                            trans_write=trans_write,
                            trans_read=trans_read)

    def _import(self, path, import_as=None,
                import_link=LinkTypes.NOLINK,
                import_mode=False,
                trans_write=None, trans_read=None):
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
                msg = f'\"{dst}\" is a symlink, dereference it and continue?'
                if not self.log.ask(msg):
                    return 0

        # create src path
        src = strip_home(dst)
        if import_as:
            # handle import as
            src = os.path.expanduser(import_as)
            src = src.rstrip(os.sep)
            src = os.path.abspath(src)
            src = strip_home(src)
            self.log.dbg(f'import src for {dst} as {src}')
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
            self.log.err(f'importing \"{path}\" failed!')
            return -1

        if self._already_exists(src, dst):
            return -1

        self.log.dbg(f'import dotfile: src:{src} dst:{dst}')

        if not self._import_to_dotpath(src, dst, trans_write=trans_write):
            return -1

        return self._import_in_config(path, src, dst, perm, linktype,
                                      import_mode,
                                      trans_w=trans_write,
                                      trans_r=trans_read)

    def _import_in_config(self, path, src, dst, perm,
                          linktype, import_mode,
                          trans_r=None, trans_w=None):
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
                                        trans_read=trans_r,
                                        trans_write=trans_w)
        if not retconf:
            self.log.warn(f'\"{path}\" ignored during import')
            return 0

        self.log.sub(f'\"{path}\" imported')
        return 1

    def _check_existing_dotfile(self, src, dst):
        """
        check if a dotfile in the dotpath
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

    def _import_to_dotpath(self, in_dotpath, in_fs, trans_write=None):
        """
        prepare hierarchy for dotfile in dotpath and copy file
        """
        srcf = os.path.join(self.dotpath, in_dotpath)

        # check we are not overwritting
        if not self._check_existing_dotfile(srcf, in_fs):
            return False

        # import the file
        if self.dry:
            self.log.dry(f'would copy {in_fs} to {srcf}')
            return True

        # apply trans_w
        in_fs = self._apply_trans_w(in_fs, trans_write)
        if not in_fs:
            # transformation failed
            return False
        # copy the file to the dotpath
        try:
            if not os.path.isdir(in_fs):
                # is a file
                self.log.dbg(f'{in_fs} is file')
                copyfile(in_fs, srcf, debug=self.debug)
            else:
                # is a dir
                if os.path.exists(srcf):
                    shutil.rmtree(srcf)
                self.log.dbg(f'{in_fs} is dir')
                copytree_with_ign(in_fs, srcf,
                                  ignore_func=self._ignore,
                                  debug=self.debug)
        except shutil.Error as exc:
            in_dotpath = exc.args[0][0][0]
            why = exc.args[0][0][2]
            self.log.err(f'importing \"{in_fs}\" failed: {why}')

        return os.path.exists(srcf)

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

    def _apply_trans_w(self, path, trans):
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
