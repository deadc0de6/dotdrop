"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

entry point
"""

import os
import sys

# local imports
from dotdrop.options import Options
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.installer import Installer
from dotdrop.updater import Updater
from dotdrop.comparator import Comparator
from dotdrop.dotfile import Dotfile
from dotdrop.config import Cfg
from dotdrop.utils import get_tmpdir, remove, strip_home, run
from dotdrop.linktypes import LinkTypes

LOG = Logger()
TRANS_SUFFIX = 'trans'

###########################################################
# entry point
###########################################################


def cmd_install(o):
    """install dotfiles for this profile"""
    dotfiles = o.dotfiles
    if o.install_keys:
        # filtered dotfiles to install
        dotfiles = [d for d in dotfiles if d.key in set(o.install_keys)]
    if not dotfiles:
        msg = 'no dotfile to install for this profile (\"{}\")'
        LOG.warn(msg.format(o.profile))
        return False

    t = Templategen(base=o.dotpath, variables=o.variables,
                    debug=o.debug)
    tmpdir = None
    if o.install_temporary:
        tmpdir = get_tmpdir()
    inst = Installer(create=o.create, backup=o.backup,
                     dry=o.dry, safe=o.safe,
                     base=o.dotpath, workdir=o.workdir,
                     diff=o.install_diff, debug=o.debug,
                     totemp=tmpdir,
                     showdiff=o.install_showdiff)
    installed = []
    for dotfile in dotfiles:
        preactions = []
        if not o.install_temporary and dotfile.actions \
                and Cfg.key_actions_pre in dotfile.actions:
            for action in dotfile.actions[Cfg.key_actions_pre]:
                preactions.append(action)
        if o.debug:
            LOG.dbg('installing {}'.format(dotfile))
        if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.PARENTS:
            r = inst.link(t, dotfile.src, dotfile.dst, actions=preactions)
        elif hasattr(dotfile, 'link') and dotfile.link == LinkTypes.CHILDREN:
            r = inst.linkall(t, dotfile.src, dotfile.dst, actions=preactions)
        else:
            src = dotfile.src
            tmp = None
            if dotfile.trans_r:
                tmp = apply_trans(o.dotpath, dotfile, debug=o.debug)
                if not tmp:
                    continue
                src = tmp
            r = inst.install(t, src, dotfile.dst, actions=preactions,
                             noempty=dotfile.noempty)
            if tmp:
                tmp = os.path.join(o.dotpath, tmp)
                if os.path.exists(tmp):
                    remove(tmp)
        if len(r) > 0:
            if not o.install_temporary and \
                    Cfg.key_actions_post in dotfile.actions:
                actions = dotfile.actions[Cfg.key_actions_post]
                # execute action
                for action in actions:
                    if o.dry:
                        LOG.dry('would execute action: {}'.format(action))
                    else:
                        if o.debug:
                            LOG.dbg('executing post action {}'.format(action))
                        action.execute()
        installed.extend(r)
    if o.install_temporary:
        LOG.log('\nInstalled to tmp \"{}\".'.format(tmpdir))
    LOG.log('\n{} dotfile(s) installed.'.format(len(installed)))
    return True


def cmd_compare(o, tmp):
    """compare dotfiles and return True if all identical"""
    dotfiles = o.dotfiles
    if dotfiles == []:
        msg = 'no dotfile defined for this profile (\"{}\")'
        LOG.warn(msg.format(o.profile))
        return True
    # compare only specific files
    same = True
    selected = dotfiles
    if o.compare_focus:
        selected = _select(o.compare_focus, dotfiles)

    if len(selected) < 1:
        return False

    t = Templategen(base=o.dotpath, variables=o.variables,
                    debug=o.debug)
    inst = Installer(create=o.create, backup=o.backup,
                     dry=o.dry, base=o.dotpath,
                     workdir=o.workdir, debug=o.debug)
    comp = Comparator(diffopts=o.compare_dopts, debug=o.debug)

    for dotfile in selected:
        if o.debug:
            LOG.dbg('comparing {}'.format(dotfile))
        src = dotfile.src
        if not os.path.lexists(os.path.expanduser(dotfile.dst)):
            line = '=> compare {}: \"{}\" does not exist on local'
            LOG.log(line.format(dotfile.key, dotfile.dst))
            same = False
            continue

        tmpsrc = None
        if dotfile.trans_r:
            # apply transformation
            tmpsrc = apply_trans(o.dotpath, dotfile, debug=o.debug)
            if not tmpsrc:
                # could not apply trans
                same = False
                continue
            src = tmpsrc
        # install dotfile to temporary dir
        ret, insttmp = inst.install_to_temp(t, tmp, src, dotfile.dst)
        if not ret:
            # failed to install to tmp
            same = False
            continue
        ignores = list(set(o.compare_ignore + dotfile.cmpignore))
        diff = comp.compare(insttmp, dotfile.dst, ignore=ignores)
        if tmpsrc:
            # clean tmp transformed dotfile if any
            tmpsrc = os.path.join(o.dotpath, tmpsrc)
            if os.path.exists(tmpsrc):
                remove(tmpsrc)
        if diff == '':
            if o.debug:
                line = '=> compare {}: diffing with \"{}\"'
                LOG.dbg(line.format(dotfile.key, dotfile.dst))
                LOG.dbg('same file')
        else:
            line = '=> compare {}: diffing with \"{}\"'
            LOG.log(line.format(dotfile.key, dotfile.dst))
            LOG.emph(diff)
            same = False

    return same


def cmd_update(o):
    """update the dotfile(s) from path(s) or key(s)"""
    ret = True
    paths = o.update_path
    iskey = o.update_iskey
    ignore = o.update_ignore
    showpatch = o.update_showpatch

    updater = Updater(o.dotpath, o.dotfiles, o.variables,
                      dry=o.dry, safe=o.safe, debug=o.debug,
                      ignore=ignore, showpatch=showpatch)
    if not iskey:
        # update paths
        if o.debug:
            LOG.dbg('update by paths: {}'.format(paths))
        for path in paths:
            if not updater.update_path(path):
                ret = False
    else:
        # update keys
        keys = paths
        if not keys:
            # if not provided, take all keys
            keys = [d.key for d in o.dotfiles]
        if o.debug:
            LOG.dbg('update by keys: {}'.format(keys))
        for key in keys:
            if not updater.update_key(key):
                ret = False
    return ret


def cmd_importer(o):
    """import dotfile(s) from paths"""
    ret = True
    cnt = 0
    paths = o.import_path
    for path in paths:
        if o.debug:
            LOG.dbg('trying to import {}'.format(path))
        if not os.path.lexists(path):
            LOG.err('\"{}\" does not exist, ignored!'.format(path))
            ret = False
            continue
        dst = path.rstrip(os.sep)
        dst = os.path.abspath(dst)
        src = strip_home(dst)
        strip = '.' + os.sep
        if o.keepdot:
            strip = os.sep
        src = src.lstrip(strip)

        # create a new dotfile
        dotfile = Dotfile('', dst, src)

        linktype = LinkTypes(o.link)

        if o.debug:
            LOG.dbg('new dotfile: {}'.format(dotfile))

        # prepare hierarchy for dotfile
        srcf = os.path.join(o.dotpath, src)
        if not os.path.exists(srcf):
            cmd = ['mkdir', '-p', '{}'.format(os.path.dirname(srcf))]
            if o.dry:
                LOG.dry('would run: {}'.format(' '.join(cmd)))
            else:
                r, _ = run(cmd, raw=False, debug=o.debug, checkerr=True)
                if not r:
                    LOG.err('importing \"{}\" failed!'.format(path))
                    ret = False
                    continue
            cmd = ['cp', '-R', '-L', dst, srcf]
            if o.dry:
                LOG.dry('would run: {}'.format(' '.join(cmd)))
                if linktype == LinkTypes.PARENTS:
                    LOG.dry('would symlink {} to {}'.format(srcf, dst))
            else:
                r, _ = run(cmd, raw=False, debug=o.debug, checkerr=True)
                if not r:
                    LOG.err('importing \"{}\" failed!'.format(path))
                    ret = False
                    continue
                if linktype == LinkTypes.PARENTS:
                    remove(dst)
                    os.symlink(srcf, dst)
        retconf, dotfile = o.conf.new(dotfile, o.profile,
                                      link=linktype, debug=o.debug)
        if retconf:
            LOG.sub('\"{}\" imported'.format(path))
            cnt += 1
        else:
            LOG.warn('\"{}\" ignored'.format(path))
    if o.dry:
        LOG.dry('new config file would be:')
        LOG.raw(o.conf.dump())
    else:
        o.conf.save()
    LOG.log('\n{} file(s) imported.'.format(cnt))
    return ret


def cmd_list_profiles(o):
    """list all profiles"""
    LOG.log('Available profile(s):')
    for p in o.profiles:
        LOG.sub(p)
    LOG.log('')


def cmd_list_files(o):
    """list all dotfiles for a specific profile"""
    if o.profile not in o.profiles:
        LOG.warn('unknown profile \"{}\"'.format(o.profile))
        return
    what = 'Dotfile(s)'
    if o.listfiles_templateonly:
        what = 'Template(s)'
    LOG.emph('{} for profile \"{}\"\n'.format(what, o.profile))
    for dotfile in o.dotfiles:
        if o.listfiles_templateonly:
            src = os.path.join(o.dotpath, dotfile.src)
            if not Templategen.is_template(src):
                continue
        LOG.log('{} (src: \"{}\", link: {})'.format(dotfile.key, dotfile.src,
                                                    dotfile.link.name.lower()))
        LOG.sub('{}'.format(dotfile.dst))
    LOG.log('')


def cmd_detail(o):
    """list details on all files for all dotfile entries"""
    if o.profile not in o.profiles:
        LOG.warn('unknown profile \"{}\"'.format(o.profile))
        return
    dotfiles = o.dotfiles
    if o.detail_keys:
        # filtered dotfiles to install
        dotfiles = [d for d in dotfiles if d.key in set(o.details_keys)]
    LOG.emph('dotfiles details for profile \"{}\":\n'.format(o.profile))
    for d in dotfiles:
        _detail(o.dotpath, d)
    LOG.log('')


###########################################################
# helpers
###########################################################


def _detail(dotpath, dotfile):
    """print details on all files under a dotfile entry"""
    LOG.log('{} (dst: \"{}\", link: {})'.format(dotfile.key, dotfile.dst,
                                                dotfile.link.name.lower()))
    path = os.path.join(dotpath, os.path.expanduser(dotfile.src))
    if not os.path.isdir(path):
        template = 'no'
        if Templategen.is_template(path):
            template = 'yes'
        LOG.sub('{} (template:{})'.format(path, template))
    else:
        for root, dir, files in os.walk(path):
            for f in files:
                p = os.path.join(root, f)
                template = 'no'
                if Templategen.is_template(p):
                    template = 'yes'
                LOG.sub('{} (template:{})'.format(p, template))


def _select(selections, dotfiles):
    selected = []
    for selection in selections:
        df = next(
            (x for x in dotfiles
                if os.path.expanduser(x.dst) == os.path.expanduser(selection)),
            None
        )
        if df:
            selected.append(df)
        else:
            LOG.err('no dotfile matches \"{}\"'.format(selection))
    return selected


def apply_trans(dotpath, dotfile, debug=False):
    """apply the read transformation to the dotfile
    return None if fails and new source if succeed"""
    src = dotfile.src
    new_src = '{}.{}'.format(src, TRANS_SUFFIX)
    trans = dotfile.trans_r
    if debug:
        LOG.dbg('executing transformation {}'.format(trans))
    s = os.path.join(dotpath, src)
    temp = os.path.join(dotpath, new_src)
    if not trans.transform(s, temp):
        msg = 'transformation \"{}\" failed for {}'
        LOG.err(msg.format(trans.key, dotfile.key))
        if new_src and os.path.exists(new_src):
            remove(new_src)
        return None
    return new_src


###########################################################
# main
###########################################################


def main():
    """entry point"""
    try:
        o = Options()
    except ValueError as e:
        LOG.err('Config format error: {}'.format(str(e)))
        return False

    ret = True
    try:

        if o.cmd_list:
            # list existing profiles
            if o.debug:
                LOG.dbg('running cmd: list')
            cmd_list_profiles(o)

        elif o.cmd_listfiles:
            # list files for selected profile
            if o.debug:
                LOG.dbg('running cmd: listfiles')
            cmd_list_files(o)

        elif o.cmd_install:
            # install the dotfiles stored in dotdrop
            if o.debug:
                LOG.dbg('running cmd: install')
            ret = cmd_install(o)

        elif o.cmd_compare:
            # compare local dotfiles with dotfiles stored in dotdrop
            if o.debug:
                LOG.dbg('running cmd: compare')
            tmp = get_tmpdir()
            ret = cmd_compare(o, tmp)
            # clean tmp directory
            remove(tmp)

        elif o.cmd_import:
            # import dotfile(s)
            if o.debug:
                LOG.dbg('running cmd: import')
            ret = cmd_importer(o)

        elif o.cmd_update:
            # update a dotfile
            if o.debug:
                LOG.dbg('running cmd: update')
            ret = cmd_update(o)

        elif o.cmd_detail:
            # detail files
            if o.debug:
                LOG.dbg('running cmd: update')
            cmd_detail(o)

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
