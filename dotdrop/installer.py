"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

handle the installation of dotfiles
"""

import os
import errno
import shutil

# local imports
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
import dotdrop.utils as utils
from dotdrop.exceptions import UndefinedException


class Installer:

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, workdir='~/.config/dotdrop',
                 debug=False, diff=True, totemp=None, showdiff=False,
                 backup_suffix='.dotdropbak', diff_cmd=''):
        """constructor
        @base: directory path where to search for templates
        @create: create directory hierarchy if missing when installing
        @backup: backup existing dotfile when installing
        @dry: just simulate
        @safe: ask for any overwrite
        @workdir: where to install template before symlinking
        @debug: enable debug
        @diff: diff when installing if True
        @totemp: deploy to this path instead of dotfile dst if not None
        @showdiff: show the diff before overwriting (or asking for)
        @backup_suffix: suffix for dotfile backup file
        @diff_cmd: diff command to use
        """
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
        self.backup_suffix = backup_suffix
        self.diff_cmd = diff_cmd
        self.comparing = False
        self.action_executed = False
        self.log = Logger()

    def _log_install(self, boolean, err):
        if not self.debug:
            return boolean, err
        if boolean:
            self.log.dbg('install: SUCCESS')
        else:
            if err:
                self.log.dbg('install: ERROR: {}'.format(err))
            else:
                self.log.dbg('install: IGNORED')
        return boolean, err

    def install(self, templater, src, dst,
                actionexec=None, noempty=False,
                ignore=[], template=True):
        """
        install src to dst using a template
        @templater: the templater object
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @actionexec: action executor callback
        @noempty: render empty template flag
        @ignore: pattern to ignore when installing
        @template: template this dotfile

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        """
        if self.debug:
            self.log.dbg('installing \"{}\" to \"{}\"'.format(src, dst))
        if not dst or not src:
            if self.debug:
                self.log.dbg('empty dst for {}'.format(src))
            return self._log_install(True, None)
        self.action_executed = False
        src = os.path.join(self.base, os.path.expanduser(src))
        if not os.path.exists(src):
            err = 'source dotfile does not exist: {}'.format(src)
            return self._log_install(False, err)
        dst = os.path.expanduser(dst)
        if self.totemp:
            dst = self._pivot_path(dst, self.totemp)
        if utils.samefile(src, dst):
            # symlink loop
            err = 'dotfile points to itself: {}'.format(dst)
            return self._log_install(False, err)
        isdir = os.path.isdir(src)
        if self.debug:
            self.log.dbg('install {} to {}'.format(src, dst))
            self.log.dbg('is a directory \"{}\": {}'.format(src, isdir))
        if isdir:
            b, e = self._install_dir(templater, src, dst,
                                     actionexec=actionexec,
                                     noempty=noempty, ignore=ignore,
                                     template=template)
            return self._log_install(b, e)
        b, e = self._install_file(templater, src, dst,
                                  actionexec=actionexec,
                                  noempty=noempty, ignore=ignore,
                                  template=template)
        return self._log_install(b, e)

    def link(self, templater, src, dst, actionexec=None, template=True):
        """
        set src as the link target of dst
        @templater: the templater
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @actionexec: action executor callback
        @template: template this dotfile

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        """
        if self.debug:
            self.log.dbg('link \"{}\" to \"{}\"'.format(src, dst))
        if not dst or not src:
            if self.debug:
                self.log.dbg('empty dst for {}'.format(src))
            return self._log_install(True, None)
        self.action_executed = False
        src = os.path.normpath(os.path.join(self.base,
                                            os.path.expanduser(src)))
        if not os.path.exists(src):
            err = 'source dotfile does not exist: {}'.format(src)
            return self._log_install(False, err)
        dst = os.path.normpath(os.path.expanduser(dst))
        if self.totemp:
            # ignore actions
            b, e = self.install(templater, src, dst, actionexec=None,
                                template=template)
            return self._log_install(b, e)

        if template and Templategen.is_template(src):
            if self.debug:
                self.log.dbg('dotfile is a template')
                self.log.dbg('install to {} and symlink'.format(self.workdir))
            tmp = self._pivot_path(dst, self.workdir, striphome=True)
            i, err = self.install(templater, src, tmp, actionexec=actionexec,
                                  template=template)
            if not i and not os.path.exists(tmp):
                return self._log_install(i, err)
            src = tmp
        b, e = self._link(src, dst, actionexec=actionexec)
        return self._log_install(b, e)

    def link_children(self, templater, src, dst, actionexec=None,
                      template=True):
        """
        link all files under a given directory
        @templater: the templater
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @actionexec: action executor callback
        @template: template this dotfile

        return
        - True, None: success
        - False, error_msg: error
        - False, None, ignored
        """
        if self.debug:
            self.log.dbg('link_children \"{}\" to \"{}\"'.format(src, dst))
        if not dst or not src:
            if self.debug:
                self.log.dbg('empty dst for {}'.format(src))
            return self._log_install(True, None)
        self.action_executed = False
        parent = os.path.join(self.base, os.path.expanduser(src))

        # Fail if source doesn't exist
        if not os.path.exists(parent):
            err = 'source dotfile does not exist: {}'.format(parent)
            return self._log_install(False, err)

        # Fail if source not a directory
        if not os.path.isdir(parent):
            if self.debug:
                self.log.dbg('symlink children of {} to {}'.format(src, dst))

            err = 'source dotfile is not a directory: {}'.format(parent)
            return self._log_install(False, err)

        dst = os.path.normpath(os.path.expanduser(dst))
        if not os.path.lexists(dst):
            self.log.sub('creating directory "{}"'.format(dst))
            os.makedirs(dst)

        if os.path.isfile(dst):
            msg = ''.join([
                'Remove regular file {} and ',
                'replace with empty directory?',
            ]).format(dst)

            if self.safe and not self.log.ask(msg):
                err = 'ignoring "{}", nothing installed'.format(dst)
                return self._log_install(False, err)
            os.unlink(dst)
            os.mkdir(dst)

        children = os.listdir(parent)
        srcs = [os.path.normpath(os.path.join(parent, child))
                for child in children]
        dsts = [os.path.normpath(os.path.join(dst, child))
                for child in children]

        installed = 0
        for i in range(len(children)):
            src = srcs[i]
            dst = dsts[i]

            if self.debug:
                self.log.dbg('symlink child {} to {}'.format(src, dst))

            if template and Templategen.is_template(src):
                if self.debug:
                    self.log.dbg('dotfile is a template')
                    self.log.dbg('install to {} and symlink'
                                 .format(self.workdir))
                tmp = self._pivot_path(dst, self.workdir, striphome=True)
                r, e = self.install(templater, src, tmp, actionexec=actionexec,
                                    template=template)
                if not r and e and not os.path.exists(tmp):
                    continue
                src = tmp

            ret, err = self._link(src, dst, actionexec=actionexec)
            if ret:
                installed += 1
                # void actionexec if dotfile installed
                # to prevent from running actions multiple times
                actionexec = None
            else:
                if err:
                    return self._log_install(ret, err)

        return self._log_install(installed > 0, None)

    def _link(self, src, dst, actionexec=None):
        """
        set src as a link target of dst

        return
        - True, None: success
        - False, error_msg: error
        - False, None, ignored
        """
        overwrite = not self.safe
        if os.path.lexists(dst):
            if os.path.realpath(dst) == os.path.realpath(src):
                msg = 'ignoring "{}", link already exists'.format(dst)
                if self.debug:
                    self.log.dbg(msg)
                return False, None
            if self.dry:
                self.log.dry('would remove {} and link to {}'.format(dst, src))
                return True, None
            if self.showdiff:
                self._diff_before_write(src, dst, quiet=False)
            msg = 'Remove "{}" for link creation?'.format(dst)
            if self.safe and not self.log.ask(msg):
                err = 'ignoring "{}", link was not created'.format(dst)
                return False, err
            overwrite = True
            try:
                utils.remove(dst)
            except OSError as e:
                err = 'something went wrong with {}: {}'.format(src, e)
                return False, err
        if self.dry:
            self.log.dry('would link {} to {}'.format(dst, src))
            return True, None
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = 'error creating directory for {}'.format(dst)
            return False, err
        r, e = self._exec_pre_actions(actionexec)
        if not r:
            return False, e
        # re-check in case action created the file
        if os.path.lexists(dst):
            msg = 'Remove "{}" for link creation?'.format(dst)
            if self.safe and not overwrite and not self.log.ask(msg):
                err = 'ignoring "{}", link was not created'.format(dst)
                return False, err
            try:
                utils.remove(dst)
            except OSError as e:
                err = 'something went wrong with {}: {}'.format(src, e)
                return False, err
        os.symlink(src, dst)
        self.log.sub('linked {} to {}'.format(dst, src))
        return True, None

    def _get_tmp_file_vars(self, src, dst):
        tmp = {}
        tmp['_dotfile_sub_abs_src'] = src
        tmp['_dotfile_sub_abs_dst'] = dst
        return tmp

    def _install_file(self, templater, src, dst,
                      actionexec=None, noempty=False,
                      ignore=[], template=True):
        """install src to dst when is a file"""
        if self.debug:
            self.log.dbg('deploy file: {}'.format(src))
            self.log.dbg('ignore empty: {}'.format(noempty))
            self.log.dbg('ignore pattern: {}'.format(ignore))
            self.log.dbg('template: {}'.format(template))
            self.log.dbg('no empty: {}'.format(noempty))

        if utils.must_ignore([src, dst], ignore, debug=self.debug):
            if self.debug:
                self.log.dbg('ignoring install of {} to {}'.format(src, dst))
            return False, None

        if utils.samefile(src, dst):
            # symlink loop
            err = 'dotfile points to itself: {}'.format(dst)
            return False, err

        if not os.path.exists(src):
            err = 'source dotfile does not exist: {}'.format(src)
            return False, err

        # handle the file
        content = None
        if template:
            # template the file
            saved = templater.add_tmp_vars(self._get_tmp_file_vars(src, dst))
            try:
                content = templater.generate(src)
            except UndefinedException as e:
                return False, str(e)
            finally:
                templater.restore_vars(saved)
            if noempty and utils.content_empty(content):
                if self.debug:
                    self.log.dbg('ignoring empty template: {}'.format(src))
                return False, None
            if content is None:
                err = 'empty template {}'.format(src)
                return False, err
        ret, err = self._write(src, dst,
                               content=content,
                               actionexec=actionexec,
                               template=template)

        # build return values
        if ret < 0:
            # error
            return False, err
        if ret > 0:
            # already exists
            if self.debug:
                self.log.dbg('ignoring {}'.format(dst))
            return False, None
        if ret == 0:
            # success
            if not self.dry and not self.comparing:
                self.log.sub('copied {} to {}'.format(src, dst))
            return True, None
        # error
        err = 'installing {} to {}'.format(src, dst)
        return False, err

    def _install_dir(self, templater, src, dst,
                     actionexec=None, noempty=False,
                     ignore=[], template=True):
        """install src to dst when is a directory"""
        if self.debug:
            self.log.dbg('install dir {}'.format(src))
            self.log.dbg('ignore empty: {}'.format(noempty))
        # default to nothing installed and no error
        ret = False, None
        if not self._create_dirs(dst):
            err = 'creating directory for {}'.format(dst)
            return False, err
        # handle all files in dir
        for entry in os.listdir(src):
            f = os.path.join(src, entry)
            if not os.path.isdir(f):
                # is file
                res, err = self._install_file(templater, f,
                                              os.path.join(dst, entry),
                                              actionexec=actionexec,
                                              noempty=noempty,
                                              ignore=ignore,
                                              template=template)
                if not res and err:
                    # error occured
                    ret = res, err
                    break
                elif res:
                    # something got installed
                    ret = True, None
            else:
                # is directory
                res, err = self._install_dir(templater, f,
                                             os.path.join(dst, entry),
                                             actionexec=actionexec,
                                             noempty=noempty,
                                             ignore=ignore,
                                             template=template)
                if not res and err:
                    # error occured
                    ret = res, err
                    break
                elif res:
                    # something got installed
                    ret = True, None
        return ret

    def _fake_diff(self, dst, content):
        """
        fake diff by comparing file content with content
        returns True if same
        """
        cur = ''
        with open(dst, 'br') as f:
            cur = f.read()
        return cur == content

    def _write(self, src, dst, content=None,
               actionexec=None, template=True):
        """
        copy dotfile / write content to file
        return  0, None:  for success,
                1, None:  when already exists
               -1, err: when error
        content is always empty if template is False
        and is to be ignored
        """
        overwrite = not self.safe
        if self.dry:
            self.log.dry('would install {}'.format(dst))
            return 0, None
        if os.path.lexists(dst):
            rights = os.stat(src).st_mode
            samerights = False
            try:
                samerights = os.stat(dst).st_mode == rights
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # broken symlink
                    err = 'broken symlink {}'.format(dst)
                    return -1, err
            diff = None
            if self.diff:
                diff = self._diff_before_write(src, dst,
                                               content=content,
                                               quiet=True)
                if not diff and samerights:
                    if self.debug:
                        self.log.dbg('{} is the same'.format(dst))
                    return 1, None
            if self.safe:
                if self.debug:
                    self.log.dbg('change detected for {}'.format(dst))
                if self.showdiff:
                    if diff is None:
                        # get diff
                        diff = self._diff_before_write(src, dst,
                                                       content=content,
                                                       quiet=True)
                        if diff:
                            self._print_diff(src, dst, diff)
                if not self.log.ask('Overwrite \"{}\"'.format(dst)):
                    self.log.warn('ignoring {}'.format(dst))
                    return 1, None
                overwrite = True
        if self.backup and os.path.lexists(dst):
            self._backup(dst)
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = 'creating directory for {}'.format(dst)
            return -1, err
        r, e = self._exec_pre_actions(actionexec)
        if not r:
            return -1, e
        if self.debug:
            self.log.dbg('install dotfile to \"{}\"'.format(dst))
        # re-check in case action created the file
        if self.safe and not overwrite and os.path.lexists(dst):
            if not self.log.ask('Overwrite \"{}\"'.format(dst)):
                self.log.warn('ignoring {}'.format(dst))
                return 1, None

        if template:
            # write content the file
            try:
                with open(dst, 'wb') as f:
                    f.write(content)
                shutil.copymode(src, dst)
            except NotADirectoryError as e:
                err = 'opening dest file: {}'.format(e)
                return -1, err
            except Exception as e:
                return -1, str(e)
        else:
            # copy file
            try:
                shutil.copyfile(src, dst)
                shutil.copymode(src, dst)
            except Exception as e:
                return -1, str(e)
        return 0, None

    def _diff_before_write(self, src, dst, content=None, quiet=False):
        """
        diff before writing
        using a temp file if content is not None
        returns diff string ('' if same)
        """
        tmp = None
        if content:
            tmp = utils.write_to_tmpfile(content)
            src = tmp
        diff = utils.diff(modified=src, original=dst, raw=False,
                          diff_cmd=self.diff_cmd)
        if tmp:
            utils.remove(tmp, logger=self.log)

        if not quiet and diff:
            self._print_diff(src, dst, diff)
        return diff

    def _print_diff(self, src, dst, diff):
        """show diff to user"""
        self.log.log('diff \"{}\" VS \"{}\"'.format(dst, src))
        self.log.emph(diff)

    def _create_dirs(self, directory):
        """mkdir -p <directory>"""
        if not self.create and not os.path.exists(directory):
            if self.debug:
                self.log.dbg('no mkdir as \"create\" set to false in config')
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
        dst = path.rstrip(os.sep) + self.backup_suffix
        self.log.log('backup {} to {}'.format(path, dst))
        os.rename(path, dst)

    def _pivot_path(self, path, newdir, striphome=False):
        """change path to be under newdir"""
        if self.debug:
            self.log.dbg('pivot new dir: \"{}\"'.format(newdir))
            self.log.dbg('strip home: {}'.format(striphome))
        if striphome:
            path = utils.strip_home(path)
        sub = path.lstrip(os.sep)
        new = os.path.join(newdir, sub)
        if self.debug:
            self.log.dbg('pivot \"{}\" to \"{}\"'.format(path, new))
        return new

    def _exec_pre_actions(self, actionexec):
        """execute action executor"""
        if self.action_executed:
            return True, None
        if not actionexec:
            return True, None
        ret, err = actionexec()
        self.action_executed = True
        return ret, err

    def _install_to_temp(self, templater, src, dst, tmpdir, template=True):
        """install a dotfile to a tempdir"""
        tmpdst = self._pivot_path(dst, tmpdir)
        r = self.install(templater, src, tmpdst, template=template)
        return r, tmpdst

    def install_to_temp(self, templater, tmpdir, src, dst, template=True):
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
            self.log.dbg('tmp install {} (defined dst: {})'.format(src, dst))
        # install the dotfile to a temp directory for comparing
        r, tmpdst = self._install_to_temp(templater, src, dst, tmpdir,
                                          template=template)
        ret, err = r
        if self.debug:
            self.log.dbg('tmp installed in {}'.format(tmpdst))
        # reset flags
        self.dry = drysaved
        self.diff = diffsaved
        self.comparing = False
        self.create = createsaved
        return ret, err, tmpdst
