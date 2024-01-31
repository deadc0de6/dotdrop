"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the update of dotfiles
"""

import os
import shutil
import filecmp

# local imports
from dotdrop.logger import Logger
from dotdrop.ftree import FTreeDir
from dotdrop.templategen import Templategen
from dotdrop.utils import ignores_to_absolute, removepath, \
    get_unique_tmp_name, write_to_tmpfile, must_ignore, \
    mirror_file_rights, get_file_perm, diff
from dotdrop.exceptions import UndefinedException


TILD = '~'


class Updater:
    """dotfiles updater"""

    def __init__(self, dotpath, variables, conf,
                 profile_key, dry=False, safe=True,
                 debug=False, ignore=None, showpatch=False,
                 ignore_missing_in_dotdrop=False):
        """constructor
        @dotpath: path where dotfiles are stored
        @variables: dictionary of variables for the templates
        @conf: configuration manager
        @profile_key: the profile key
        @dry: simulate
        @safe: ask for overwrite if True
        @debug: enable debug
        @ignore: pattern to ignore when updating
        @showpatch: show patch if dotfile to update is a template
        """
        self.dotpath = dotpath
        self.variables = variables
        self.conf = conf
        self.profile_key = profile_key
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.ignore = ignore or []
        self.showpatch = showpatch
        self.ignore_missing_in_dotdrop = ignore_missing_in_dotdrop
        self.templater = Templategen(variables=self.variables,
                                     base=self.dotpath,
                                     debug=self.debug)
        # save template vars
        self.tvars = self.templater.add_tmp_vars()
        self.log = Logger(debug=self.debug)

    def update_path(self, path):
        """update the dotfile installed on path"""
        path = os.path.expanduser(path)
        if not os.path.lexists(path):
            self.log.err(f'\"{path}\" does not exist!')
            return False
        dotfiles = self.conf.get_dotfile_by_dst(path,
                                                profile_key=self.profile_key)
        if not dotfiles:
            return False
        for dotfile in dotfiles:
            if not dotfile:
                err = f'invalid dotfile for update: {dotfile.key}'
                self.log.err(err)
                return False

            msg = f'updating {dotfile} from path \"{path}\"'
            self.log.dbg(msg)
            if not self._update(path, dotfile):
                return False
        return True

    def update_key(self, key):
        """update the dotfile referenced by key"""
        dotfile = self.conf.get_dotfile(key, profile_key=self.profile_key)
        if not dotfile:
            self.log.dbg(f'no such dotfile: \"{key}\"')
            msg = f'invalid dotfile for update: {key}'
            self.log.err(msg)
            return False
        self.log.dbg(f'updating {dotfile} from key \"{key}\"')
        path = self.conf.path_to_dotfile_dst(dotfile.dst)
        return self._update(path, dotfile)

    def _update(self, path, dotfile):
        """update dotfile from file pointed by path"""
        ret = False
        new_path = None
        ignores = list(set(self.ignore + dotfile.upignore))
        prefixes = [dotfile.dst, dotfile.src]
        ignores = ignores_to_absolute(ignores, prefixes,
                                      debug=self.debug)
        self.log.dbg(f'ignore pattern(s) for {path}: {ignores}')

        deployed_path = os.path.expanduser(path)
        local_path = os.path.join(self.dotpath, dotfile.src)
        local_path = os.path.expanduser(local_path)

        if not os.path.exists(deployed_path):
            msg = f'\"{deployed_path}\" does not exist'
            self.log.err(msg)
            return False

        if not os.path.exists(local_path):
            msg = f'\"{local_path}\" does not exist, import it first'
            self.log.err(msg)
            return False

        ignore_missing_in_dotdrop = self.ignore_missing_in_dotdrop or \
            dotfile.ignore_missing_in_dotdrop

        if ignore_missing_in_dotdrop and not os.path.exists(local_path):
            self.log.sub(f'\"{dotfile.key}\" ignored')
            return True

        # apply write transformation if any
        new_path = self._apply_trans_update(deployed_path, dotfile)
        if not new_path:
            return False

        # save current rights
        deployed_mode = get_file_perm(deployed_path)
        local_mode = get_file_perm(local_path)

        # handle the pointed file
        if os.path.isdir(new_path):
            ret = self._handle_dir(new_path, local_path,
                                   dotfile, ignores)
        else:
            ret = self._handle_file(new_path, local_path,
                                    ignores)
        if not ret:
            return False

        # mirror rights
        if deployed_mode != local_mode:
            msg = f'adopt mode {deployed_mode:o} for {dotfile.key}'
            self.log.dbg(msg)
            if self.conf.update_dotfile(dotfile.key, deployed_mode):
                ret = True
            self._mirror_file_perms(deployed_path, local_path)

        # clean temporary files
        if new_path != deployed_path and os.path.exists(new_path):
            removepath(new_path, logger=self.log)
        return ret

    def _apply_trans_update(self, path, dotfile):
        """apply write transformation to dotfile"""
        trans = dotfile.get_trans_update()
        if not trans:
            return path
        self.log.dbg(f'executing write transformation {trans}')
        tmp = get_unique_tmp_name()
        self.templater.restore_vars(self.tvars)
        newvars = dotfile.get_dotfile_variables()
        self.templater.add_tmp_vars(newvars=newvars)
        if not trans.transform(path, tmp, templater=self.templater,
                               debug=self.debug):
            if os.path.exists(tmp):
                removepath(tmp, logger=self.log)
            err = f'transformation \"{trans.key}\" failed for {dotfile.key}'
            self.log.err(err)
            return None
        return tmp

    def _is_template(self, path):
        if not Templategen.path_is_template(path,
                                            debug=self.debug):
            self.log.dbg(f'{path} is NO template')
            return False
        self.log.warn(f'{path} uses template, update manually')
        return True

    def _show_patch(self, fpath, tpath):
        """provide a way to manually patch the template"""
        content = self._resolve_template(tpath)
        tmp = write_to_tmpfile(content)
        mirror_file_rights(tpath, tmp)
        cmds = ['diff', '-u', tmp, fpath, '|', 'patch', tpath]
        cmdss = ' '.join(cmds)
        self.log.warn(f'try patching with: \"{cmdss}\"')
        return False

    def _resolve_template(self, tpath):
        """resolve the template to a temporary file"""
        self.templater.restore_vars(self.tvars)
        return self.templater.generate(tpath)

    def _same_rights(self, left, right):
        """return True if files have the same modes"""
        try:
            lefts = get_file_perm(left)
            rights = get_file_perm(right)
            return lefts == rights
        except OSError as exc:
            self.log.err(exc)
            return False

    def _mirror_file_perms(self, src, dst):
        srcr = get_file_perm(src)
        dstr = get_file_perm(dst)
        if srcr == dstr:
            return
        msg = f'copy rights from {src} ({srcr:o}) to {dst} ({dstr:o})'
        self.log.dbg(msg)
        try:
            mirror_file_rights(src, dst)
        except OSError as exc:
            self.log.err(exc)

    def _handle_file(self, deployed_path, local_path,
                     ignores, compare=True):
        """sync path (deployed file) and local_path (dotdrop dotfile path)"""
        if self._must_ignore([deployed_path, local_path], ignores):
            self.log.sub(f'\"{local_path}\" ignored')
            return True
        self.log.dbg(f'update for file {deployed_path} and {local_path}')
        if self._is_template(local_path):
            # dotfile is a template
            self.log.dbg(f'{local_path} is a template')
            if self.showpatch:
                try:
                    self._show_patch(deployed_path, local_path)
                except UndefinedException as exc:
                    msg = f'unable to show patch for {deployed_path}: {exc}'
                    self.log.warn(msg)
            return False
        if compare and \
                filecmp.cmp(deployed_path, local_path, shallow=False) and \
                self._same_rights(deployed_path, local_path):
            # no difference
            self.log.dbg(f'identical files: {deployed_path} and {local_path}')
            return True
        if not self._overwrite(deployed_path, local_path):
            return False
        try:
            if self.dry:
                self.log.dry(f'would cp {deployed_path} {local_path}')
            else:
                self.log.dbg(f'cp {deployed_path} {local_path}')
                shutil.copy2(deployed_path, local_path)
                # self._mirror_file_perms(deployed_path, local_path)
                self.log.sub(f'\"{local_path}\" updated')
        except IOError as exc:
            self.log.warn(f'{deployed_path} update failed, do manually: {exc}')
            return False
        return True

    def _handle_dir(self, deployed_path, local_path,
                    dotfile, ignores):
        """sync path (local dir) and local_path (dotdrop dir path)"""
        self.log.dbg(f'handle update for dir {deployed_path} to {local_path}')

        # get absolute paths
        deployed_path = os.path.expanduser(deployed_path)
        local_path = os.path.expanduser(local_path)

        local_tree = FTreeDir(local_path,
                              ignores=ignores,
                              debug=self.debug)
        deploy_tree = FTreeDir(deployed_path,
                               ignores=ignores,
                               debug=self.debug)
        lonly, ronly, common = local_tree.compare(deploy_tree)

        # those only in dotpath
        for i in lonly:
            path = os.path.join(local_path, i)
            if self.dry:
                self.log.dry(f'would rm -r {path}')
                continue
            self.log.dbg(f'rm -r {path}')
            if not self._confirm_rm_r(path):
                continue
            removepath(path, logger=self.log)
            self.log.sub(f'\"{path}\" removed')

        ignore_missing_in_dotdrop = self.ignore_missing_in_dotdrop or \
            dotfile.ignore_missing_in_dotdrop
        if not ignore_missing_in_dotdrop:
            for i in ronly:
                # only in deployed dir
                srcpath = os.path.join(deployed_path, i)
                dstpath = os.path.join(local_path, i)
                if self.dry:
                    self.log.dry(f'would cp -r {srcpath} {dstpath}')
                    continue
                self.log.dbg(f'cp {srcpath} {dstpath}')
                try:
                    if not os.path.isdir(srcpath):
                        # we do not care about directory
                        os.makedirs(os.path.dirname(dstpath), exist_ok=True)
                        shutil.copy2(srcpath, dstpath)
                    # self._mirror_file_perms(srcpath, dstpath)
                except IOError as exc:
                    msg = f'{srcpath} update failed, do manually: {exc}'
                    self.log.warn(msg)
                    return False
                self.log.sub(f'\"{dstpath}\" updated')

        for i in common:
            srcpath = os.path.join(deployed_path, i)
            dstpath = os.path.join(local_path, i)
            if os.path.isdir(srcpath):
                continue
            if not self._same_rights(dstpath, srcpath):
                # update rights
                self._mirror_file_perms(srcpath, dstpath)
            out = diff(modified=dstpath, original=srcpath,
                       debug=self.debug)
            if not out:
                continue
            if self.dry:
                msg = f'would update content of {dstpath} from {srcpath}'
                self.log.dry(msg)
                continue
            self.log.dbg(f'cp {srcpath} {dstpath}')
            try:
                shutil.copy2(srcpath, dstpath)
                self._mirror_file_perms(srcpath, dstpath)
            except IOError as exc:
                msg = f'{srcpath} update failed, do manually: {exc}'
                self.log.warn(msg)
                return False
            self.log.sub(f'\"{dstpath}\" content updated')

        return True

    def _overwrite(self, src, dst):
        """ask for overwritting"""
        msg = f'Overwrite \"{dst}\" with \"{src}\"?'
        if self.safe and not self.log.ask(msg):
            return False
        return True

    def _confirm_rm_r(self, directory):
        """ask for rm -r directory"""
        msg = f'Recursively remove \"{directory}\"?'
        if self.safe and not self.log.ask(msg):
            return False
        return True

    def _must_ignore(self, paths, ignores):
        if must_ignore(paths, ignores, debug=self.debug):
            self.log.dbg(f'ignoring update for {paths}')
            return True
        return False
