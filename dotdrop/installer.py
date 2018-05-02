"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
handle the installation of dotfiles
"""

import os

# local imports
from dotdrop.logger import Logger
import dotdrop.utils as utils


class Installer:

    BACKUP_SUFFIX = '.dotdropbak'

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, debug=False, diff=True):
        self.create = create
        self.backup = backup
        self.dry = dry
        self.safe = safe
        self.base = base
        self.debug = debug
        self.diff = diff
        self.comparing = False
        self.log = Logger(debug=self.debug)

    def install(self, templater, profile, src, dst):
        '''Install the dotfile for profile "profile"'''
        src = os.path.join(self.base, os.path.expanduser(src))
        dst = os.path.join(self.base, os.path.expanduser(dst))
        self.log.dbg('install {} to {}'.format(src, dst))
        if os.path.isdir(src):
            return self._handle_dir(templater, profile, src, dst)
        return self._handle_file(templater, profile, src, dst)

    def link(self, src, dst):
        '''Sets src as the link target of dst'''
        src = os.path.join(self.base, os.path.expanduser(src))
        dst = os.path.join(self.base, os.path.expanduser(dst))
        if os.path.exists(dst):
            if os.path.realpath(dst) == os.path.realpath(src):
                self.log.sub('ignoring "{}", link exists'.format(dst))
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
            except OSError:
                self.log.err('something went wrong with {}'.format(src))
                return []
        if self.dry:
            self.log.dry('would link {} to {}'.format(dst, src))
            return []
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            self.log.err('creating directory for \"{}\"'.format(dst))
            return []
        os.symlink(src, dst)
        self.log.sub('linked {} to {}'.format(dst, src))
        return [(src, dst)]

    def _handle_file(self, templater, profile, src, dst):
        '''Install a file using templater for "profile"'''
        self.log.dbg('generate template for {}'.format(src))
        content = templater.generate(src, profile)
        if content is None:
            self.log.err('generate from template \"{}\"'.format(src))
            return []
        if not os.path.exists(src):
            self.log.err('source dotfile does not exist: \"{}\"'.format(src))
            return []
        st = os.stat(src)
        ret = self._write(dst, content, st.st_mode)
        if ret < 0:
            self.log.err('installing \"{}\" to \"{}\"'.format(src, dst))
            return []
        if ret > 0:
            self.log.dbg('ignoring \"{}\", same content'.format(dst))
            return []
        if ret == 0:
            if not self.dry and not self.comparing:
                self.log.sub('copied \"{}\" to \"{}\"'.format(src, dst))
            return [(src, dst)]
        return []

    def _handle_dir(self, templater, profile, src, dst):
        '''Install a directory using templater for "profile"'''
        ret = []
        for entry in os.listdir(src):
            f = os.path.join(src, entry)
            if not os.path.isdir(f):
                res = self._handle_file(
                    templater, profile, f, os.path.join(dst, entry))
                ret.extend(res)
            else:
                res = self._handle_dir(
                    templater, profile, f, os.path.join(dst, entry))
                ret.extend(res)
        return ret

    def _fake_diff(self, dst, content):
        '''Fake diff by comparing file content with "content"'''
        cur = ''
        with open(dst, 'br') as f:
            cur = f.read()
        return cur == content

    def _write(self, dst, content, rights):
        '''Write file
        returns  0 for success,
                 1 when already exists
                -1 when error'''
        if self.dry:
            self.log.dry('would install {}'.format(dst))
            return 0
        if os.path.exists(dst):
            samerights = os.stat(dst).st_mode == rights
            if self.diff and self._fake_diff(dst, content) and samerights:
                self.log.dbg('{} is the same'.format(dst))
                return 1
            if self.safe and not self.log.ask('Overwrite \"{}\"'.format(dst)):
                self.log.warn('ignoring \"{}\", already present'.format(dst))
                return 1
        if self.backup and os.path.exists(dst):
            self._backup(dst)
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            self.log.err('creating directory for \"{}\"'.format(dst))
            return -1
        self.log.dbg('write content to {}'.format(dst))
        try:
            with open(dst, 'wb') as f:
                f.write(content)
        except NotADirectoryError as e:
            self.log.err('opening dest file: {}'.format(e))
            return -1
        os.chmod(dst, rights)
        return 0

    def _create_dirs(self, directory):
        '''mkdir -p "directory"'''
        if not self.create and not os.path.exists(directory):
            return False
        if os.path.exists(directory):
            return True
        self.log.dbg('mkdir -p {}'.format(directory))
        os.makedirs(directory)
        return os.path.exists(directory)

    def _backup(self, path):
        '''Backup the file'''
        if self.dry:
            return
        dst = path.rstrip(os.sep) + self.BACKUP_SUFFIX
        self.log.log('backup {} to {}'.format(path, dst))
        os.rename(path, dst)

    def _install_to_temp(self, templater, profile, src, dst, tmpdir):
        '''Install a dotfile to a tempdir for comparing'''
        sub = dst
        if dst[0] == os.sep:
            sub = dst[1:]
        tmpdst = os.path.join(tmpdir, sub)
        return self.install(templater, profile, src, tmpdst), tmpdst

    def compare(self, templater, tmpdir, profile, src, dst, opts=''):
        '''Compare temporary generated dotfile with local one'''
        self.comparing = True
        retval = False, ''
        drysaved = self.dry
        self.dry = False
        diffsaved = self.diff
        self.diff = False
        createsaved = self.create
        self.create = True
        src = os.path.expanduser(src)
        dst = os.path.expanduser(dst)
        self.log.dbg('comparing {} and {}'.format(src, dst))
        if not os.path.exists(dst):
            retval = False, '\"{}\" does not exist on local\n'.format(dst)
        else:
            ret, tmpdst = self._install_to_temp(templater,
                                                profile,
                                                src, dst,
                                                tmpdir)
            if ret:
                self.log.dbg('diffing {} and {}'.format(tmpdst, dst))
                diff = utils.diff(tmpdst, dst, raw=False, opts=opts)
                if diff == '':
                    retval = True, ''
                else:
                    retval = False, diff
        self.dry = drysaved
        self.diff = diffsaved
        self.comparing = False
        self.create = createsaved
        return retval
