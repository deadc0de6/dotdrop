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
from dotdrop.utils import copyfile, get_file_perm, \
    pivot_path, must_ignore, removepath, \
    samefile, write_to_tmpfile, fastdiff, \
    content_empty
from dotdrop.utils import chmod as chmodit
from dotdrop.utils import diff as diffit
from dotdrop.exceptions import UndefinedException
from dotdrop.cfg_yaml import CfgYaml


class Installer:
    """dotfile installer"""

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, workdir='~/.config/dotdrop',
                 debug=False, diff=True, totemp=None, showdiff=False,
                 backup_suffix='.dotdropbak', diff_cmd='',
                 remove_existing_in_dir=False, force_chmod=False):
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
        @remove_existing_in_dir: remove file in dir dotfiles
                                 if not managed by dotdrop
        @force_chmod: apply chmod without confirmation
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
        self.remove_existing_in_dir = remove_existing_in_dir
        self.force_chmod = force_chmod
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
                chmod=None):
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
        msg = f'installing \"{src}\" to \"{dst}\" (link: {linktype})'
        self.log.dbg(msg)
        src, dst, cont, err = self._check_paths(src, dst)
        if not cont:
            return self._log_install(cont, err)

        # check source file exists
        src = os.path.join(self.base, src)
        if not os.path.exists(src):
            err = f'source dotfile does not exist: {src}'
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
        self.log.dbg(f'install {src} to {dst}')
        self.log.dbg(f'\"{src}\" is a directory: {isdir}')

        if linktype == LinkTypes.NOLINK:
            # normal file
            if isdir:
                ret, err, ins = self._copy_dir(templater, src, dst,
                                               actionexec=actionexec,
                                               noempty=noempty, ignore=ignore,
                                               is_template=is_template,
                                               chmod=chmod)
                if self.remove_existing_in_dir and ins:
                    self._remove_existing_in_dir(dst, ins)
            else:
                ret, err = self._copy_file(templater, src, dst,
                                           actionexec=actionexec,
                                           noempty=noempty, ignore=ignore,
                                           is_template=is_template)
        elif linktype in (LinkTypes.LINK, LinkTypes.ABSOLUTE):
            # symlink
            ret, err = self._link_absolute(templater, src, dst,
                                           actionexec=actionexec,
                                           is_template=is_template,
                                           ignore=ignore,
                                           chmod=chmod)
        elif linktype == LinkTypes.RELATIVE:
            # symlink
            ret, err = self._link_relative(templater, src, dst,
                                           actionexec=actionexec,
                                           is_template=is_template,
                                           ignore=ignore,
                                           chmod=chmod)
        elif linktype == LinkTypes.LINK_CHILDREN:
            # symlink direct children
            if not isdir:
                msg = f'symlink children of {src} to {dst}'
                self.log.dbg(msg)
                err = f'source dotfile is not a directory: {src}'
                ret = False
            else:
                ret, err = self._link_children(templater, src, dst,
                                               actionexec=actionexec,
                                               is_template=is_template,
                                               ignore=ignore)

        if self.log.debug and chmod:
            cur = get_file_perm(dst)
            if chmod == CfgYaml.chmod_ignore:
                chmodstr = CfgYaml.chmod_ignore
            else:
                chmodstr = f'{chmod:o}'
            self.log.dbg(
                f'before chmod (cur:{cur:o}, new:{chmodstr}): '
                f'installed:{ret} err:{err}'
            )

        if self.dry:
            return self._log_install(ret, err)

        self._apply_chmod_after_install(src, dst, ret, err,
                                        chmod=chmod,
                                        linktype=linktype)

        return self._log_install(ret, err)

    def _apply_chmod_after_install(self, src, dst, ret, err,
                                   chmod=None,
                                   is_sub=False,
                                   linktype=LinkTypes.NOLINK):
        """
        handle chmod after install
        - on success (r, not err)
        - no change (not r, not err)
        but not when
        - error (not r, err)
        - aborted (not r, err)
        - special keyword "preserve"
        is_sub is used to specify if the file/dir is
        part of a dotfile directory
        """
        apply_chmod = linktype in [LinkTypes.NOLINK, LinkTypes.LINK_CHILDREN]
        apply_chmod = apply_chmod and os.path.exists(dst)
        apply_chmod = apply_chmod and (ret or (not ret and not err))
        apply_chmod = apply_chmod and chmod != CfgYaml.chmod_ignore
        if is_sub:
            chmod = None
        if not apply_chmod:
            self.log.dbg('no chmod applied')
            return
        if not chmod:
            chmod = get_file_perm(src)
            self.log.dbg(f'dotfile in dotpath perm: {chmod:o}')
        self.log.dbg(f'applying chmod {chmod:o} to {dst}')
        dstperms = get_file_perm(dst)
        if dstperms != chmod:
            # apply mode
            msg = f'chmod {dst} to {chmod:o}'
            if not self.force_chmod and self.safe and not self.log.ask(msg):
                ret = False
                err = 'aborted'
            else:
                if not self.comparing:
                    self.log.sub(f'chmod {dst} to {chmod:o}')
                if chmodit(dst, chmod, debug=self.debug):
                    ret = True
                else:
                    ret = False
                    err = 'chmod failed'

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
        self.log.dbg(f'tmp install {src} (defined dst: {dst})')
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
        tmpdst = pivot_path(dst, tmpdir, logger=self.log)
        ret, err = self.install(templater, src, tmpdst,
                                LinkTypes.NOLINK,
                                is_template=is_template,
                                chmod=chmod, ignore=ignore)
        if ret:
            self.log.dbg(f'tmp installed in {tmpdst}')

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

    def _link_absolute(self, templater, src, dst,
                       actionexec=None,
                       is_template=True,
                       ignore=None,
                       chmod=None):
        """
        install link:absolute|link

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        return self._link_dotfile(templater, src, dst,
                                  actionexec=actionexec,
                                  is_template=is_template,
                                  ignore=ignore,
                                  absolute=True,
                                  chmod=chmod)

    def _link_relative(self, templater, src, dst,
                       actionexec=None,
                       is_template=True,
                       ignore=None,
                       chmod=None):
        """
        install link:relative

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        return self._link_dotfile(templater, src, dst,
                                  actionexec=actionexec,
                                  is_template=is_template,
                                  ignore=ignore,
                                  absolute=False,
                                  chmod=chmod)

    def _link_dotfile(self, templater, src, dst, actionexec=None,
                      is_template=True, ignore=None, absolute=True,
                      chmod=None):
        """
        symlink

        chmod is only used if the dotfile is a template
        and needs to be installed to the workdir first

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted
        """
        if is_template:
            self.log.dbg(f'is a template, installing to {self.workdir}')
            tmp = pivot_path(dst, self.workdir,
                             striphome=True, logger=self.log)
            ret, err = self.install(templater, src, tmp,
                                    LinkTypes.NOLINK,
                                    actionexec=actionexec,
                                    is_template=is_template,
                                    ignore=ignore,
                                    chmod=chmod)
            if not ret and not os.path.exists(tmp):
                return ret, err
            src = tmp
        ret, err = self._symlink(src, dst, actionexec=actionexec,
                                 absolute=absolute)
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
                self.log.dry(f'would create directory "{dst}"')
            else:
                if not self.comparing:
                    self.log.sub(f'creating directory "{dst}"')
                self._create_dirs(dst)

        if os.path.isfile(dst):
            msg = ''.join([
                f'Remove regular file {dst} and ',
                'replace with empty directory?',
            ])

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

            if must_ignore([subsrc, subdst], ignore, debug=self.debug):
                self.log.dbg(
                    f'ignoring install of {src} to {dst}',
                )
                continue

            self.log.dbg(f'symlink child {subsrc} to {subdst}')

            if is_template:
                self.log.dbg('child is a template')
                self.log.dbg(f'install to {self.workdir} and symlink')
                tmp = pivot_path(subdst, self.workdir,
                                 striphome=True, logger=self.log)
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

    def _symlink(self, src, dst, actionexec=None, absolute=True):
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
                msg = f'ignoring "{dst}", link already exists'
                self.log.dbg(msg)
                return False, None
            if self.dry:
                self.log.dry(f'would remove {dst} and link to {src}')
                return True, None
            if self.showdiff:
                self._show_diff_before_write(src, dst)
            msg = f'Remove "{dst}" for link creation?'
            if self.safe and not self.log.ask(msg):
                return False, 'aborted'

            # remove symlink
            if self.backup and not os.path.isdir(dst):
                if not self._backup(dst):
                    return False, f'could not backup {dst}'
            overwrite = True
            try:
                removepath(dst)
            except OSError as exc:
                err = f'something went wrong with {src}: {exc}'
                return False, err

        if self.dry:
            self.log.dry(f'would link {dst} to {src}')
            return True, None

        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = f'error creating directory for {dst}'
            return False, err

        # execute pre-actions
        ret, err = self._exec_pre_actions(actionexec)
        if not ret:
            return False, err

        # re-check in case action created the file
        if os.path.lexists(dst):
            msg = f'Remove "{dst}" for link creation?'
            if self.safe and not overwrite and not self.log.ask(msg):
                return False, 'aborted'
            try:
                removepath(dst)
            except OSError as exc:
                err = f'something went wrong with {src}: {exc}'
                return False, err

        # create symlink
        lnk_src = src
        if not absolute:
            # relative symlink
            dstrel = dst
            if not os.path.isdir(dstrel):
                dstrel = os.path.dirname(dstrel)
            lnk_src = os.path.relpath(src, dstrel)
        os.symlink(lnk_src, dst)
        self.log.dbg(
            f'symlink {dst} to {lnk_src} '
            f'(mode:{get_file_perm(dst):o})'
        )
        if not self.comparing:
            self.log.sub(f'linked {dst} to {lnk_src}')
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
        self.log.dbg(f'deploy file: {src}')
        self.log.dbg(f'ignore empty: {noempty}')
        self.log.dbg(f'ignore pattern: {ignore}')
        self.log.dbg(f'is_template: {is_template}')
        self.log.dbg(f'no empty: {noempty}')

        # ignore file
        if must_ignore([src, dst], ignore, debug=self.debug):
            self.log.dbg(f'ignoring install of {src} to {dst}')
            return False, None

        # check no loop
        if samefile(src, dst):
            err = f'dotfile points to itself: {dst}'
            return False, err

        # check source file exists
        if not os.path.exists(src):
            err = f'source dotfile does not exist: {src}'
            return False, err

        # handle the file
        content = None
        if is_template:
            # template the file
            self.log.dbg(f'it is a template: {src}')
            saved = templater.add_tmp_vars(self._get_tmp_file_vars(src, dst))
            try:
                content = templater.generate(src)
            except UndefinedException as exc:
                return False, str(exc)
            finally:
                templater.restore_vars(saved)
            # test is empty
            if noempty and content_empty(content):
                self.log.dbg(f'ignoring empty template: {src}')
                return False, None
            if content is None:
                err = f'empty template {src}'
                return False, err

        # write the file
        ret, err = self._write(src, dst,
                               content=content,
                               actionexec=actionexec)

        if ret and not err:
            rights = f'{get_file_perm(src):o}'
            self.log.dbg(f'installed file {src} to {dst} ({rights})')
            if not self.dry and not self.comparing:
                self.log.sub(f'install {src} to {dst}')
        return ret, err

    def _copy_dir(self, templater, src, dst,
                  actionexec=None, noempty=False,
                  ignore=None, is_template=True,
                  chmod=None):
        """
        install src to dst when is a directory

        return
        - True, None        : success
        - False, error_msg  : error
        - False, None       : ignored
        - False, 'aborted'    : user aborted

        third arg returned is the list of managed dotfiles
        in the destination or an empty list if anything
        fails
        """
        self.log.dbg(f'deploy dir {src}')
        # default to nothing installed and no error
        ret = False
        dst_dotfiles = []

        # handle all files in dir
        for entry in os.listdir(src):
            fpath = os.path.join(src, entry)
            self.log.dbg(f'deploy sub from {dst}: {entry}')
            if not os.path.isdir(fpath):
                # is file
                fdst = os.path.join(dst, entry)
                dst_dotfiles.append(fdst)
                res, err = self._copy_file(templater, fpath,
                                           fdst,
                                           actionexec=actionexec,
                                           noempty=noempty,
                                           ignore=ignore,
                                           is_template=is_template)
                if not res and err:
                    # error occured
                    return res, err, []

                self._apply_chmod_after_install(fpath, fdst, ret, err,
                                                chmod=chmod, is_sub=True)

                if res:
                    # something got installed

                    ret = True
            else:
                # is directory
                dpath = os.path.join(dst, entry)
                dst_dotfiles.append(dpath)
                res, err, subs = self._copy_dir(templater, fpath,
                                                dpath,
                                                actionexec=actionexec,
                                                noempty=noempty,
                                                ignore=ignore,
                                                is_template=is_template)
                dst_dotfiles.extend(subs)
                if not res and err:
                    # error occured
                    return res, err, []

                if res:
                    # something got installed
                    ret = True

        return ret, None, dst_dotfiles

    def _is_path_in(self, path, paths):
        """return true if path is in paths"""
        return any(samefile(path, p) for p in paths)

    def _remove_existing_in_dir(self, directory, installed_files=None):
        """
        with --remove-existing this will remove
        any file in managed directory which
        are not handled by dotdrop
        """
        if not installed_files:
            return
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return
        to_remove = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                path = os.path.join(root, name)
                if self._is_path_in(path, installed_files):
                    continue
                to_remove.append(os.path.abspath(path))
            for name in dirs:
                path = os.path.join(root, name)
                if self._is_path_in(path, installed_files):
                    continue
                to_remove.append(os.path.abspath(path))
        for path in to_remove:
            if self.dry:
                self.log.dry(f'would remove {path}')
                continue
            if self.safe:
                if not self.log.ask(f'remove unmanaged \"{path}\"'):
                    return
            self.log.dbg(f'removing not managed: {path}')
            removepath(path, logger=self.log)

    @classmethod
    def _write_content_to_file(cls, content, src, dst):
        """write content to file"""
        if content:
            # write content the file
            try:
                with open(dst, 'wb') as file:
                    file.write(content)
            except NotADirectoryError as exc:
                err = f'opening dest file: {exc}'
                return False, err
            except OSError as exc:
                return False, str(exc)
            except TypeError as exc:
                return False, str(exc)
        else:
            # copy file
            try:
                # do NOT copy meta here
                shutil.copyfile(src, dst)
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
            self.log.dry(f'would install {dst}')
            return True, None

        if os.path.lexists(dst):
            # file/symlink exists
            self.log.dbg(f'file already exists on filesystem: {dst}')
            try:
                os.stat(dst)
            except OSError as exc:
                if exc.errno == errno.ENOENT:
                    # broken symlink
                    err = f'broken symlink {dst}'
                    return False, err

            if self.diff:
                if not self._is_different(src, dst, content=content):
                    self.log.dbg(f'{dst} is the same')
                    return False, None

            if self.safe:
                self.log.dbg(f'change detected for {dst}')
                if self.showdiff:
                    # get diff
                    self._show_diff_before_write(src, dst,
                                                 content=content)
                if not self.log.ask(f'Overwrite \"{dst}\"'):
                    return False, 'aborted'
                overwrite = True

            if self.backup:
                if not self._backup(dst):
                    return False, f'could not backup {dst}'
        else:
            self.log.dbg(f'file does not exist on filesystem: {dst}')

        # create hierarchy
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            err = f'creating directory for {dst}'
            return False, err

        # execute pre actions
        ret, err = self._exec_pre_actions(actionexec)
        if not ret:
            return False, err

        self.log.dbg(f'installing file to \"{dst}\"')
        # re-check in case action created the file
        if self.safe and not overwrite and \
                os.path.lexists(dst) and \
                not self.log.ask(f'Overwrite \"{dst}\"'):
            self.log.warn(f'ignoring {dst}')
            return False, 'aborted'

        # writing to file
        self.log.dbg(f'before writing to {dst} ({get_file_perm(src):o})')
        ret = self._write_content_to_file(content, src, dst)
        self.log.dbg(f'written to {dst} ({get_file_perm(src):o})')
        return ret

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
            tmp = write_to_tmpfile(content)
            src = tmp
        ret = fastdiff(src, dst)
        if ret:
            self.log.dbg('content differ')
        if content:
            removepath(tmp)
        return ret

    def _show_diff_before_write(self, src, dst, content=None):
        """
        diff before writing
        using a temp file if content is not None
        returns diff string ('' if same)
        """
        tmp = None
        if content:
            tmp = write_to_tmpfile(content)
            src = tmp
        diff = diffit(modified=src, original=dst,
                      diff_cmd=self.diff_cmd)
        if tmp:
            removepath(tmp, logger=self.log)

        if diff:
            self._print_diff(src, dst, diff)
        return diff

    def _print_diff(self, src, dst, diff):
        """show diff to user"""
        self.log.log(f'diff \"{dst}\" VS \"{src}\"')
        self.log.emph(diff)

    def _create_dirs(self, directory):
        """mkdir -p <directory>"""
        if not self.create and not os.path.exists(directory):
            self.log.dbg('no mkdir as \"create\" set to false in config')
            return False
        if os.path.exists(directory):
            return True
        if self.dry:
            self.log.dry(f'would mkdir -p {directory}')
            return True
        self.log.dbg(f'mkdir -p {directory}')

        os.makedirs(directory, exist_ok=True)
        return os.path.exists(directory)

    def _backup(self, path):
        """backup file pointed by path"""
        if self.dry:
            return True
        dst = path.rstrip(os.sep) + self.backup_suffix
        self.log.log(f'backup {path} to {dst}')
        # os.rename(path, dst)
        # copy to preserve mode on chmod=preserve
        # since we expect dotfiles this shouldn't have
        # such a big impact but who knows.
        if not copyfile(path, dst, debug=self.debug):
            return False
        if not os.path.exists(dst):
            return False
        stat = os.stat(path)
        os.chown(dst, stat.st_uid, stat.st_gid)
        return True

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
                self.log.dbg(f'install: ERROR: {err}')
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
            err = f'empty dst or src for {src}'
            self.log.dbg(err)
            return None, None, False, err

        # normalize src and dst
        src = os.path.expanduser(src)
        src = os.path.normpath(src)

        dst = os.path.expanduser(dst)
        dst = os.path.normpath(dst)

        return src, dst, True, None
