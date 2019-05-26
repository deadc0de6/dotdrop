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
from dotdrop.utils import get_tmpdir, remove, strip_home, run
from dotdrop.linktypes import LinkTypes

LOG = Logger()
TRANS_SUFFIX = 'trans'

###########################################################
# entry point
###########################################################


def action_executor(o, dotfile, actions, defactions, templater, post=False):
    """closure for action execution"""
    def execute():
        """
        execute actions and return
        True, None if ok
        False, errstring if issue
        """
        s = 'pre' if not post else 'post'

        # execute default actions
        for action in defactions:
            if o.dry:
                LOG.dry('would execute def-{}-action: {}'.format(s,
                                                                 action))
                continue
            if o.debug:
                LOG.dbg('executing def-{}-action {}'.format(s, action))
            ret = action.execute(templater=templater)
            if not ret:
                err = 'def-{}-action \"{}\" failed'.format(s, action.key)
                LOG.err(err)
                return False, err

        # execute actions
        for action in actions:
            if o.dry:
                LOG.dry('would execute {}-action: {}'.format(s, action))
                continue
            if o.debug:
                LOG.dbg('executing {}-action {}'.format(s, action))
            ret = action.execute(templater=templater)
            if not ret:
                err = '{}-action \"{}\" failed'.format(s, action.key)
                LOG.err(err)
                return False, err
        return True, None
    return execute


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
                     showdiff=o.install_showdiff,
                     backup_suffix=o.install_backup_suffix)
    installed = 0
    tvars = t.add_tmp_vars()
    for dotfile in dotfiles:
        # add dotfile variables
        t.restore_vars(tvars)
        newvars = dotfile.get_vars()
        t.add_tmp_vars(newvars=newvars)

        preactions = []
        if not o.install_temporary and dotfile.actions:
            preactions = [a for a in dotfile.actions if a.is_pre()]
        defactions = [a for a in o.install_default_actions if a.is_pre()]
        pre_actions_exec = action_executor(o, dotfile, preactions,
                                           defactions, t, post=False)

        if o.debug:
            LOG.dbg('installing {}'.format(dotfile))
        if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.LINK:
            r = inst.link(t, dotfile.src, dotfile.dst,
                          actionexec=pre_actions_exec)
        elif hasattr(dotfile, 'link') and \
                dotfile.link == LinkTypes.LINK_CHILDREN:
            r = inst.link_children(t, dotfile.src, dotfile.dst,
                                   actionexec=pre_actions_exec)
        else:
            src = dotfile.src
            tmp = None
            if dotfile.trans_r:
                tmp = apply_trans(o.dotpath, dotfile, debug=o.debug)
                if not tmp:
                    continue
                src = tmp
            r, err = inst.install(t, src, dotfile.dst,
                                  actionexec=pre_actions_exec,
                                  noempty=dotfile.noempty)
            if tmp:
                tmp = os.path.join(o.dotpath, tmp)
                if os.path.exists(tmp):
                    remove(tmp)
        if r:
            if not o.install_temporary:
                defactions = [a for a in o.install_default_actions
                              if not a.is_pre()]
                postactions = [a for a in dotfile.actions if not a.is_pre()]
                post_actions_exec = action_executor(o, dotfile, postactions,
                                                    defactions, t, post=True)
                post_actions_exec()
            installed += 1
        elif not r and err:
            LOG.err('installing \"{}\" failed: {}'.format(dotfile.key, err))
    if o.install_temporary:
        LOG.log('\ninstalled to tmp \"{}\".'.format(tmpdir))
    LOG.log('\n{} dotfile(s) installed.'.format(installed))
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
                     workdir=o.workdir, debug=o.debug,
                     backup_suffix=o.install_backup_suffix)
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

        # is a symlink pointing to itself
        asrc = os.path.join(o.dotpath, os.path.expanduser(src))
        adst = os.path.expanduser(dotfile.dst)
        if os.path.samefile(asrc, adst):
            if o.debug:
                line = '=> compare {}: diffing with \"{}\"'
                LOG.dbg(line.format(dotfile.key, dotfile.dst))
                LOG.dbg('points to itself')
            continue

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

    if not paths:
        # update the entire profile
        if iskey:
            paths = [d.key for d in o.dotfiles]
        else:
            paths = [d.dst for d in o.dotfiles]
        msg = 'Update all dotfiles for profile \"{}\"'.format(o.profile)
        if o.safe and not LOG.ask(msg):
            return False

    if not paths:
        LOG.log('no dotfile to update')
        return True
    if o.debug:
        LOG.dbg('dotfile to update: {}'.format(paths))

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
        if not os.path.exists(path):
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

        # set the link attribute
        linktype = o.import_link
        if linktype == LinkTypes.LINK_CHILDREN and \
                not os.path.isdir(path):
            LOG.err('importing \"{}\" failed!'.format(path))
            ret = False
            continue

        if o.debug:
            LOG.dbg('new dotfile: src:{} dst:{}'.format(src, dst))

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
            else:
                r, _ = run(cmd, raw=False, debug=o.debug, checkerr=True)
                if not r:
                    LOG.err('importing \"{}\" failed!'.format(path))
                    ret = False
                    continue
        retconf, dotfile = o.conf.new(src, dst, o.profile,
                                      linktype, debug=o.debug)
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
    if o.debug:
        LOG.dbg('new config file is:')
        LOG.raw(o.conf.dump())
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
    if o.profile not in [x.key for x in o.profiles]:
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
    if o.profile not in [x.key for x in o.profiles]:
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
        LOG.err('Config error: {}'.format(str(e)))
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
                LOG.dbg('running cmd: detail')
            cmd_detail(o)

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    if ret and o.conf.save():
        LOG.log('config file updated')

    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
