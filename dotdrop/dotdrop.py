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
from dotdrop.utils import get_tmpdir, remove, strip_home, \
    run, uniq_list, patch_ignores
from dotdrop.linktypes import LinkTypes
from dotdrop.exceptions import YamlException

LOG = Logger()
TRANS_SUFFIX = 'trans'

###########################################################
# entry point
###########################################################


def action_executor(o, actions, defactions, templater, post=False):
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
            ret = action.execute(templater=templater, debug=o.debug)
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
            ret = action.execute(templater=templater, debug=o.debug)
            if not ret:
                err = '{}-action \"{}\" failed'.format(s, action.key)
                LOG.err(err)
                return False, err
        return True, None
    return execute


def cmd_install(o):
    """install dotfiles for this profile"""
    dotfiles = o.dotfiles
    prof = o.conf.get_profile(o.profile)
    pro_pre_actions = prof.get_pre_actions() if prof else []
    pro_post_actions = prof.get_post_actions() if prof else []

    if o.install_keys:
        # filtered dotfiles to install
        uniq = uniq_list(o.install_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
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

    # execute profile pre-action
    if o.debug:
        LOG.dbg('execute profile pre actions')
    ret, err = action_executor(o, pro_pre_actions, [], t, post=False)()
    if not ret:
        return False

    # install each dotfile
    for dotfile in dotfiles:
        # add dotfile variables
        t.restore_vars(tvars)
        newvars = dotfile.get_dotfile_variables()
        t.add_tmp_vars(newvars=newvars)

        preactions = []
        if not o.install_temporary:
            preactions.extend(dotfile.get_pre_actions())
        defactions = o.install_default_actions_pre
        pre_actions_exec = action_executor(o, preactions, defactions,
                                           t, post=False)

        if o.debug:
            LOG.dbg('installing {}'.format(dotfile))
        if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.LINK:
            r, err = inst.link(t, dotfile.src, dotfile.dst,
                               actionexec=pre_actions_exec)
        elif hasattr(dotfile, 'link') and \
                dotfile.link == LinkTypes.LINK_CHILDREN:
            r, err = inst.link_children(t, dotfile.src, dotfile.dst,
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
            # dotfile was installed
            if not o.install_temporary:
                defactions = o.install_default_actions_post
                postactions = dotfile.get_post_actions()
                post_actions_exec = action_executor(o, postactions, defactions,
                                                    t, post=True)
                post_actions_exec()
            installed += 1
        elif not r:
            # dotfile was NOT installed
            if o.install_force_action:
                # pre-actions
                if o.debug:
                    LOG.dbg('force pre action execution ...')
                pre_actions_exec()
                # post-actions
                if o.debug:
                    LOG.dbg('force post action execution ...')
                postactions = dotfile.get_post_actions()
                post_actions_exec = action_executor(o, postactions, defactions,
                                                    t, post=True)
                post_actions_exec()
            if err:
                LOG.err('installing \"{}\" failed: {}'.format(dotfile.key,
                                                              err))

    # execute profile post-action
    if installed > 0 or o.install_force_action:
        if o.debug:
            LOG.dbg('execute profile post actions')
        ret, err = action_executor(o, pro_post_actions, [], t, post=False)()
        if not ret:
            return False

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
            if o.debug:
                LOG.dbg('applying transformation before comparing')
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
        ignores = patch_ignores(ignores, dotfile.dst, debug=o.debug)
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

    updater = Updater(o.dotpath, o.variables,
                      o.conf.get_dotfile,
                      o.conf.get_dotfile_by_dst,
                      o.conf.path_to_dotfile_dst,
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
        overwrite = not os.path.exists(srcf)
        if os.path.exists(srcf):
            overwrite = True
            if o.safe:
                c = Comparator(debug=o.debug)
                diff = c.compare(srcf, dst)
                if diff != '':
                    # files are different, dunno what to do
                    LOG.log('diff \"{}\" VS \"{}\"'.format(dst, srcf))
                    LOG.emph(diff)
                    # ask user
                    msg = 'Dotfile \"{}\" already exists, overwrite?'
                    overwrite = LOG.ask(msg.format(srcf))

        if o.debug:
            LOG.dbg('will overwrite: {}'.format(overwrite))
        if overwrite:
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
        retconf = o.conf.new(src, dst, linktype, o.profile)
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
    if o.profile not in [p.key for p in o.profiles]:
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
    if o.profile not in [p.key for p in o.profiles]:
        LOG.warn('unknown profile \"{}\"'.format(o.profile))
        return
    dotfiles = o.dotfiles
    if o.detail_keys:
        # filtered dotfiles to install
        uniq = uniq_list(o.details_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    LOG.emph('dotfiles details for profile \"{}\":\n'.format(o.profile))
    for d in dotfiles:
        _detail(o.dotpath, d)
    LOG.log('')


def cmd_remove(o):
    """remove dotfile from dotpath and from config"""
    paths = o.remove_path
    iskey = o.remove_iskey

    if not paths:
        LOG.log('no dotfile to remove')
        return False
    if o.debug:
        LOG.dbg('dotfile(s) to remove: {}'.format(','.join(paths)))

    removed = []
    for key in paths:
        if not iskey:
            # by path
            dotfile = o.conf.get_dotfile_by_dst(key)
            if not dotfile:
                LOG.warn('{} ignored, does not exist'.format(key))
                continue
            k = dotfile.key
        else:
            # by key
            dotfile = o.conf.get_dotfile(key)
            if not dotfile:
                LOG.warn('{} ignored, does not exist'.format(key))
                continue
            k = key

        # ignore if uses any type of link
        if dotfile.link != LinkTypes.NOLINK:
            LOG.warn('dotfile uses link, remove manually')
            continue

        if o.debug:
            LOG.dbg('removing {}'.format(key))

        # make sure is part of the profile
        if dotfile.key not in [d.key for d in o.dotfiles]:
            LOG.warn('{} ignored, not associated to this profile'.format(key))
            continue
        profiles = o.conf.get_profiles_by_dotfile_key(k)
        pkeys = ','.join([p.key for p in profiles])
        if o.dry:
            LOG.dry('would remove {} from {}'.format(dotfile, pkeys))
            continue
        msg = 'Remove \"{}\" from all these profiles: {}'.format(k, pkeys)
        if o.safe and not LOG.ask(msg):
            return False
        if o.debug:
            LOG.dbg('remove dotfile: {}'.format(dotfile))

        for profile in profiles:
            if not o.conf.del_dotfile_from_profile(dotfile, profile):
                return False
        if not o.conf.del_dotfile(dotfile):
            return False

        # remove dotfile from dotpath
        dtpath = os.path.join(o.dotpath, dotfile.src)
        remove(dtpath)
        removed.append(dotfile.key)

    if o.dry:
        LOG.dry('new config file would be:')
        LOG.raw(o.conf.dump())
    else:
        o.conf.save()
    if removed:
        LOG.log('\ndotfile(s) removed: {}'.format(','.join(removed)))
    else:
        LOG.log('\nno dotfile removed')
    return True


###########################################################
# helpers
###########################################################


def _detail(dotpath, dotfile):
    """display details on all files under a dotfile entry"""
    LOG.log('{} (dst: \"{}\", link: {})'.format(dotfile.key, dotfile.dst,
                                                dotfile.link.name.lower()))
    path = os.path.join(dotpath, os.path.expanduser(dotfile.src))
    if not os.path.isdir(path):
        template = 'no'
        if Templategen.is_template(path):
            template = 'yes'
        LOG.sub('{} (template:{})'.format(path, template))
    else:
        for root, _, files in os.walk(path):
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
    """
    apply the read transformation to the dotfile
    return None if fails and new source if succeed
    """
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
    except YamlException as e:
        LOG.err('config file error: {}'.format(str(e)))
        return False

    if o.debug:
        LOG.dbg('\n\n')

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

        elif o.cmd_remove:
            # remove dotfile
            if o.debug:
                LOG.dbg('running cmd: remove')
            cmd_remove(o)

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
