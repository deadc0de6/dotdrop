"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
handle the installation of dotfiles
"""

import os
import utils
from logger import Logger


class Installer:

    BACKUP_SUFFIX = '.dotdropbak'

    def __init__(self, base='.', create=True, backup=True,
                 dry=False, safe=False, quiet=False, diff=True):
        self.create = create
        self.backup = backup
        self.dry = dry
        self.safe = safe
        self.base = base
        self.quiet = quiet
        self.diff = diff
        self.comparing = False
        self.log = Logger()

    def install(self, templater, profile, src, dst):
        '''Install the dotfile for profile "profile"'''
        src = os.path.join(self.base, os.path.expanduser(src))
        dst = os.path.join(self.base, os.path.expanduser(dst))
        if os.path.isdir(src):
            return self._handle_dir(templater, profile, src, dst)
        return self._handle_file(templater, profile, src, dst)

    def link(self, src, dst):
        '''Sets src as the link target of dst'''
        src = os.path.join(self.base, os.path.expanduser(src))
        dst = os.path.join(self.base, os.path.expanduser(dst))
        if os.path.exists(dst):
            if os.path.realpath(dst) == os.path.realpath(src):
                self.log.sub('ignoring "%s", link exists' % dst)
                return []
            if self.dry:
                self.log.dry('would remove %s and link it to %s'
                             % (dst, src))
                return []
            if self.safe and \
                    not self.log.ask('Remove "%s" for link creation?' % dst):
                self.log.warn('ignoring "%s", link was not created' % dst)
                return []
            try:
                utils.remove(dst)
            except OSError:
                self.log.err('something went wrong with %s' % src)
                return []
        if self.dry:
            self.log.dry('would link %s to %s' % (dst, src))
            return []
        os.symlink(src, dst)
        self.log.sub('linked %s to %s' % (dst, src))
        # Follows original developer's behavior
        return [(src, dst)]

    def _handle_file(self, templater, profile, src, dst):
        '''Install a file using templater for "profile"'''
        content = templater.generate(src, profile)
        if content is None:
            self.log.err('generate from template \"%s\"' % (src))
            return []
        if not os.path.exists(src):
            self.log.err('installing %s to %s' % (src, dst))
            return []
        st = os.stat(src)
        ret = self._write(dst, content, st.st_mode)
        if ret < 0:
            self.log.err('installing %s to %s' % (src, dst))
            return []
        if ret > 0:
            if not self.quiet:
                self.log.sub('ignoring \"%s\", same content' % (dst))
            return []
        if ret == 0:
            if not self.quiet and not self.dry and not self.comparing:
                self.log.sub('copied %s to %s' % (src, dst))
            return [(src, dst)]
        return []

    def _handle_dir(self, templater, profile, src, dst):
        '''Install a folder using templater for "profile"'''
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
        '''Write file'''
        if self.dry:
            self.log.dry('would install %s' % (dst))
            return 0
        if os.path.exists(dst):
            if self.diff and self._fake_diff(dst, content):
                return 1
            if self.safe and not self.log.ask('Overwrite \"%s\"' % (dst)):
                self.log.warn('ignoring \"%s\", already present' % (dst))
                return 1
        if self.backup and os.path.exists(dst):
            self._backup(dst)
        base = os.path.dirname(dst)
        if not self._create_dirs(base):
            self.log.err('creating directory for %s' % (dst))
            return -1
        with open(dst, 'wb') as f:
            f.write(content)
        os.chmod(dst, rights)
        return 0

    def _create_dirs(self, folder):
        '''mkdir -p "folder"'''
        if not self.create and not os.path.exists(folder):
            return False
        if os.path.exists(folder):
            return True
        os.makedirs(folder)
        return os.path.exists(folder)

    def _backup(self, path):
        '''Backup the file'''
        if self.dry:
            return
        dst = path.rstrip(os.sep) + self.BACKUP_SUFFIX
        self.log.log('backup %s to %s' % (path, dst))
        os.rename(path, dst)

    def _install_to_temp(self, templater, profile, src, dst, tmpfolder):
        '''Install a dotfile to a tempfolder for comparing'''
        sub = dst
        if dst[0] == os.sep:
            sub = dst[1:]
        tmpdst = os.path.join(tmpfolder, sub)
        return self.install(templater, profile, src, tmpdst), tmpdst

    def compare(self, templater, tmpfolder, profile, src, dst):
        '''Compare temporary generated dotfile with local one'''
        self.comparing = True
        retval = False, ''
        drysaved = self.dry
        self.dry = False
        diffsaved = self.diff
        self.diff = False
        src = os.path.expanduser(src)
        dst = os.path.expanduser(dst)
        if not os.path.exists(dst):
            retval = False, '\"%s\" does not exist on local\n' % (dst)
        else:
            ret, tmpdst = self._install_to_temp(templater,
                                                profile,
                                                src, dst,
                                                tmpfolder)
            if ret:
                diff = utils.diff(tmpdst, dst, log=False, raw=False)
                if diff == '':
                    retval = True, ''
                else:
                    retval = False, diff
        self.dry = drysaved
        self.diff = diffsaved
        self.comparing = False
        return retval
