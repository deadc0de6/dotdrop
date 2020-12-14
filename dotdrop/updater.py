"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the update of dotfiles
"""

import os
import shutil
import filecmp
import fnmatch

# local imports
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.utils import patch_ignores, removepath, get_unique_tmp_name, \
    write_to_tmpfile, must_ignore, mirror_file_rights, get_file_perm
from dotdrop.exceptions import UndefinedException


TILD = '~'


class Updater:

    def __init__(self, dotpath, variables, conf,
                 dry=False, safe=True, debug=False,
                 ignore=[], showpatch=False,
                 ignore_missing_in_dotdrop=False):
        """constructor
        @dotpath: path where dotfiles are stored
        @variables: dictionary of variables for the templates
        @conf: configuration manager
        @dry: simulate
        @safe: ask for overwrite if True
        @debug: enable debug
        @ignore: pattern to ignore when updating
        @showpatch: show patch if dotfile to update is a template
        """
        self.dotpath = dotpath
        self.variables = variables
        self.conf = conf
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.ignore = ignore
        self.ignores = None
        self.showpatch = showpatch
        self.ignore_missing_in_dotdrop = ignore_missing_in_dotdrop
        self.templater = Templategen(variables=self.variables,
                                     base=self.dotpath,
                                     debug=self.debug)
        # save template vars
        self.tvars = self.templater.add_tmp_vars()
        self.log = Logger()

    def update_path(self, path):
        """update the dotfile installed on path"""
        path = os.path.expanduser(path)
        if not os.path.lexists(path):
            self.log.err('\"{}\" does not exist!'.format(path))
            return False
        dotfiles = self.conf.get_dotfile_by_dst(path)
        if not dotfiles:
            return False
        for dotfile in dotfiles:
            if not dotfile:
                msg = 'invalid dotfile for update: {}'
                self.log.err(msg.format(dotfile.key))
                return False

            if self.debug:
                msg = 'updating {} from path \"{}\"'
                self.log.dbg(msg.format(dotfile, path))
            if not self._update(path, dotfile):
                return False
        return True

    def update_key(self, key):
        """update the dotfile referenced by key"""
        dotfile = self.conf.get_dotfile(key)
        if not dotfile:
            return False
        if self.debug:
            self.log.dbg('updating {} from key \"{}\"'.format(dotfile, key))
        path = self.conf.path_to_dotfile_dst(dotfile.dst)
        return self._update(path, dotfile)

    def _update(self, path, dotfile):
        """update dotfile from file pointed by path"""
        ret = False
        new_path = None
        ignores = list(set(self.ignore + dotfile.upignore))
        self.ignores = patch_ignores(ignores, dotfile.dst, debug=self.debug)
        if self.debug:
            self.log.dbg('ignore pattern(s): {}'.format(self.ignores))

        deployed_path = os.path.expanduser(path)
        local_path = os.path.join(self.dotpath, dotfile.src)
        local_path = os.path.expanduser(local_path)

        if not os.path.exists(deployed_path):
            msg = '\"{}\" does not exist'
            self.log.err(msg.format(deployed_path))
            return False

        if not os.path.exists(local_path):
            msg = '\"{}\" does not exist, import it first'
            self.log.err(msg.format(local_path))
            return False

        ignore_missing_in_dotdrop = self.ignore_missing_in_dotdrop or \
            dotfile.ignore_missing_in_dotdrop
        if (ignore_missing_in_dotdrop and not os.path.exists(local_path)) or \
                self._ignore([deployed_path, local_path]):
            self.log.sub('\"{}\" ignored'.format(dotfile.key))
            return True
        # apply write transformation if any
        new_path = self._apply_trans_w(deployed_path, dotfile)
        if not new_path:
            return False

        # save current rights
        deployed_mode = get_file_perm(deployed_path)
        local_mode = get_file_perm(local_path)

        # handle the pointed file
        if os.path.isdir(new_path):
            ret = self._handle_dir(new_path, local_path, dotfile)
        else:
            ret = self._handle_file(new_path, local_path, dotfile)

        if deployed_mode != local_mode:
            # mirror rights
            if self.debug:
                m = 'adopt mode {:o} for {}'
                self.log.dbg(m.format(deployed_mode, dotfile.key))
            r = self.conf.update_dotfile(dotfile.key, deployed_mode)
            if r:
                ret = True

        # clean temporary files
        if new_path != deployed_path and os.path.exists(new_path):
            removepath(new_path, logger=self.log)
        return ret

    def _apply_trans_w(self, path, dotfile):
        """apply write transformation to dotfile"""
        trans = dotfile.get_trans_w()
        if not trans:
            return path
        if self.debug:
            self.log.dbg('executing write transformation {}'.format(trans))
        tmp = get_unique_tmp_name()
        self.templater.restore_vars(self.tvars)
        newvars = dotfile.get_dotfile_variables()
        self.templater.add_tmp_vars(newvars=newvars)
        if not trans.transform(path, tmp, templater=self.templater,
                               debug=self.debug):
            msg = 'transformation \"{}\" failed for {}'
            self.log.err(msg.format(trans.key, dotfile.key))
            if os.path.exists(tmp):
                removepath(tmp, logger=self.log)
            return None
        return tmp

    def _is_template(self, path):
        if not Templategen.is_template(path, ignore=self.ignores):
            if self.debug:
                self.log.dbg('{} is NO template'.format(path))
            return False
        self.log.warn('{} uses template, update manually'.format(path))
        return True

    def _show_patch(self, fpath, tpath):
        """provide a way to manually patch the template"""
        content = self._resolve_template(tpath)
        tmp = write_to_tmpfile(content)
        mirror_file_rights(tpath, tmp)
        cmds = ['diff', '-u', tmp, fpath, '|', 'patch', tpath]
        self.log.warn('try patching with: \"{}\"'.format(' '.join(cmds)))
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
        except OSError as e:
            self.log.err(e)
            return False

    def _mirror_rights(self, src, dst):
        srcr = get_file_perm(src)
        dstr = get_file_perm(dst)
        if srcr == dstr:
            return
        if self.debug:
            msg = 'copy rights from {} ({:o}) to {} ({:o})'
            self.log.dbg(msg.format(src, srcr, dst, dstr))
        try:
            mirror_file_rights(src, dst)
        except OSError as e:
            self.log.err(e)

    def _handle_file(self, deployed_path, local_path, dotfile, compare=True):
        """sync path (deployed file) and local_path (dotdrop dotfile path)"""
        if self._ignore([deployed_path, local_path]):
            self.log.sub('\"{}\" ignored'.format(local_path))
            return True
        if self.debug:
            self.log.dbg('update for file {} and {}'.format(
                deployed_path,
                local_path,
            ))
        if self._is_template(local_path):
            # dotfile is a template
            if self.debug:
                self.log.dbg('{} is a template'.format(local_path))
            if self.showpatch:
                try:
                    self._show_patch(deployed_path, local_path)
                except UndefinedException as e:
                    msg = 'unable to show patch for {}: {}'.format(
                        deployed_path,
                        e,
                    )
                    self.log.warn(msg)
            return False
        if compare and \
                filecmp.cmp(deployed_path, local_path, shallow=False) and \
                self._same_rights(deployed_path, local_path):
            # no difference
            if self.debug:
                self.log.dbg('identical files: {} and {}'.format(
                    deployed_path,
                    local_path,
                ))
            return True
        if not self._overwrite(deployed_path, local_path):
            return False
        try:
            if self.dry:
                self.log.dry('would cp {} {}'.format(deployed_path, local_path))
            else:
                if self.debug:
                    self.log.dbg('cp {} {}'.format(deployed_path, local_path))
                shutil.copyfile(deployed_path, local_path)
                self._mirror_rights(deployed_path, local_path)
                self.log.sub('\"{}\" updated'.format(local_path))
        except IOError as e:
            self.log.warn('{} update failed, do manually: {}'.format(
                deployed_path,
                e
            ))
            return False
        return True

    def _handle_dir(self, deployed_path, local_path, dotfile):
        """sync path (local dir) and local_path (dotdrop dir path)"""
        if self.debug:
            self.log.dbg('handle update for dir {} to {}'.format(
                deployed_path,
                local_path,
            ))
        # paths must be absolute (no tildes)
        path = os.path.expanduser(deployed_path)
        local_path = os.path.expanduser(local_path)
        if self._ignore([path, local_path]):
            self.log.sub('\"{}\" ignored'.format(local_path))
            return True
        # find the differences
        diff = filecmp.dircmp(path, local_path, ignore=None)
        # handle directories diff
        ret = self._merge_dirs(diff, dotfile)
        self._mirror_rights(path, local_path)
        return ret

    def _merge_dirs(self, diff, dotfile):
        """Synchronize directories recursively."""
        left, right = diff.left, diff.right
        if self.debug:
            self.log.dbg('sync dir {} to {}'.format(left, right))
        if self._ignore([left, right]):
            return True

        # create dirs that don't exist in dotdrop
        for toadd in diff.left_only:
            exist = os.path.join(left, toadd)
            if not os.path.isdir(exist):
                # ignore files for now
                continue
            # match to dotdrop dotpath
            new = os.path.join(right, toadd)
            if self._ignore([exist, new]):
                self.log.sub('\"{}\" ignored'.format(exist))
                continue
            if self.dry:
                self.log.dry('would cp -r {} {}'.format(exist, new))
                continue
            if self.debug:
                self.log.dbg('cp -r {} {}'.format(exist, new))

            # Newly created directory should be copied as is (for efficiency).
            def ig(src, names):
                whitelist, blacklist = set(), set()
                for ignore in self.ignores:
                    for name in names:
                        path = os.path.join(src, name)
                        if ignore.startswith('!') and \
                                fnmatch.fnmatch(path, ignore[1:]):
                            # add to whitelist
                            whitelist.add(name)
                        elif fnmatch.fnmatch(path, ignore):
                            # add to blacklist
                            blacklist.add(name)
                return blacklist - whitelist

            shutil.copytree(exist, new, ignore=ig)
            self.log.sub('\"{}\" dir added'.format(new))

        # remove dirs that don't exist in deployed version
        for toremove in diff.right_only:
            old = os.path.join(right, toremove)
            if not os.path.isdir(old):
                # ignore files for now
                continue
            if self._ignore([old]):
                continue
            if self.dry:
                self.log.dry('would rm -r {}'.format(old))
                continue
            if self.debug:
                self.log.dbg('rm -r {}'.format(old))
            if not self._confirm_rm_r(old):
                continue
            removepath(old, logger=self.log)
            self.log.sub('\"{}\" dir removed'.format(old))

        # handle files diff
        # sync files that exist in both but are different
        fdiff = diff.diff_files
        fdiff.extend(diff.funny_files)
        fdiff.extend(diff.common_funny)
        for f in fdiff:
            fleft = os.path.join(left, f)
            fright = os.path.join(right, f)
            if self._ignore([fleft, fright]):
                continue
            if self.dry:
                self.log.dry('would cp {} {}'.format(fleft, fright))
                continue
            if self.debug:
                self.log.dbg('cp {} {}'.format(fleft, fright))
            self._handle_file(fleft, fright, dotfile, compare=False)

        # copy files that don't exist in dotdrop
        for toadd in diff.left_only:
            exist = os.path.join(left, toadd)
            if os.path.isdir(exist):
                # ignore dirs, done above
                continue
            new = os.path.join(right, toadd)
            if self._ignore([exist, new]):
                continue
            if self.dry:
                self.log.dry('would cp {} {}'.format(exist, new))
                continue
            if self.debug:
                self.log.dbg('cp {} {}'.format(exist, new))
            shutil.copyfile(exist, new)
            self._mirror_rights(exist, new)
            self.log.sub('\"{}\" added'.format(new))

        # remove files that don't exist in deployed version
        for toremove in diff.right_only:
            new = os.path.join(right, toremove)
            if not os.path.exists(new):
                continue
            if os.path.isdir(new):
                # ignore dirs, done above
                continue
            if self._ignore([new]):
                continue
            if self.dry:
                self.log.dry('would rm {}'.format(new))
                continue
            if self.debug:
                self.log.dbg('rm {}'.format(new))
            removepath(new, logger=self.log)
            self.log.sub('\"{}\" removed'.format(new))

        # compare rights
        for common in diff.common_files:
            leftf = os.path.join(left, common)
            rightf = os.path.join(right, common)
            if not self._same_rights(leftf, rightf):
                self._mirror_rights(leftf, rightf)

        # Recursively decent into common subdirectories.
        for subdir in diff.subdirs.values():
            self._merge_dirs(subdir, dotfile)

        # Nothing more to do here.
        return True

    def _overwrite(self, src, dst):
        """ask for overwritting"""
        msg = 'Overwrite \"{}\" with \"{}\"?'.format(dst, src)
        if self.safe and not self.log.ask(msg):
            return False
        return True

    def _confirm_rm_r(self, directory):
        """ask for rm -r directory"""
        msg = 'Recursively remove \"{}\"?'.format(directory)
        if self.safe and not self.log.ask(msg):
            return False
        return True

    def _ignore(self, paths):
        if must_ignore(paths, self.ignores, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring update for {}'.format(paths))
            return True
        return False
