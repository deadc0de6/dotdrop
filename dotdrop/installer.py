"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the installation of dotfiles
"""

import os

# local imports
from dotdrop.logger import Logger
from dotdrop.comparator import Comparator
from dotdrop.templategen import Templategen
import dotdrop.utils as utils


class Installer:

    BACKUP_SUFFIX = '.dotdropbak'

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, workdir='~/.config/dotdrop',
                 debug=False, diff=True, totemp=None, showdiff=False):
        self.create = create
        self.backup = backup
        self.dry = dry
        self.safe = safe
        self.workdir = os.path.expanduser(workdir)
        self.base = base
        self.debug = debug
        self.diff = diff
        self.totemp = totemp
        self.showdiff = showdiff
        self.comparing = False
        self.action_executed = False
        self.log = Logger()

    def install(self, templater, src, dst, actions=[], noempty=False):
        """install the src to dst using a template"""
        self.action_executed = False
        src = os.path.join(self.base, os.path.expanduser(src))
        if not os.path.exists(src):
            self.log.err('source dotfile does not exist: {}'.format(src))
            return []
        dst = os.path.expanduser(dst)
        if self.totemp:
            dst = self._pivot_path(dst, self.totemp)
        if utils.samefile(src, dst):
            # symlink loop
            self.log.err('dotfile points to itself: {}'.format(dst))
            return []
        if self.debug:
            self.log.dbg('install {} to {}'.format(src, dst))
        if os.path.isdir(src):
            return self._handle_dir(templater, src, dst, actions=actions,
                                    noempty=noempty)
        return self._handle_file(templater, src, dst,
                                 actions=actions, noempty=noempty)

    def link(self, templater, src, dst, actions=[]):
        """set src as the link target of dst"""
        self.action_executed = False
        src = os.path.join(self.base, os.path.expanduser(src))
        if not os.path.exists(src):
            self.log.err('source dotfile does not exist: {}'.format(src))
            return []
        dst = os.path.expanduser(dst)
        if self.totemp:
            # ignore actions
            return self.install(templater, src, dst, actions=[])

        if Templategen.is_template(src):
            if self.debug:
                self.log.dbg('dotfile is a template')
                self.log.dbg('install to {} and symlink'.format(self.workdir))
            tmp = self._pivot_path(dst, self.workdir, striphome=True)
            i = self.install(templater, src, tmp, actions=actions)
            if not i and not os.path.exists(tmp):
                return []
            src = tmp
        return self._link(src, dst, actions=actions)

    def _link(self, src, dst, actions=[]):
        """set src as a link target of dst"""
        if os.path.lexists(dst):
            if os.path.realpath(dst) == os.path.realpath(src):
                if self.debug:
                    self.log.dbg('ignoring "{}", link exists'.format(dst))
                return []
            if self.dry:
                self.log.dry('would remove {} and link to {}'.format(dst, src))
                return []
            msg = 'Remove "{}" for link creation?'.format(dst)
            if self.safe and not self.log.ask(msg):
                msg = 'ignoring "{}", link was not created'
                self.log.warn(msg.format(dst))
                return []
            try:
                utils.remove(dst)
            except OSError as e:
                self.log.err('something went wrong with {}: {}'.format(src, e))
                return []
        if self.dry:
            self.log.dry('would link {} to {}'.format(dst, src))
            return []
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            self.log.err('creating directory for {}'.format(dst))
            return []
        self._exec_pre_actions(actions)
        os.symlink(src, dst)
        self.log.sub('linked {} to {}'.format(dst, src))
        return [(src, dst)]

    def _handle_file(self, templater, src, dst, actions=[], noempty=False):
        """install src to dst when is a file"""
        if self.debug:
            self.log.dbg('generate template for {}'.format(src))
            self.log.dbg('ignore empty: {}'.format(noempty))
        if utils.samefile(src, dst):
            # symlink loop
            self.log.err('dotfile points to itself: {}'.format(dst))
            return []
        content = templater.generate(src)
        if noempty and utils.content_empty(content):
            self.log.warn('ignoring empty template: {}'.format(src))
            return []
        if content is None:
            self.log.err('generate from template {}'.format(src))
            return []
        if not os.path.exists(src):
            self.log.err('source dotfile does not exist: {}'.format(src))
            return []
        st = os.stat(src)
        ret = self._write(src, dst, content, st.st_mode, actions=actions)
        if ret < 0:
            self.log.err('installing {} to {}'.format(src, dst))
            return []
        if ret > 0:
            if self.debug:
                self.log.dbg('ignoring {}'.format(dst))
            return []
        if ret == 0:
            if not self.dry and not self.comparing:
                self.log.sub('copied {} to {}'.format(src, dst))
            return [(src, dst)]
        return []

    def _handle_dir(self, templater, src, dst, actions=[], noempty=False):
        """install src to dst when is a directory"""
        if self.debug:
            self.log.dbg('install dir {}'.format(src))
            self.log.dbg('ignore empty: {}'.format(noempty))
        ret = []
        if not self._create_dirs(dst):
            return []
        # handle all files in dir
        for entry in os.listdir(src):
            f = os.path.join(src, entry)
            if not os.path.isdir(f):
                res = self._handle_file(templater, f, os.path.join(dst, entry),
                                        actions=actions, noempty=noempty)
                ret.extend(res)
            else:
                res = self._handle_dir(templater, f, os.path.join(dst, entry),
                                       actions=actions, noempty=noempty)
                ret.extend(res)
        return ret

    def _fake_diff(self, dst, content):
        """fake diff by comparing file content with content"""
        cur = ''
        with open(dst, 'br') as f:
            cur = f.read()
        return cur == content

    def _write(self, src, dst, content, rights, actions=[]):
        """write content to file
        return  0 for success,
                1 when already exists
               -1 when error"""
        if self.dry:
            self.log.dry('would install {}'.format(dst))
            return 0
        if os.path.lexists(dst):
            samerights = os.stat(dst).st_mode == rights
            if self.diff and self._fake_diff(dst, content) and samerights:
                if self.debug:
                    self.log.dbg('{} is the same'.format(dst))
                return 1
            if self.safe:
                if self.debug:
                    self.log.dbg('change detected for {}'.format(dst))
                if self.showdiff:
                    self._diff_before_write(src, dst, content)
                if not self.log.ask('Overwrite \"{}\"'.format(dst)):
                    self.log.warn('ignoring {}'.format(dst))
                    return 1
        if self.backup and os.path.lexists(dst):
            self._backup(dst)
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            self.log.err('creating directory for {}'.format(dst))
            return -1
        if self.debug:
            self.log.dbg('write content to {}'.format(dst))
        self._exec_pre_actions(actions)
        try:
            with open(dst, 'wb') as f:
                f.write(content)
        except NotADirectoryError as e:
            self.log.err('opening dest file: {}'.format(e))
            return -1
        os.chmod(dst, rights)
        return 0

    def _diff_before_write(self, src, dst, src_content):
        """diff before writing when using --showdiff - not efficient"""
        # create tmp to diff for templates
        tmpfile = utils.get_tmpfile()
        with open(tmpfile, 'wb') as f:
            f.write(src_content)
        comp = Comparator(debug=self.debug)
        diff = comp.compare(tmpfile, dst)
        # fake the output for readability
        self.log.log('diff \"{}\" VS \"{}\"'.format(src, dst))
        self.log.emph(diff)
        if tmpfile:
            utils.remove(tmpfile)

    def _create_dirs(self, directory):
        """mkdir -p <directory>"""
        if not self.create and not os.path.exists(directory):
            return False
        if os.path.exists(directory):
            return True
        if self.dry:
            self.log.dry('would mkdir -p {}'.format(directory))
            return True
        if self.debug:
            self.log.dbg('mkdir -p {}'.format(directory))
        os.makedirs(directory)
        return os.path.exists(directory)

    def _backup(self, path):
        """backup file pointed by path"""
        if self.dry:
            return
        dst = path.rstrip(os.sep) + self.BACKUP_SUFFIX
        self.log.log('backup {} to {}'.format(path, dst))
        os.rename(path, dst)

    def _pivot_path(self, path, newdir, striphome=False):
        """change path to be under newdir"""
        if striphome:
            home = os.path.expanduser('~')
            path = path.lstrip(home)
        sub = path.lstrip(os.sep)
        return os.path.join(newdir, sub)

    def _exec_pre_actions(self, actions):
        """execute pre-actions if any"""
        if self.action_executed:
            return
        for action in actions:
            if self.dry:
                self.log.dry('would execute action: {}'.format(action))
            else:
                if self.debug:
                    self.log.dbg('executing pre action {}'.format(action))
                action.execute()
        self.action_executed = True

    def _install_to_temp(self, templater, src, dst, tmpdir):
        """install a dotfile to a tempdir"""
        tmpdst = self._pivot_path(dst, tmpdir)
        return self.install(templater, src, tmpdst), tmpdst

    def install_to_temp(self, templater, tmpdir, src, dst):
        """install a dotfile to a tempdir"""
        ret = False
        tmpdst = ''
        # save some flags while comparing
        self.comparing = True
        drysaved = self.dry
        self.dry = False
        diffsaved = self.diff
        self.diff = False
        createsaved = self.create
        self.create = True
        # normalize src and dst
        src = os.path.expanduser(src)
        dst = os.path.expanduser(dst)
        if self.debug:
            self.log.dbg('tmp install {} to {}'.format(src, dst))
        # install the dotfile to a temp directory for comparing
        ret, tmpdst = self._install_to_temp(templater, src, dst, tmpdir)
        if self.debug:
            self.log.dbg('tmp installed in {}'.format(tmpdst))
        # reset flags
        self.dry = drysaved
        self.diff = diffsaved
        self.comparing = False
        self.create = createsaved
        return ret, tmpdst
