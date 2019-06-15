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
from dotdrop.templategen import Templategen
from dotdrop.utils import patch_ignores, remove, get_unique_tmp_name, \
    write_to_tmpfile, must_ignore


TILD = '~'


class Updater:

    def __init__(self, dotpath, variables,
                 dotfile_key_getter, dotfile_dst_getter,
                 dotfile_path_normalizer,
                 dry=False, safe=True,
                 debug=False, ignore=[], showpatch=False):
        """constructor
        @dotpath: path where dotfiles are stored
        @variables: dictionary of variables for the templates
        @dotfile_key_getter: func to get a dotfile by key
        @dotfile_dst_getter: func to get a dotfile by dst
        @dotfile_path_normalizer: func to normalize dotfile dst
        @dry: simulate
        @safe: ask for overwrite if True
        @debug: enable debug
        @ignore: pattern to ignore when updating
        @showpatch: show patch if dotfile to update is a template
        """
        self.dotpath = dotpath
        self.variables = variables
        self.dotfile_key_getter = dotfile_key_getter
        self.dotfile_dst_getter = dotfile_dst_getter
        self.dotfile_path_normalizer = dotfile_path_normalizer
        self.dry = dry
        self.safe = safe
        self.debug = debug
        self.ignore = ignore
        self.showpatch = showpatch
        self.log = Logger()

    def update_path(self, path):
        """update the dotfile installed on path"""
        path = os.path.expanduser(path)
        if not os.path.lexists(path):
            self.log.err('\"{}\" does not exist!'.format(path))
            return False
        dotfile = self.dotfile_dst_getter(path)
        if not dotfile:
            return False
        if self.debug:
            self.log.dbg('updating {} from path \"{}\"'.format(dotfile, path))
        return self._update(path, dotfile)

    def update_key(self, key):
        """update the dotfile referenced by key"""
        dotfile = self.dotfile_key_getter(key)
        if not dotfile:
            return False
        if self.debug:
            self.log.dbg('updating {} from key \"{}\"'.format(dotfile, key))
        path = self.dotfile_path_normalizer(dotfile.dst)
        return self._update(path, dotfile)

    def _update(self, path, dotfile):
        """update dotfile from file pointed by path"""
        ret = False
        new_path = None
        ignores = list(set(self.ignore + dotfile.upignore))
        self.ignores = patch_ignores(ignores, dotfile.dst, debug=self.debug)
        if self.debug:
            self.log.dbg('ignore pattern(s): {}'.format(self.ignores))

        path = os.path.expanduser(path)
        dtpath = os.path.join(self.dotpath, dotfile.src)
        dtpath = os.path.expanduser(dtpath)

        if self._ignore([path, dtpath]):
            self.log.sub('\"{}\" ignored'.format(dotfile.key))
            return True
        # apply write transformation if any
        new_path = self._apply_trans_w(path, dotfile)
        if not new_path:
            return False
        if os.path.isdir(new_path):
            ret = self._handle_dir(new_path, dtpath)
        else:
            ret = self._handle_file(new_path, dtpath)
        # clean temporary files
        if new_path != path and os.path.exists(new_path):
            remove(new_path)
        return ret

    def _apply_trans_w(self, path, dotfile):
        """apply write transformation to dotfile"""
        trans = dotfile.get_trans_w()
        if not trans:
            return path
        if self.debug:
            self.log.dbg('executing write transformation {}'.format(trans))
        tmp = get_unique_tmp_name()
        if not trans.transform(path, tmp):
            msg = 'transformation \"{}\" failed for {}'
            self.log.err(msg.format(trans.key, dotfile.key))
            if os.path.exists(tmp):
                remove(tmp)
            return None
        return tmp

    def _is_template(self, path):
        if not Templategen.is_template(path):
            if self.debug:
                self.log.dbg('{} is NO template'.format(path))
            return False
        self.log.warn('{} uses template, update manually'.format(path))
        return True

    def _show_patch(self, fpath, tpath):
        """provide a way to manually patch the template"""
        content = self._resolve_template(tpath)
        tmp = write_to_tmpfile(content)
        cmds = ['diff', '-u', tmp, fpath, '|', 'patch', tpath]
        self.log.warn('try patching with: \"{}\"'.format(' '.join(cmds)))
        return False

    def _resolve_template(self, tpath):
        """resolve the template to a temporary file"""
        t = Templategen(variables=self.variables, base=self.dotpath,
                        debug=self.debug)
        return t.generate(tpath)

    def _handle_file(self, path, dtpath, compare=True):
        """sync path (deployed file) and dtpath (dotdrop dotfile path)"""
        if self._ignore([path, dtpath]):
            self.log.sub('\"{}\" ignored'.format(dtpath))
            return True
        if self.debug:
            self.log.dbg('update for file {} and {}'.format(path, dtpath))
        if self._is_template(dtpath):
            # dotfile is a template
            if self.debug:
                self.log.dbg('{} is a template'.format(dtpath))
            if self.showpatch:
                self._show_patch(path, dtpath)
            return False
        if compare and filecmp.cmp(path, dtpath, shallow=True):
            # no difference
            if self.debug:
                self.log.dbg('identical files: {} and {}'.format(path, dtpath))
            return True
        if not self._overwrite(path, dtpath):
            return False
        try:
            if self.dry:
                self.log.dry('would cp {} {}'.format(path, dtpath))
            else:
                if self.debug:
                    self.log.dbg('cp {} {}'.format(path, dtpath))
                shutil.copyfile(path, dtpath)
                self.log.sub('\"{}\" updated'.format(dtpath))
        except IOError as e:
            self.log.warn('{} update failed, do manually: {}'.format(path, e))
            return False
        return True

    def _handle_dir(self, path, dtpath):
        """sync path (deployed dir) and dtpath (dotdrop dir path)"""
        if self.debug:
            self.log.dbg('handle update for dir {} to {}'.format(path, dtpath))
        # paths must be absolute (no tildes)
        path = os.path.expanduser(path)
        dtpath = os.path.expanduser(dtpath)
        if self._ignore([path, dtpath]):
            self.log.sub('\"{}\" ignored'.format(dtpath))
            return True
        # find the differences
        diff = filecmp.dircmp(path, dtpath, ignore=None)
        # handle directories diff
        return self._merge_dirs(diff)

    def _merge_dirs(self, diff):
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
            shutil.copytree(exist, new)
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
            remove(old)
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
            self._handle_file(fleft, fright, compare=False)

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
            remove(new)
            self.log.sub('\"{}\" removed'.format(new))

        # Recursively decent into common subdirectories.
        for subdir in diff.subdirs.values():
            self._merge_dirs(subdir)

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
