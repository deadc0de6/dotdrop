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
from dotdrop.linktypes import LinkTypes
from dotdrop import utils
from dotdrop.exceptions import UndefinedException


class Installer:
    """dotfile installer"""

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, workdir='~/.config/dotdrop',
                 debug=False, diff=True, totemp=None, showdiff=False,
                 backup_suffix='.dotdropbak', diff_cmd=''):
        """
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
        workdir = os.path.expanduser(workdir)
        workdir = os.path.normpath(workdir)
        self.workdir = workdir
        base = os.path.expanduser(base)
        base = os.path.normpath(base)
        self.base = base
        self.debug = debug
        self.diff = diff
        self.totemp = totemp
        self.showdiff = showdiff
        self.backup_suffix = backup_suffix
        self.diff_cmd = diff_cmd
        self.action_executed = False
        # avoids printing file copied logs
        # when using install_to_tmp for comparing
        self.comparing = False

        self.log = Logger(debug=self.debug)

    ########################################################
    # public methods
    ########################################################

    def install(self, templater, src, dst, linktype,
                actionexec=None, noempty=False,
                ignore=None, is_template=True,
                chmod=None, force_chmod=False):
        """
        install src to dst

        @templater: the templater object
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @linktype: linktypes.LinkTypes
        @actionexec: action executor callback
        @noempty: render empty template flag
        @ignore: pattern to ignore when installing
        @is_template: this dotfile is a template
        @chmod: rights to apply if any
        @force_chmod: do not ask user to chmod

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        """
        if not src or not dst:
            # fake dotfile
            self.log.dbg('fake dotfile installed')
            self._exec_pre_actions(actionexec)
            return True, None
        msg = 'installing \"{}\" to \"{}\" (link: {})'
        self.log.dbg(msg.format(src, dst, str(linktype)))
        src, dst, cont, err = self._check_paths(src, dst)
        if not cont:
            return self._log_install(cont, err)

        # check source file exists
        src = os.path.join(self.base, src)
        if not os.path.exists(src):
            err = 'source dotfile does not exist: {}'.format(src)
            return self._log_install(False, err)

        self.action_executed = False

        # install to temporary dir
        # and ignore any actions
        if self.totemp:
            ret, err, _ = self.install_to_temp(templater,
                                               self.totemp,
                                               src, dst,
                                               is_template=is_template,
                                               chmod=chmod,
                                               ignore=ignore)
            return self._log_install(ret, err)

        isdir = os.path.isdir(src)
        self.log.dbg('install {} to {}'.format(src, dst))
        self.log.dbg('\"{}\" is a directory: {}'.format(src, isdir))

        if linktype == LinkTypes.NOLINK:
            # normal file
            if isdir:
                ret, err = self._copy_dir(templater, src, dst,
                                          actionexec=actionexec,
                                          noempty=noempty, ignore=ignore,
                                          is_template=is_template)
            else:
                ret, err = self._copy_file(templater, src, dst,
                                           actionexec=actionexec,
                                           noempty=noempty, ignore=ignore,
                                           is_template=is_template)
        elif linktype == LinkTypes.LINK:
            # symlink
            ret, err = self._link(templater, src, dst,
                                  actionexec=actionexec,
                                  is_template=is_template,
                                  ignore=ignore)
        elif linktype == LinkTypes.LINK_CHILDREN:
            # symlink direct children
            if not isdir:
                msg = 'symlink children of {} to {}'
                self.log.dbg(msg.format(src, dst))
                err = 'source dotfile is not a directory: {}'.format(src)
                ret = False
            else:
                ret, err = self._link_children(templater, src, dst,
                                               actionexec=actionexec,
                                               is_template=is_template,
                                               ignore=ignore)

        self.log.dbg('before chmod: {} err:{}'.format(ret, err))

        if self.dry:
            return self._log_install(ret, err)

        # handle chmod
        # - on success (r, not err)
        # - no change (not r, not err)
        # but not when
        # - error (not r, err)
        # - aborted (not r, err)
        if os.path.exists(dst) and (ret or (not ret and not err)):
            if not chmod:
                chmod = utils.get_file_perm(src)
            dstperms = utils.get_file_perm(dst)
            if dstperms != chmod:
                # apply mode
                msg = 'chmod {} to {:o}'.format(dst, chmod)
                if not force_chmod and self.safe and not self.log.ask(msg):
                    ret = False
                    err = 'aborted'
                else:
                    if not self.comparing:
                        self.log.sub('chmod {} to {:o}'.format(dst, chmod))
                    if utils.chmod(dst, chmod, debug=self.debug):
                        ret = True
                    else:
                        ret = False
                        err = 'chmod failed'

        return self._log_install(ret, err)

    def install_to_temp(self, templater, tmpdir, src, dst,
                        is_template=True, chmod=None, ignore=None,
                        set_create=False):
        """
        install a dotfile to a tempdir

        @templater: the templater object
        @tmpdir: where to install
        @src: dotfile source path in dotpath
        @dst: dotfile destination path in the FS
        @is_template: this dotfile is a template
        @chmod: rights to apply if any
        @ignore: patterns to ignore
        @set_create: force create to True

        return
        - success, error-if-any, dotfile-installed-path
        """
        self.log.dbg('tmp install {} (defined dst: {})'.format(src, dst))
        src, dst, cont, err = self._check_paths(src, dst)
        if not cont:
            self._log_install(cont, err)
            return cont, err, None

        ret = False
        tmpdst = ''

        # save flags
        self.comparing = True
        drysaved = self.dry
        self.dry = False
        diffsaved = self.diff
        self.diff = False
        if set_create:
            createsaved = self.create
            self.create = True
        totemp = self.totemp
        self.totemp = None

        # install the dotfile to a temp directory
        tmpdst = self._pivot_path(dst, tmpdir)
        ret, err = self.install(templater, src, tmpdst,
                                LinkTypes.NOLINK,
                                is_template=is_template,
                                chmod=chmod, ignore=ignore)
        if ret:
            self.log.dbg('tmp installed in {}'.format(tmpdst))

        # restore flags
        self.dry = drysaved
        self.diff = diffsaved
        if set_create:
            self.create = createsaved
        self.comparing = False
        self.totemp = totemp

        return ret, err, tmpdst

    ########################################################
    # low level accessors for public methods
    ########################################################

    def _link(self, templater, src, dst, actionexec=None,
              is_template=True, ignore=None):
        """
        install link:link

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        if is_template:
            self.log.dbg('is a template')
            self.log.dbg('install to {}'.format(self.workdir))
            tmp = self._pivot_path(dst, self.workdir, striphome=True)
            ret, err = self.install(templater, src, tmp,
                                    LinkTypes.NOLINK,
                                    actionexec=actionexec,
                                    is_template=is_template,
                                    ignore=ignore)
            if not ret and not os.path.exists(tmp):
                return ret, err
            src = tmp
        ret, err = self._symlink(src, dst, actionexec=actionexec)
        return ret, err

    def _link_children(self, templater, src, dst,
                       actionexec=None, is_template=True, ignore=None):
        """
        install link:link_children

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        parent = os.path.join(self.base, src)
        if not os.path.lexists(dst):
            if self.dry:
                self.log.dry('would create directory "{}"'.format(dst))
            else:
                if not self.comparing:
                    self.log.sub('creating directory "{}"'.format(dst))
                self._create_dirs(dst)

        if os.path.isfile(dst):
            msg = ''.join([
                'Remove regular file {} and ',
                'replace with empty directory?',
            ]).format(dst)

            if self.safe and not self.log.ask(msg):
                return False, 'aborted'
            os.unlink(dst)
            self._create_dirs(dst)

        children = os.listdir(parent)
        srcs = [os.path.normpath(os.path.join(parent, child))
                for child in children]
        dsts = [os.path.normpath(os.path.join(dst, child))
                for child in children]

        installed = 0
        for i in range(len(children)):
            subsrc = srcs[i]
            subdst = dsts[i]

            if utils.must_ignore([subsrc, subdst], ignore, debug=self.debug):
                self.log.dbg(
                    'ignoring install of {} to {}'.format(src, dst),
                )
                continue

            self.log.dbg('symlink child {} to {}'.format(subsrc, subdst))

            if is_template:
                self.log.dbg('child is a template')
                self.log.dbg('install to {} and symlink'
                             .format(self.workdir))
                tmp = self._pivot_path(subdst, self.workdir, striphome=True)
                ret2, err2 = self.install(templater, subsrc, tmp,
                                          LinkTypes.NOLINK,
                                          actionexec=actionexec,
                                          is_template=is_template,
                                          ignore=ignore)
                if not ret2 and err2 and not os.path.exists(tmp):
                    continue
                subsrc = tmp

            ret, err = self._symlink(subsrc, subdst, actionexec=actionexec)
            if ret:
                installed += 1
                # void actionexec if dotfile installed
                # to prevent from running actions multiple times
                actionexec = None
            else:
                if err:
                    return ret, err

        return installed > 0, None

    ########################################################
    # file operations
    ########################################################

    def _symlink(self, src, dst, actionexec=None):
        """
        set src as a link target of dst

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        overwrite = not self.safe

        if os.path.lexists(dst):
            # symlink exists
            if os.path.realpath(dst) == os.path.realpath(src):
                msg = 'ignoring "{}", link already exists'.format(dst)
                self.log.dbg(msg)
                return False, None
            if self.dry:
                self.log.dry('would remove {} and link to {}'.format(dst, src))
                return True, None
            if self.showdiff:
                self._show_diff_before_write(src, dst)
            msg = 'Remove "{}" for link creation?'.format(dst)
            if self.safe and not self.log.ask(msg):
                return False, 'aborted'

            # remove symlink
            overwrite = True
            try:
                utils.removepath(dst)
            except OSError as exc:
                err = 'something went wrong with {}: {}'.format(src, exc)
                return False, err

        if self.dry:
            self.log.dry('would link {} to {}'.format(dst, src))
            return True, None

        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = 'error creating directory for {}'.format(dst)
            return False, err

        # execute pre-actions
        ret, err = self._exec_pre_actions(actionexec)
        if not ret:
            return False, err

        # re-check in case action created the file
        if os.path.lexists(dst):
            msg = 'Remove "{}" for link creation?'.format(dst)
            if self.safe and not overwrite and not self.log.ask(msg):
                return False, 'aborted'
            try:
                utils.removepath(dst)
            except OSError as exc:
                err = 'something went wrong with {}: {}'.format(src, exc)
                return False, err

        # create symlink
        os.symlink(src, dst)
        if not self.comparing:
            self.log.sub('linked {} to {}'.format(dst, src))
        return True, None

    def _copy_file(self, templater, src, dst,
                   actionexec=None, noempty=False,
                   ignore=None, is_template=True):
        """
        install src to dst when is a file

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        self.log.dbg('deploy file: {}'.format(src))
        self.log.dbg('ignore empty: {}'.format(noempty))
        self.log.dbg('ignore pattern: {}'.format(ignore))
        self.log.dbg('is_template: {}'.format(is_template))
        self.log.dbg('no empty: {}'.format(noempty))

        # ignore file
        if utils.must_ignore([src, dst], ignore, debug=self.debug):
            self.log.dbg('ignoring install of {} to {}'.format(src, dst))
            return False, None

        # check no loop
        if utils.samefile(src, dst):
            err = 'dotfile points to itself: {}'.format(dst)
            return False, err

        # check source file exists
        if not os.path.exists(src):
            err = 'source dotfile does not exist: {}'.format(src)
            return False, err

        # handle the file
        content = None
        if is_template:
            # template the file
            saved = templater.add_tmp_vars(self._get_tmp_file_vars(src, dst))
            try:
                content = templater.generate(src)
            except UndefinedException as exc:
                return False, str(exc)
            finally:
                templater.restore_vars(saved)
            # test is empty
            if noempty and utils.content_empty(content):
                self.log.dbg('ignoring empty template: {}'.format(src))
                return False, None
            if content is None:
                err = 'empty template {}'.format(src)
                return False, err

        # write the file
        ret, err = self._write(src, dst,
                               content=content,
                               actionexec=actionexec)
        if ret and not err:
            if not self.dry and not self.comparing:
                self.log.sub('install {} to {}'.format(src, dst))
        return ret, err

    def _copy_dir(self, templater, src, dst,
                  actionexec=None, noempty=False,
                  ignore=None, is_template=True):
        """
        install src to dst when is a directory

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        self.log.dbg('deploy dir {}'.format(src))
        # default to nothing installed and no error
        ret = False, None

        # handle all files in dir
        for entry in os.listdir(src):
            fpath = os.path.join(src, entry)
            self.log.dbg('deploy sub from {}: {}'.format(dst, entry))
            if not os.path.isdir(fpath):
                # is file
                res, err = self._copy_file(templater, fpath,
                                           os.path.join(dst, entry),
                                           actionexec=actionexec,
                                           noempty=noempty,
                                           ignore=ignore,
                                           is_template=is_template)
                if not res and err:
                    # error occured
                    return res, err

                if res:
                    # something got installed
                    ret = True, None
            else:
                # is directory
                res, err = self._copy_dir(templater, fpath,
                                          os.path.join(dst, entry),
                                          actionexec=actionexec,
                                          noempty=noempty,
                                          ignore=ignore,
                                          is_template=is_template)
                if not res and err:
                    # error occured
                    return res, err

                if res:
                    # something got installed
                    ret = True, None
        return ret

    @classmethod
    def _write_content_to_file(cls, content, src, dst):
        """write content to file"""

        if content:
            # write content the file
            try:
                with open(dst, 'wb') as file:
                    file.write(content)
                shutil.copymode(src, dst)
            except NotADirectoryError as exc:
                err = 'opening dest file: {}'.format(exc)
                return False, err
            except OSError as exc:
                return False, str(exc)
            except TypeError as exc:
                return False, str(exc)
        else:
            # copy file
            try:
                shutil.copyfile(src, dst)
                shutil.copymode(src, dst)
            except OSError as exc:
                return False, str(exc)
        return True, None

    def _write(self, src, dst, content=None,
               actionexec=None):
        """
        copy dotfile / write content to file

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        overwrite = not self.safe
        if self.dry:
            self.log.dry('would install {}'.format(dst))
            return True, None

        if os.path.lexists(dst):
            # file/symlink exists
            try:
                os.stat(dst)
            except OSError as exc:
                if exc.errno == errno.ENOENT:
                    # broken symlink
                    err = 'broken symlink {}'.format(dst)
                    return False, err

            if self.diff:
                if not self._is_different(src, dst, content=content):
                    self.log.dbg('{} is the same'.format(dst))
                    return False, None

            if self.safe:
                self.log.dbg('change detected for {}'.format(dst))
                if self.showdiff:
                    # get diff
                    self._show_diff_before_write(src, dst,
                                                 content=content)
                if not self.log.ask('Overwrite \"{}\"'.format(dst)):
                    return False, 'aborted'
                overwrite = True

            if self.backup:
                self._backup(dst)

        # create hierarchy
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = 'creating directory for {}'.format(dst)
            return False, err

        # execute pre actions
        ret, err = self._exec_pre_actions(actionexec)
        if not ret:
            return False, err

        self.log.dbg('install file to \"{}\"'.format(dst))
        # re-check in case action created the file
        if self.safe and not overwrite and \
                os.path.lexists(dst) and \
                not self.log.ask('Overwrite \"{}\"'.format(dst)):
            self.log.warn('ignoring {}'.format(dst))
            return False, 'aborted'

        # writing to file
        return self._write_content_to_file(content, src, dst)

    ########################################################
    # helpers
    ########################################################

    @classmethod
    def _get_tmp_file_vars(cls, src, dst):
        tmp = {}
        tmp['_dotfile_sub_abs_src'] = src
        tmp['_dotfile_sub_abs_dst'] = dst
        return tmp

    def _is_different(self, src, dst, content=None):
        """
        returns True if file is different and
        needs to be installed
        """
        # check file content
        tmp = None
        if content:
            tmp = utils.write_to_tmpfile(content)
            src = tmp
        ret = utils.fastdiff(src, dst)
        if ret:
            self.log.dbg('content differ')
        if content:
            utils.removepath(tmp)
        return ret

    def _show_diff_before_write(self, src, dst, content=None):
        """
        diff before writing
        using a temp file if content is not None
        returns diff string ('' if same)
        """
        tmp = None
        if content:
            tmp = utils.write_to_tmpfile(content)
            src = tmp
        diff = utils.diff(modified=src, original=dst,
                          diff_cmd=self.diff_cmd)
        if tmp:
            utils.removepath(tmp, logger=self.log)

        if diff:
            self._print_diff(src, dst, diff)
        return diff

    def _print_diff(self, src, dst, diff):
        """show diff to user"""
        self.log.log('diff \"{}\" VS \"{}\"'.format(dst, src))
        self.log.emph(diff)

    def _create_dirs(self, directory):
        """mkdir -p <directory>"""
        if not self.create and not os.path.exists(directory):
            self.log.dbg('no mkdir as \"create\" set to false in config')
            return False
        if os.path.exists(directory):
            return True
        if self.dry:
            self.log.dry('would mkdir -p {}'.format(directory))
            return True
        self.log.dbg('mkdir -p {}'.format(directory))

        os.makedirs(directory, exist_ok=True)
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
        self.log.dbg('pivot new dir: \"{}\"'.format(newdir))
        self.log.dbg('strip home: {}'.format(striphome))
        if striphome:
            path = utils.strip_home(path)
        sub = path.lstrip(os.sep)
        new = os.path.join(newdir, sub)
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

    def _log_install(self, boolean, err):
        """
        log installation process
        returns success, error-if-any
        """
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

    def _check_paths(self, src, dst):
        """
        check and normalize param
        returns <src>, <dst>, <continue>, <error>
        """
        # check both path are valid
        if not dst or not src:
            err = 'empty dst or src for {}'.format(src)
            self.log.dbg(err)
            return None, None, False, err

        # normalize src and dst
        src = os.path.expanduser(src)
        src = os.path.normpath(src)

        dst = os.path.expanduser(dst)
        dst = os.path.normpath(dst)

        return src, dst, True, None
